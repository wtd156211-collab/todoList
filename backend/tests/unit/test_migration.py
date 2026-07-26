from pathlib import Path


def test_initial_migration_exists() -> None:
    assert Path("alembic/versions/0001_initial_schema.py").is_file()
