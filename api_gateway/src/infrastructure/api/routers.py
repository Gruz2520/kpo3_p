from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

from ...application.use_cases import ProxyUseCase
from ..clients.http_client import MicroserviceClient

router = APIRouter()

PAYMENTS_SERVICE_URL = "http://payments_service:8001"
ORDERS_SERVICE_URL = "http://orders_service:8002"

def get_payments_client() -> MicroserviceClient:
    return MicroserviceClient(PAYMENTS_SERVICE_URL)

def get_orders_client() -> MicroserviceClient:
    return MicroserviceClient(ORDERS_SERVICE_URL)

def get_proxy_use_case(
    payments_client: MicroserviceClient = Depends(get_payments_client),
    orders_client: MicroserviceClient = Depends(get_orders_client)
) -> ProxyUseCase:
    return ProxyUseCase(payments_client, orders_client)

@router.api_route("/payments/{path:path}", methods=["GET"], summary="Проксирование GET запросов к Payments Service", operation_id="payments_proxy_get", include_in_schema=False)
async def payments_proxy_get(
    path: str,
    request: Request,
    use_case: ProxyUseCase = Depends(get_proxy_use_case)
):
    try:
        response = await use_case.execute("payments", path, request)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к Payments Service: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/payments/{path:path}", methods=["POST"], summary="Проксирование POST запросов к Payments Service", operation_id="payments_proxy_post", include_in_schema=False)
async def payments_proxy_post(
    path: str,
    request: Request,
    use_case: ProxyUseCase = Depends(get_proxy_use_case)
):
    try:
        response = await use_case.execute("payments", path, request)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к Payments Service: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/payments/{path:path}", methods=["PUT"], summary="Проксирование PUT запросов к Payments Service", operation_id="payments_proxy_put", include_in_schema=False)
async def payments_proxy_put(
    path: str,
    request: Request,
    use_case: ProxyUseCase = Depends(get_proxy_use_case)
):
    try:
        response = await use_case.execute("payments", path, request)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к Payments Service: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/payments/{path:path}", methods=["DELETE"], summary="Проксирование DELETE запросов к Payments Service", operation_id="payments_proxy_delete", include_in_schema=False)
async def payments_proxy_delete(
    path: str,
    request: Request,
    use_case: ProxyUseCase = Depends(get_proxy_use_case)
):
    try:
        response = await use_case.execute("payments", path, request)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к Payments Service: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/orders/{path:path}", methods=["GET"], summary="Проксирование GET запросов к Orders Service", operation_id="orders_proxy_get", include_in_schema=False)
async def orders_proxy_get(
    path: str,
    request: Request,
    use_case: ProxyUseCase = Depends(get_proxy_use_case)
):
    try:
        response = await use_case.execute("orders", path, request)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к Orders Service: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/orders/{path:path}", methods=["POST"], summary="Проксирование POST запросов к Orders Service", operation_id="orders_proxy_post", include_in_schema=False)
async def orders_proxy_post(
    path: str,
    request: Request,
    use_case: ProxyUseCase = Depends(get_proxy_use_case)
):
    try:
        response = await use_case.execute("orders", path, request)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к Orders Service: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/orders/{path:path}", methods=["PUT"], summary="Проксирование PUT запросов к Orders Service", operation_id="orders_proxy_put", include_in_schema=False)
async def orders_proxy_put(
    path: str,
    request: Request,
    use_case: ProxyUseCase = Depends(get_proxy_use_case)
):
    try:
        response = await use_case.execute("orders", path, request)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к Orders Service: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/orders/{path:path}", methods=["DELETE"], summary="Проксирование DELETE запросов к Orders Service", operation_id="orders_proxy_delete", include_in_schema=False)
async def orders_proxy_delete(
    path: str,
    request: Request,
    use_case: ProxyUseCase = Depends(get_proxy_use_case)
):
    try:
        response = await use_case.execute("orders", path, request)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к Orders Service: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", summary="Проверка работоспособности шлюза", operation_id="routers_health_check")
async def health_check():
    return {"status": "API Gateway is running"} 