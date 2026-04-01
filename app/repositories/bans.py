from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Users, Ban
from app.schemas import Ban_Create

class BanRepository:
    @staticmethod
    async def get_all(session: AsyncSession):
        return await session.scalars(select(Ban))

    @staticmethod
    async def get_ban_user(session: AsyncSession,
                           user: Users):
        return await session.scalar(select(Ban).where(Ban.user_id == user.id))

    @staticmethod
    async def create_ban(session: AsyncSession,
                         user: Users,
                         data: Ban_Create):
        new_ban = Ban(
            user_id=user.id,
            reason=data.reason,
            expires_at=data.expires_at
        )
        user.is_banned = True
        session.add(new_ban)
        await session.commit()
        await session.refresh(new_ban)
        return new_ban

    @staticmethod
    async def unban(session: AsyncSession,
                    ban: Ban,
                    user: Users):
        await session.delete(ban)
        user.is_banned = False
        await session.commit()
        return
