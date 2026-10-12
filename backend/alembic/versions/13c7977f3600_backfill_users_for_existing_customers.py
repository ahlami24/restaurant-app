"""backfill users for existing customers

Revision ID: 13c7977f3600
Revises: 1f1510e14daa
Create Date: 2026-10-07 15:04:13.735415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13c7977f3600'
down_revision: Union[str, Sequence[str], None] = '1f1510e14daa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text("""
        INSERT INTO users (name, phone, password_hash, role)
        VALUES (
            (SELECT name FROM customers WHERE user_id IS NULL),
            (SELECT phone FROM customers WHERE user_id IS NULL),
            '$argon2id$v=19$m=65536,t=3,p=4$NfEnyCBJPBACAAX8I4T0Og$D/IImXv0GlC1N7V/pg3xA+Zf/rk8xAvhjtUU2sApkjM',
            'customer'
        )
    """))


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("""
        DELETE FROM users WHERE phone = '0911000000' AND role = 'customer'
    """))
