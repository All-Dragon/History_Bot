from API.routers.questions_router.questions_shemas import *
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter
from typing import List
from JWT.auth import get_current_user, require_role
import logging

logger = logging.getLogger(__name__)

questions_router = APIRouter(
    prefix= '/question',
    tags = ['question']
)


@questions_router.get('', response_model=List[QuestionOut])
async def get_all_questions(session: AsyncSession = Depends(get_async_session),
                            current_user: Users = Depends(require_role('Преподаватель', 'Админ'))):
    logger.info('Просмотр всех вопросов пользователем %s', current_user.telegram_id)
    result = await session.scalars(select(Questions))
    result = result.all()
    if not result:
        logger.warning('В базе нет доступных вопросов')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= 'В базе ещё нет доступных вопросов')
    logger.info('Успешный просмотр всех вопросов пользователем %s', current_user.telegram_id)
    return result

@questions_router.get('/my', response_model= List[QuestionOut])
async def get_my_questions(session: AsyncSession = Depends(get_async_session),
                           current_user: Users = Depends(require_role('Преподаватель', 'Админ'))):
    logger.info('Просмотр своих вопросов пользователем %s', current_user.telegram_id)

    result = await session.scalars(select(Questions).where(Questions.created_by == current_user.id))
    result = result.all()
    if result is None:
        logger.warning('Вопросы пользователя %s не найдены', current_user.telegram_id)
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= 'Вопросы не найдены, проверьте создавали ли вы их.')
    logger.info('Успешный просмотр своих вопросов пользователем %s', current_user.telegram_id)
    return result


@questions_router.get("/random", response_model=QuestionOut)
async def get_random_question(
    session: AsyncSession = Depends(get_async_session),
    topic: Optional[str] = None,
    difficulty: Optional[int] = None
):
    logger.info('Просмотр рандомных вопросов')
    query = select(Questions).where(Questions.status == 'published')

    if topic:
        query = query.where(func.lower(Questions.topic) == topic.lower())
    if difficulty:
        query = query.where(Questions.difficulty == difficulty)

    query = query.order_by(func.random()).limit(1)

    result = await session.execute(query)
    question = result.scalar()

    if not question:
        logger.warning('Нет опубликованных вопросов')
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail= 'Нет опубликованных вопросов')

    logger.info('Успешно получен случайный вопрос %s', question.id)
    return QuestionOut.model_validate(question)


@questions_router.get('/{question_id}', response_model= QuestionOut)
async def get_question_by_id(question_id: int, session: AsyncSession = Depends(get_async_session)):
    logger.info('Просмотр вопроса %s', question_id)
    result = await session.scalar(select(Questions).where(Questions.id == question_id))
    if not result:
        logger.warning('Вопрос с id %s не найден', question_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f'Вопрос с ID: {question_id} не найден')
    logger.info('Успешный просмотр вопроса %s', question_id)
    return QuestionOut.model_validate(result)


@questions_router.post('/new', status_code= status.HTTP_201_CREATED, response_model= QuestionOut)
async def create_question(
        data: QuestionCreate,
        session: AsyncSession = Depends(get_async_session),
        current_user: Users = Depends(require_role('Преподаватель', 'Админ'))):
    logger.info('Создание нового вопроса пользователем %s', current_user.telegram_id)

    if data.question_type == 'multiple_choice':
        if not data.options:
            logger.warning('Не указаны варианты ответов для multiple_choice')
            raise HTTPException(
                status = status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail = 'Для типа "multiple_choice" необходимы варианты ответов!'
            )
    elif data.question_type == 'free_text':
        if data.options is not None:
            logger.warning('Не указаны варианты ответов для free_text')
            raise HTTPException(
                status=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail='Для типа "free_text" поле options не используется!'
            )

    question = Questions(
        text = data.text,
        options = list(data.options) if data.options else None,
        correct_answer = data.correct_answer,
        topic = data.topic,
        difficulty = data.difficulty,
        created_by = current_user.id,
        image_url = str(data.image_url) if data.image_url else None,
        status = data.status,
        question_type = data.question_type,
    )
    try:
        session.add(question)
        await session.commit()
        await session.refresh(question)
        logger.info('Успешное создание вопроса %s пользователем %s', question.id, current_user.telegram_id)
    except Exception as e:
        await session.rollback()
        logger.exception('Ошибка при создании вопроса')
        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f'Ошибка сервера'
        )

    return QuestionOut.model_validate(question)