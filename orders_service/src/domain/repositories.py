from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal

from .entities import Order
from .value_objects import OrderStatus

class IOrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Order]:
        pass

    @abstractmethod
    def add(self, order: Order):
        pass

    @abstractmethod
    def update(self, order: Order):
        pass

class IOutboxMessageRepository(ABC):
    @abstractmethod
    def get_unprocessed(self, limit: int = 10) -> List[dict]:
        pass

    @abstractmethod
    def add(self, order_id: str, user_id: int, amount: Decimal, message_type: str, payload: str):
        pass

    @abstractmethod
    def mark_as_processed(self, message_id: str):
        pass

class IPaymentStatusInboxRepository(ABC):
    @abstractmethod
    def get_by_message_id(self, message_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def add(self, message_id: str, order_id: str, payment_status: str, processed: bool):
        pass

    @abstractmethod
    def mark_as_processed(self, message_id: str):
        pass 