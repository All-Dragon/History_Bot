from datetime import datetime
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional


class AnswersStats(BaseModel):
    total_question: int = Field(..., description= 'Сколько всего вопросов решил')
    right_answer: int = Field(..., description= 'Сколько всего правильных ответов дал')

    @computed_field
    @property
    def right_answer_percentage(self) -> str:
        if self.total_question == 0:
            return str(0.0) + '%'
        elif self.right_answer == 0:
            return str(0.0) + '%'
        return str(round(self.right_answer / self.total_question * 100, 2)) + '%'


class Stats_User(BaseModel):
    total_user: int
    current_user: int
    deleted_user: int


class AnswerDetail(BaseModel):
    username: str = Field(..., description= 'Никнейм пользователя, давшего ответ')
    user_answer: str = Field(..., description= 'Ответ пользователя')
    is_correct: bool = Field(..., description= 'Верно или нет')
    answered_at: datetime = Field(..., description= 'Время и дата ответа')

    model_config = {"from_attributes": True}