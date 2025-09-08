"""
Database models and Pydantic schemas for core crawl fingerprinting functionality.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, HttpUrl, validator

from app.core.db import Base


class FingerprintSession(Base):
    """
    Represents a fingerprinting session that processes pages from a CrawlSession.
    """
    __tablename__ = "fingerprint_sessions"
    __table_args__ = {"schema": "crawl_data"}
    
    id = Column(Integer, primary_key=True, index=True)
    crawl_session_id = Column(Integer, ForeignKey("crawl_data.crawl_sessions.id"), nullable=False)
    competitor = Column(String, nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    total_processed = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    
    # Relationships
    crawl_session = relationship("CrawlSession", foreign_keys=[crawl_session_id])
    fingerprints = relationship("PageFingerprint", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FingerprintSession(id={self.id}, competitor='{self.competitor}', processed={self.total_processed})>"


class PageFingerprint(Base):
    """
    Represents a fingerprint result for a specific page with stable content hash.
    """
    __tablename__ = "page_fingerprints"
    __table_args__ = {"schema": "crawl_data"}
    
    id = Column(Integer, primary_key=True, index=True)
    fingerprint_session_id = Column(Integer, ForeignKey("crawl_data.fingerprint_sessions.id"), nullable=False)
    crawled_page_id = Column(Integer, ForeignKey("crawl_data.crawled_pages.id"), nullable=False)
    
    # Core fingerprint data
    url = Column(String, nullable=False, index=True)
    key_url = Column(String, nullable=False, index=True)  # canonical URL if found
    page_type = Column(String, nullable=False, index=True)  # mapped from primary_category
    content_hash = Column(String, nullable=False, index=True)  # stable text-based hash
    normalized_text_len = Column(Integer, nullable=False)
    
    # Content processing flags
    low_text_pdf = Column(Boolean, default=False)
    needs_render = Column(Boolean, default=False)
    
    # Fetch metadata
    fetch_status = Column(Integer, nullable=True)
    content_type = Column(String, nullable=True)
    content_length = Column(Integer, nullable=False, default=0)
    fetch_elapsed_ms = Column(Integer, nullable=False, default=0)
    fetch_notes = Column(Text, nullable=True)  # Error messages, warnings, etc.
    
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("FingerprintSession", back_populates="fingerprints")
    crawled_page = relationship("CrawledPage", foreign_keys=[crawled_page_id])
    
    def __repr__(self):
        return f"<PageFingerprint(id={self.id}, url='{self.url}', page_type='{self.page_type}', hash='{self.content_hash[:8]}...')>"


# Pydantic Models for API

class FingerprintRequest(BaseModel):
    """Request model for fingerprinting a crawl session."""
    crawl_session_id: int
    competitor: str
    
    @validator('competitor')
    def competitor_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Competitor name cannot be empty')
        return v.strip()


class FetchMeta(BaseModel):
    """Metadata from the fetch operation."""
    status: Optional[int] = None
    content_type: Optional[str] = None
    content_length: int = 0
    elapsed_ms: int = 0
    notes: Optional[str] = None


class FingerprintResult(BaseModel):
    """Result of fingerprinting a single page."""
    url: str
    key_url: str  # canonical URL if found, otherwise same as url
    page_type: str  # mapped from primary_category
    content_hash: str
    normalized_text_len: int
    low_text_pdf: bool = False
    needs_render: bool = False
    meta: FetchMeta


class FingerprintResponse(BaseModel):
    """Response from the fingerprint endpoint."""
    fingerprint_session_id: int
    crawl_session_id: int
    competitor: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_processed: int = 0
    total_errors: int = 0
    fingerprints: List[FingerprintResult] = []


class ClassifiedItem(BaseModel):
    """Validated input from discovery results."""
    url: HttpUrl
    score: float
    primary_category: str
    status: Optional[int] = None
    depth: Optional[int] = None
    signals: List[str] = []
    size_bytes: Optional[int] = None
    
    @validator('score')
    def score_must_be_valid(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v
    
    @validator('primary_category')
    def category_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Primary category cannot be empty')
        return v.strip()
