from API.routers.questions_router.questions_shemas import *
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter

questions_router = APIRouter(
    prefix= '/question',
    tags = ['question']
)


@questions_router.get('')
async def get_all_questions(session: AsyncSession = Depends(get_async_session)):
    result = await session.scalars(select(Questions))
    result = result.all()
    return result

@questions_router.get('/{question_id}', response_model= QuestionOut)
async def get_question_by_id(question_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.scalar(select(Questions).where(Questions.id == question_id))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f'Вопрос с ID: {question_id} не найден')
    return result


@questions_router.post('/new', status_code= status.HTTP_201_CREATED, response_model= QuestionOut)
async def create_question(data: QuestionCreate, session: AsyncSession = Depends(get_async_session)):
    created_by = 1 # Заглушка, потом смени на telegram_id

    if data.question_type == 'multiple_choice':
        if not data.options:
            raise HTTPException(
                status = status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail = 'Для типа "multiple_choice" необходимы варианты ответов!'
            )
    elif data.question_type == 'free_text':
        if data.options is not None:
            raise HTTPException(
                status=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail='Для типа "free_text" поле options не используется!'
            )

    question = Questions(
        text = data.text,
        options = data.options,
        correct_answer = data.correct_answer,
        topic = data.topic,
        difficulty = data.difficulty,
        created_by = created_by,
        image_url = data.image_url,
        status = data.status,
        question_type = data.question_type,
    )
    try:
        session.add(question)
        await session.commit()
        await session.refresh(question)
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f'Ошибка: {str(e)}'
        )
    return question