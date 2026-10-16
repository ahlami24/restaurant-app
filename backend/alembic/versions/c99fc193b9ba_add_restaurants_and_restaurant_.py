"""add restaurants and restaurant memberships

Revision ID: c99fc193b9ba
Revises: 91bda81843fb
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c99fc193b9ba"
down_revision: Union[str, Sequence[str], None] = "91bda81843fb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.create_index(
        "ix_restaurants_slug",
        "restaurants",
        ["slug"],
        unique=True,
    )

    op.create_table(
        "restaurant_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "restaurant_id",
            sa.Integer(),
            sa.ForeignKey("restaurants.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "restaurant_id",
            name="uq_user_restaurant_membership",
        ),
    )

    op.add_column(
        "foods",
        sa.Column("restaurant_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_foods_restaurant_id",
        "foods",
        "restaurants",
        ["restaurant_id"],
        ["id"],
    )

    op.add_column(
        "orders",
        sa.Column("restaurant_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_orders_restaurant_id",
        "orders",
        "restaurants",
        ["restaurant_id"],
        ["id"],
    )

    # Create the initial restaurant.
    result = op.get_bind().execute(
        sa.text(
            """
            INSERT INTO restaurants (name, slug, is_active)
            VALUES ('Baraka Restaurant', 'baraka-restaurant', TRUE)
            RETURNING id
            """
        )
    )
    restaurant_id = result.scalar_one()

    # Assign existing records to the initial restaurant.
    op.execute(
        sa.text(
            "UPDATE foods SET restaurant_id = :rid"
        ).bindparams(rid=restaurant_id)
    )
    op.execute(
        sa.text(
            "UPDATE orders SET restaurant_id = :rid"
        ).bindparams(rid=restaurant_id)
    )

    # Assign user ID 10 as the restaurant owner.
    op.execute(
        sa.text(
            """
            INSERT INTO restaurant_memberships
                (user_id, restaurant_id, role)
            VALUES (10, :rid, 'owner')
            """
        ).bindparams(rid=restaurant_id)
    )

    # Require restaurant ownership for every food and order.
    op.alter_column(
        "foods",
        "restaurant_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "orders",
        "restaurant_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_orders_restaurant_id", "orders", type_="foreignkey"
    )
    op.drop_column("orders", "restaurant_id")

    op.drop_constraint(
        "fk_foods_restaurant_id", "foods", type_="foreignkey"
    )
    op.drop_column("foods", "restaurant_id")

    op.drop_table("restaurant_memberships")
    op.drop_index("ix_restaurants_slug", table_name="restaurants")
    op.drop_table("restaurants")

    