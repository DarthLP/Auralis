"""
Capabilities API endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.db import get_db
from app.models.product import Capability

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


@router.get("/")
async def get_capabilities(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search capabilities by name or definition"),
    limit: int = Query(100, description="Maximum number of capabilities to return"),
    offset: int = Query(0, description="Number of capabilities to skip")
) -> List[dict]:
    """
    Get all capabilities with optional search.
    """
    try:
        query = db.query(Capability)
        
        # Apply search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    Capability.name.ilike(search_term),
                    Capability.definition.ilike(search_term),
                    Capability.tags.any(lambda tag: tag.ilike(search_term))
                )
            )
        
        capabilities = query.order_by(Capability.name.asc()).offset(offset).limit(limit).all()
        
        # Convert to dict format expected by frontend
        result = []
        for capability in capabilities:
            capability_dict = {
                "id": capability.id,
                "name": capability.name,
                "definition": capability.definition,
                "tags": capability.tags or []
            }
            result.append(capability_dict)
        
        logger.info(f"Retrieved {len(result)} capabilities")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving capabilities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{capability_id}")
async def get_capability(capability_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Get a specific capability by ID.
    """
    try:
        capability = db.query(Capability).filter(Capability.id == capability_id).first()
        
        if not capability:
            raise HTTPException(status_code=404, detail="Capability not found")
        
        return {
            "id": capability.id,
            "name": capability.name,
            "definition": capability.definition,
            "tags": capability.tags or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving capability {capability_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
