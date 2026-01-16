from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, field_validator, HttpUrl, validator, ValidationInfo
from typing import Optional, List, Literal, Union, Annotated


class QuestionBase(BaseModel):
    text: str = Field(..., min_length=8, max_length=2000)
    topic: Optional[str] = Field(None, max_length=120)
    difficulty: int = Field(default=1, ge=1, le=5)
    image_url: Optional[HttpUrl] = None
    status: Literal["draft", "published", "archived"] = "draft"
    question_type: Literal["multiple_choice", "free_text"] = "multiple_choice"


class MultipleChoiceCreate(QuestionBase):
    question_type: Literal["multiple_choice"] = "multiple_choice"
    options: List[str] = Field(..., min_items=2, max_items=8, description= 'Варианты ответов (минимум 2, максимум 8)')
    correct_answer: str = Field(..., description="Правильный вариант (должен быть в options)")

    @field_validator("options", mode="before")
    @classmethod
    def normalize_options(cls, v: any) -> List[str]:
        if isinstance(v, tuple):
            v = list(v)
        if not isinstance(v, list):
            raise ValueError("options должно быть списком")
        return [str(item) for item in v]  # защита от любых не-строк

    @field_validator("correct_answer")
    @classmethod
    def check_correct_in_options(cls, v: str, info: ValidationInfo) -> str:
        options = info.data.get("options")
        if options is not None and v not in options:
            raise ValueError("Правильный ответ должен быть одним из вариантов в options")
        return v


class FreeTextCreate(QuestionBase):
    question_type: Literal["free_text"] = "free_text"
    correct_answer: str = Field(..., min_length=1, max_length=200)
    options: None = Field(default=None, description="Не используется")

    @field_validator("options", mode="before")
    @classmethod
    def forbid_options(cls, v: any) -> None:
        if v is not None:
            raise ValueError("Для free_text поле options должно отсутствовать или быть null")
        return None

    @field_validator("options", mode="before")
    @classmethod
    def forbid_options_in_free_text(cls, v):
        if v is not None:
            raise ValueError("Поле options не должно передаваться для типа free_text")
        return None

# Для клиента удобнее иметь одну точку входа
QuestionCreate = Union[MultipleChoiceCreate, FreeTextCreate]


class QuestionOut(QuestionBase):
    id: int
    created_by: int
    created_at: datetime
    options: Optional[List[str]] = None
    correct_answer: str

    @field_validator("options", mode="before")
    @classmethod
    def normalize_options(cls, v):
        if v is None:
            return None
        if isinstance(v, (list, tuple)):
            return [str(item) for item in v]
        raise ValueError("Некорректный формат options")

    model_config = {"from_attributes": True}

    model_config = {"from_attributes": True}
