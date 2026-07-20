"""seed duplicate window setting

Revision ID: c59e1d571771
Revises: f35d850bcec5
Create Date: 2026-07-20 11:17:03.983728

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c59e1d571771'
down_revision: Union[str, None] = 'f35d850bcec5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

local_settings = sa.table(
    "local_settings",
    sa.column("key", sa.String),
    sa.column("value", sa.String),
    sa.column("updated_at", sa.DateTime),
)


def upgrade() -> None:
    op.bulk_insert(
        local_settings,
        [{"key": "duplicate_window_seconds", "value": "60", "updated_at": datetime.now(timezone.utc)}],
    )


def downgrade() -> None:
    op.execute("DELETE FROM local_settings WHERE key = 'duplicate_window_seconds'")
