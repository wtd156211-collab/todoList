from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: UUID, payload: TaskCreate) -> Task:
        task = Task(
            user_id=user_id,
            category_id=payload.category_id,
            title=payload.title.strip(),
            note=payload.note,
            priority=payload.priority,
            timezone=payload.timezone,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def list(self, user_id: UUID) -> list[Task]:
        result = await self.session.scalars(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )
        return list(result)

    async def update(self, user_id: UUID, task_id: UUID, payload: TaskUpdate) -> Task:
        task = await self._get_owned(user_id, task_id)
        if task.version != payload.version:
            raise ApiError(409, "CONFLICT", "任务已在其他设备修改，请刷新后重试")

        changes = payload.model_dump(exclude_unset=True, exclude={"version"})
        for field, value in changes.items():
            setattr(task, field, value)
        if payload.status == "completed":
            task.completed_at = datetime.now(timezone.utc)
        elif payload.status == "todo":
            task.completed_at = None
        task.version += 1
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, user_id: UUID, task_id: UUID) -> None:
        task = await self._get_owned(user_id, task_id)
        await self.session.delete(task)
        await self.session.commit()

    async def _get_owned(self, user_id: UUID, task_id: UUID) -> Task:
        task = await self.session.scalar(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        if task is None:
            raise ApiError(404, "NOT_FOUND", "任务不存在或已被删除")
        return task
