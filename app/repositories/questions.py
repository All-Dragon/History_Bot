from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models import Questions, Users
from typing import Optional
from app.schemas import QuestionCreate
class QuestionRepository:
    @staticmethod
    async def get_all_questions(session: AsyncSession):
        return await session.scalars(select(Questions))

    @staticmethod
    async def get_all_my_questions(session: AsyncSession,
                                   user: Users):
        return await session.scalars(select(Questions).where(Questions.created_by == user.id))

    @staticmethod
    async def get_random_questions(session: AsyncSession,
                                   topic: Optional[str] = None,
                                   difficulty: Optional[int] = None):
        query = select(Questions).where(Questions.status == 'published')

        if topic:
            query = query.where(func.lower(Questions.topic) == topic.lower())
        if difficulty:
            query = query.where(Questions.difficulty == difficulty)

        query = query.order_by(func.random()).limit(1)

        result = await session.execute(query)
        question = result.scalar()
        return question

    @staticmethod
    async def get_by_questions_id(session: AsyncSession,
                                  question_id: int):
        return await session.scalar(select(Questions).where(Questions.id == question_id))


    @staticmethod
    async def create_question(session: AsyncSession,
                              data: QuestionCreate,
                              current_user = Users):

        question = Questions(
            text=data.text,
            options=list(data.options) if data.options else None,
            correct_answer=data.correct_answer,
            topic=data.topic,
            difficulty=data.difficulty,
            created_by=current_user.id,
            image_url=str(data.image_url) if data.image_url else None,
            status=data.status,
            question_type=data.question_type,
        )
        try:
            session.add(question)
            await session.commit()
            await session.refresh(question)
            return question
        except Exception:
            await session.rollback()
            raise

