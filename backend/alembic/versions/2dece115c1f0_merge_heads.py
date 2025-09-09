"""merge_heads

Revision ID: 2dece115c1f0
Revises: 001_extraction_pipeline, 048c91eeb66c
Create Date: 2025-09-09 15:16:47.153981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2dece115c1f0'
down_revision: Union[str, Sequence[str], None] = ('001_extraction_pipeline', '048c91eeb66c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
