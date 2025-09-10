"""
Companies API endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, String
from datetime import datetime, timezone

from app.core.db import get_db
from app.models.company import Company, CompanySummary
from app.models.product import Product
from app.models.signal import Signal
from app.models.extraction import ExtractedCompany

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["companies"])


def format_datetime_for_api(dt: datetime) -> str:
    """Format datetime for API response in ISO format with Z suffix."""
    if dt is None:
        return None
    # Convert to UTC and format with Z suffix for Zod compatibility
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def normalize_website_url(website: str) -> str:
    """Normalize website URL by adding https:// protocol if missing."""
    if not website:
        return website
    
    # If it already has a protocol, return as-is
    if website.startswith(('http://', 'https://')):
        return website
    
    # Add https:// protocol
    return f"https://{website}"


@router.get("/")
async def get_companies(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search companies by name, aliases, or tags"),
    status: Optional[str] = Query(None, description="Filter by status (active, dormant)"),
    limit: int = Query(100, description="Maximum number of companies to return"),
    offset: int = Query(0, description="Number of companies to skip")
) -> List[dict]:
    """
    Get all companies with optional filtering and search.
    """
    try:
        query = db.query(Company)
        
        # Apply search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    Company.name.ilike(search_term),
                    Company.aliases.cast(String).ilike(search_term),
                    Company.tags.cast(String).ilike(search_term)
                )
            )
        
        # Apply status filter
        if status:
            query = query.filter(Company.status == status)
        
        # Order by: "Your Company" first, then alphabetically by name
        companies = query.order_by(
            Company.is_self.desc(),
            Company.name.asc()
        ).offset(offset).limit(limit).all()
        
        # Convert to dict format expected by frontend
        result = []
        for company in companies:
            company_dict = {
                "id": company.id,
                "name": company.name,
                "aliases": company.aliases or [],
                "hq_country": company.hq_country,
                "website": normalize_website_url(company.website),
                "status": company.status,
                "tags": company.tags or [],
                "short_desc": getattr(company, 'short_desc', None),
                "logoUrl": company.logo_url,
                "isSelf": company.is_self
            }
            result.append(company_dict)
        
        logger.info(f"Retrieved {len(result)} companies")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving companies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/extracted")
async def get_extracted_companies(
    db: Session = Depends(get_db),
    competitor: Optional[str] = Query(None, description="Filter by competitor name"),
    limit: int = Query(100, description="Maximum number of extracted companies to return"),
    offset: int = Query(0, description="Number of companies to skip")
) -> List[dict]:
    """
    Get extracted companies from extraction sessions.
    """
    try:
        query = db.query(ExtractedCompany)
        
        # Apply competitor filter
        if competitor:
            query = query.filter(ExtractedCompany.competitor == competitor)
        
        # Order by creation date (newest first)
        companies = query.order_by(
            ExtractedCompany.first_seen.desc()
        ).offset(offset).limit(limit).all()
        
        # Convert to dict format
        result = []
        for company in companies:
            company_dict = {
                "id": company.id,
                "name": company.name,
                "normalized_name": company.normalized_name,
                "aliases": company.aliases or [],
                "website": normalize_website_url(company.website),
                "hq_country": company.hq_country,
                "status": company.status,
                "tags": company.tags or [],
                "short_desc": company.short_desc,
                "competitor": company.competitor,
                "confidence_score": company.confidence_score,
                "created_at": format_datetime_for_api(company.first_seen),
                "last_updated": format_datetime_for_api(company.last_updated)
            }
            result.append(company_dict)
        
        logger.info(f"Retrieved {len(result)} extracted companies")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving extracted companies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}")
async def get_company(company_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Get a specific company by ID.
    """
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {
            "id": company.id,
            "name": company.name,
            "aliases": company.aliases or [],
            "hq_country": company.hq_country,
            "website": normalize_website_url(company.website),
            "status": company.status,
            "tags": company.tags or [],
            "short_desc": getattr(company, 'short_desc', None),
            "logoUrl": company.logo_url,
            "isSelf": company.is_self
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/summaries")
async def get_company_summaries(company_id: str, db: Session = Depends(get_db)) -> List[dict]:
    """
    Get company summaries for a specific company.
    """
    try:
        # Check if company exists
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        summaries = db.query(CompanySummary).filter(
            CompanySummary.company_id == company_id
        ).all()
        
        result = []
        for summary in summaries:
            summary_dict = {
                "company_id": summary.company_id,
                "one_liner": summary.one_liner,
                "founded_year": summary.founded_year,
                "hq_city": summary.hq_city,
                "employees": summary.employees,
                "footprint": summary.footprint,
                "sites": summary.sites or [],
                "sources": summary.sources or []
            }
            result.append(summary_dict)
        
        logger.info(f"Retrieved {len(result)} summaries for company {company_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving company summaries for {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/products")
async def get_company_products(company_id: str, db: Session = Depends(get_db)) -> List[dict]:
    """
    Get products for a specific company.
    """
    try:
        # Check if company exists
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        products = db.query(Product).filter(Product.company_id == company_id).all()
        
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
                "released_at": format_datetime_for_api(product.released_at),
                "eol_at": format_datetime_for_api(product.eol_at),
                "compliance": product.compliance or []
            }
            result.append(product_dict)
        
        logger.info(f"Retrieved {len(result)} products for company {company_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving company products for {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/signals")
async def get_company_signals(
    company_id: str,
    db: Session = Depends(get_db),
    days: int = Query(60, description="Number of days to look back for signals"),
    limit: int = Query(50, description="Maximum number of signals to return")
) -> List[dict]:
    """
    Get recent signals for a specific company.
    """
    try:
        # Check if company exists
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        signals = db.query(Signal).filter(
            Signal.company_ids.contains([company_id]),
            Signal.published_at >= cutoff_date
        ).order_by(Signal.published_at.desc()).limit(limit).all()
        
        result = []
        for signal in signals:
            signal_dict = {
                "id": signal.id,
                "type": signal.type,
                "headline": signal.headline,
                "summary": signal.summary,
                "published_at": format_datetime_for_api(signal.published_at),
                "url": signal.url,
                "company_ids": signal.company_ids or [],
                "product_ids": signal.product_ids or [],
                "capability_ids": signal.capability_ids or [],
                "impact": signal.impact,
                "source_id": signal.source_id
            }
            result.append(signal_dict)
        
        logger.info(f"Retrieved {len(result)} signals for company {company_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving company signals for {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


