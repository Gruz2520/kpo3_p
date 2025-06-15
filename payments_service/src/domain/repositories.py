from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal
from .entities import Account
from .value_objects import MessageStatus

class IAccountRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[Account]:
        pass

    @abstractmethod
    def add(self, account: Account):
        pass

    @abstractmethod
    def update(self, account: Account):
        pass

    @abstractmethod
    def save(self, account: Account):
        pass

class IInboxMessageRepository(ABC):
    @abstractmethod
    def get_by_id(self, message_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def get_by_order_id(self, order_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def add(self, message_id: str, user_id: int, order_id: str, amount: Decimal, status: MessageStatus):
        pass

    @abstractmethod
    def update_status(self, message_id: str, status: MessageStatus):
        pass

class IOutboxMessageRepository(ABC):
    @abstractmethod
    def get_unprocessed(self, limit: int = 10) -> List[dict]:
        pass

    @abstractmethod
    def add(self, message_id: str, user_id: int, order_id: str, payment_status: str):
        pass

    @abstractmethod
    def mark_as_processed(self, message_id: str):
        pass 