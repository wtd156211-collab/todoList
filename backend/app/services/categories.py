from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, user_id: UUID) -> list[Category]:
        result = await self.session.scalars(
            select(Category).where(Category.user_id == user_id).order_by(Category.sort_order, Category.created_at)
        )
        return list(result)

    async def create(self, user_id: UUID, name: str, color: str) -> Category:
        category = Category(user_id=user_id, name=name.strip(), color=color)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
