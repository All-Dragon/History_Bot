from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from Database.models import Users, Questions, Answers
from sqlalchemy.orm import joinedload
class StatRepository:

    @staticmethod
    async def get_my_stats(session: AsyncSession,
                           current_user: Users):
        result = await session.execute(
            select(
                func.sum(
                    case(
                        (Answers.user_id == current_user.id, 1),
                        else_=0
                    )
                ).label('total_question'),

                func.sum(
                    case(
                        (
                            (Answers.user_id == current_user.id) &
                            (Answers.is_correct == True),
                            1
                        ),

                        else_=0
                    )
                ).label('right_answer')

            )
        )

        return result

    @staticmethod
    async def get_stats_user(session: AsyncSession,
                             current_user: Users):
        result = await session.execute(
            select(
                func.count(Users.id).label('total_user'),

                func.count(
                    case(
                        (Users.deleted_at.is_(None), Users.id)
                    )
                ).label('current_user'),

                func.count(
                    case(
                        (Users.deleted_at.isnot(None), Users.id)
                    )
                ).label('deleted_user')
            )
        )
        return result

    @staticmethod
    async def get_stats_answer(session: AsyncSession,
                               current_user: Users,
                               question_id: int):
        result = await session.execute(
            select(Answers)
            .where(Answers.question_id == question_id)
            .options(joinedload(Answers.user))
            .order_by(Answers.created_at.desc())
        )
        result = result.scalars().all()
        return result
