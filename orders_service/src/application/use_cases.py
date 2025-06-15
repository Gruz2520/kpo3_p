from decimal import Decimal
from typing import List, Optional
import json
import httpx

from src.domain.entities import Order
from src.domain.value_objects import OrderStatus
from src.domain.repositories import IOrderRepository, IOutboxMessageRepository, IPaymentStatusInboxRepository
from src.application.dtos import CreateOrderRequest, OrderResponse, PaymentStatusUpdateRequest
from src.infrastructure.messaging.outbox_publisher import HTTPOutboxPublisher
import uuid

class CreateOrderUseCase:
    def __init__(
        self, 
        order_repo: IOrderRepository,
        outbox_repo: IOutboxMessageRepository
    ):
        self.order_repo = order_repo
        self.outbox_repo = outbox_repo

    def execute(self, request: CreateOrderRequest) -> OrderResponse:
        if request.amount <= 0:
            raise ValueError("Сумма заказа должна быть положительной.")

        new_order = Order(
            user_id=request.user_id,
            amount=request.amount,
            description=request.description,
            status=OrderStatus.NEW.value 
        )
        self.order_repo.add(new_order)

        payment_request_payload = {
            "user_id": request.user_id,
            "order_id": new_order.id,
            "amount": float(request.amount),
            "message_id": str(uuid.uuid4())
        }
        self.outbox_repo.add(
            order_id=new_order.id,
            user_id=request.user_id,
            amount=request.amount,
            message_type="payment_request",
            payload=json.dumps(payment_request_payload)
        )
        
        return OrderResponse(
            id=new_order.id,
            user_id=new_order.user_id,
            amount=new_order.amount,
            description=new_order.description,
            status=OrderStatus[new_order.status],
            created_at=new_order.created_at,
            updated_at=new_order.updated_at
        )

class GetUserOrdersUseCase:
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo

    def execute(self, user_id: int) -> List[OrderResponse]:
        orders = self.order_repo.get_by_user_id(user_id)
        return [
            OrderResponse(
                id=order.id,
                user_id=order.user_id,
                amount=order.amount,
                description=order.description,
                status=OrderStatus[order.status],
                created_at=order.created_at,
                updated_at=order.updated_at
            )
            for order in orders
        ]

class GetOrderStatusUseCase:
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo

    def execute(self, order_id: str) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("Заказ не найден")
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            amount=order.amount,
            description=order.description,
            status=OrderStatus[order.status],
            created_at=order.created_at,
            updated_at=order.updated_at
        )

class UpdateOrderPaymentStatusUseCase:
    def __init__(
        self, 
        order_repo: IOrderRepository, 
        inbox_repo: IPaymentStatusInboxRepository
    ):
        self.order_repo = order_repo
        self.inbox_repo = inbox_repo

    def execute(self, request: PaymentStatusUpdateRequest) -> dict:
        existing_inbox_message = self.inbox_repo.get_by_message_id(request.message_id)
        if existing_inbox_message and existing_inbox_message["processed"]:
            return {"message": "Статус платежа для заказа уже обработан (идемпотентность)"}
        
        self.inbox_repo.add(
            message_id=request.message_id,
            order_id=request.order_id,
            payment_status=request.payment_status,
            processed=False
        )

        order = self.order_repo.get_by_id(request.order_id)
        if not order:
            raise ValueError("Заказ не найден")
        
        if request.payment_status == OrderStatus.FINISHED.value:
            order.update_status(OrderStatus.FINISHED.value)
        elif request.payment_status == OrderStatus.CANCELLED.value:
            order.update_status(OrderStatus.CANCELLED.value)
        else:
            raise ValueError("Недопустимый статус оплаты")
        
        self.order_repo.update(order)
        self.inbox_repo.mark_as_processed(request.message_id)

        return {"message": f"Статус заказа {request.order_id} обновлен до {order.status}"}

class PublishOutboxMessagesUseCase:
    def __init__(
        self, 
        outbox_repo: IOutboxMessageRepository,
        publisher: HTTPOutboxPublisher
    ):
        self.outbox_repo = outbox_repo
        self.publisher = publisher

    async def execute(self):
        messages = self.outbox_repo.get_unprocessed()
        for message_data in messages:
            try:
                payload = json.loads(message_data["payload"])
                amount_in_payload = Decimal(str(payload["amount"]))

                if amount_in_payload == Decimal('0.00'):
                    self.outbox_repo.mark_as_processed(message_data["id"])
                    print(f"Outbox-сообщение с нулевой суммой для order_id={message_data['order_id']} помечено как обработанное.")
                    continue

                await self.publisher.publish(message_data) 
                self.outbox_repo.mark_as_processed(message_data["id"])
                print(f"Отправлено Outbox-сообщение из Orders Service: order_id={message_data['order_id']}")
            except httpx.HTTPStatusError as e:
                print(f"Ошибка HTTP при отправке Outbox-сообщения Payments Service: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                print(f"Ошибка сети при отправке Outbox-сообщения Payments Service: {e}")
            except Exception as e:
                print(f"Неожиданная ошибка при обработке Outbox-сообщения в Orders Service: {e}") 