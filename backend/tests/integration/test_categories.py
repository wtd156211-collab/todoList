import asyncio
from importlib import import_module
from pathlib import Path
from uuid import UUID

import httpx


def test_category_routes_use_authenticated_user() -> None:
    assert Path("app/api/categories.py").is_file()
    categories_api = import_module("app.api.categories")
    app = import_module("app.main").app

    class FakeCategoryService:
        async def list(self, user_id: UUID) -> list[dict[str, object]]:
            assert user_id == UUID("00000000-0000-0000-0000-000000000001")
            return [{"id": "00000000-0000-0000-0000-000000000020", "name": "工作", "color": "#2563EB"}]

        async def create(self, user_id: UUID, name: str, color: str) -> dict[str, object]:
            assert user_id == UUID("00000000-0000-0000-0000-000000000001")
            assert (name, color) == ("个人", "#F97316")
            return {"id": "00000000-0000-0000-0000-000000000021", "name": name, "color": color}

    app.dependency_overrides[categories_api.get_current_user_id] = lambda: UUID(
        "00000000-0000-0000-0000-000000000001"
    )
    app.dependency_overrides[categories_api.get_category_service] = lambda: FakeCategoryService()

    async def request_categories() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            listed = await client.get("/flowlist/api/v1/categories")
            created = await client.post(
                "/flowlist/api/v1/categories",
                json={"name": "个人", "color": "#F97316"},
            )
            return listed, created

    try:
        listed, created = asyncio.run(request_categories())
    finally:
        app.dependency_overrides.clear()

    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "工作"
    assert created.status_code == 201
    assert created.json()["name"] == "个人"
