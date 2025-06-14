from decimal import Decimal
from typing import Optional

class Account:
    def __init__(
        self, 
        user_id: int, 
        balance: Decimal = Decimal('0.00'), 
        id: Optional[int] = None
    ):
        self.id = id
        self.user_id = user_id
        self.balance = balance

    def top_up(self, amount: Decimal):
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance += amount

    def deduct(self, amount: Decimal):
        if amount <= 0:
            raise ValueError("Сумма списания должна быть положительной")
        if self.balance < amount:
            raise ValueError("Недостаточно средств на счёте")
        self.balance -= amount

    def __eq__(self, other):
        if not isinstance(other, Account):
            return NotImplemented
        return self.id == other.id and self.user_id == other.user_id

    def __hash__(self):
        return hash((self.id, self.user_id)) 