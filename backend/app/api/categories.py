from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.tasks import get_current_user_id
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services.auth import get_session
from app.services.categories import CategoryService


router = APIRouter(prefix="/flowlist/api/v1/categories", tags=["categories"])


async def get_category_service(session: AsyncSession = Depends(get_session)) -> CategoryService:
    return CategoryService(session)


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    user_id: UUID = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
) -> list[CategoryResponse] | list[dict[str, object]]:
    return await service.list(user_id)


@router.post("", status_code=201, response_model=CategoryResponse)
async def create_category(
    payload: CategoryCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse | dict[str, object]:
    return await service.create(user_id, payload.name, payload.color)
