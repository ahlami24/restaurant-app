from alembic import op
import sqlalchemy as sa


revision = "04040adf92e9"
down_revision = "2e7dcbe9f666"

branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE userrole_new AS ENUM ('user', 'platform_admin')"
    )

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole_new
        USING (
            CASE
                WHEN role::text = 'platform_admin'
                    THEN 'platform_admin'
                ELSE 'user'
            END
        )::userrole_new
    """)

    op.execute("DROP TYPE userrole")
    op.execute("ALTER TYPE userrole_new RENAME TO userrole")

    op.alter_column(
        "customers",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_index("ix_customers_phone", table_name="customers")
    op.drop_column("customers", "name")
    op.drop_column("customers", "phone")

    # Delivery capability is independent of restaurant assignment.
    op.create_table(
        "delivery_persons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_delivery_person_user_id"),
    )


def downgrade() -> None:
    op.drop_table("delivery_persons")

    op.add_column(
        "customers",
        sa.Column("name", sa.String(), nullable=True),
    )
    op.add_column(
        "customers",
        sa.Column("phone", sa.String(), nullable=True),
    )

    op.execute("""
        UPDATE customers
        SET
            name = users.name,
            phone = users.phone
        FROM users
        WHERE customers.user_id = users.id
    """)

    op.alter_column(
        "customers",
        "name",
        existing_type=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "customers",
        "phone",
        existing_type=sa.String(),
        nullable=False,
    )

    op.create_index(
        "ix_customers_phone",
        "customers",
        ["phone"],
        unique=True,
    )

    op.execute("""
        CREATE TYPE userrole_old AS ENUM (
            'customer',
            'restaurant_owner',
            'delivery_person',
            'platform_admin'
        )
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole_old
        USING (
            CASE
                WHEN role::text = 'platform_admin'
                    THEN 'platform_admin'
                ELSE 'customer'
            END
        )::userrole_old
    """)

    op.execute("DROP TYPE userrole")
    op.execute("ALTER TYPE userrole_old RENAME TO userrole")