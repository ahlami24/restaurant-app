from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d84e1b0aaa7b"
down_revision: Union[str, Sequence[str], None] = "c99fc193b9ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'platform_admin'"
    )


def downgrade() -> None:
    # PostgreSQL does not directly support removing an enum value.
    pass