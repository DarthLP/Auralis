"""
Releases API endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta, timezone

from app.core.db import get_db
from app.models.signal import Release

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/releases", tags=["releases"])


def format_datetime_for_api(dt: datetime) -> str:
    """Format datetime for API response in ISO format with Z suffix."""
    if dt is None:
        return None
    # Convert to UTC and format with Z suffix for Zod compatibility
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


@router.get("/")
async def get_releases(
    db: Session = Depends(get_db),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    days: Optional[int] = Query(None, description="Filter releases from last N days"),
    search: Optional[str] = Query(None, description="Search releases by version or notes"),
    limit: int = Query(100, description="Maximum number of releases to return"),
    offset: int = Query(0, description="Number of releases to skip")
) -> List[dict]:
    """
    Get all releases with optional filtering and search.
    """
    try:
        query = db.query(Release)
        
        # Apply filters
        if company_id:
            query = query.filter(Release.company_id == company_id)
        if product_id:
            query = query.filter(Release.product_id == product_id)
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Release.released_at >= cutoff_date)
        
        # Apply search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    Release.version.ilike(search_term),
                    Release.notes.ilike(search_term)
                )
            )
        
        releases = query.order_by(Release.released_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to dict format expected by frontend
        result = []
        for release in releases:
            release_dict = {
                "id": release.id,
                "company_id": release.company_id,
                "product_id": release.product_id,
                "version": release.version,
                "notes": release.notes,
                "released_at": format_datetime_for_api(release.released_at),
                "source_id": release.source_id
            }
            result.append(release_dict)
        
        logger.info(f"Retrieved {len(result)} releases")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving releases: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{release_id}")
async def get_release(release_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Get a specific release by ID.
    """
    try:
        release = db.query(Release).filter(Release.id == release_id).first()
        
        if not release:
            raise HTTPException(status_code=404, detail="Release not found")
        
        return {
            "id": release.id,
            "company_id": release.company_id,
            "product_id": release.product_id,
            "version": release.version,
            "notes": release.notes,
            "released_at": release.released_at.isoformat(),
            "source_id": release.source_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving release {release_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recent/recent-releases")
async def get_recent_releases(
    db: Session = Depends(get_db),
    days: int = Query(90, description="Number of days to look back"),
    limit: int = Query(8, description="Maximum number of releases to return")
) -> List[dict]:
    """
    Get recent releases, excluding "Your Company" releases.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        releases = db.query(Release).filter(
            and_(
                Release.released_at >= cutoff_date,
                Release.company_id != 'cmp_self'  # Exclude "Your Company"
            )
        ).order_by(Release.released_at.desc()).limit(limit).all()
        
        result = []
        for release in releases:
            release_dict = {
                "id": release.id,
                "company_id": release.company_id,
                "product_id": release.product_id,
                "version": release.version,
                "notes": release.notes,
                "released_at": format_datetime_for_api(release.released_at),
                "source_id": release.source_id
            }
            result.append(release_dict)
        
        logger.info(f"Retrieved {len(result)} recent releases")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving recent releases: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
