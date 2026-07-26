from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate


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
