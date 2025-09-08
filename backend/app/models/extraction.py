"""
Database models for the extraction pipeline.

Includes entities, sources, snapshots, changes, and AI cache tables
for the schema-first extraction system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Column, DateTime, Float, Integer, String, Text, JSON, 
    ForeignKey, Boolean, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.db import Base


class ExtractionSession(Base):
    """
    Tracks extraction sessions that process fingerprint sessions.
    """
    __tablename__ = "extraction_sessions"
    __table_args__ = {"schema": "crawl_data"}
    
    id = Column(Integer, primary_key=True, index=True)
    fingerprint_session_id = Column(
        Integer, 
        ForeignKey("crawl_data.fingerprint_sessions.id"), 
        nullable=False,
        index=True
    )
    competitor = Column(String, nullable=False, index=True)
    schema_version = Column(String, nullable=False, default="v1")
    
    # Session lifecycle
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Processing stats
    total_pages = Column(Integer, default=0)
    processed_pages = Column(Integer, default=0)
    skipped_pages = Column(Integer, default=0)  # hash-and-skip
    failed_pages = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    total_retries = Column(Integer, default=0)
    
    # Entity counts
    companies_found = Column(Integer, default=0)
    products_found = Column(Integer, default=0)
    capabilities_found = Column(Integer, default=0)
    releases_found = Column(Integer, default=0)
    documents_found = Column(Integer, default=0)
    signals_found = Column(Integer, default=0)
    changes_detected = Column(Integer, default=0)
    
    # Error tracking
    error_summary = Column(JSON, nullable=True)  # {"page_id": "error_reason", ...}
    
    # Relationships
    fingerprint_session = relationship("FingerprintSession", foreign_keys=[fingerprint_session_id])
    sources = relationship("ExtractionSource", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExtractionSession(id={self.id}, competitor='{self.competitor}', processed={self.processed_pages}/{self.total_pages})>"


# Entity tables - normalized storage for operational queries
class Company(Base):
    """Extracted company entities."""
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint('competitor', 'normalized_name', name='uq_company_competitor_name'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    competitor = Column(String, nullable=False, index=True)
    
    # Identity fields
    name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False, index=True)  # For deduplication
    aliases = Column(JSON, default=list)  # List of known aliases
    
    # Core attributes
    website = Column(String, nullable=True)
    hq_country = Column(String, nullable=True)
    status = Column(String, nullable=True)  # active, dormant
    tags = Column(JSON, default=list)
    
    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = Column(Float, default=0.0)  # Aggregate confidence
    
    # Relationships
    products = relationship("Product", back_populates="company", cascade="all, delete-orphan")
    snapshots = relationship("EntitySnapshot", 
                           primaryjoin="and_(Company.id==EntitySnapshot.entity_id, EntitySnapshot.entity_type=='Company')",
                           cascade="all, delete-orphan")


class Product(Base):
    """Extracted product entities."""
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint('company_id', 'normalized_name', 'version', name='uq_product_company_name_version'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("crawl_data.companies.id"), nullable=False, index=True)
    
    # Identity fields
    name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=True)  # For versioned products
    
    # Core attributes
    category = Column(String, nullable=True, index=True)
    stage = Column(String, nullable=True)  # alpha, beta, ga, discontinued
    markets = Column(JSON, default=list)  # Target markets
    tags = Column(JSON, default=list)
    short_desc = Column(Text, nullable=True)
    
    # URLs and media
    product_url = Column(String, nullable=True)
    docs_url = Column(String, nullable=True)
    media = Column(JSON, nullable=True)  # hero images, videos
    
    # Specifications
    spec_profile = Column(String, nullable=True)
    specs = Column(JSON, nullable=True)  # Structured specifications
    
    # Lifecycle
    released_at = Column(DateTime, nullable=True)
    eol_at = Column(DateTime, nullable=True)
    compliance = Column(JSON, default=list)  # Compliance certifications
    
    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    company = relationship("Company", back_populates="products")
    snapshots = relationship("EntitySnapshot",
                           primaryjoin="and_(Product.id==EntitySnapshot.entity_id, EntitySnapshot.entity_type=='Product')",
                           cascade="all, delete-orphan")


class Capability(Base):
    """Extracted capability entities."""
    __tablename__ = "capabilities"
    __table_args__ = (
        UniqueConstraint('normalized_name', 'category', name='uq_capability_name_category'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identity
    name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)
    tags = Column(JSON, default=list)
    
    # References (natural keys, resolved during normalization)
    product_refs = Column(JSON, default=list)  # List of product references
    
    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    snapshots = relationship("EntitySnapshot",
                           primaryjoin="and_(Capability.id==EntitySnapshot.entity_id, EntitySnapshot.entity_type=='Capability')",
                           cascade="all, delete-orphan")


class Release(Base):
    """Extracted release/version entities."""
    __tablename__ = "releases"
    __table_args__ = (
        UniqueConstraint('normalized_name', 'version', 'date', name='uq_release_name_version_date'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identity
    name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=True)
    date = Column(DateTime, nullable=True, index=True)
    
    # Content
    notes = Column(Text, nullable=True)
    highlights = Column(JSON, default=list)  # Key features/changes
    release_url = Column(String, nullable=True)
    
    # References
    product_refs = Column(JSON, default=list)  # Products affected by this release
    company_refs = Column(JSON, default=list)  # Companies involved
    
    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    snapshots = relationship("EntitySnapshot",
                           primaryjoin="and_(Release.id==EntitySnapshot.entity_id, EntitySnapshot.entity_type=='Release')",
                           cascade="all, delete-orphan")


class Document(Base):
    """Extracted document entities."""
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint('url', 'title', name='uq_document_url_title'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identity
    title = Column(String, nullable=False)
    doc_type = Column(String, nullable=True, index=True)  # datasheet, whitepaper, api, manual, blog
    url = Column(String, nullable=True)
    
    # Content
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    author = Column(String, nullable=True)
    
    # References
    product_refs = Column(JSON, default=list)
    company_refs = Column(JSON, default=list)
    
    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    snapshots = relationship("EntitySnapshot",
                           primaryjoin="and_(Document.id==EntitySnapshot.entity_id, EntitySnapshot.entity_type=='Document')",
                           cascade="all, delete-orphan")


class Signal(Base):
    """Extracted signal entities (news, events, changes)."""
    __tablename__ = "signals"
    __table_args__ = (
        UniqueConstraint('title', 'date', 'signal_type', name='uq_signal_title_date_type'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identity
    title = Column(String, nullable=False)
    signal_type = Column(String, nullable=False, index=True)  # news, pricing_change, partnership, hiring, release
    date = Column(DateTime, nullable=True, index=True)
    
    # Content
    summary = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)
    impact_level = Column(String, nullable=True)  # low, medium, high
    
    # References
    company_refs = Column(JSON, default=list)
    product_refs = Column(JSON, default=list)
    
    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    snapshots = relationship("EntitySnapshot",
                           primaryjoin="and_(Signal.id==EntitySnapshot.entity_id, EntitySnapshot.entity_type=='Signal')",
                           cascade="all, delete-orphan")


class ExtractionSource(Base):
    """
    Tracks the source of each extraction with field-level provenance.
    """
    __tablename__ = "extraction_sources"
    __table_args__ = (
        UniqueConstraint('entity_type', 'entity_id', 'url', 'content_hash', name='uq_source_entity_url_hash'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_session_id = Column(
        Integer, 
        ForeignKey("crawl_data.extraction_sessions.id"), 
        nullable=False,
        index=True
    )
    
    # Entity reference
    entity_type = Column(String, nullable=False, index=True)  # Company, Product, etc.
    entity_id = Column(String, nullable=False, index=True)
    
    # Source metadata
    url = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    page_type = Column(String, nullable=False)
    
    # Extraction metadata
    method = Column(String, nullable=False)  # rules, ai
    ai_model = Column(String, nullable=True)  # deepseek_r1, etc.
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    
    # Field-level provenance (which fields came from this source)
    fields_extracted = Column(JSON, default=list)  # ["name", "description", "pricing"]
    field_confidences = Column(JSON, default=dict)  # {"name": 0.95, "description": 0.8}
    
    # Processing metadata
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    cache_hit = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("ExtractionSession", back_populates="sources")
    
    def __repr__(self):
        return f"<ExtractionSource(entity_type='{self.entity_type}', method='{self.method}', confidence={self.confidence})>"


class EntitySnapshot(Base):
    """
    Immutable snapshots of entity state for change detection.
    """
    __tablename__ = "entity_snapshots"
    __table_args__ = (
        Index('ix_entity_snapshots_entity_created', 'entity_type', 'entity_id', 'created_at'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Entity reference
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    
    # Snapshot metadata
    schema_version = Column(String, nullable=False)
    data_json = Column(JSON, nullable=False)  # Complete entity state
    data_hash = Column(String, nullable=False, index=True)  # For deduplication
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    extraction_session_id = Column(
        Integer,
        ForeignKey("crawl_data.extraction_sessions.id"),
        nullable=True,
        index=True
    )
    
    def __repr__(self):
        return f"<EntitySnapshot(entity_type='{self.entity_type}', entity_id='{self.entity_id}', created_at='{self.created_at}')>"


class EntityChange(Base):
    """
    Records detected changes between entity snapshots.
    """
    __tablename__ = "entity_changes"
    __table_args__ = (
        Index('ix_entity_changes_entity_created', 'entity_type', 'entity_id', 'created_at'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Entity reference
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    
    # Change metadata
    change_hash = Column(String, nullable=False, index=True)  # Deduplication
    summary = Column(String, nullable=False)  # Human-readable summary
    change_type = Column(String, nullable=False)  # created, updated, deleted
    
    # Change details
    diff_json = Column(JSON, nullable=False)  # Detailed field-level diff
    fields_changed = Column(JSON, default=list)  # List of changed field names
    previous_snapshot_id = Column(String, nullable=True)
    current_snapshot_id = Column(String, nullable=False)
    
    # Timing and source
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    extraction_session_id = Column(
        Integer,
        ForeignKey("crawl_data.extraction_sessions.id"),
        nullable=False,
        index=True
    )
    
    def __repr__(self):
        return f"<EntityChange(entity_type='{self.entity_type}', change_type='{self.change_type}', summary='{self.summary[:50]}...')>"


class AICache(Base):
    """
    Cache for AI extraction responses to reduce costs and improve performance.
    """
    __tablename__ = "ai_cache"
    __table_args__ = (
        Index('ix_ai_cache_key_expires', 'cache_key', 'expires_at'),
        Index('ix_ai_cache_last_used', 'last_used_at'),
        {"schema": "crawl_data"}
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Cache key (deterministic hash of request parameters)
    cache_key = Column(String, nullable=False, unique=True, index=True)
    
    # Request metadata
    model_name = Column(String, nullable=False)
    schema_version = Column(String, nullable=False)
    prompt_hash = Column(String, nullable=False)  # Hash of just the prompt content
    
    # Response data
    response_json = Column(JSON, nullable=False)  # Cached AI response
    
    # Cache management
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0)
    
    # Performance metadata
    original_tokens_input = Column(Integer, nullable=True)
    original_tokens_output = Column(Integer, nullable=True)
    original_processing_time_ms = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<AICache(cache_key='{self.cache_key[:16]}...', hits={self.hit_count}, expires='{self.expires_at}')>"
