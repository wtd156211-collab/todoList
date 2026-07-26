import asyncio
from importlib import import_module
from pathlib import Path

import httpx


def test_health_is_available_under_flowlist_prefix() -> None:
    assert Path("app/main.py").is_file()
    app = import_module("app.main").app

    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/flowlist/api/v1/health")

    response = asyncio.run(request_health())
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
