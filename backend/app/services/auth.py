from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import UUID

import httpx
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.db.session import create_session_factory
from app.models.user import User


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = create_session_factory()
    async with factory() as session:
        yield session


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def login(self, code: str | None) -> dict[str, object]:
        if not code:
            raise ApiError(422, "VALIDATION_ERROR", "缺少微信登录凭证")

        openid = await self._exchange_wechat_code(code)
        user = await self._find_or_create_user(openid)
        return self._tokens_for(user)

    async def refresh(self, refresh_token: str | None) -> dict[str, object]:
        if not refresh_token:
            raise ApiError(422, "VALIDATION_ERROR", "缺少刷新令牌")

        try:
            payload = decode_refresh_token(refresh_token, self.settings.jwt_secret, datetime.now(timezone.utc))
            user_id = UUID(str(payload["sub"]))
        except (ValueError, KeyError):
            raise ApiError(401, "AUTHENTICATION_FAILED", "登录状态已失效") from None

        user = await self.session.get(User, user_id)
        if user is None:
            raise ApiError(401, "AUTHENTICATION_FAILED", "登录状态已失效")
        return self._tokens_for(user)

    async def _exchange_wechat_code(self, code: str) -> str:
        params = {
            "appid": self.settings.wechat_app_id,
            "secret": self.settings.wechat_app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get("https://api.weixin.qq.com/sns/jscode2session", params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError:
            raise ApiError(401, "AUTHENTICATION_FAILED", "微信登录暂不可用") from None

        openid = payload.get("openid")
        if not isinstance(openid, str) or not openid:
            raise ApiError(401, "AUTHENTICATION_FAILED", "微信登录失败")
        return openid

    async def _find_or_create_user(self, openid: str) -> User:
        user = await self.session.scalar(select(User).where(User.wechat_openid == openid))
        if user is not None:
            return user

        user = User(wechat_openid=openid)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    def _tokens_for(self, user: User) -> dict[str, object]:
        now = datetime.now(timezone.utc)
        return {
            "accessToken": create_access_token(user.id, self.settings.jwt_secret, now),
            "refreshToken": create_refresh_token(user.id, self.settings.jwt_secret, now),
            "user": {"id": user.id, "openid": user.wechat_openid},
        }


async def get_auth_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(session, settings)
