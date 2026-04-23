"""fix_filetype_enum

Revision ID: 4e95c0d8e40c
Revises: 6c6bcaea3052
Create Date: 2026-04-23 07:00:28.423915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e95c0d8e40c'
down_revision: Union[str, None] = '6c6bcaea3052'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Fix filetype Enum
    op.execute("ALTER TYPE filetype RENAME TO filetype_old")
    op.execute("CREATE TYPE filetype AS ENUM ('PDF', 'MP3', 'MP4', 'WAV', 'M4A', 'WEBM')")
    op.execute("ALTER TABLE files ALTER COLUMN file_type TYPE filetype USING file_type::text::filetype")
    op.execute("DROP TYPE filetype_old")

    # 2. Fix filestatus Enum (Change to lowercase values as requested)
    op.execute("ALTER TYPE filestatus RENAME TO filestatus_old")
    op.execute("CREATE TYPE filestatus AS ENUM ('uploading', 'processing', 'ready', 'failed')")
    op.execute("ALTER TABLE files ALTER COLUMN status TYPE filestatus USING status::text::filestatus")
    op.execute("DROP TYPE filestatus_old")


def downgrade() -> None:
    pass
