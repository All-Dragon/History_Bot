from sqlalchemy import create_engine, String, Integer, ForeignKey, text, Boolean, select, or_, desc, asc, func, Table, \
    Column, case, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship, selectinload, joinedload, \
    sessionmaker
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.types import DateTime, JSON
from datetime import datetime
from typing import Optional, List
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.ext.mutable import MutableList

roles = ('Ученик', 'Преподаватель', 'Админ')
user_role_enum = PG_ENUM(*roles, name = 'user_role')

question_types = ('multiple_choice', 'free_text')
question_types_enum = PG_ENUM(*question_types, name = 'question_type')

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique= True, index = True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable= True)

    role: Mapped[str] = mapped_column(
        user_role_enum,
        default= 'Ученик',
        nullable= False
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone= True),
        nullable= True,
        index = True
    )


    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )


    questions: Mapped[list['Questions']] = relationship(back_populates='author')
    answers: Mapped[list['Answers']] = relationship(back_populates='user')
    groups: Mapped[list['GroupMember']] = relationship(back_populates= 'user')
    bans: Mapped[list['Ban']] = relationship(back_populates= 'user')
    created_groups: Mapped[list['Groups']] = relationship(
        'Groups', back_populates='teacher', foreign_keys='Groups.teacher_id'
    )
    created_tests: Mapped[List["Test"]] = relationship("Test", back_populates="creator")
    test_attempts: Mapped[List["TestAttempt"]] = relationship("TestAttempt", back_populates="user")

    @classmethod
    def active(cls):
        return cls.deleted_at.is_(None)
    @classmethod
    def non_active(cls):
        return cls.deleted_at.is_not(None)
    @classmethod
    def by_telegram_id(cls, telegram_id: int):
        return cls.telegram_id == telegram_id


class Questions(Base):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    text: Mapped[str] = mapped_column(String, nullable= False)

    options: Mapped[Optional[list[str]]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=True,
        default = None
    )

    correct_answer: Mapped[str] = mapped_column(String, nullable= False)
    topic: Mapped[str | None] = mapped_column(String, nullable= True)
    difficulty: Mapped[int] = mapped_column(Integer, default= 1)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    image_url: Mapped[str | None] = mapped_column(String, nullable= True)
    status: Mapped[str] = mapped_column(String(20), default='draft', index=True)  # draft → published → archived
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )
    question_type: Mapped[str] = mapped_column(
        question_types_enum,
        default = 'multiple_choice',
        index = True,
        nullable= False
    )



    author: Mapped['Users'] = relationship(back_populates= 'questions')
    answers: Mapped['Answers'] = relationship(back_populates= 'question')
    test_questions: Mapped[List["TestQuestion"]] = relationship("TestQuestion", back_populates="question")

class Answers(Base):
    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey('questions.id'))
    answer: Mapped[str] = mapped_column(String, nullable= False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable= False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped['Users'] = relationship(back_populates= 'answers')
    question: Mapped[Questions] = relationship(back_populates= 'answers')

class Groups(Base):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    name: Mapped[str] = mapped_column(String, nullable= False)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable= False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    teacher: Mapped['Users'] = relationship('Users', back_populates='created_groups')
    members: Mapped[list['GroupMember']] = relationship(back_populates= 'group')

class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey('groups.id'), nullable= False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable= False)
    joint_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped['Groups'] = relationship(back_populates= 'members')
    user: Mapped['Users'] = relationship(back_populates= 'groups')

class Ban(Base):
    __tablename__ = 'bans'

    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    reason: Mapped[str] = mapped_column(String, nullable= False)
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone= True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped['Users'] = relationship(back_populates= 'bans')



test_status_enum = PG_ENUM(
    "draft",
    "published",
    "archived",
    name="test_status"
)

attempt_status_enum = PG_ENUM(
    "in_progress",
    "finished",
    "cancelled",
    name="attempt_status"
)



class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)

    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        test_status_enum,
        nullable=False,
        server_default="draft",
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    creator: Mapped["Users"] = relationship(
        back_populates="created_tests"
    )

    questions: Mapped[List["TestQuestion"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="TestQuestion.order"
    )

    attempts: Mapped[List["TestAttempt"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan"
    )





from sqlalchemy import UniqueConstraint

class TestQuestion(Base):
    __tablename__ = "test_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id"),
        nullable=False,
        index=True
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
        index=True
    )

    order: Mapped[int] = mapped_column(Integer, nullable=False)

    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1"
    )

    test: Mapped["Test"] = relationship(back_populates="questions")
    question: Mapped["Questions"] = relationship(
        back_populates="test_questions"
    )

    __table_args__ = (
        UniqueConstraint(
            "test_id",
            "question_id",
            name="uq_test_question"
        ),
    )


from sqlalchemy import Index

class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id"),
        nullable=False,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    score: Mapped[Optional[int]] = mapped_column(Integer)

    max_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0"
    )

    status: Mapped[str] = mapped_column(
        attempt_status_enum,
        nullable=False,
        server_default="in_progress",
        index=True
    )

    test: Mapped["Test"] = relationship(back_populates="attempts")
    user: Mapped["Users"] = relationship(back_populates="test_attempts")

    answers: Mapped[List["TestAnswer"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_test_attempt_user_test",
            "user_id",
            "test_id"
        ),
    )


class TestAnswer(Base):
    __tablename__ = "test_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("test_attempts.id"),
        nullable=False,
        index=True
    )

    test_question_id: Mapped[int] = mapped_column(
        ForeignKey("test_questions.id"),
        nullable=False,
        index=True
    )

    user_answer: Mapped[str] = mapped_column(String, nullable=False)

    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)

    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    attempt: Mapped["TestAttempt"] = relationship(back_populates="answers")
    test_question: Mapped["TestQuestion"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "test_question_id",
            name="uq_attempt_question"
        ),
    )
