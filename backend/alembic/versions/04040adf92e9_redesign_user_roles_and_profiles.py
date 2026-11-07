from alembic import op
import sqlalchemy as sa

revision = "04040adf92e9"
down_revision = "2e7dcbe9f666"
branch_labels = None
depends_on = None


def _assert_no_rows(query: str, message: str) -> None:
    count = op.get_bind().execute(sa.text(query)).scalar_one()
    if count:
        raise RuntimeError(f"{message} Found {count} affected row(s).")


def upgrade() -> None:
    # Refuse destructive changes when legacy records cannot be represented
    # safely by the new profile-based schema.
    _assert_no_rows(
        "SELECT COUNT(*) FROM customers WHERE user_id IS NULL",
        "Customers without linked users must be reconciled before migration.",
    )
    _assert_no_rows(
        """
        SELECT COUNT(*) FROM customers c
        JOIN users u ON u.id = c.user_id
        WHERE c.name IS DISTINCT FROM u.name
           OR c.phone IS DISTINCT FROM u.phone
        """,
        "Customer name/phone differs from its linked user; reconcile first.",
    )
    _assert_no_rows(
        "SELECT COUNT(*) FROM foods WHERE restaurant_id IS NULL",
        "Foods without a restaurant must be assigned before migration.",
    )
    _assert_no_rows(
        "SELECT COUNT(*) FROM orders WHERE restaurant_id IS NULL",
        "Orders without a restaurant must be assigned before migration.",
    )

    # Preserve the delivery capability before replacing the legacy enum.
    op.create_table(
        "delivery_persons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_delivery_person_user_id"),
    )
    op.execute("""
        INSERT INTO delivery_persons (user_id)
        SELECT id FROM users WHERE role::text = 'delivery_person'
    """)

    op.alter_column("foods", "restaurant_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("orders", "restaurant_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("customers", "user_id", existing_type=sa.Integer(), nullable=False)

    op.drop_index("ix_customers_phone", table_name="customers")
    op.drop_column("customers", "name")
    op.drop_column("customers", "phone")

    op.execute("CREATE TYPE userrole_new AS ENUM ('user', 'platform_admin')")
    op.execute("""
        ALTER TABLE users ALTER COLUMN role TYPE userrole_new
        USING (CASE WHEN role::text = 'platform_admin'
                    THEN 'platform_admin' ELSE 'user' END)::userrole_new
    """)
    op.execute("DROP TYPE userrole")
    op.execute("ALTER TYPE userrole_new RENAME TO userrole")


def downgrade() -> None:
    op.add_column("customers", sa.Column("name", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("phone", sa.String(), nullable=True))
    op.execute("""
        UPDATE customers SET name = users.name, phone = users.phone
        FROM users WHERE customers.user_id = users.id
    """)
    op.alter_column("customers", "name", existing_type=sa.String(), nullable=False)
    op.alter_column("customers", "phone", existing_type=sa.String(), nullable=False)
    op.create_index("ix_customers_phone", "customers", ["phone"], unique=True)
    op.alter_column("customers", "user_id", existing_type=sa.Integer(), nullable=True)

    op.execute("""
        CREATE TYPE userrole_old AS ENUM
        ('customer', 'restaurant_owner', 'delivery_person', 'platform_admin')
    """)
    op.execute("""
        ALTER TABLE users ALTER COLUMN role TYPE userrole_old
        USING (
            CASE
                WHEN role::text = 'platform_admin' THEN 'platform_admin'
                WHEN EXISTS (
                    SELECT 1 FROM restaurant_memberships rm
                    WHERE rm.user_id = users.id AND rm.role = 'owner'
                ) THEN 'restaurant_owner'
                WHEN EXISTS (
                    SELECT 1 FROM delivery_persons dp
                    WHERE dp.user_id = users.id
                ) THEN 'delivery_person'
                ELSE 'customer'
            END
        )::userrole_old
    """)
    op.execute("DROP TYPE userrole")
    op.execute("ALTER TYPE userrole_old RENAME TO userrole")

    op.drop_table("delivery_persons")
    op.alter_column("foods", "restaurant_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("orders", "restaurant_id", existing_type=sa.Integer(), nullable=True)
