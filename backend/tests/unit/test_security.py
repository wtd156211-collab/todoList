from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
from uuid import UUID


def test_access_token_round_trips_subject_and_type() -> None:
    assert Path("app/core/security.py").is_file()
    security = import_module("app.core.security")
    now = datetime(2026, 7, 26, tzinfo=timezone.utc)

    token = security.create_access_token(
        UUID("00000000-0000-0000-0000-000000000001"),
        "test-secret-with-at-least-thirty-two-bytes",
        now,
    )
    payload = security.decode_access_token(
        token,
        "test-secret-with-at-least-thirty-two-bytes",
        now + timedelta(minutes=1),
    )

    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"
    assert payload["type"] == "access"


def test_refresh_token_has_refresh_type() -> None:
    assert Path("app/core/security.py").is_file()
    security = import_module("app.core.security")
    now = datetime(2026, 7, 26, tzinfo=timezone.utc)

    token = security.create_refresh_token(
        UUID("00000000-0000-0000-0000-000000000001"),
        "test-secret-with-at-least-thirty-two-bytes",
        now,
    )

    assert security.decode_refresh_token(
        token,
        "test-secret-with-at-least-thirty-two-bytes",
        now + timedelta(minutes=1),
    )["type"] == "refresh"
