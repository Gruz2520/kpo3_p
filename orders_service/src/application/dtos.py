from pydantic import BaseModel
from decimal import Decimal
import datetime
from src.domain.value_objects import OrderStatus

class CreateOrderRequest(BaseModel):
    user_id: int
    amount: Decimal
    description: str

class OrderResponse(BaseModel):
    id: str
    user_id: int
    amount: Decimal
    description: str
    status: OrderStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime

class PaymentStatusUpdateRequest(BaseModel):
    user_id: int
    order_id: str
    payment_status: str # FINISHED or CANCELLED
    message_id: str 