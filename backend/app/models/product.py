"""
Product database models.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class Product(Base):
    """Product model for storing product information."""
    
    __tablename__ = "products"
    __table_args__ = {'schema': None}  # Use default schema
    
    id = Column(String, primary_key=True, index=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=True, index=True)  # Removed required constraint
    name = Column(String, nullable=True, index=True)  # Removed required constraint
    category = Column(String, nullable=True)  # Removed required constraint
    stage = Column(String, nullable=True)  # Removed required constraint
    markets = Column(ARRAY(String), default=list)
    tags = Column(ARRAY(String), default=list)
    short_desc = Column(Text, nullable=True)
    product_url = Column(String, nullable=True)
    docs_url = Column(String, nullable=True)
    media = Column(JSON, nullable=True)  # { hero?: string; video?: string }
    spec_profile = Column(String, nullable=True)
    specs = Column(JSON, nullable=True)  # Record<string, SpecValue>
    released_at = Column(DateTime(timezone=True), nullable=True)
    eol_at = Column(DateTime(timezone=True), nullable=True)
    compliance = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="products")
    capabilities = relationship("ProductCapability", back_populates="product")
    signals = relationship("Signal", secondary="signal_products", back_populates="products")


class Capability(Base):
    """Capability model for storing capability definitions."""
    
    __tablename__ = "capabilities"
    __table_args__ = {'schema': None}  # Use default schema
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True, index=True)  # Removed required constraint
    definition = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product_capabilities = relationship("ProductCapability", back_populates="capability")
    signals = relationship("Signal", secondary="signal_capabilities", back_populates="capabilities")


class ProductCapability(Base):
    """Product capability model for linking products to capabilities."""
    
    __tablename__ = "product_capabilities"
    __table_args__ = {'schema': None}  # Use default schema
    
    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    capability_id = Column(String, ForeignKey("capabilities.id"), nullable=False, index=True)
    maturity = Column(String, nullable=False)  # CapabilityMaturity enum
    details = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=True)  # Record<string, string | number>
    observed_at = Column(DateTime(timezone=True), nullable=True)
    source_id = Column(String, nullable=True)
    method = Column(String, nullable=True)  # 'measured' | 'reported' | 'inferred'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="capabilities")
    capability = relationship("Capability", back_populates="product_capabilities")
