import asyncio
from importlib import import_module
from pathlib import Path
from uuid import UUID

import httpx


def test_upload_policy_uses_authenticated_user_and_task() -> None:
    assert Path("app/api/attachments.py").is_file()
    attachments_api = import_module("app.api.attachments")
    app = import_module("app.main").app

    class FakeAttachmentService:
        async def create_upload_policy(self, user_id: UUID, task_id: UUID, payload: object) -> dict[str, object]:
            assert user_id == UUID("00000000-0000-0000-0000-000000000001")
            assert task_id == UUID("00000000-0000-0000-0000-000000000010")
            assert payload.filename == "receipt.pdf"
            assert payload.mime_type == "application/pdf"
            assert payload.size_bytes == 1024
            return {
                "attachmentId": "00000000-0000-0000-0000-000000000020",
                "objectKey": "flowlist/user/task/file.pdf",
                "host": "https://flowlist.oss-cn-beijing.aliyuncs.com",
                "formData": {"key": "flowlist/user/task/file.pdf"},
            }

    app.dependency_overrides[attachments_api.get_current_user_id] = lambda: UUID(
        "00000000-0000-0000-0000-000000000001"
    )
    app.dependency_overrides[attachments_api.get_attachment_service] = lambda: FakeAttachmentService()

    async def request_policy() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/flowlist/api/v1/tasks/00000000-0000-0000-0000-000000000010/attachments/upload-policy",
                json={"filename": "receipt.pdf", "mimeType": "application/pdf", "sizeBytes": 1024},
            )

    try:
        response = asyncio.run(request_policy())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["attachmentId"] == "00000000-0000-0000-0000-000000000020"
