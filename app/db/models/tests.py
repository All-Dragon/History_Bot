from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import attempt_status_enum, test_status_enum

if TYPE_CHECKING:
    from .questions import Questions
    from .users import Users


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        test_status_enum,
        nullable=False,
        server_default="draft",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    creator: Mapped[Users] = relationship(back_populates="created_tests")
    questions: Mapped[list[TestQuestion]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="TestQuestion.order",
    )
    attempts: Mapped[list[TestAttempt]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
    )


class TestQuestion(Base):
    __tablename__ = "test_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    test: Mapped[Test] = relationship(back_populates="questions")
    question: Mapped[Questions] = relationship(back_populates="test_questions")

    __table_args__ = (
        UniqueConstraint(
            "test_id",
            "question_id",
            name="uq_test_question",
        ),
    )


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    score: Mapped[Optional[int]] = mapped_column(Integer)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(
        attempt_status_enum,
        nullable=False,
        server_default="in_progress",
        index=True,
    )

    test: Mapped[Test] = relationship(back_populates="attempts")
    user: Mapped[Users] = relationship(back_populates="test_attempts")
    answers: Mapped[list[TestAnswer]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_test_attempt_user_test",
            "user_id",
            "test_id",
        ),
    )


class TestAnswer(Base):
    __tablename__ = "test_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id"), nullable=False, index=True)
    test_question_id: Mapped[int] = mapped_column(ForeignKey("test_questions.id"), nullable=False, index=True)
    user_answer: Mapped[str] = mapped_column(String, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    attempt: Mapped[TestAttempt] = relationship(back_populates="answers")
    test_question: Mapped[TestQuestion] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "test_question_id",
            name="uq_attempt_question",
        ),
    )
