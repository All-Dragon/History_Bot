"""empty message

Revision ID: d95f9757ce74
Revises: 58fe61caefec
Create Date: 2026-01-16 00:07:59.806156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd95f9757ce74'
down_revision: Union[str, Sequence[str], None] = '58fe61caefec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    question_type_enum = postgresql.ENUM(
        'multiple_choice', 'free_text',
        name='question_type'
    )
    question_type_enum.create(op.get_bind(), checkfirst=True)


    op.add_column(
        'questions',
        sa.Column(
            'question_type',
            question_type_enum,
            nullable=False,
            server_default='multiple_choice'
        )
    )


    op.alter_column(
        'questions',
        'options',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=True
    )


    op.create_index(
        op.f('ix_questions_question_type'),
        'questions',
        ['question_type'],
        unique=False
    )


def downgrade() -> None:

    op.drop_index(
        op.f('ix_questions_question_type'),
        table_name='questions'
    )


    op.drop_column('questions', 'question_type')


    op.alter_column(
        'questions',
        'options',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=False
    )


    question_type_enum = postgresql.ENUM(
        name='question_type'
    )
    question_type_enum.drop(op.get_bind(), checkfirst=True)
