"""
Signals API endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta

from app.core.db import get_db
from app.models.signal import Signal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/")
async def get_signals(
    db: Session = Depends(get_db),
    type: Optional[str] = Query(None, description="Filter by signal type"),
    impact: Optional[str] = Query(None, description="Filter by impact level"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    days: Optional[int] = Query(None, description="Filter signals from last N days"),
    search: Optional[str] = Query(None, description="Search signals by headline or summary"),
    limit: int = Query(100, description="Maximum number of signals to return"),
    offset: int = Query(0, description="Number of signals to skip")
) -> List[dict]:
    """
    Get all signals with optional filtering and search.
    """
    try:
        query = db.query(Signal)
        
        # Apply filters
        if type:
            query = query.filter(Signal.type == type)
        if impact:
            query = query.filter(Signal.impact == impact)
        if company_id:
            query = query.filter(Signal.company_ids.contains([company_id]))
        if product_id:
            query = query.filter(Signal.product_ids.contains([product_id]))
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Signal.published_at >= cutoff_date)
        
        # Apply search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    Signal.headline.ilike(search_term),
                    Signal.summary.ilike(search_term)
                )
            )
        
        signals = query.order_by(Signal.published_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to dict format expected by frontend
        result = []
        for signal in signals:
            signal_dict = {
                "id": signal.id,
                "type": signal.type,
                "headline": signal.headline,
                "summary": signal.summary,
                "published_at": signal.published_at.isoformat(),
                "url": signal.url,
                "company_ids": signal.company_ids or [],
                "product_ids": signal.product_ids or [],
                "capability_ids": signal.capability_ids or [],
                "impact": signal.impact,
                "source_id": signal.source_id
            }
            result.append(signal_dict)
        
        logger.info(f"Retrieved {len(result)} signals")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving signals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{signal_id}")
async def get_signal(signal_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Get a specific signal by ID.
    """
    try:
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        return {
            "id": signal.id,
            "type": signal.type,
            "headline": signal.headline,
            "summary": signal.summary,
            "published_at": signal.published_at.isoformat(),
            "url": signal.url,
            "company_ids": signal.company_ids or [],
            "product_ids": signal.product_ids or [],
            "capability_ids": signal.capability_ids or [],
            "impact": signal.impact,
            "source_id": signal.source_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving signal {signal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recent/this-week")
async def get_this_week_signals(
    db: Session = Depends(get_db),
    limit: int = Query(5, description="Maximum number of signals to return")
) -> List[dict]:
    """
    Get signals from the last 7 days, excluding "Your Company" signals.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        signals = db.query(Signal).filter(
            and_(
                Signal.published_at >= cutoff_date,
                ~Signal.company_ids.contains(['cmp_self'])  # Exclude "Your Company"
            )
        ).order_by(
            Signal.impact.desc(),
            Signal.published_at.desc()
        ).limit(limit).all()
        
        result = []
        for signal in signals:
            signal_dict = {
                "id": signal.id,
                "type": signal.type,
                "headline": signal.headline,
                "summary": signal.summary,
                "published_at": signal.published_at.isoformat(),
                "url": signal.url,
                "company_ids": signal.company_ids or [],
                "product_ids": signal.product_ids or [],
                "capability_ids": signal.capability_ids or [],
                "impact": signal.impact,
                "source_id": signal.source_id
            }
            result.append(signal_dict)
        
        logger.info(f"Retrieved {len(result)} signals from this week")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving this week's signals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
