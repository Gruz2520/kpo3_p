from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
import datetime

from src.domain.entities import Account
from src.domain.value_objects import MessageStatus
from src.domain.repositories import IAccountRepository, IInboxMessageRepository, IOutboxMessageRepository
from src.infrastructure.persistence.sqlalchemy_models import AccountModel, InboxMessageModel, OutboxMessageModel

class AccountRepository(IAccountRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Optional[Account]:
        account_model = self.db.query(AccountModel).filter(AccountModel.user_id == user_id).first()
        if account_model:
            return Account(
                id=account_model.id,
                user_id=account_model.user_id,
                balance=account_model.balance
            )
        return None

    def add(self, account: Account):
        account_model = AccountModel(
            user_id=account.user_id,
            balance=account.balance
        )
        self.db.add(account_model)
        self.db.flush() # To get the generated ID
        account.id = account_model.id # Update the domain entity with the generated ID
        # db.commit() will be handled by the session outside the repo

    def update(self, account: Account):
        account_model = self.db.query(AccountModel).filter(AccountModel.id == account.id).first()
        if account_model:
            account_model.balance = account.balance
            self.db.add(account_model)
            # db.commit() will be handled by the session outside the repo

    def save(self, account: Account):
        # This method is for either adding a new account or updating an existing one
        # In SQLAlchemy, you generally add if new, merge if exists, then commit.
        # For simplicity, we'll assume add/update covers this for now.
        existing_account_model = self.db.query(AccountModel).filter(AccountModel.user_id == account.user_id).first()
        if existing_account_model:
            existing_account_model.balance = account.balance
            self.db.add(existing_account_model)
            account.id = existing_account_model.id # Ensure domain entity ID is updated
        else:
            self.add(account)
        self.db.flush()

class InboxMessageRepository(IInboxMessageRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, message_id: str) -> Optional[dict]:
        message_model = self.db.query(InboxMessageModel).filter(InboxMessageModel.id == message_id).first()
        if message_model:
            return {
                "id": message_model.id,
                "user_id": message_model.user_id,
                "order_id": message_model.order_id,
                "amount": message_model.amount,
                "status": message_model.status.value, # Convert Enum to string
                "created_at": message_model.created_at,
                "processed_at": message_model.processed_at
            }
        return None

    def get_by_order_id(self, order_id: str) -> Optional[dict]:
        message_model = self.db.query(InboxMessageModel).filter(InboxMessageModel.order_id == order_id).first()
        if message_model:
            return {
                "id": message_model.id,
                "user_id": message_model.user_id,
                "order_id": message_model.order_id,
                "amount": message_model.amount,
                "status": message_model.status.value, # Convert Enum to string
                "created_at": message_model.created_at,
                "processed_at": message_model.processed_at
            }
        return None

    def add(self, message_id: str, user_id: int, order_id: str, amount: Decimal, status: MessageStatus):
        inbox_message_model = InboxMessageModel(
            id=message_id,
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            status=status,
            created_at=datetime.datetime.utcnow()
        )
        self.db.add(inbox_message_model)
        # db.commit() will be handled by the session outside the repo

    def update_status(self, message_id: str, status: MessageStatus):
        message_model = self.db.query(InboxMessageModel).filter(InboxMessageModel.id == message_id).first()
        if message_model:
            message_model.status = status
            message_model.processed_at = datetime.datetime.utcnow()
            self.db.add(message_model)
            # db.commit() will be handled by the session outside the repo

class OutboxMessageRepository(IOutboxMessageRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_unprocessed(self, limit: int = 10) -> List[dict]:
        messages = self.db.query(OutboxMessageModel).filter(OutboxMessageModel.processed == False).limit(limit).all()
        return [
            {
                "id": msg.id,
                "user_id": msg.user_id,
                "order_id": msg.order_id,
                "payment_status": msg.payment_status,
                "created_at": msg.created_at
            }
            for msg in messages
        ]

    def add(self, message_id: str, user_id: int, order_id: str, payment_status: str):
        outbox_message_model = OutboxMessageModel(
            id=message_id,
            user_id=user_id,
            order_id=order_id,
            payment_status=payment_status,
            created_at=datetime.datetime.utcnow()
        )
        self.db.add(outbox_message_model)
        # db.commit() will be handled by the session outside the repo

    def mark_as_processed(self, message_id: str):
        message_model = self.db.query(OutboxMessageModel).filter(OutboxMessageModel.id == message_id).first()
        if message_model:
            message_model.processed = True
            message_model.sent_at = datetime.datetime.utcnow()
            self.db.add(message_model)
            # self.db.commit() # Removed to allow higher-level transaction management 