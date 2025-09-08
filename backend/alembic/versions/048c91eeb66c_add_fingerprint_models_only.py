"""Add fingerprint models only

Revision ID: 048c91eeb66c
Revises: aad702e7f0d1
Create Date: 2025-09-08 09:14:30.992837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '048c91eeb66c'
down_revision: Union[str, Sequence[str], None] = 'aad702e7f0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create fingerprint_sessions table
    op.create_table('fingerprint_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crawl_session_id', sa.Integer(), nullable=False),
        sa.Column('competitor', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_processed', sa.Integer(), nullable=True),
        sa.Column('total_errors', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['crawl_session_id'], ['crawl_data.crawl_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_fingerprint_sessions_competitor'), 'fingerprint_sessions', ['competitor'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_fingerprint_sessions_id'), 'fingerprint_sessions', ['id'], unique=False, schema='crawl_data')
    
    # Create page_fingerprints table
    op.create_table('page_fingerprints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fingerprint_session_id', sa.Integer(), nullable=False),
        sa.Column('crawled_page_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('key_url', sa.String(), nullable=False),
        sa.Column('page_type', sa.String(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('normalized_text_len', sa.Integer(), nullable=False),
        sa.Column('low_text_pdf', sa.Boolean(), nullable=True),
        sa.Column('needs_render', sa.Boolean(), nullable=True),
        sa.Column('fetch_status', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('content_length', sa.Integer(), nullable=False),
        sa.Column('fetch_elapsed_ms', sa.Integer(), nullable=False),
        sa.Column('fetch_notes', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['crawled_page_id'], ['crawl_data.crawled_pages.id'], ),
        sa.ForeignKeyConstraint(['fingerprint_session_id'], ['crawl_data.fingerprint_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_page_fingerprints_content_hash'), 'page_fingerprints', ['content_hash'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_page_fingerprints_id'), 'page_fingerprints', ['id'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_page_fingerprints_key_url'), 'page_fingerprints', ['key_url'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_page_fingerprints_page_type'), 'page_fingerprints', ['page_type'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_page_fingerprints_url'), 'page_fingerprints', ['url'], unique=False, schema='crawl_data')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop page_fingerprints table
    op.drop_index(op.f('ix_crawl_data_page_fingerprints_url'), table_name='page_fingerprints', schema='crawl_data')
    op.drop_index(op.f('ix_crawl_data_page_fingerprints_page_type'), table_name='page_fingerprints', schema='crawl_data')
    op.drop_index(op.f('ix_crawl_data_page_fingerprints_key_url'), table_name='page_fingerprints', schema='crawl_data')
    op.drop_index(op.f('ix_crawl_data_page_fingerprints_id'), table_name='page_fingerprints', schema='crawl_data')
    op.drop_index(op.f('ix_crawl_data_page_fingerprints_content_hash'), table_name='page_fingerprints', schema='crawl_data')
    op.drop_table('page_fingerprints', schema='crawl_data')
    
    # Drop fingerprint_sessions table
    op.drop_index(op.f('ix_crawl_data_fingerprint_sessions_id'), table_name='fingerprint_sessions', schema='crawl_data')
    op.drop_index(op.f('ix_crawl_data_fingerprint_sessions_competitor'), table_name='fingerprint_sessions', schema='crawl_data')
    op.drop_table('fingerprint_sessions', schema='crawl_data')
