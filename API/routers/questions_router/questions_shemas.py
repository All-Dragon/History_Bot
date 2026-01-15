from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, field_validator, HttpUrl, validator
from typing import Optional, List, Literal, Union


class QuestionBase(BaseModel):
    text: str = Field(..., min_length=8, max_length=2000)
    topic: Optional[str] = Field(None, max_length=120)
    difficulty: int = Field(default=1, ge=1, le=5)
    image_url: Optional[HttpUrl] = None
    status: Literal["draft", "published", "archived"] = "draft"
    question_type: Literal["multiple_choice", "free_text"] = "multiple_choice"


class MultipleChoiceCreate(QuestionBase):
    question_type: Literal["multiple_choice"] = "multiple_choice"
    options: List[str] = Field(..., min_items=2, max_items=8)
    correct_answer: str = Field(...)

    @validator("correct_answer")
    def correct_answer_must_be_in_options(cls, v, values):
        if "options" in values and v not in values["options"]:
            raise ValueError("Правильный ответ должен быть одним из предложенных вариантов")
        return v


class FreeTextCreate(QuestionBase):
    question_type: Literal["free_text"] = "free_text"
    correct_answer: str = Field(..., min_length=1, max_length=200)
    options: Optional[List[str]] = Field(None, description="Не используется для свободного ответа")

# Для клиента удобнее иметь одну точку входа
QuestionCreate = Union[MultipleChoiceCreate, FreeTextCreate]


class QuestionOut(QuestionBase):
    id: int
    created_by: int
    created_at: datetime
    options: Optional[List[str]] = None
    correct_answer: str

    class Config:
        from_attributes = True
