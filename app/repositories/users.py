from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Users
from datetime import datetime, timezone
from app.schemas import CreateUser
from app.core.hash import hash_password

class UserRepository:
    @staticmethod
    async def get_all_user(
            session: AsyncSession
    ) -> list[Users] | None:
        return await session.scalars(select(Users))

    @staticmethod
    async def get_by_telegram_id(session: AsyncSession,
                                 telegram_id: int):
        return await session.scalar(select(Users).where(Users.telegram_id == telegram_id))

    @staticmethod
    async def create_user(session: AsyncSession,
                          data: CreateUser):
        password = hash_password(data.password)
        new_user = Users(
            telegram_id=data.telegram_id,
            password_hash = password,
            username=data.username,
            role=data.role,
            is_banned=data.is_banned
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    @staticmethod
    async def change_name(
            session: AsyncSession,
            user: Users,
            new_name: str
    ):
        user.username = new_name
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def change(
            session: AsyncSession,
            user: Users,
            updated_data: dict
    ):
        for field, value in updated_data.items():
            setattr(user, field, value)

        await session.commit()
        await session.refresh(user)
        return user


    @staticmethod
    async def get_active_user(
            session: AsyncSession,
            telegram_id: int
    ):
        user = await session.scalar(
            select(Users).where(Users.telegram_id == telegram_id, Users.active())
        )
        return user

    @staticmethod
    async def get_deleted_user(
            session: AsyncSession,
            telegram_id: int
    ):
        user = await session.scalar(
            select(Users).where(Users.telegram_id == telegram_id, Users.non_active())
        )
        return user

    @staticmethod
    async def restore_user(
            session: AsyncSession,
            user: Users
    ):
        user.deleted_at = None
        try:
            await session.commit()
            await session.refresh(user)
        except Exception as e:
            await session.rollback()
        return user


    @staticmethod
    async def soft_delete_user(
            session: AsyncSession,
            user: Users
    ):
        user.deleted_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def hard_delete_user(
            session: AsyncSession,
            user: Users
    ):
        await session.delete(user)
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
        return
