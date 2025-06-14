import sys
import os

# Add the current directory (api_gateway) to sys.path to allow absolute imports from src
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI
import httpx
import asyncio
import json
from fastapi.openapi.utils import get_openapi

from src.infrastructure.api.routers import router as api_gateway_router, get_payments_client, get_orders_client, PAYMENTS_SERVICE_URL, ORDERS_SERVICE_URL

app = FastAPI(title="API Gateway - Aggregated API")

app.include_router(api_gateway_router)

async def fetch_openapi_spec(service_url: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{service_url}/openapi.json")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Ошибка HTTP при получении OpenAPI спецификации от {service_url}: {e.response.status_code} - {e.response.text}")
            return {}
        except httpx.RequestError as e:
            print(f"Ошибка сети при получении OpenAPI спецификации от {service_url}: {e}")
            return {}

@app.on_event("startup")
async def startup_event():
    # Initialize a base OpenAPI schema with API Gateway's own endpoints
    # This will include /health. Proxy routes are already excluded by include_in_schema=False in routers.py
    current_openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0", # Keep original version or update as needed
        routes=app.routes,
    )

    # Fetch external OpenAPI specs
    payments_spec = await fetch_openapi_spec(PAYMENTS_SERVICE_URL)
    orders_spec = await fetch_openapi_spec(ORDERS_SERVICE_URL)

    # Merge OpenAPI specs from payments_service
    if payments_spec and "paths" in payments_spec:
        for path, methods in payments_spec["paths"].items():
            new_path = f"/payments{path}"
            current_openapi_schema["paths"][new_path] = methods
        if "components" in payments_spec and "schemas" in payments_spec["components"]:
            if "components" not in current_openapi_schema: current_openapi_schema["components"] = {"schemas": {}}
            elif "schemas" not in current_openapi_schema["components"]: current_openapi_schema["components"]["schemas"] = {}
            current_openapi_schema["components"]["schemas"].update(payments_spec["components"]["schemas"])

    # Merge OpenAPI specs from orders_service
    if orders_spec and "paths" in orders_spec:
        for path, methods in orders_spec["paths"].items():
            new_path = f"/orders{path}"
            current_openapi_schema["paths"][new_path] = methods
        if "components" in orders_spec and "schemas" in orders_spec["components"]:
            if "components" not in current_openapi_schema: current_openapi_schema["components"] = {"schemas": {}}
            elif "schemas" not in current_openapi_schema["components"]: current_openapi_schema["components"]["schemas"] = {}
            current_openapi_schema["components"]["schemas"].update(orders_spec["components"]["schemas"])

    # Assign the completely merged schema back to app.openapi_schema
    app.openapi_schema = current_openapi_schema
    # print("ОБЪЕДИНЕННАЯ СХЕМА OPENAPI:")
    # print(json.dumps(app.openapi_schema, indent=2)) # Removed for clean output

@app.on_event("shutdown")
async def shutdown_event():
    # Close httpx clients on shutdown
    payments_client = get_payments_client()
    orders_client = get_orders_client()
    await payments_client.close()
    await orders_client.close()

# Health check endpoint
# Removed to avoid duplicate operation ID, already defined in routers.py
# @app.get("/health", summary="Проверка работоспособности шлюза")
# async def health_check():
#     return {"status": "API Gateway is running"} 