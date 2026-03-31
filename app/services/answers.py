from app.repositories.answers import AnswerRepository
from app.repositories.questions import QuestionRepository
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.answers import AnswerCreate
from app.db.models import Users
logger = logging.getLogger(__name__)

class AnswerService:
    @staticmethod
    async def all(session: AsyncSession,
                  current_user: Users):
        logger.info('Получение всех ответов пользователем %s', current_user.telegram_id)
        answer = await AnswerRepository.get_all(session = session)
        answer = answer.all()
        if not answer:
            logger.warning('В БД ещё нет ответов на вопросы')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Ответов ещё нет')
        logger.info('Успешное получение ответов пользователем %s', current_user.telegram_id)
        return answer

    @staticmethod
    async def create(session: AsyncSession,
                     current_user: Users,
                     data: AnswerCreate):
        logger.info('Создание ответа на вопрос пользователем %s', current_user.telegram_id)
        question = await QuestionRepository.get_by_questions_id(session = session,
                                                              question_id = data.question_id)
        if not question:
            logger.warning('Пользователь попытался ответить на несуществующий вопрос')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Вопрос не найден')

        try:
            answer = await AnswerRepository.create_answer(session = session,
                                                current_user = current_user,
                                                data = data)
            logger.info('Успешное создание ответа на вопрос пользователем %s', current_user.telegram_id)
        except Exception as e:
            logger.exception('Ошибка создания ответа на вопрос пользователем %s', current_user.telegram_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера')
        return answer

    @staticmethod
    async def get(session: AsyncSession,
                  answer_id: int,
                  current_user: Users):
        logger.info('Получение ответа %s пользователем %s', answer_id, current_user.telegram_id)
        answer = await AnswerRepository.get_by_id(session = session,
                                                  answer_id = answer_id)
        if not answer:
            logger.warning('Ответа под таким id %s не существует', answer_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Ответа под таким answer_id: {answer_id} нет')
        logger.info('Успешное получение ответа %s пользователем %s', answer_id, current_user.telegram_id)
        return answer