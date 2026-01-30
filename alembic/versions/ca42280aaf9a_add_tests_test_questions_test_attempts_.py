"""add tests, test_questions, test_attempts, test_answers

Revision ID: ca42280aaf9a
Revises: d95f9757ce74
Create Date: 2026-01-30 22:34:07.546070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca42280aaf9a'
down_revision: Union[str, Sequence[str], None] = 'd95f9757ce74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- tests ----------
    op.create_table(
        'tests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.String(length=20),
            server_default='draft',
            nullable=False
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'])
    )

    op.create_index('ix_tests_creator_id', 'tests', ['creator_id'])
    op.create_index('ix_tests_status', 'tests', ['status'])

    # ---------- test_attempts ----------
    op.create_table(
        'test_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'started_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_score', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['test_id'], ['tests.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    op.create_index('ix_test_attempts_test_id', 'test_attempts', ['test_id'])
    op.create_index('ix_test_attempts_user_id', 'test_attempts', ['user_id'])

    # ---------- test_questions ----------
    op.create_table(
        'test_questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column(
            'points',
            sa.Integer(),
            server_default='1',
            nullable=False
        ),
        sa.ForeignKeyConstraint(['test_id'], ['tests.id']),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.UniqueConstraint(
            'test_id',
            'question_id',
            name='uq_test_questions_test_question'
        )
    )

    op.create_index('ix_test_questions_test_id', 'test_questions', ['test_id'])
    op.create_index('ix_test_questions_question_id', 'test_questions', ['question_id'])

    # ---------- test_answers ----------
    op.create_table(
        'test_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('attempt_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('answer', sa.String(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column(
            'answered_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['attempt_id'], ['test_attempts.id']),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
    )

    op.create_index('ix_test_answers_attempt_id', 'test_answers', ['attempt_id'])
    op.create_index('ix_test_answers_question_id', 'test_answers', ['question_id'])


def downgrade() -> None:
    op.drop_index('ix_test_answers_question_id', table_name='test_answers')
    op.drop_index('ix_test_answers_attempt_id', table_name='test_answers')
    op.drop_table('test_answers')

    op.drop_index('ix_test_questions_question_id', table_name='test_questions')
    op.drop_index('ix_test_questions_test_id', table_name='test_questions')
    op.drop_table('test_questions')

    op.drop_index('ix_test_attempts_user_id', table_name='test_attempts')
    op.drop_index('ix_test_attempts_test_id', table_name='test_attempts')
    op.drop_table('test_attempts')

    op.drop_index('ix_tests_status', table_name='tests')
    op.drop_index('ix_tests_creator_id', table_name='tests')
    op.drop_table('tests')

