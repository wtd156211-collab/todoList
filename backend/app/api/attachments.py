from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.tasks import get_current_user_id
from app.core.config import Settings, get_settings
from app.schemas.attachment import AttachmentCreate, UploadPolicyResponse
from app.services.attachments import AttachmentService
from app.services.auth import get_session


router = APIRouter(prefix="/flowlist/api/v1", tags=["attachments"])


async def get_attachment_service(
    session: AsyncSession = Depends(get_session), settings: Settings = Depends(get_settings)
) -> AttachmentService:
    return AttachmentService(session, settings)


@router.post("/tasks/{task_id}/attachments/upload-policy", response_model=UploadPolicyResponse)
async def create_upload_policy(
    task_id: UUID,
    payload: AttachmentCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: AttachmentService = Depends(get_attachment_service),
) -> dict[str, object]:
    return await service.create_upload_policy(user_id, task_id, payload)
