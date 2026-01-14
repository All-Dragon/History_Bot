"""constrain role column with enum

Revision ID: b846cc988501
Revises: 4898f868bf2e
Create Date: 2026-01-14 21:40:32.216575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b846cc988501'
down_revision: Union[str, Sequence[str], None] = '4898f868bf2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:



    op.execute("""
        UPDATE users
        SET role = 'Ученик'
        WHERE role NOT IN ('Ученик', 'Преподаватель', 'Админ');
    """)

    user_role_enum = postgresql.ENUM(
        'Ученик', 'Преподаватель', 'Админ',
        name='user_role'
    )
    user_role_enum.create(op.get_bind(), checkfirst=True)


    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role
        TYPE user_role
        USING role::text::user_role;
    """)


def downgrade() -> None:

    op.alter_column(
        'users',
        'role',
        existing_type=postgresql.ENUM('Ученик', 'Преподаватель', 'Админ', name='user_role'),
        type_=sa.VARCHAR(),
        existing_nullable=False
    )

    user_role_enum = postgresql.ENUM(
        'Ученик', 'Преподаватель', 'Админ',
        name='user_role'
    )
    user_role_enum.drop(op.get_bind(), checkfirst=True)

    # ### end Alembic commands ###
