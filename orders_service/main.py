from __future__ import annotations
import sys
import os

# Add the current directory (orders_service) to sys.path to allow absolute imports from src
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import datetime
import enum
import uuid
import httpx
import asyncio
import json
from typing import List
from fastapi import status

from src.infrastructure.persistence.database import Base, engine, SessionLocal
from src.infrastructure.api.routers import router as orders_router
from src.infrastructure.persistence.repositories_impl import OutboxMessageRepository
from src.infrastructure.messaging.outbox_publisher import HTTPOutboxPublisher
from src.application.use_cases import PublishOutboxMessagesUseCase, CreateOrderUseCase, GetUserOrdersUseCase, GetOrderStatusUseCase, UpdateOrderPaymentStatusUseCase
from src.domain.value_objects import OrderStatus
from src.application.dtos import CreateOrderRequest, OrderResponse, PaymentStatusUpdateRequest

PAYMENTS_SERVICE_URL = "http://payments_service:8001"

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Orders Service")

from decimal import Decimal
app.json_encoders = {
    Decimal: float
}

app.include_router(orders_router)

async def start_outbox_publisher():
    http_client = httpx.AsyncClient()
    while True:
        db = SessionLocal()
        try:
            outbox_repo = OutboxMessageRepository(db)
            publisher = HTTPOutboxPublisher(http_client, PAYMENTS_SERVICE_URL)
            use_case = PublishOutboxMessagesUseCase(outbox_repo, publisher)
            await use_case.execute()
            db.commit()
        except Exception as e:
            print(f"Ошибка при публикации Outbox-сообщений: {e}")
        finally:
            db.close()
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_outbox_publisher())

@app.on_event("shutdown")
async def shutdown_event():
    pass

@app.get("/health")
async def health_check():
    return {"status": "Orders Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 