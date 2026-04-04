"""add password_hash in users

Revision ID: c9d11f60907a
Revises: f5ad38aa3a63
Create Date: 2026-04-03 19:54:18.874635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d11f60907a'
down_revision: Union[str, Sequence[str], None] = 'f5ad38aa3a63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))
    op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")
    op.alter_column('users', 'password_hash', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
