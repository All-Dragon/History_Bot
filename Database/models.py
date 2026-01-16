from sqlalchemy import create_engine, String, Integer, ForeignKey, text, Boolean, select, or_, desc, asc, func, Table, \
    Column, case, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship, selectinload, joinedload, \
    sessionmaker
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.types import DateTime, JSON
from datetime import datetime
from typing import Optional
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
        nullable=True
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