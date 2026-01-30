"""normalize_test_schema_v2

Revision ID: f9eb0703a5b3
Revises: ca42280aaf9a
Create Date: 2026-01-30 22:42:53.204129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f9eb0703a5b3'
down_revision: Union[str, Sequence[str], None] = 'ca42280aaf9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    # ===== ENUMS =====
    attempt_status = postgresql.ENUM(
        "in_progress", "finished", "cancelled",
        name="attempt_status",
        create_type=True
    )
    test_status = postgresql.ENUM(
        "draft", "published", "archived",
        name="test_status",
        create_type=True
    )

    # создаём ENUM-типы, если их ещё нет
    attempt_status.create(op.get_bind(), checkfirst=True)
    test_status.create(op.get_bind(), checkfirst=True)

    # ===== TEST ANSWERS =====
    op.add_column("test_answers", sa.Column("test_question_id", sa.Integer(), nullable=False))
    op.add_column("test_answers", sa.Column("user_answer", sa.String(), nullable=False))

    op.drop_index("ix_test_answers_question_id", table_name="test_answers")
    op.create_index("ix_test_answers_test_question_id", "test_answers", ["test_question_id"])

    op.drop_constraint("test_answers_question_id_fkey", "test_answers", type_="foreignkey")
    op.create_foreign_key(
        "fk_test_answers_test_question",
        "test_answers",
        "test_questions",
        ["test_question_id"],
        ["id"]
    )

    op.create_unique_constraint("uq_attempt_question", "test_answers", ["attempt_id", "test_question_id"])

    op.drop_column("test_answers", "question_id")
    op.drop_column("test_answers", "answer")

    # ===== TEST ATTEMPTS =====
    op.add_column("test_attempts", sa.Column("score", sa.Integer()))
    op.add_column("test_attempts", sa.Column("max_score", sa.Integer(), server_default=text("0"), nullable=False))
    op.add_column("test_attempts", sa.Column("status", attempt_status, nullable=False))

    # Убираем дефолт перед сменой типа
    op.alter_column("test_attempts", "status", server_default=None)

    # Меняем тип через кастинг
    op.execute("""
        ALTER TABLE test_attempts
        ALTER COLUMN status TYPE attempt_status
        USING status::text::attempt_status
    """)

    # Устанавливаем новый дефолт уже после кастинга
    op.alter_column("test_attempts", "status", server_default=text("'in_progress'"))

    op.create_index("ix_test_attempt_user_test", "test_attempts", ["user_id", "test_id"])
    op.create_index("ix_test_attempts_status", "test_attempts", ["status"])

    op.drop_column("test_attempts", "total_score")

    # ===== TEST QUESTIONS =====
    op.drop_constraint("uq_test_questions_test_question", "test_questions", type_="unique")
    op.create_unique_constraint("uq_test_question", "test_questions", ["test_id", "question_id"])

    # ===== TESTS =====
    # Убираем дефолт перед сменой типа
    op.alter_column("tests", "status", server_default=None)

    # Меняем тип через кастинг
    op.execute("""
        ALTER TABLE tests
        ALTER COLUMN status TYPE test_status
        USING status::text::test_status
    """)

    # Ставим дефолт уже после кастинга
    op.alter_column("tests", "status", server_default=text("'draft'"))


def downgrade() -> None:
    attempt_status = postgresql.ENUM("in_progress", "finished", "cancelled", name="attempt_status")
    test_status = postgresql.ENUM("draft", "published", "archived", name="test_status")

    # ===== TESTS =====
    op.alter_column("tests", "status", server_default=None)
    op.execute("""
        ALTER TABLE tests
        ALTER COLUMN status TYPE VARCHAR(20)
        USING status::text
    """)
    op.alter_column("tests", "status", server_default=text("'draft'"))

    # ===== TEST QUESTIONS =====
    op.drop_constraint("uq_test_question", "test_questions", type_="unique")
    op.create_unique_constraint("uq_test_questions_test_question", "test_questions", ["test_id", "question_id"])

    # ===== TEST ATTEMPTS =====
    op.add_column("test_attempts", sa.Column("total_score", sa.Integer()))

    op.drop_index("ix_test_attempts_status", table_name="test_attempts")
    op.drop_index("ix_test_attempt_user_test", table_name="test_attempts")

    op.alter_column("test_attempts", "status", server_default=None)
    op.execute("""
        ALTER TABLE test_attempts
        ALTER COLUMN status TYPE VARCHAR(20)
        USING status::text
    """)
    op.alter_column("test_attempts", "status", server_default=text("'in_progress'"))

    op.drop_column("test_attempts", "max_score")
    op.drop_column("test_attempts", "score")

    # ===== TEST ANSWERS =====
    op.add_column("test_answers", sa.Column("question_id", sa.Integer(), nullable=False))
    op.add_column("test_answers", sa.Column("answer", sa.String(), nullable=False))

    op.drop_constraint("uq_attempt_question", "test_answers", type_="unique")
    op.drop_constraint("fk_test_answers_test_question", "test_answers", type_="foreignkey")

    op.create_foreign_key(
        "test_answers_question_id_fkey",
        "test_answers",
        "questions",
        ["question_id"],
        ["id"]
    )

    op.drop_index("ix_test_answers_test_question_id", table_name="test_answers")
    op.create_index("ix_test_answers_question_id", "test_answers", ["question_id"])

    op.drop_column("test_answers", "user_answer")
    op.drop_column("test_answers", "test_question_id")

    # ===== DROP ENUMS =====
    attempt_status.drop(op.get_bind(), checkfirst=True)
    test_status.drop(op.get_bind(), checkfirst=True)