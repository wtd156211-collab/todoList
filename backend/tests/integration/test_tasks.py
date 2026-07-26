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


def test_list_tasks_uses_authenticated_user() -> None:
    assert Path("app/api/tasks.py").is_file()
    tasks_api = import_module("app.api.tasks")
    app = import_module("app.main").app

    class FakeTaskService:
        async def list(self, user_id: UUID) -> list[dict[str, object]]:
            assert user_id == UUID("00000000-0000-0000-0000-000000000001")
            return [
                {
                    "id": "00000000-0000-0000-0000-000000000010",
                    "title": "整理项目计划",
                    "note": "",
                    "priority": "medium",
                    "status": "todo",
                    "version": 1,
                }
            ]

    app.dependency_overrides[tasks_api.get_current_user_id] = lambda: UUID(
        "00000000-0000-0000-0000-000000000001"
    )
    app.dependency_overrides[tasks_api.get_task_service] = lambda: FakeTaskService()

    async def list_tasks() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/flowlist/api/v1/tasks")

    try:
        response = asyncio.run(list_tasks())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["title"] == "整理项目计划"


def test_complete_task_uses_current_user_and_version() -> None:
    assert Path("app/api/tasks.py").is_file()
    tasks_api = import_module("app.api.tasks")
    app = import_module("app.main").app

    class FakeTaskService:
        async def update(self, user_id: UUID, task_id: UUID, payload: object) -> dict[str, object]:
            assert user_id == UUID("00000000-0000-0000-0000-000000000001")
            assert task_id == UUID("00000000-0000-0000-0000-000000000010")
            assert payload.version == 1
            assert payload.status == "completed"
            return {
                "id": str(task_id),
                "title": "整理项目计划",
                "note": "",
                "priority": "medium",
                "status": "completed",
                "version": 2,
            }

    app.dependency_overrides[tasks_api.get_current_user_id] = lambda: UUID(
        "00000000-0000-0000-0000-000000000001"
    )
    app.dependency_overrides[tasks_api.get_task_service] = lambda: FakeTaskService()

    async def complete_task() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.patch(
                "/flowlist/api/v1/tasks/00000000-0000-0000-0000-000000000010",
                json={"status": "completed", "version": 1},
            )

    try:
        response = asyncio.run(complete_task())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["version"] == 2


def test_delete_task_uses_current_user() -> None:
    assert Path("app/api/tasks.py").is_file()
    tasks_api = import_module("app.api.tasks")
    app = import_module("app.main").app

    class FakeTaskService:
        async def delete(self, user_id: UUID, task_id: UUID) -> None:
            assert user_id == UUID("00000000-0000-0000-0000-000000000001")
            assert task_id == UUID("00000000-0000-0000-0000-000000000010")

    app.dependency_overrides[tasks_api.get_current_user_id] = lambda: UUID(
        "00000000-0000-0000-0000-000000000001"
    )
    app.dependency_overrides[tasks_api.get_task_service] = lambda: FakeTaskService()

    async def delete_task() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.delete("/flowlist/api/v1/tasks/00000000-0000-0000-0000-000000000010")

    try:
        response = asyncio.run(delete_task())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
