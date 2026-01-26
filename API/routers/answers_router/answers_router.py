from API.routers.bans_router.bans_schemas import *
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter
from API.routers.answers_router.answer_schemas import *
from JWT.auth import require_role, get_current_user

answers_router = APIRouter(
    prefix= '/answers',
    tags= ['answers']
)

@answers_router.get('')
async def get_all_answers(session: AsyncSession = Depends(get_async_session),
                          current_user: Users = Depends(require_role('Админ'))):

    result = await session.scalars(select(Answers))
    result = result.all()

    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= 'Ответов ещё нет')

    return result




@answers_router.post('/create', response_model= AnswerRead, status_code= status.HTTP_201_CREATED)
async def create_answer(data: AnswerCreate,
                        current_user: Users = Depends(get_current_user),
                        session: AsyncSession = Depends(get_async_session)
                        ):

    question = await session.scalar(select(Questions).where(Questions.id == data.question_id))
    if not question:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail= 'Вопрос не найден')


    new_answer = Answers(
        user_id = current_user.id,
        question_id = data.question_id,
        answer = data.answer,
        is_correct = data.is_correct
    )

    session.add(new_answer)
    await session.commit()
    await session.refresh(new_answer)

    return AnswerRead.model_validate(new_answer)


@answers_router.get('/{answer_id}', response_model= AnswerRead)
async def get_answer_by_id(answer_id: int,
                           session: AsyncSession = Depends(get_async_session),
                           current_user: Users = Depends(require_role('Админ'))):

    result = await session.scalar(select(Answers).where(Answers.id == answer_id))
    if result is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= f'Ответа под таким answer_id: {answer_id} нет')

    return AnswerRead.model_validate(result)

