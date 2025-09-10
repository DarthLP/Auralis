"""
Company database models.
"""

from sqlalchemy import Column, String, Boolean, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base
from app.models.signal import signal_companies  # ensure association table is registered


class Company(Base):
    """Company model for storing company information."""
    
    __tablename__ = "companies"
    __table_args__ = {'schema': None}  # Use default schema
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True, index=True)  # Removed required constraint
    aliases = Column(ARRAY(String), default=list)
    hq_country = Column(String, nullable=True)
    website = Column(String, nullable=True)
    status = Column(String, nullable=True, default="active")  # Removed required constraint
    tags = Column(ARRAY(String), default=list)
    # short_desc = Column(Text, nullable=True)  # Short description from extraction - temporarily disabled
    logo_url = Column(String, nullable=True)
    is_self = Column(Boolean, default=False)  # true if "Your Company"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    summaries = relationship("CompanySummary", back_populates="company")
    products = relationship("Product", back_populates="company")
    signals = relationship("Signal", secondary=signal_companies, back_populates="companies")


class CompanySummary(Base):
    """Company summary model for storing detailed company information."""
    
    __tablename__ = "company_summaries"
    __table_args__ = {'schema': None}  # Use default schema
    
    company_id = Column(String, ForeignKey("companies.id"), primary_key=True, index=True)
    one_liner = Column(Text, nullable=False)
    founded_year = Column(Integer, nullable=True)
    hq_city = Column(String, nullable=True)
    employees = Column(String, nullable=True)
    footprint = Column(String, nullable=True)
    sites = Column(ARRAY(String), default=list)
    sources = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="summaries")
