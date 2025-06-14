import httpx
import json
from src.domain.repositories import IOutboxMessageRepository

class HTTPOutboxPublisher:
    def __init__(self, http_client: httpx.AsyncClient, orders_service_url: str):
        self.http_client = http_client
        self.orders_service_url = orders_service_url

    async def publish(self, message_data: dict):
        payload = {
            "user_id": message_data["user_id"],
            "order_id": message_data["order_id"],
            "payment_status": message_data["payment_status"],
            "message_id": message_data["id"]
        }
        response = await self.http_client.post(
            f"{self.orders_service_url}/orders/payment-status",
            json=payload
        )
        response.raise_for_status() 