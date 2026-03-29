from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.Database.models import Users

class LoginRepository:
    @staticmethod
    async def get_by_telegram_id(
            session: AsyncSession,
            telegram_id: int
    ) -> Users | None:
        return await session.scalar(select(Users).where(Users.telegram_id == telegram_id))