from datetime import datetime
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional

class AnswerBase(BaseModel):
    question_id: int = Field(..., description='ID вопроса')

class AnswerCreate(AnswerBase):
    answer: str = Field(..., min_length=1, description='Ответ пользователя')
    is_correct: bool = Field(default= False, description="Правильно ли ответил")
    @field_validator("answer")
    @classmethod
    def strip_answer(cls, v: str):
        return v.strip()

class AnswerRead(AnswerBase):
    id: int
    user_id: int
    answer: str
    is_correct: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class AnswerOut(AnswerBase):
    id: int
    answer: str
    is_correct: bool

    model_config = {"from_attributes": True}

