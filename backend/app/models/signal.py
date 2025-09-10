"""
Signal database models.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base

# Association tables for many-to-many relationships
signal_companies = Table(
    'signal_companies',
    Base.metadata,
    Column('signal_id', String, ForeignKey('signals.id'), primary_key=True),
    Column('company_id', String, ForeignKey('companies.id'), primary_key=True)
)

signal_products = Table(
    'signal_products',
    Base.metadata,
    Column('signal_id', String, ForeignKey('signals.id'), primary_key=True),
    Column('product_id', String, ForeignKey('products.id'), primary_key=True)
)

signal_capabilities = Table(
    'signal_capabilities',
    Base.metadata,
    Column('signal_id', String, ForeignKey('signals.id'), primary_key=True),
    Column('capability_id', String, ForeignKey('capabilities.id'), primary_key=True)
)


class Signal(Base):
    """Signal model for storing market signals and news."""
    
    __tablename__ = "signals"
    __table_args__ = {'schema': None}  # Use default schema
    
    id = Column(String, primary_key=True, index=True)
    type = Column(String, nullable=False)  # SignalType enum
    headline = Column(String, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    url = Column(String, nullable=False)
    company_ids = Column(ARRAY(String), default=list)
    product_ids = Column(ARRAY(String), default=list)
    capability_ids = Column(ARRAY(String), default=list)
    impact = Column(String, nullable=False)  # '-2' | '-1' | '0' | '1' | '2'
    source_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    companies = relationship("Company", secondary=signal_companies, back_populates="signals")
    products = relationship("Product", secondary=signal_products, back_populates="signals")
    capabilities = relationship("Capability", secondary=signal_capabilities, back_populates="signals")




class Source(Base):
    """Source model for storing data sources."""
    
    __tablename__ = "sources"
    __table_args__ = {'schema': None}  # Use default schema
    
    id = Column(String, primary_key=True, index=True)
    origin = Column(String, nullable=False)
    author = Column(String, nullable=True)
    retrieved_at = Column(DateTime(timezone=True), nullable=True)
    credibility = Column(String, nullable=True)  # 'low' | 'medium' | 'high'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
