"""
Database models for crawl data storage.
"""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class CrawlSession(Base):
    """
    Represents a complete crawl session.
    """
    __tablename__ = "crawl_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String, nullable=False, index=True)
    base_domain = Column(String, nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    total_pages = Column(Integer, default=0)
    limits = Column(JSON)  # Store crawl configuration
    warnings = Column(JSON)  # Store any warnings
    log_file = Column(String, nullable=True)
    json_file = Column(String, nullable=True)
    
    # Relationship to pages
    pages = relationship("CrawledPage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CrawlSession(id={self.id}, target_url='{self.target_url}', pages={self.total_pages})>"


class CrawledPage(Base):
    """
    Represents a single crawled page with all its metadata.
    """
    __tablename__ = "crawled_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("crawl_sessions.id"), nullable=False)
    
    # Page identification
    url = Column(String, nullable=False, index=True)
    canonical_url = Column(String, nullable=False, index=True)  # For deduplication
    content_hash = Column(String, nullable=True, index=True)
    
    # Crawl metadata
    status_code = Column(Integer, nullable=True)
    depth = Column(Integer, nullable=False, default=0)
    size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Classification results
    primary_category = Column(String, nullable=False, index=True)
    secondary_categories = Column(JSON)  # List of additional categories
    score = Column(Float, nullable=False, default=0.0, index=True)
    signals = Column(JSON)  # List of classification signals
    
    # Relationship to session
    session = relationship("CrawlSession", back_populates="pages")
    
    def __repr__(self):
        return f"<CrawledPage(id={self.id}, url='{self.url}', category='{self.primary_category}', score={self.score})>"


class PageContent(Base):
    """
    Optional: Store actual page content for analysis.
    """
    __tablename__ = "page_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("crawled_pages.id"), nullable=False)
    
    # Content storage
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    h1_text = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)  # Clean text content
    raw_html = Column(Text, nullable=True)  # Full HTML (optional)
    
    # Analysis results (for future AI processing)
    ai_summary = Column(Text, nullable=True)
    ai_categories = Column(JSON, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<PageContent(id={self.id}, page_id={self.page_id}, title='{self.title}')>"
