from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    note: str = Field(default="", max_length=10000)
    category_id: UUID | None = Field(default=None, alias="categoryId")
    priority: Literal["low", "medium", "high"] = "medium"
    due_at: str | None = Field(default=None, alias="dueAt")
    timezone: str = "Asia/Shanghai"
    reminder_at: str | None = Field(default=None, alias="reminderAt")


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    note: str
    priority: Literal["low", "medium", "high"]
    status: Literal["todo", "completed"]
    version: int


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
