"""add_short_desc_to_companies

Revision ID: b8b213b18603
Revises: 2dece115c1f0
Create Date: 2025-09-09 15:16:52.653270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8b213b18603'
down_revision: Union[str, Sequence[str], None] = '2dece115c1f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add short_desc column to companies table
    op.add_column('companies', sa.Column('short_desc', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove short_desc column from companies table
    op.drop_column('companies', 'short_desc')
