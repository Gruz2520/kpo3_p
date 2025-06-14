import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.application.use_cases import (
    CreateAccountUseCase,
    TopUpAccountUseCase,
    GetAccountBalanceUseCase,
    ProcessPaymentUseCase,
    PublishOutboxMessagesUseCase
)
from src.application.dtos import (
    CreateAccountRequest,
    TopUpAccountRequest,
    AccountBalanceResponse,
    PaymentProcessRequest,
    AccountResponse
)
from src.domain.entities import Account
from src.domain.value_objects import MessageStatus
from src.domain.repositories import IAccountRepository, IInboxMessageRepository, IOutboxMessageRepository
from src.infrastructure.messaging.outbox_publisher import HTTPOutboxPublisher

class TestCreateAccountUseCase:
    @pytest.fixture
    def mock_account_repository(self):
        return Mock(spec=IAccountRepository)

    @pytest.fixture
    def create_account_use_case(self, mock_account_repository):
        return CreateAccountUseCase(mock_account_repository)

    def test_create_account_success(self, create_account_use_case, mock_account_repository):
        request = CreateAccountRequest(user_id=1)
        mock_account_repository.get_by_user_id.return_value = None

        def set_id(account_obj):
            account_obj.id = 1  # Simulate ID being set by DB

        mock_account_repository.add.side_effect = set_id

        response = create_account_use_case.execute(request)

        assert isinstance(response, AccountResponse)
        assert response.user_id == request.user_id
        assert response.balance == Decimal('0.00')
        assert response.id == 1 # Assert that ID is set
        mock_account_repository.add.assert_called_once()

    def test_create_account_already_exists(self, create_account_use_case, mock_account_repository):
        request = CreateAccountRequest(user_id=1)
        mock_account_repository.get_by_user_id.return_value = Account(user_id=1)

        with pytest.raises(ValueError, match="Счёт для данного пользователя уже существует"):
            create_account_use_case.execute(request)

class TestTopUpAccountUseCase:
    @pytest.fixture
    def mock_account_repository(self):
        return Mock(spec=IAccountRepository)

    @pytest.fixture
    def top_up_account_use_case(self, mock_account_repository):
        return TopUpAccountUseCase(mock_account_repository)

    def test_top_up_account_success(self, top_up_account_use_case, mock_account_repository):
        request = TopUpAccountRequest(user_id=1, amount=Decimal('50.00'))
        account = Account(user_id=1, balance=Decimal('100.00'))
        mock_account_repository.get_by_user_id.return_value = account

        response = top_up_account_use_case.execute(request)

        assert isinstance(response, AccountBalanceResponse)
        assert response.user_id == request.user_id
        assert response.balance == Decimal('150.00')
        mock_account_repository.update.assert_called_once_with(account)

    def test_top_up_account_not_found(self, top_up_account_use_case, mock_account_repository):
        request = TopUpAccountRequest(user_id=1, amount=Decimal('50.00'))
        mock_account_repository.get_by_user_id.return_value = None

        with pytest.raises(ValueError, match="Счёт не найден"):
            top_up_account_use_case.execute(request)

class TestGetAccountBalanceUseCase:
    @pytest.fixture
    def mock_account_repository(self):
        return Mock(spec=IAccountRepository)

    @pytest.fixture
    def get_account_balance_use_case(self, mock_account_repository):
        return GetAccountBalanceUseCase(mock_account_repository)

    def test_get_account_balance_success(self, get_account_balance_use_case, mock_account_repository):
        user_id = 1
        account = Account(user_id=user_id, balance=Decimal('200.00'))
        mock_account_repository.get_by_user_id.return_value = account

        response = get_account_balance_use_case.execute(user_id)

        assert isinstance(response, AccountBalanceResponse)
        assert response.user_id == user_id
        assert response.balance == Decimal('200.00')

    def test_get_account_balance_not_found(self, get_account_balance_use_case, mock_account_repository):
        user_id = 1
        mock_account_repository.get_by_user_id.return_value = None

        with pytest.raises(ValueError, match="Счёт не найден"):
            get_account_balance_use_case.execute(user_id) 