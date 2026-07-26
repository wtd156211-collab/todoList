from importlib import import_module
from pathlib import Path


def test_task_model_contains_ownership_and_version_columns() -> None:
    assert Path("app/models/task.py").is_file()
    task_module = import_module("app.models.task")

    columns = task_module.Task.__table__.columns
    assert {"id", "user_id", "title", "priority", "status", "version", "created_at", "updated_at"} <= set(columns.keys())


def test_metadata_registers_all_core_tables() -> None:
    assert Path("app/models/__init__.py").is_file()
    models_module = import_module("app.models")

    assert {
        "users",
        "categories",
        "tasks",
        "task_attachments",
        "reminders",
        "notifications",
    } <= set(models_module.Base.metadata.tables.keys())
