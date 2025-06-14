import httpx

class MicroserviceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client = httpx.AsyncClient()

    async def send_request(
        self,
        method: str,
        path: str,
        headers: dict,
        params: dict,
        content: bytes
    ) -> httpx.Response:
        url = f"{self.base_url}/{path}"
        return await self._client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            content=content
        )

    async def close(self):
        await self._client.aclose() 