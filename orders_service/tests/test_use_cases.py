import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from decimal import Decimal
from unittest.mock import Mock

from src.application.use_cases import CreateOrderUseCase
from src.application.dtos import CreateOrderRequest, OrderResponse
from src.domain.entities import Order
from src.domain.value_objects import OrderStatus
from src.domain.repositories import IOrderRepository, IOutboxMessageRepository

class TestCreateOrderUseCase:
    @pytest.fixture
    def mock_order_repository(self):
        return Mock(spec=IOrderRepository)

    @pytest.fixture
    def mock_outbox_message_repository(self):
        return Mock(spec=IOutboxMessageRepository)

    @pytest.fixture
    def create_order_use_case(self, mock_order_repository, mock_outbox_message_repository):
        return CreateOrderUseCase(mock_order_repository, mock_outbox_message_repository)

    def test_create_order_success(self, create_order_use_case, mock_order_repository, mock_outbox_message_repository):
        # Arrange
        request = CreateOrderRequest(
            user_id=1,
            amount=Decimal('100.00'),
            description="Test Order"
        )

        # Act
        response = create_order_use_case.execute(request)

        # Assert
        assert isinstance(response, OrderResponse)
        assert response.user_id == request.user_id
        assert response.amount == request.amount
        assert response.description == request.description
        assert response.status == OrderStatus.NEW
        mock_order_repository.add.assert_called_once()
        mock_outbox_message_repository.add.assert_called_once()

    def test_create_order_with_negative_amount_raises_error(self, create_order_use_case):
        # Arrange
        request = CreateOrderRequest(
            user_id=1,
            amount=Decimal('-10.00'),
            description="Negative Amount Order"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Сумма заказа должна быть положительной."):
            create_order_use_case.execute(request)

    def test_create_order_with_zero_amount_raises_error(self, create_order_use_case):
        # Arrange
        request = CreateOrderRequest(
            user_id=1,
            amount=Decimal('0.00'),
            description="Zero Amount Order"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Сумма заказа должна быть положительной."):
            create_order_use_case.execute(request) 