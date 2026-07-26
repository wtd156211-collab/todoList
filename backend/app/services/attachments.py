import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import PurePath
from uuid import UUID, uuid4

from app.core.errors import ApiError
from app.core.config import Settings
from app.models.attachment import TaskAttachment
from app.models.task import Task
from app.schemas.attachment import AttachmentCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def build_object_key(user_id: UUID, task_id: UUID, filename: str) -> str:
    suffix = PurePath(filename).suffix.lower()
    return f"flowlist/{user_id}/{task_id}/{uuid4()}{suffix}"


def validate_upload_request(filename: str, mime_type: str, size_bytes: int) -> None:
    if not filename or mime_type not in ALLOWED_MIME_TYPES or size_bytes <= 0 or size_bytes > MAX_UPLOAD_BYTES:
        raise ApiError(422, "UPLOAD_REJECTED", "附件仅支持 JPEG、PNG 或 PDF，且不能超过 10 MiB")


class AttachmentService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def create_upload_policy(
        self, user_id: UUID, task_id: UUID, payload: AttachmentCreate
    ) -> dict[str, object]:
        validate_upload_request(payload.filename, payload.mime_type, payload.size_bytes)
        task = await self.session.scalar(select(Task).where(Task.id == task_id, Task.user_id == user_id))
        if task is None:
            raise ApiError(404, "NOT_FOUND", "任务不存在或已删除")

        attachment = TaskAttachment(
            task_id=task_id,
            object_key=build_object_key(user_id, task_id, payload.filename),
            filename=payload.filename,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
        )
        self.session.add(attachment)
        await self.session.commit()
        await self.session.refresh(attachment)
        return self._post_policy(attachment)

    def _post_policy(self, attachment: TaskAttachment) -> dict[str, object]:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        policy = {
            "expiration": expires_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "conditions": [
                ["eq", "$key", attachment.object_key],
                ["eq", "$Content-Type", attachment.mime_type],
                ["content-length-range", 0, MAX_UPLOAD_BYTES],
            ],
        }
        encoded_policy = base64.b64encode(json.dumps(policy, separators=(",", ":")).encode()).decode()
        signature = base64.b64encode(
            hmac.new(
                self.settings.oss_access_key_secret.encode(), encoded_policy.encode(), hashlib.sha1
            ).digest()
        ).decode()
        return {
            "attachmentId": str(attachment.id),
            "objectKey": attachment.object_key,
            "host": self._host(),
            "formData": {
                "key": attachment.object_key,
                "policy": encoded_policy,
                "OSSAccessKeyId": self.settings.oss_access_key_id,
                "signature": signature,
                "success_action_status": "204",
                "Content-Type": attachment.mime_type,
            },
        }

    def _host(self) -> str:
        endpoint = self.settings.oss_endpoint.rstrip("/")
        scheme, host = endpoint.split("://", maxsplit=1)
        return f"{scheme}://{self.settings.oss_bucket}.{host}"
