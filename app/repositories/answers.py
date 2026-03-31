from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Users, Answers
from app.schemas.answers import AnswerCreate

class AnswerRepository:
    @staticmethod
    async def get_all(session: AsyncSession):
        return await session.scalars(select(Answers))

    @staticmethod
    async def get_by_id(session: AsyncSession,
                        answer_id: int):
        return await session.scalar(select(Answers).where(Answers.id == answer_id))

    @staticmethod
    async def create_answer(session: AsyncSession,
                            current_user: Users,
                            data: AnswerCreate):
        new_answer = Answers(
            user_id=current_user.id,
            question_id=data.question_id,
            answer=data.answer,
            is_correct=data.is_correct
        )
        session.add(new_answer)
        await session.commit()
        await session.refresh(new_answer)
        return new_answer