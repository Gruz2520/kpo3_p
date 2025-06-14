from pydantic import BaseModel
from decimal import Decimal

class CreateAccountRequest(BaseModel):
    user_id: int

class TopUpAccountRequest(BaseModel):
    user_id: int
    amount: Decimal

class AccountBalanceResponse(BaseModel):
    user_id: int
    balance: Decimal

class PaymentProcessRequest(BaseModel):
    user_id: int
    order_id: str
    amount: Decimal
    message_id: str # For idempotency

class AccountResponse(BaseModel):
    id: int
    user_id: int
    balance: Decimal 