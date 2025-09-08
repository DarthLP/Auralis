"""Create crawl_data schema

Revision ID: 82b6043f2107
Revises: aad702e7f0d1
Create Date: 2025-09-08 09:12:33.801107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82b6043f2107'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the crawl_data schema
    op.execute("CREATE SCHEMA IF NOT EXISTS crawl_data")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the crawl_data schema
    op.execute("DROP SCHEMA IF EXISTS crawl_data CASCADE")
