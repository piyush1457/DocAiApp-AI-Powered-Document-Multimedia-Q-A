"""fix_refresh_token_timezone

Revision ID: 43b35647d338
Revises: 4e95c0d8e40c
Create Date: 2026-05-05 09:51:10.090102

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '43b35647d338'
down_revision: Union[str, None] = '4e95c0d8e40c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix expires_at: TIMESTAMP -> TIMESTAMP WITH TIME ZONE
    op.alter_column(
        'refresh_tokens',
        'expires_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
    )
    # Fix last_used_at: TIMESTAMP -> TIMESTAMP WITH TIME ZONE
    op.alter_column(
        'refresh_tokens',
        'last_used_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
        postgresql_using="last_used_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        'refresh_tokens',
        'last_used_at',
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
        postgresql_using="last_used_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        'refresh_tokens',
        'expires_at',
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
    )
