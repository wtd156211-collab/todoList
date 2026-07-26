import asyncio
from importlib import import_module
from pathlib import Path

import httpx


def test_wechat_login_returns_service_tokens_without_exposing_wechat_secrets() -> None:
    assert Path("app/api/auth.py").is_file()
    auth_api = import_module("app.api.auth")
    app = import_module("app.main").app

    class FakeAuthService:
        async def login(self, code: str) -> dict[str, object]:
            assert code == "mini-program-code"
            return {
                "accessToken": "access-token",
                "refreshToken": "refresh-token",
                "user": {"id": "00000000-0000-0000-0000-000000000001", "openid": "mock-openid"},
            }

    app.dependency_overrides[auth_api.get_auth_service] = lambda: FakeAuthService()

    async def login() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/flowlist/api/v1/auth/wechat-login", json={"code": "mini-program-code"})

    try:
        response = asyncio.run(login())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "accessToken": "access-token",
        "refreshToken": "refresh-token",
        "user": {"id": "00000000-0000-0000-0000-000000000001", "openid": "mock-openid"},
    }


def test_refresh_returns_rotated_tokens() -> None:
    assert Path("app/api/auth.py").is_file()
    auth_api = import_module("app.api.auth")
    app = import_module("app.main").app

    class FakeAuthService:
        async def refresh(self, refresh_token: str) -> dict[str, object]:
            assert refresh_token == "refresh-token"
            return {
                "accessToken": "new-access-token",
                "refreshToken": "new-refresh-token",
                "user": {"id": "00000000-0000-0000-0000-000000000001", "openid": "mock-openid"},
            }

    app.dependency_overrides[auth_api.get_auth_service] = lambda: FakeAuthService()

    async def refresh() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/flowlist/api/v1/auth/refresh", json={"refreshToken": "refresh-token"})

    try:
        response = asyncio.run(refresh())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["accessToken"] == "new-access-token"
