import httpx
import json
from src.domain.repositories import IOutboxMessageRepository

class HTTPOutboxPublisher:
    def __init__(self, http_client: httpx.AsyncClient, payments_service_url: str):
        self.http_client = http_client
        self.payments_service_url = payments_service_url

    async def publish(self, message_data: dict):
        # Assuming message_data["payload"] is a JSON string
        payload = json.loads(message_data["payload"])
        response = await self.http_client.post(
            f"{self.payments_service_url}/payments/process",
            json=payload
        )
        response.raise_for_status() 