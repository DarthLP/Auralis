"""
Products API endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, String

from app.core.db import get_db
from app.models.product import Product, ProductCapability, Capability
from app.models.company import Company

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/")
async def get_products(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search products by name or description"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    stage: Optional[str] = Query(None, description="Filter by stage"),
    limit: int = Query(100, description="Maximum number of products to return"),
    offset: int = Query(0, description="Number of products to skip")
) -> List[dict]:
    """
    Get all products with optional filtering and search.
    """
    try:
        query = db.query(Product)
        
        # Apply search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.short_desc.ilike(search_term),
                    Product.tags.cast(String).ilike(search_term)
                )
            )
        
        # Apply filters
        if company_id:
            query = query.filter(Product.company_id == company_id)
        if category:
            query = query.filter(Product.category == category)
        if stage:
            query = query.filter(Product.stage == stage)
        
        products = query.order_by(Product.name.asc()).offset(offset).limit(limit).all()
        
        # Convert to dict format expected by frontend
        result = []
        for product in products:
            product_dict = {
                "id": product.id,
                "company_id": product.company_id,
                "name": product.name,
                "category": product.category,
                "stage": product.stage,
                "markets": product.markets or [],
                "tags": product.tags or [],
                "short_desc": product.short_desc,
                "product_url": product.product_url,
                "docs_url": product.docs_url,
                "media": product.media,
                "spec_profile": product.spec_profile,
                "specs": product.specs,
                "released_at": product.released_at.isoformat() if product.released_at else None,
                "eol_at": product.eol_at.isoformat() if product.eol_at else None,
                "compliance": product.compliance or []
            }
            result.append(product_dict)
        
        logger.info(f"Retrieved {len(result)} products")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{product_id}")
async def get_product(product_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Get a specific product by ID.
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "id": product.id,
            "company_id": product.company_id,
            "name": product.name,
            "category": product.category,
            "stage": product.stage,
            "markets": product.markets or [],
            "tags": product.tags or [],
            "short_desc": product.short_desc,
            "product_url": product.product_url,
            "docs_url": product.docs_url,
            "media": product.media,
            "spec_profile": product.spec_profile,
            "specs": product.specs,
            "released_at": product.released_at.isoformat() if product.released_at else None,
            "eol_at": product.eol_at.isoformat() if product.eol_at else None,
            "compliance": product.compliance or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{product_id}/capabilities")
async def get_product_capabilities(product_id: str, db: Session = Depends(get_db)) -> List[dict]:
    """
    Get product capabilities for a specific product.
    """
    try:
        # Check if product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get product capabilities with capability details
        capabilities = db.query(ProductCapability, Capability).join(
            Capability, ProductCapability.capability_id == Capability.id
        ).filter(ProductCapability.product_id == product_id).all()
        
        result = []
        for product_capability, capability in capabilities:
            capability_dict = {
                "id": product_capability.id,
                "product_id": product_capability.product_id,
                "capability_id": product_capability.capability_id,
                "maturity": product_capability.maturity,
                "details": product_capability.details,
                "metrics": product_capability.metrics,
                "observed_at": product_capability.observed_at.isoformat() if product_capability.observed_at else None,
                "source_id": product_capability.source_id,
                "method": product_capability.method,
                "capability": {
                    "id": capability.id,
                    "name": capability.name,
                    "definition": capability.definition,
                    "tags": capability.tags or []
                }
            }
            result.append(capability_dict)
        
        logger.info(f"Retrieved {len(result)} capabilities for product {product_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product capabilities for {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{product_id}/company")
async def get_product_company(product_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Get the company that owns a specific product.
    """
    try:
        # Get product with company
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        company = db.query(Company).filter(Company.id == product.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {
            "id": company.id,
            "name": company.name,
            "aliases": company.aliases or [],
            "hq_country": company.hq_country,
            "website": company.website,
            "status": company.status,
            "tags": company.tags or [],
            "logoUrl": company.logo_url,
            "isSelf": company.is_self
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving company for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
