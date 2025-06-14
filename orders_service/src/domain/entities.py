from decimal import Decimal
from typing import Optional
import datetime
import uuid

class Order:
    def __init__(
        self, 
        user_id: int, 
        amount: Decimal,
        description: str,
        status: str, # Will be OrderStatus enum value
        id: Optional[str] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None
    ):
        self.id = id if id else str(uuid.uuid4())
        self.user_id = user_id
        self.amount = amount
        self.description = description
        self.status = status
        self.created_at = created_at if created_at else datetime.datetime.now(datetime.UTC)
        self.updated_at = updated_at if updated_at else datetime.datetime.now(datetime.UTC)

    def update_status(self, new_status: str):
        self.status = new_status
        self.updated_at = datetime.datetime.now(datetime.UTC)

    def __eq__(self, other):
        if not isinstance(other, Order):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id) 