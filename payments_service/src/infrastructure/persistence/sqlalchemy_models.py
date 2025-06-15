from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
import datetime

from src.infrastructure.persistence.database import Base
from src.domain.value_objects import MessageStatus

class AccountModel(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    balance = Column(Numeric(10, 2), default=0.00)

class InboxMessageModel(Base):
    __tablename__ = "inbox_messages"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer)
    order_id = Column(String, index=True)
    amount = Column(Numeric(10, 2))
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

class OutboxMessageModel(Base):
    __tablename__ = "outbox_messages"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer)
    order_id = Column(String)
    payment_status = Column(String) # FINISHED or CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    processed = Column(Boolean, default=False) 