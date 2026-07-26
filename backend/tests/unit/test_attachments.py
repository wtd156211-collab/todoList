from uuid import UUID

import pytest

from app.core.errors import ApiError
from app.core.config import Settings
from app.schemas.attachment import AttachmentCreate
from app.services.attachments import AttachmentService, build_object_key, validate_upload_request


def test_object_key_is_scoped_to_user_and_task() -> None:
    key = build_object_key(
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
        "receipt.pdf",
    )

    assert key.startswith(
        "flowlist/00000000-0000-0000-0000-000000000001/00000000-0000-0000-0000-000000000002/"
    )
    assert key.endswith(".pdf")


def test_upload_rejects_unsupported_mime_type() -> None:
    with pytest.raises(ApiError) as error:
        validate_upload_request("animated.gif", "image/gif", 1024)

    assert error.value.code == "UPLOAD_REJECTED"


def test_upload_rejects_files_larger_than_ten_mebibytes() -> None:
    with pytest.raises(ApiError) as error:
        validate_upload_request("large.pdf", "application/pdf", 10 * 1024 * 1024 + 1)

    assert error.value.code == "UPLOAD_REJECTED"


def test_upload_policy_hides_tasks_owned_by_another_user() -> None:
    class EmptySession:
        async def scalar(self, statement: object) -> None:
            return None

    settings = Settings.model_construct(
        oss_access_key_secret="secret",
        oss_access_key_id="key-id",
        oss_bucket="flowlist",
        oss_endpoint="https://oss-cn-beijing.aliyuncs.com",
    )
    service = AttachmentService(EmptySession(), settings)

    with pytest.raises(ApiError) as error:
        import asyncio

        asyncio.run(
            service.create_upload_policy(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                AttachmentCreate(filename="receipt.pdf", mimeType="application/pdf", sizeBytes=1024),
            )
        )

    assert error.value.code == "NOT_FOUND"
