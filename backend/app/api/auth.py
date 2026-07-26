from fastapi import APIRouter, Depends

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import AuthService, get_auth_service


router = APIRouter(prefix="/flowlist/api/v1/auth", tags=["auth"])


@router.post("/wechat-login", response_model=TokenResponse)
async def wechat_login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, object]:
    return await service.login(payload.code)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, object]:
    return await service.refresh(payload.refresh_token)
