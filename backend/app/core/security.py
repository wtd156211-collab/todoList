from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt


ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=30)
REFRESH_TOKEN_TTL = timedelta(days=30)


def create_token(user_id: UUID, secret: str, now: datetime, token_type: str, ttl: timedelta) -> str:
    issued_at = now.astimezone(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + ttl).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str, now: datetime, expected_type: str) -> dict[str, str | int]:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"verify_exp": False})
    except jwt.InvalidTokenError as error:
        raise ValueError("invalid access token") from error

    if payload.get("type") != expected_type or int(payload.get("exp", 0)) < int(now.timestamp()):
        raise ValueError("expired or invalid access token")
    return payload


def create_access_token(user_id: UUID, secret: str, now: datetime) -> str:
    return create_token(user_id, secret, now, "access", ACCESS_TOKEN_TTL)


def decode_access_token(token: str, secret: str, now: datetime) -> dict[str, str | int]:
    return decode_token(token, secret, now, "access")


def create_refresh_token(user_id: UUID, secret: str, now: datetime) -> str:
    return create_token(user_id, secret, now, "refresh", REFRESH_TOKEN_TTL)


def decode_refresh_token(token: str, secret: str, now: datetime) -> dict[str, str | int]:
    return decode_token(token, secret, now, "refresh")
