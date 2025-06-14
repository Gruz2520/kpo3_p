from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
import datetime

from src.domain.entities import Order
from src.domain.value_objects import OrderStatus
from src.domain.repositories import IOrderRepository, IOutboxMessageRepository, IPaymentStatusInboxRepository
from src.infrastructure.persistence.sqlalchemy_models import OrderModel, OutboxMessageModel, PaymentStatusInboxModel

class OrderRepository(IOrderRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: str) -> Optional[Order]:
        order_model = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if order_model:
            return Order(
                id=order_model.id,
                user_id=order_model.user_id,
                amount=order_model.amount,
                description=order_model.description,
                status=order_model.status.value,
                created_at=order_model.created_at,
                updated_at=order_model.updated_at
            )
        return None

    def get_by_user_id(self, user_id: int) -> List[Order]:
        order_models = self.db.query(OrderModel).filter(OrderModel.user_id == user_id).all()
        return [
            Order(
                id=order_model.id,
                user_id=order_model.user_id,
                amount=order_model.amount,
                description=order_model.description,
                status=order_model.status.value,
                created_at=order_model.created_at,
                updated_at=order_model.updated_at
            )
            for order_model in order_models
        ]

    def add(self, order: Order):
        order_model = OrderModel(
            id=order.id,
            user_id=order.user_id,
            amount=order.amount,
            description=order.description,
            status=OrderStatus[order.status] # Convert string back to Enum for storage
        )
        self.db.add(order_model)
        self.db.flush() # To get the generated ID if not already set

    def update(self, order: Order):
        order_model = self.db.query(OrderModel).filter(OrderModel.id == order.id).first()
        if order_model:
            order_model.user_id = order.user_id
            order_model.amount = order.amount
            order_model.description = order.description
            order_model.status = OrderStatus[order.status] # Convert string back to Enum for storage
            order_model.updated_at = order.updated_at
            self.db.add(order_model)

class OutboxMessageRepository(IOutboxMessageRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_unprocessed(self, limit: int = 10) -> List[dict]:
        messages = self.db.query(OutboxMessageModel).filter(OutboxMessageModel.processed == False).limit(limit).all()
        return [
            {
                "id": msg.id,
                "order_id": msg.order_id,
                "user_id": msg.user_id,
                "amount": msg.amount,
                "message_type": msg.message_type,
                "payload": msg.payload,
                "created_at": msg.created_at
            }
            for msg in messages
        ]

    def add(self, order_id: str, user_id: int, amount: Decimal, message_type: str, payload: str):
        outbox_message_model = OutboxMessageModel(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            message_type=message_type,
            payload=payload,
            created_at=datetime.datetime.utcnow()
        )
        self.db.add(outbox_message_model)
        self.db.flush() # To get the generated ID

    def mark_as_processed(self, message_id: str):
        message_model = self.db.query(OutboxMessageModel).filter(OutboxMessageModel.id == message_id).first()
        if message_model:
            message_model.processed = True
            message_model.sent_at = datetime.datetime.utcnow()
            self.db.add(message_model)

# IPaymentStatusInboxRepository is an ABC, not to be instantiated directly

class PaymentStatusInboxRepository(IPaymentStatusInboxRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_message_id(self, message_id: str) -> Optional[dict]:
        message_model = self.db.query(PaymentStatusInboxModel).filter(PaymentStatusInboxModel.id == message_id).first()
        if message_model:
            return {
                "id": message_model.id,
                "order_id": message_model.order_id,
                "payment_status": message_model.payment_status,
                "created_at": message_model.created_at,
                "processed_at": message_model.processed_at,
                "processed": message_model.processed
            }
        return None

    def add(self, message_id: str, order_id: str, payment_status: str, processed: bool):
        inbox_message_model = PaymentStatusInboxModel(
            id=message_id,
            order_id=order_id,
            payment_status=payment_status,
            processed=processed,
            created_at=datetime.datetime.utcnow()
        )
        self.db.add(inbox_message_model)
        self.db.flush() # To ensure ID is set for the message

    def mark_as_processed(self, message_id: str):
        message_model = self.db.query(PaymentStatusInboxModel).filter(PaymentStatusInboxModel.id == message_id).first()
        if message_model:
            message_model.processed = True
            message_model.processed_at = datetime.datetime.utcnow()
            self.db.add(message_model) 