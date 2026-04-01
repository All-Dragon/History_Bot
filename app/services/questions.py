from app.repositories import QuestionRepository
from app.schemas import QuestionCreate
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Users
from typing import Optional
logger = logging.getLogger(__name__)

class QuestionService:
    @staticmethod
    async def all(session: AsyncSession,
                  current_user: Users):
        logger.info('Просмотр всех вопросов пользователем %s', current_user.telegram_id)
        questions = await QuestionRepository.get_all_questions(session = session)
        questions = questions.all()
        if not questions:
            logger.warning('В базе нет доступных вопросов')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='В базе ещё нет доступных вопросов')
        return questions

    @staticmethod
    async def all_my(session: AsyncSession,
                     current_user: Users):
        logger.info('Просмотр своих вопросов пользователем %s', current_user.telegram_id)
        questions = await QuestionRepository.get_all_my_questions(session = session, user = current_user)
        if not questions:
            logger.warning('Вопросы пользователя %s не найдены', current_user.telegram_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Вопросы не найдены, проверьте создавали ли вы их.')
        logger.info('Успешный просмотр своих вопросов пользователем %s', current_user.telegram_id)
        return questions


    @staticmethod
    async def random(session: AsyncSession,
                     topic: Optional[str] = None,
                     difficulty: Optional[int] = None
                     ):
        logger.info('Просмотр рандомных вопросов')
        question = await QuestionRepository.get_random_questions(session = session,
                                                           topic = topic,
                                                           difficulty = difficulty)
        if not question:
            logger.warning('Нет опубликованных вопросов')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Нет опубликованных вопросов')

        logger.info('Успешно получен случайный вопрос %s', question.id)
        return question


    @staticmethod
    async def by_id(session: AsyncSession,
                    question_id: int):
        logger.info('Просмотр вопроса %s', question_id)

        question = await QuestionRepository.get_by_questions_id(session = session,
                                                          question_id = question_id)
        if not question:
            logger.warning('Вопрос с id %s не найден', question_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Вопрос с ID: {question_id} не найден')
        logger.info('Успешный просмотр вопроса %s', question_id)
        return question


    @staticmethod
    async def create(session: AsyncSession,
                     data: QuestionCreate,
                     current_user: Users):
        logger.info('Создание нового вопроса пользователем %s', current_user.telegram_id)

        if data.question_type == 'multiple_choice':
            if not data.options:
                logger.warning('Не указаны варианты ответов для multiple_choice')
                raise HTTPException(
                    status=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail='Для типа "multiple_choice" необходимы варианты ответов!'
                )
        elif data.question_type == 'free_text':
            if data.options is not None:
                logger.warning('Не указаны варианты ответов для free_text')
                raise HTTPException(
                    status=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail='Для типа "free_text" поле options не используется!'
                )

        try:
            question = await QuestionRepository.create_question(session = session,
                                                                data = data,
                                                                current_user = current_user)
            logger.info('Успешное создание вопроса %s пользователем %s', question.id, current_user.telegram_id)
        except Exception as e:
            logger.exception('Ошибка при создании вопроса')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Ошибка сервера'
            )

        return question
