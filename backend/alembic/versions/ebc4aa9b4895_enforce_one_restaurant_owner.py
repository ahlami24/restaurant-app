import sqlalchemy as sa

from alembic import op

revision = "ebc4aa9b4895"
down_revision = "04040adf92e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    duplicate_owners = op.get_bind().execute(
        sa.text("""
            SELECT restaurant_id, COUNT(*) AS owner_count
            FROM restaurant_memberships
            WHERE role = 'owner'
            GROUP BY restaurant_id
            HAVING COUNT(*) > 1
        """)
    ).all()

    if duplicate_owners:
        raise RuntimeError(
            "Cannot enforce one owner per restaurant. "
            f"Restaurants with multiple owners: {duplicate_owners}"
        )

    op.create_index(
        "uq_restaurant_single_owner",
        "restaurant_memberships",
        ["restaurant_id"],
        unique=True,
        postgresql_where=sa.text("role = 'owner'"),
        sqlite_where=sa.text("role = 'owner'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_restaurant_single_owner",
        table_name="restaurant_memberships",
    )
