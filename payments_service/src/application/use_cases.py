from decimal import Decimal
from typing import List, Optional
import httpx
import uuid

from src.domain.entities import Account
from src.domain.value_objects import MessageStatus
from src.domain.repositories import IAccountRepository, IInboxMessageRepository, IOutboxMessageRepository
from src.application.dtos import (
    CreateAccountRequest,
    TopUpAccountRequest,
    AccountBalanceResponse,
    PaymentProcessRequest,
    AccountResponse
)
from src.infrastructure.messaging.outbox_publisher import HTTPOutboxPublisher

class CreateAccountUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

    def execute(self, request: CreateAccountRequest) -> AccountResponse:
        existing_account = self.account_repo.get_by_user_id(request.user_id)
        if existing_account:
            raise ValueError("Счёт для данного пользователя уже существует")
        
        new_account = Account(user_id=request.user_id)
        self.account_repo.add(new_account)
        return AccountResponse(
            id=new_account.id,
            user_id=new_account.user_id,
            balance=new_account.balance
        )

class TopUpAccountUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

    def execute(self, request: TopUpAccountRequest) -> AccountBalanceResponse:
        account = self.account_repo.get_by_user_id(request.user_id)
        if not account:
            raise ValueError("Счёт не найден")
        
        account.top_up(request.amount)
        self.account_repo.update(account) # Save changes to the account
        return AccountBalanceResponse(
            user_id=account.user_id,
            balance=account.balance
        )

class GetAccountBalanceUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

    def execute(self, user_id: int) -> AccountBalanceResponse:
        account = self.account_repo.get_by_user_id(user_id)
        if not account:
            raise ValueError("Счёт не найден")
        return AccountBalanceResponse(
            user_id=account.user_id,
            balance=account.balance
        )

class ProcessPaymentUseCase:
    def __init__(
        self, 
        account_repo: IAccountRepository, 
        inbox_repo: IInboxMessageRepository, 
        outbox_repo: IOutboxMessageRepository
    ):
        self.account_repo = account_repo
        self.inbox_repo = inbox_repo
        self.outbox_repo = outbox_repo

    def execute(self, request: PaymentProcessRequest) -> dict:
        # 1. Проверка на идемпотентность (Transactional Inbox Part 1)
        existing_message = self.inbox_repo.get_by_id(request.message_id)
        if existing_message and existing_message["status"] == MessageStatus.PROCESSED.value:
            return {"message": "Платёж уже обработан (идемпотентность)"}
        
        if existing_message and existing_message["status"] == MessageStatus.PENDING.value:
            return {"message": "Платёж уже находится в обработке"}

        # Сохраняем входящее сообщение в Inbox со статусом PENDING
        self.inbox_repo.add(request.message_id, request.user_id, request.order_id, request.amount, MessageStatus.PENDING)

        payment_status = "CANCELLED"
        message = "Ошибка обработки платежа."

        try:
            account = self.account_repo.get_by_user_id(request.user_id)
            if not account:
                # Если счета нет, создаем новый (fail событие)
                new_account = Account(user_id=request.user_id, balance=Decimal('0.00'))
                self.account_repo.add(new_account)
                account = new_account
                message = "Счёт пользователя не существовал, создан новый счёт с нулевым балансом."
            elif account.balance < request.amount:
                message = "Недостаточно средств на счёте."
            else:
                account.deduct(request.amount)
                self.account_repo.update(account) # Обновляем баланс
                payment_status = "FINISHED"
                message = "Платёж успешно выполнен."

            # Обновляем статус InboxMessage и добавляем OutboxMessage
            self.inbox_repo.update_status(request.message_id, MessageStatus.PROCESSED)
            self.outbox_repo.add(str(uuid.uuid4()), request.user_id, request.order_id, payment_status)

            return {"message": message, "order_id": request.order_id, "payment_status": payment_status}

        except ValueError as e:
            self.inbox_repo.update_status(request.message_id, MessageStatus.FAILED)
            raise e # Re-raise for API layer to handle
        except Exception as e:
            self.inbox_repo.update_status(request.message_id, MessageStatus.FAILED)
            raise e


class PublishOutboxMessagesUseCase:
    def __init__(
        self, 
        outbox_repo: IOutboxMessageRepository,
        publisher: HTTPOutboxPublisher # Changed to use HTTPOutboxPublisher
    ):
        self.outbox_repo = outbox_repo
        self.publisher = publisher

    async def execute(self):
        messages = self.outbox_repo.get_unprocessed() # Get unprocessed messages
        for message_data in messages:
            try:
                await self.publisher.publish(message_data) # Use the publisher
                self.outbox_repo.mark_as_processed(message_data["id"])
                print(f"Отправлено Outbox-сообщение: order_id={message_data['order_id']}, status={message_data['payment_status']}")
            except httpx.HTTPStatusError as e:
                print(f"Ошибка HTTP при отправке Outbox-сообщения Orders Service: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                print(f"Ошибка сети при отправке Outbox-сообщения Orders Service: {e}")
            except Exception as e:
                print(f"Неожиданная ошибка при обработке Outbox-сообщения: {e}") 