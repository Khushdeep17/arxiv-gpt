"""tighten_user_auth_constraints

Revision ID: c7e48b12f6a9
Revises: 22729fb824a0
Create Date: 2026-10-31 23:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7e48b12f6a9'
down_revision: Union[str, Sequence[str], None] = '22729fb824a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: enforce non-null email and hashed_password, and add functional unique index on LOWER(email)."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'email',
            existing_type=sa.String(length=255),
            nullable=False,
        )
        batch_op.alter_column(
            'hashed_password',
            existing_type=sa.String(length=255),
            nullable=False,
        )
    op.create_index(
        'uq_users_lower_email',
        'users',
        [sa.text('LOWER(email)')],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema: drop functional index and restore columns to nullable."""
    op.drop_index('uq_users_lower_email', table_name='users')
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'hashed_password',
            existing_type=sa.String(length=255),
            nullable=True,
        )
        batch_op.alter_column(
            'email',
            existing_type=sa.String(length=255),
            nullable=True,
        )

