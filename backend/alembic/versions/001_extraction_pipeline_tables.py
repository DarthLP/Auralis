"""add_extraction_pipeline_tables

Revision ID: 001_extraction_pipeline
Revises: aad702e7f0d1
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_extraction_pipeline'
down_revision = 'aad702e7f0d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create extraction_sessions table
    op.create_table('extraction_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fingerprint_session_id', sa.Integer(), nullable=False),
        sa.Column('competitor', sa.String(), nullable=False),
        sa.Column('schema_version', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('processed_pages', sa.Integer(), nullable=True),
        sa.Column('skipped_pages', sa.Integer(), nullable=True),
        sa.Column('failed_pages', sa.Integer(), nullable=True),
        sa.Column('cache_hits', sa.Integer(), nullable=True),
        sa.Column('total_retries', sa.Integer(), nullable=True),
        sa.Column('companies_found', sa.Integer(), nullable=True),
        sa.Column('products_found', sa.Integer(), nullable=True),
        sa.Column('capabilities_found', sa.Integer(), nullable=True),
        sa.Column('releases_found', sa.Integer(), nullable=True),
        sa.Column('documents_found', sa.Integer(), nullable=True),
        sa.Column('signals_found', sa.Integer(), nullable=True),
        sa.Column('changes_detected', sa.Integer(), nullable=True),
        sa.Column('error_summary', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['fingerprint_session_id'], ['crawl_data.fingerprint_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_extraction_sessions_competitor'), 'extraction_sessions', ['competitor'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_extraction_sessions_fingerprint_session_id'), 'extraction_sessions', ['fingerprint_session_id'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_extraction_sessions_id'), 'extraction_sessions', ['id'], unique=False, schema='crawl_data')

    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('competitor', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('normalized_name', sa.String(), nullable=False),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('hq_country', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('competitor', 'normalized_name', name='uq_company_competitor_name'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_companies_competitor'), 'companies', ['competitor'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_companies_normalized_name'), 'companies', ['normalized_name'], unique=False, schema='crawl_data')

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('normalized_name', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('stage', sa.String(), nullable=True),
        sa.Column('markets', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('short_desc', sa.Text(), nullable=True),
        sa.Column('product_url', sa.String(), nullable=True),
        sa.Column('docs_url', sa.String(), nullable=True),
        sa.Column('media', sa.JSON(), nullable=True),
        sa.Column('spec_profile', sa.String(), nullable=True),
        sa.Column('specs', sa.JSON(), nullable=True),
        sa.Column('released_at', sa.DateTime(), nullable=True),
        sa.Column('eol_at', sa.DateTime(), nullable=True),
        sa.Column('compliance', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['crawl_data.companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'normalized_name', 'version', name='uq_product_company_name_version'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_products_category'), 'products', ['category'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_products_company_id'), 'products', ['company_id'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_products_normalized_name'), 'products', ['normalized_name'], unique=False, schema='crawl_data')

    # Create capabilities table
    op.create_table('capabilities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('normalized_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('product_refs', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('normalized_name', 'category', name='uq_capability_name_category'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_capabilities_category'), 'capabilities', ['category'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_capabilities_normalized_name'), 'capabilities', ['normalized_name'], unique=False, schema='crawl_data')

    # Create releases table
    op.create_table('releases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('normalized_name', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('highlights', sa.JSON(), nullable=True),
        sa.Column('release_url', sa.String(), nullable=True),
        sa.Column('product_refs', sa.JSON(), nullable=True),
        sa.Column('company_refs', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('normalized_name', 'version', 'date', name='uq_release_name_version_date'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_releases_date'), 'releases', ['date'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_releases_normalized_name'), 'releases', ['normalized_name'], unique=False, schema='crawl_data')

    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('doc_type', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('product_refs', sa.JSON(), nullable=True),
        sa.Column('company_refs', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url', 'title', name='uq_document_url_title'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_documents_doc_type'), 'documents', ['doc_type'], unique=False, schema='crawl_data')

    # Create signals table
    op.create_table('signals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('signal_type', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('impact_level', sa.String(), nullable=True),
        sa.Column('company_refs', sa.JSON(), nullable=True),
        sa.Column('product_refs', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('title', 'date', 'signal_type', name='uq_signal_title_date_type'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_signals_date'), 'signals', ['date'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_signals_signal_type'), 'signals', ['signal_type'], unique=False, schema='crawl_data')

    # Create extraction_sources table
    op.create_table('extraction_sources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('extraction_session_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('page_type', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('ai_model', sa.String(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('fields_extracted', sa.JSON(), nullable=True),
        sa.Column('field_confidences', sa.JSON(), nullable=True),
        sa.Column('tokens_input', sa.Integer(), nullable=True),
        sa.Column('tokens_output', sa.Integer(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('cache_hit', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['extraction_session_id'], ['crawl_data.extraction_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entity_type', 'entity_id', 'url', 'content_hash', name='uq_source_entity_url_hash'),
        schema='crawl_data'
    )
    op.create_index(op.f('ix_crawl_data_extraction_sources_entity_id'), 'extraction_sources', ['entity_id'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_extraction_sources_entity_type'), 'extraction_sources', ['entity_type'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_extraction_sources_extraction_session_id'), 'extraction_sources', ['extraction_session_id'], unique=False, schema='crawl_data')

    # Create entity_snapshots table
    op.create_table('entity_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('schema_version', sa.String(), nullable=False),
        sa.Column('data_json', sa.JSON(), nullable=False),
        sa.Column('data_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('extraction_session_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['extraction_session_id'], ['crawl_data.extraction_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='crawl_data'
    )
    op.create_index('ix_entity_snapshots_entity_created', 'entity_snapshots', ['entity_type', 'entity_id', 'created_at'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_entity_snapshots_data_hash'), 'entity_snapshots', ['data_hash'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_entity_snapshots_entity_id'), 'entity_snapshots', ['entity_id'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_entity_snapshots_entity_type'), 'entity_snapshots', ['entity_type'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_entity_snapshots_extraction_session_id'), 'entity_snapshots', ['extraction_session_id'], unique=False, schema='crawl_data')

    # Create entity_changes table
    op.create_table('entity_changes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('change_hash', sa.String(), nullable=False),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('change_type', sa.String(), nullable=False),
        sa.Column('diff_json', sa.JSON(), nullable=False),
        sa.Column('fields_changed', sa.JSON(), nullable=True),
        sa.Column('previous_snapshot_id', sa.String(), nullable=True),
        sa.Column('current_snapshot_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('extraction_session_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['extraction_session_id'], ['crawl_data.extraction_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='crawl_data'
    )
    op.create_index('ix_entity_changes_entity_created', 'entity_changes', ['entity_type', 'entity_id', 'created_at'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_entity_changes_change_hash'), 'entity_changes', ['change_hash'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_entity_changes_entity_id'), 'entity_changes', ['entity_id'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_entity_changes_entity_type'), 'entity_changes', ['entity_type'], unique=False, schema='crawl_data')
    op.create_index(op.f('ix_crawl_data_entity_changes_extraction_session_id'), 'entity_changes', ['extraction_session_id'], unique=False, schema='crawl_data')

    # Create ai_cache table
    op.create_table('ai_cache',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('cache_key', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('schema_version', sa.String(), nullable=False),
        sa.Column('prompt_hash', sa.String(), nullable=False),
        sa.Column('response_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=True),
        sa.Column('original_tokens_input', sa.Integer(), nullable=True),
        sa.Column('original_tokens_output', sa.Integer(), nullable=True),
        sa.Column('original_processing_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
        schema='crawl_data'
    )
    op.create_index('ix_ai_cache_key_expires', 'ai_cache', ['cache_key', 'expires_at'], unique=False, schema='crawl_data')
    op.create_index('ix_ai_cache_last_used', 'ai_cache', ['last_used_at'], unique=False, schema='crawl_data')


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('ai_cache', schema='crawl_data')
    op.drop_table('entity_changes', schema='crawl_data')
    op.drop_table('entity_snapshots', schema='crawl_data')
    op.drop_table('extraction_sources', schema='crawl_data')
    op.drop_table('signals', schema='crawl_data')
    op.drop_table('documents', schema='crawl_data')
    op.drop_table('releases', schema='crawl_data')
    op.drop_table('capabilities', schema='crawl_data')
    op.drop_table('products', schema='crawl_data')
    op.drop_table('companies', schema='crawl_data')
    op.drop_table('extraction_sessions', schema='crawl_data')
