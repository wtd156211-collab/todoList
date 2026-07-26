from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse
from app.services.auth import get_session
from app.services.tasks import TaskService


router = APIRouter(prefix="/flowlist/api/v1/tasks", tags=["tasks"])
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> UUID:
    if credentials is None:
        raise ApiError(401, "AUTHENTICATION_FAILED", "缺少登录凭证")
    try:
        payload = decode_access_token(
            credentials.credentials,
            settings.jwt_secret,
            datetime.now(timezone.utc),
        )
        return UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        raise ApiError(401, "AUTHENTICATION_FAILED", "登录状态已失效") from None


async def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    return TaskService(session)


@router.post("", status_code=201, response_model=TaskResponse)
async def create_task(
    payload: TaskCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse | dict[str, object]:
    return await service.create(user_id, payload)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    user_id: UUID = Depends(get_current_user_id),
    service: TaskService = Depends(get_task_service),
) -> dict[str, object]:
    return {"items": await service.list(user_id)}
