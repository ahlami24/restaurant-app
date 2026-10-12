"""link existing customers to users

Revision ID: b7eb58f749c3
Revises: 13c7977f3600
Create Date: 2026-10-07 15:32:34.084504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7eb58f749c3'
down_revision: Union[str, Sequence[str], None] = '13c7977f3600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text("""
        UPDATE customers
        SET user_id = (
            SELECT id
            FROM users
            WHERE users.phone = customers.phone
        )
        WHERE customers.user_id IS NULL;
    """))


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("""
        UPDATE customers
        SET user_id = NULL
        WHERE user_id IN (
            SELECT id
            FROM users
            WHERE users.phone = customers.phone
        );
    """))