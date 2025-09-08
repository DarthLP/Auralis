"""
Core crawl API endpoints for fingerprinting crawl sessions.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.core_crawl import FingerprintRequest, FingerprintResponse
from app.services.core_crawl import CoreCrawlService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crawl", tags=["core_crawl"])


@router.post("/fingerprint", response_model=FingerprintResponse)
async def fingerprint_crawl_session(
    request: FingerprintRequest, 
    db: Session = Depends(get_db)
) -> FingerprintResponse:
    """
    Fingerprint pages from a crawl session using the 3-step pipeline:
    1. Filter - Apply score threshold, canonicalize URLs, deduplicate, apply caps
    2. Fetch - Download content with httpx, detect content types, size limits
    3. Fingerprint - Generate stable content hashes based on content type
    
    This endpoint processes pages that were discovered by the /discover endpoint
    and generates stable content fingerprints for change detection.
    
    Args:
        request: FingerprintRequest with crawl_session_id and competitor name
        db: Database session dependency
        
    Returns:
        FingerprintResponse with fingerprint results and metadata
        
    Raises:
        HTTPException: 404 if crawl session not found, 500 for processing errors
    """
    try:
        logger.info(f"Starting fingerprinting for crawl session {request.crawl_session_id}")
        
        # Create service instance
        service = CoreCrawlService(db)
        
        # Process the crawl session
        result = await service.fingerprint_session(request)
        
        logger.info(f"Fingerprinting completed: {result.total_processed} processed, {result.total_errors} errors")
        
        return result
        
    except ValueError as e:
        # Crawl session not found
        logger.error(f"Crawl session not found: {e}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "CRAWL_SESSION_NOT_FOUND",
                "message": str(e)
            }
        )
    except Exception as e:
        # Unexpected error
        logger.error(f"Fingerprinting failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "FINGERPRINTING_FAILED",
                "message": "An unexpected error occurred during fingerprinting",
                "details": str(e)
            }
        )


@router.get("/sessions/{session_id}/fingerprints")
async def get_session_fingerprints(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get fingerprint results for a specific crawl session.
    
    Args:
        session_id: Crawl session ID
        db: Database session dependency
        
    Returns:
        List of fingerprint results for the session
    """
    from app.models.core_crawl import FingerprintSession, PageFingerprint
    
    # Find fingerprint session
    fingerprint_session = db.query(FingerprintSession).filter(
        FingerprintSession.crawl_session_id == session_id
    ).first()
    
    if not fingerprint_session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "FINGERPRINT_SESSION_NOT_FOUND",
                "message": f"No fingerprint session found for crawl session {session_id}"
            }
        )
    
    # Get fingerprint results
    fingerprints = db.query(PageFingerprint).filter(
        PageFingerprint.fingerprint_session_id == fingerprint_session.id
    ).all()
    
    return {
        "fingerprint_session_id": fingerprint_session.id,
        "crawl_session_id": session_id,
        "competitor": fingerprint_session.competitor,
        "started_at": fingerprint_session.started_at,
        "completed_at": fingerprint_session.completed_at,
        "total_processed": fingerprint_session.total_processed,
        "total_errors": fingerprint_session.total_errors,
        "fingerprints": [
            {
                "url": fp.url,
                "key_url": fp.key_url,
                "page_type": fp.page_type,
                "content_hash": fp.content_hash,
                "normalized_text_len": fp.normalized_text_len,
                "low_text_pdf": fp.low_text_pdf,
                "needs_render": fp.needs_render,
                "meta": {
                    "status": fp.fetch_status,
                    "content_type": fp.content_type,
                    "content_length": fp.content_length,
                    "elapsed_ms": fp.fetch_elapsed_ms,
                    "notes": fp.fetch_notes
                }
            }
            for fp in fingerprints
        ]
    }


@router.get("/sessions")
async def list_crawl_sessions(
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    List recent crawl sessions with basic information.
    
    Args:
        db: Database session dependency
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip
        
    Returns:
        List of crawl sessions with metadata
    """
    from app.models.crawl import CrawlSession
    
    sessions = db.query(CrawlSession).order_by(
        CrawlSession.started_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "sessions": [
            {
                "id": session.id,
                "target_url": session.target_url,
                "base_domain": session.base_domain,
                "started_at": session.started_at,
                "completed_at": session.completed_at,
                "total_pages": session.total_pages,
                "warnings": session.warnings
            }
            for session in sessions
        ],
        "total": len(sessions),
        "limit": limit,
        "offset": offset
    }
