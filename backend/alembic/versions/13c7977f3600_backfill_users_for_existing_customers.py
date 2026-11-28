"""backfill users for existing customers

Revision ID: 13c7977f3600
Revises: 1f1510e14daa
Create Date: 2026-10-07 15:04:13.735415

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "13c7977f3600"
down_revision: Union[str, Sequence[str], None] = "1f1510e14daa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY_PASSWORD_MARKER = "LEGACY_ACCOUNT_PASSWORD_RESET_REQUIRED"


def upgrade() -> None:
    op.execute(
        sa.text("""
            INSERT INTO users (name, phone, password_hash, role)
            SELECT
                name,
                phone,
                :password_marker,
                'customer'::userrole
            FROM customers
            WHERE user_id IS NULL
        """).bindparams(password_marker=LEGACY_PASSWORD_MARKER)
    )


def downgrade() -> None:
    op.execute(
        sa.text("""
            DELETE FROM users
            WHERE password_hash = :password_marker
              AND role::text = 'customer'
        """).bindparams(password_marker=LEGACY_PASSWORD_MARKER)
    )
