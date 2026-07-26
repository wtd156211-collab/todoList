import asyncio
from importlib import import_module

import httpx


def test_health_response_has_request_id() -> None:
    app = import_module("app.main").app

    async def get_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/flowlist/api/v1/health")

    response = asyncio.run(get_health())

    assert response.headers["x-request-id"]
