from importlib import import_module
from pathlib import Path

import pytest
from pydantic import ValidationError


def test_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    assert Path("app/core/config.py").is_file()
    settings_module = import_module("app.core.config")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        settings_module.Settings()
