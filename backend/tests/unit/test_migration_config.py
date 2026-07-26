from importlib import import_module
from pathlib import Path


def test_asyncpg_url_converts_to_sync_psycopg_url() -> None:
    assert Path("app/db/migration.py").is_file()
    migration_module = import_module("app.db.migration")

    assert (
        migration_module.to_sync_database_url("postgresql+asyncpg://flowlist:secret@postgres:5432/flowlist")
        == "postgresql+psycopg://flowlist:secret@postgres:5432/flowlist"
    )
