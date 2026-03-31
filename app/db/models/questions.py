from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base
from .enums import question_types_enum

if TYPE_CHECKING:
    from .answers import Answers
    from .tests import TestQuestion
    from .users import Users


class Questions(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)

    options: Mapped[Optional[list[str]]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=True,
        default=None,
    )

    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    question_type: Mapped[str] = mapped_column(
        question_types_enum,
        default="multiple_choice",
        index=True,
        nullable=False,
    )

    author: Mapped[Users] = relationship(back_populates="questions")
    answers: Mapped[list[Answers]] = relationship(back_populates="question")
    test_questions: Mapped[list[TestQuestion]] = relationship(back_populates="question")
