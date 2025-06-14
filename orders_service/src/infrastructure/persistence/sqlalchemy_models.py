from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Boolean
import datetime
import uuid

from src.infrastructure.persistence.database import Base
from src.domain.value_objects import OrderStatus

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, index=True)
    amount = Column(Numeric(10, 2))
    description = Column(String)
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class OutboxMessageModel(Base):
    __tablename__ = "outbox_messages"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, unique=True, index=True)
    user_id = Column(Integer)
    amount = Column(Numeric(10, 2))
    message_type = Column(String) # e.g., 'payment_request'
    payload = Column(String) # JSON string of the message content
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    processed = Column(Boolean, default=False)

class PaymentStatusInboxModel(Base):
    __tablename__ = "payment_status_inbox"
    id = Column(String, primary_key=True, index=True) # Message ID for idempotency
    order_id = Column(String, index=True)
    payment_status = Column(String) # FINISHED or CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processed = Column(Boolean, default=False) 