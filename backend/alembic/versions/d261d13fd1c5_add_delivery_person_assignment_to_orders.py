"""Add delivery person assignment to orders

Revision ID: d261d13fd1c5
Revises: ff15a4a0f83d
Create Date: 2026-11-21
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d261d13fd1c5"
down_revision: Union[str, Sequence[str], None] = "ff15a4a0f83d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("delivery_person_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_orders_delivery_person_id_delivery_persons",
        "orders",
        "delivery_persons",
        ["delivery_person_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_orders_delivery_person_id_delivery_persons",
        "orders",
        type_="foreignkey",
    )
    op.drop_column("orders", "delivery_person_id")
