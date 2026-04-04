from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import user_role_enum

if TYPE_CHECKING:
    from .answers import Answers
    from .bans import Ban
    from .groups import GroupMember, Groups
    from .questions import Questions
    from .tests import Test, TestAttempt


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    password_hash: Mapped[str] = mapped_column(String, nullable = False)

    role: Mapped[str] = mapped_column(
        user_role_enum,
        default="Ученик",
        nullable=False,
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    questions: Mapped[list[Questions]] = relationship(back_populates="author")
    answers: Mapped[list[Answers]] = relationship(back_populates="user")
    groups: Mapped[list[GroupMember]] = relationship(back_populates="user")
    bans: Mapped[list[Ban]] = relationship(back_populates="user")
    created_groups: Mapped[list[Groups]] = relationship(
        "Groups",
        back_populates="teacher",
        foreign_keys="Groups.teacher_id",
    )
    created_tests: Mapped[list[Test]] = relationship("Test", back_populates="creator")
    test_attempts: Mapped[list[TestAttempt]] = relationship("TestAttempt", back_populates="user")

    @classmethod
    def active(cls):
        return cls.deleted_at.is_(None)

    @classmethod
    def non_active(cls):
        return cls.deleted_at.is_not(None)

    @classmethod
    def by_telegram_id(cls, telegram_id: int):
        return cls.telegram_id == telegram_id
