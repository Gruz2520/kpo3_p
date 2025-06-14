import pytest
from unittest.mock import Mock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.application.use_cases import ProxyUseCase
from src.infrastructure.clients.http_client import MicroserviceClient
from fastapi import Request

class TestProxyUseCase:
    @pytest.fixture
    def mock_payments_client(self):
        return AsyncMock(spec=MicroserviceClient)

    @pytest.fixture
    def mock_orders_client(self):
        return AsyncMock(spec=MicroserviceClient)

    @pytest.fixture
    def proxy_use_case(self, mock_payments_client, mock_orders_client):
        return ProxyUseCase(mock_payments_client, mock_orders_client)

    @pytest.mark.asyncio
    async def test_execute_payments_service(self, proxy_use_case, mock_payments_client):
        # Arrange
        service_name = "payments"
        path = "/accounts"
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {"test-header": "value"}
        mock_request.query_params = {"param": "value"}
        mock_request.body = AsyncMock(return_value=b'')

        mock_response = Mock()
        mock_response.json.return_value = {"message": "Success"}
        mock_response.status_code = 200
        mock_payments_client.send_request.return_value = mock_response

        # Act
        response = await proxy_use_case.execute(service_name, path, mock_request)

        # Assert
        assert response == mock_response
        mock_payments_client.send_request.assert_called_once_with(
            method="GET",
            path="/accounts",
            headers=mock_request.headers,
            params=mock_request.query_params,
            content=b''
        )

    @pytest.mark.asyncio
    async def test_execute_orders_service(self, proxy_use_case, mock_orders_client):
        # Arrange
        service_name = "orders"
        path = "/orders"
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'{"user_id": 1, "amount": 100}')

        mock_response = Mock()
        mock_response.json.return_value = {"order_id": "123"}
        mock_response.status_code = 201
        mock_orders_client.send_request.return_value = mock_response

        # Act
        response = await proxy_use_case.execute(service_name, path, mock_request)

        # Assert
        assert response == mock_response
        mock_orders_client.send_request.assert_called_once_with(
            method="POST",
            path="/orders",
            headers=mock_request.headers,
            params=mock_request.query_params,
            content=b'{"user_id": 1, "amount": 100}'
        )

    @pytest.mark.asyncio
    async def test_execute_unknown_service_raises_error(self, proxy_use_case):
        # Arrange
        service_name = "unknown_service"
        path = "/some_path"
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'')

        # Act & Assert
        with pytest.raises(ValueError, match="Неизвестный сервис"):
            await proxy_use_case.execute(service_name, path, mock_request) 