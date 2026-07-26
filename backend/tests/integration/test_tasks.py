import asyncio
from importlib import import_module
from pathlib import Path
from uuid import UUID

import httpx


def test_create_task_uses_authenticated_user_not_request_user_id() -> None:
    assert Path("app/api/tasks.py").is_file()
    tasks_api = import_module("app.api.tasks")
    app = import_module("app.main").app

    class FakeTaskService:
        async def create(self, user_id: UUID, payload: object) -> dict[str, object]:
            assert user_id == UUID("00000000-0000-0000-0000-000000000001")
            assert payload.title == "整理项目计划"
            return {
                "id": "00000000-0000-0000-0000-000000000010",
                "title": payload.title,
                "note": "",
                "priority": "medium",
                "status": "todo",
                "version": 1,
            }

    app.dependency_overrides[tasks_api.get_current_user_id] = lambda: UUID(
        "00000000-0000-0000-0000-000000000001"
    )
    app.dependency_overrides[tasks_api.get_task_service] = lambda: FakeTaskService()

    async def create_task() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/flowlist/api/v1/tasks",
                json={"title": "整理项目计划", "priority": "medium"},
            )

    try:
        response = asyncio.run(create_task())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["title"] == "整理项目计划"
