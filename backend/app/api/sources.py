"""
Sources API endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone

from app.core.db import get_db
from app.models.signal import Source

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sources", tags=["sources"])


def format_datetime_for_api(dt: datetime) -> str:
    """Format datetime for API response in ISO format with Z suffix."""
    if dt is None:
        return None
    # Convert to UTC and format with Z suffix for Zod compatibility
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


@router.get("/")
async def get_sources(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search sources by origin or author"),
    credibility: Optional[str] = Query(None, description="Filter by credibility level"),
    limit: int = Query(100, description="Maximum number of sources to return"),
    offset: int = Query(0, description="Number of sources to skip")
) -> List[dict]:
    """
    Get all sources with optional filtering and search.
    """
    try:
        query = db.query(Source)
        
        # Apply search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    Source.origin.ilike(search_term),
                    Source.author.ilike(search_term)
                )
            )
        
        # Apply credibility filter
        if credibility:
            query = query.filter(Source.credibility == credibility)
        
        sources = query.order_by(Source.origin.asc()).offset(offset).limit(limit).all()
        
        # Convert to dict format expected by frontend
        result = []
        for source in sources:
            source_dict = {
                "id": source.id,
                "origin": source.origin,
                "author": source.author,
                "retrieved_at": format_datetime_for_api(source.retrieved_at),
                "credibility": source.credibility
            }
            result.append(source_dict)
        
        logger.info(f"Retrieved {len(result)} sources")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving sources: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{source_id}")
async def get_source(source_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Get a specific source by ID.
    """
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        return {
            "id": source.id,
            "origin": source.origin,
            "author": source.author,
            "retrieved_at": format_datetime_for_api(source.retrieved_at),
            "credibility": source.credibility
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving source {source_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
