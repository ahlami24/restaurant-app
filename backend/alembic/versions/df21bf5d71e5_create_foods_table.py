"""create foods table

Revision ID: df21bf5d71e5
Revises:
Create Date: 2026-09-28 09:26:42.157466

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "df21bf5d71e5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("foods")