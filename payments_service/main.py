import sys
import os
import uuid

# Add the current directory (payments_service) to sys.path to allow absolute imports from src
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import datetime
import enum
import asyncio
import json
import httpx

from src.infrastructure.persistence.database import Base, engine, get_db, SessionLocal
from src.infrastructure.api.routers import router as payments_router
from src.infrastructure.persistence.repositories_impl import OutboxMessageRepository
from src.infrastructure.messaging.outbox_publisher import HTTPOutboxPublisher
from src.application.use_cases import PublishOutboxMessagesUseCase

# Orders Service URL for Outbox messages
ORDERS_SERVICE_URL = "http://127.0.0.1:8002"

# Database Configuration
DATABASE_URL = "sqlite:///./payments.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Models
class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    balance = Column(Numeric(10, 2), default=0.00)

class MessageStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class InboxMessage(Base):
    __tablename__ = "inbox_messages"
    id = Column(String, primary_key=True, index=True) # Message ID for idempotency
    user_id = Column(Integer)
    order_id = Column(String, index=True)
    amount = Column(Numeric(10, 2))
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

class OutboxMessage(Base):
    __tablename__ = "outbox_messages"
    id = Column(String, primary_key=True, index=True) # Unique message ID
    user_id = Column(Integer)
    order_id = Column(String)
    payment_status = Column(String) # FINISHED or CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    processed = Column(Boolean, default=False)

# Create Database Tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models for Request/Response
class CreateAccountRequest(BaseModel):
    user_id: int

class TopUpAccountRequest(BaseModel):
    user_id: int
    amount: float

class AccountBalanceResponse(BaseModel):
    user_id: int
    balance: float

class PaymentProcessRequest(BaseModel):
    user_id: int
    order_id: str
    amount: float
    message_id: str # For idempotency

# FastAPI App
app = FastAPI(title="Payments Service")

app.include_router(payments_router)

@app.post("/accounts", summary="Создать счёт для пользователя")
def create_account(request: CreateAccountRequest, db: Session = Depends(get_db)):
    db_account = db.query(Account).filter(Account.user_id == request.user_id).first()
    if db_account:
        raise HTTPException(status_code=400, detail="Счёт для данного пользователя уже существует")
    
    new_account = Account(user_id=request.user_id, balance=0.00)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return {"message": "Счёт успешно создан", "account_id": new_account.id, "user_id": new_account.user_id, "balance": new_account.balance}

@app.post("/accounts/top-up", summary="Пополнить счёт пользователя")
def top_up_account(request: TopUpAccountRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.user_id == request.user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма пополнения должна быть положительной")
    
    # Атомарное обновление баланса
    # В реальной системе можно использовать lock или Compare-and-Swap
    account.balance += request.amount
    db.commit()
    db.refresh(account)
    return {"message": "Счёт успешно пополнен", "user_id": account.user_id, "new_balance": account.balance}

@app.get("/accounts/{user_id}/balance", response_model=AccountBalanceResponse, summary="Просмотреть баланс счёта")
def get_account_balance(user_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    return AccountBalanceResponse(user_id=account.user_id, balance=float(account.balance))

@app.post("/payments/process", summary="Обработка платежа (Transactional Inbox)")
def process_payment(request: PaymentProcessRequest, db: Session = Depends(get_db)):
    # Проверка на идемпотентность: ищем сообщение по message_id в Inbox
    existing_message = db.query(InboxMessage).filter(InboxMessage.id == request.message_id).first()
    if existing_message and existing_message.status == MessageStatus.PROCESSED:
        return {"message": "Платёж уже обработан (идемпотентность)"}
    
    if existing_message and existing_message.status == MessageStatus.PENDING:
        return {"message": "Платёж уже находится в обработке"}

    # Сохраняем входящее сообщение в Inbox (Transaction Inbox Part 1)
    inbox_message = InboxMessage(
        id=request.message_id,
        user_id=request.user_id,
        order_id=request.order_id,
        amount=request.amount,
        status=MessageStatus.PENDING
    )
    db.add(inbox_message)
    db.commit() # Отдельный коммит для InboxMessage, чтобы зафиксировать его статус PENDING

    try:
        account = db.query(Account).filter(Account.user_id == request.user_id).first()
        if not account:
            # Создаем счет, если его нет (fail событие)
            new_account = Account(user_id=request.user_id, balance=0.00)
            db.add(new_account)
            db.commit()
            db.refresh(new_account)
            account = new_account # Обновляем account
            # Регистрируем ошибку и отправляем OUTBOX сообщение
            payment_status = "CANCELLED"
            message = "Счёт пользователя не существовал, создан новый счёт с нулевым балансом."
        elif account.balance < request.amount:
            # Недостаточно средств (fail событие)
            payment_status = "CANCELLED"
            message = "Недостаточно средств на счёте."
        else:
            # Списание средств (success событие)
            account.balance -= request.amount
            payment_status = "FINISHED"
            message = "Платёж успешно выполнен."
        
        # Обновляем статус InboxMessage и добавляем OutboxMessage в рамках одной транзакции
        inbox_message.status = MessageStatus.PROCESSED
        inbox_message.processed_at = datetime.datetime.utcnow()
        
        outbox_message = OutboxMessage(
            id=str(uuid.uuid4()), # Уникальный ID для исходящего сообщения
            user_id=request.user_id,
            order_id=request.order_id,
            payment_status=payment_status
        )
        db.add(outbox_message)
        
        db.commit() # Коммит всей транзакции: обновление счета, статуса InboxMessage, добавление OutboxMessage
        
        return {"message": message, "order_id": request.order_id, "payment_status": payment_status}

    except Exception as e:
        db.rollback()
        # Отмечаем сообщение как FAILED, если произошла ошибка
        inbox_message.status = MessageStatus.FAILED
        inbox_message.processed_at = datetime.datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=f"Ошибка обработки платежа: {str(e)}")

# Background task for publishing Outbox messages
async def start_outbox_publisher():
    http_client = httpx.AsyncClient()
    while True:
        db = SessionLocal()
        try:
            outbox_repo = OutboxMessageRepository(db)
            publisher = HTTPOutboxPublisher(http_client, ORDERS_SERVICE_URL)
            use_case = PublishOutboxMessagesUseCase(outbox_repo, publisher)
            await use_case.execute()
            db.commit() # Сохраняем изменения в базе данных
        except Exception as e:
            print(f"Ошибка при публикации Outbox-сообщений: {e}")
        finally:
            db.close()
        await asyncio.sleep(5) # Проверять каждые 5 секунд

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_outbox_publisher())

@app.on_event("shutdown")
async def shutdown_event():
    # Закрытие HTTP клиента, если он не закрывается автоматически
    pass # httpx.AsyncClient() as client: closes automatically 