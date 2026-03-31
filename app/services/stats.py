from app.repositories.stats import StatRepository
from app.repositories.questions import QuestionRepository
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Users
from app.schemas.stats import AnswersStats, Stats_User, AnswerDetail


logger = logging.getLogger(__name__)

class StatService:

    @staticmethod
    async def my_stat(session: AsyncSession,
                      current_user: Users):
        logger.info('Извлечение статистики пользователя %s', current_user.telegram_id)
        try:
            result = await StatRepository.get_my_stats(session = session,
                                             current_user = current_user)
            stats_row = result.one_or_none()
            if stats_row is None:
                return AnswersStats(total_question=0, right_answer=0)
            stats_data = {
                'total_question': stats_row.total_question or 0,
                'right_answer': stats_row.right_answer or 0
            }
            logger.info('Успешное извлечение статистики пользователя %s', current_user.telegram_id)
            return AnswersStats(**stats_data)

        except Exception as e:
            logger.exception('Ошибка при извлечении статистики пользователя %s', current_user.telegram_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve statistics"
            )

    @staticmethod
    async def overview(session: AsyncSession,
                       current_user: Users):
        logger.info('Извлечение статистики по использованию сервиса')
        try:
            result = await StatRepository.get_stats_user(session = session,
                                                   current_user = current_user)
            stats_row = result.one()
            stats_data = {
                'total_user': stats_row.total_user,
                'current_user': stats_row.current_user,
                'deleted_user': stats_row.deleted_user
            }
            logger.info('Успешное извелечени статистики по использованию сервиса')
            return Stats_User(**stats_data)
        except Exception as e:
            logger.exception('Не удалось получить статистику по использованию сервиса')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve statistics"
            )

    @staticmethod
    async def answers_stats(session: AsyncSession,
                            question_id: int,
                            current_user: Users):
        logger.info('Получение ответов на вопрос %s', question_id)
        question = await QuestionRepository.get_by_questions_id(session = session,
                                                                question_id = question_id)
        if not question or question.created_by != current_user.id:
            logger.warning('У пользователя %s нет доступа к запрашиваемому вопросу %s', current_user.telegram_id,
                           question_id)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Нет доступа к этому вопросу')

        try:
            result = await StatRepository.get_stats_answer(session = session,
                                                           current_user = current_user,
                                                           question_id = question_id)
            logger.info('Успешное получение ответов на вопрос %s', question_id)
            return [
                AnswerDetail(
                    username=answer.user.username if answer.user else "Аноним",
                    user_answer=answer.answer,
                    is_correct=answer.is_correct,
                    answered_at=answer.created_at
                )
                for answer in result
            ]

        except Exception as e:
            logger.exception('Не удалось получить ответы на вопрос %s', question_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve answers"
            )
