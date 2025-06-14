from ..infrastructure.clients.http_client import MicroserviceClient
from fastapi import Request
import httpx

class ProxyUseCase:
    def __init__(
        self, 
        payments_client: MicroserviceClient,
        orders_client: MicroserviceClient
    ):
        self.payments_client = payments_client
        self.orders_client = orders_client

    async def execute(
        self,
        service_name: str,
        path: str,
        request: Request
    ) -> httpx.Response:
        if service_name == "payments":
            client = self.payments_client
        elif service_name == "orders":
            client = self.orders_client
        else:
            raise ValueError("Неизвестный сервис")

        return await client.send_request(
            method=request.method,
            path=path,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        ) 