"""
FastAPI endpoints for the extraction pipeline.

Provides REST API for running schema-first extraction on fingerprint sessions,
with progress tracking and error handling.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.config import settings
from app.services.extract import ExtractionService
from app.services.theta_client import ThetaClient
from app.services.export_utils import ensure_exports_directory, export_extraction_data
from app.services.normalize import NormalizationService
from app.services.advisory_locks import competitor_lock
from app.models.core_crawl import PageFingerprint, FingerprintSession
from app.models.extraction import ExtractionSession
from app.api.extract_stream import (
    emit_page_queued, emit_page_started, emit_page_extracted, 
    emit_page_merged, emit_page_failed, emit_metrics, emit_session_finished
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extract", tags=["extraction"])


# Request/Response Models
class ExtractionRequest(BaseModel):
    """Request to start extraction on a fingerprint session."""
    fingerprint_session_id: int
    competitor: str
    schema_version: Optional[str] = Field(default="v1", description="Schema version to use")
    force_reprocess: bool = Field(default=False, description="Force reprocessing even if already extracted")


class ExtractionStats(BaseModel):
    """Statistics for an extraction session."""
    total_pages: int = 0
    processed_pages: int = 0
    skipped_pages: int = 0
    failed_pages: int = 0
    cache_hits: int = 0
    total_retries: int = 0
    
    # Entity counts
    companies_found: int = 0
    products_found: int = 0
    capabilities_found: int = 0
    releases_found: int = 0
    documents_found: int = 0
    signals_found: int = 0
    changes_detected: int = 0


class ExtractionResponse(BaseModel):
    """Response from extraction endpoint."""
    extraction_session_id: int
    fingerprint_session_id: int
    competitor: str
    schema_version: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # "running", "completed", "failed", "degraded"
    stats: ExtractionStats
    error_summary: Optional[Dict[str, str]] = None  # page_id -> error_reason
    

class ExtractionPageResult(BaseModel):
    """Result for a single page extraction."""
    page_id: int
    url: str
    status: str  # "success", "skipped", "failed"
    method: Optional[str] = None  # "rules", "ai"
    confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    entities_found: Optional[int] = None
    error: Optional[str] = None


# Dependency injection
def get_extraction_service(db: Session = Depends(get_db)) -> ExtractionService:
    """Get extraction service with dependencies."""
    theta_client = ThetaClient(db)
    return ExtractionService(theta_client)


@router.post("/run", response_model=ExtractionResponse)
async def run_extraction(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    # Ensure exports directory exists
    ensure_exports_directory()
    """
    Start extraction on a fingerprint session.
    
    This endpoint initiates the extraction process and returns immediately.
    The actual extraction runs in the background, and progress can be tracked
    via the session ID.
    """
    try:
        # Validate fingerprint session exists
        fingerprint_session = db.query(FingerprintSession).filter(
            FingerprintSession.id == request.fingerprint_session_id
        ).first()
        
        if not fingerprint_session:
            raise HTTPException(
                status_code=404,
                detail=f"Fingerprint session {request.fingerprint_session_id} not found"
            )
        
        # Check if extraction already exists and not forcing reprocess
        existing_extraction = db.query(ExtractionSession).filter(
            ExtractionSession.fingerprint_session_id == request.fingerprint_session_id,
            ExtractionSession.competitor == request.competitor,
            ExtractionSession.schema_version == request.schema_version
        ).first()
        
        if existing_extraction and not request.force_reprocess:
            # Return existing extraction session
            return ExtractionResponse(
                extraction_session_id=existing_extraction.id,
                fingerprint_session_id=existing_extraction.fingerprint_session_id,
                competitor=existing_extraction.competitor,
                schema_version=existing_extraction.schema_version,
                started_at=existing_extraction.started_at,
                completed_at=existing_extraction.completed_at,
                status="completed" if existing_extraction.completed_at else "running",
                stats=ExtractionStats(
                    total_pages=existing_extraction.total_pages or 0,
                    processed_pages=existing_extraction.processed_pages or 0,
                    skipped_pages=existing_extraction.skipped_pages or 0,
                    failed_pages=existing_extraction.failed_pages or 0,
                    cache_hits=existing_extraction.cache_hits or 0,
                    total_retries=existing_extraction.total_retries or 0,
                    companies_found=existing_extraction.companies_found or 0,
                    products_found=existing_extraction.products_found or 0,
                    capabilities_found=existing_extraction.capabilities_found or 0,
                    releases_found=existing_extraction.releases_found or 0,
                    documents_found=existing_extraction.documents_found or 0,
                    signals_found=existing_extraction.signals_found or 0,
                    changes_detected=existing_extraction.changes_detected or 0
                ),
                error_summary=existing_extraction.error_summary
            )
        
        # Create new extraction session
        extraction_session = ExtractionSession(
            fingerprint_session_id=request.fingerprint_session_id,
            competitor=request.competitor,
            schema_version=request.schema_version,
            started_at=datetime.utcnow()
        )
        
        db.add(extraction_session)
        db.commit()
        db.refresh(extraction_session)
        
        # Start background BATCH extraction (restructured pipeline)
        background_tasks.add_task(
            _run_batch_extraction_background,
            extraction_session.id,
            extraction_service
        )
        
        return ExtractionResponse(
            extraction_session_id=extraction_session.id,
            fingerprint_session_id=extraction_session.fingerprint_session_id,
            competitor=extraction_session.competitor,
            schema_version=extraction_session.schema_version,
            started_at=extraction_session.started_at,
            status="running",
            stats=ExtractionStats()
        )
        
    except Exception as e:
        logger.error(f"Failed to start extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start extraction: {e}")


@router.get("/status/{extraction_session_id}", response_model=ExtractionResponse)
async def get_extraction_status(
    extraction_session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the status of an extraction session.
    """
    extraction_session = db.query(ExtractionSession).filter(
        ExtractionSession.id == extraction_session_id
    ).first()
    
    if not extraction_session:
        raise HTTPException(
            status_code=404,
            detail=f"Extraction session {extraction_session_id} not found"
        )
    
    # Determine status
    if extraction_session.completed_at:
        if extraction_session.failed_pages and extraction_session.processed_pages:
            fail_rate = extraction_session.failed_pages / (extraction_session.processed_pages + extraction_session.failed_pages)
            status = "degraded" if fail_rate > settings.EXTRACTOR_FAIL_THRESHOLD else "completed"
        else:
            status = "completed"
    else:
        status = "running"
    
    return ExtractionResponse(
        extraction_session_id=extraction_session.id,
        fingerprint_session_id=extraction_session.fingerprint_session_id,
        competitor=extraction_session.competitor,
        schema_version=extraction_session.schema_version,
        started_at=extraction_session.started_at,
        completed_at=extraction_session.completed_at,
        status=status,
        stats=ExtractionStats(
            total_pages=extraction_session.total_pages or 0,
            processed_pages=extraction_session.processed_pages or 0,
            skipped_pages=extraction_session.skipped_pages or 0,
            failed_pages=extraction_session.failed_pages or 0,
            cache_hits=extraction_session.cache_hits or 0,
            total_retries=extraction_session.total_retries or 0,
            companies_found=extraction_session.companies_found or 0,
            products_found=extraction_session.products_found or 0,
            capabilities_found=extraction_session.capabilities_found or 0,
            releases_found=extraction_session.releases_found or 0,
            documents_found=extraction_session.documents_found or 0,
            signals_found=extraction_session.signals_found or 0,
            changes_detected=extraction_session.changes_detected or 0
        ),
        error_summary=extraction_session.error_summary
    )


@router.get("/sessions", response_model=List[ExtractionResponse])
async def list_extraction_sessions(
    competitor: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List extraction sessions with optional filtering.
    """
    query = db.query(ExtractionSession)
    
    if competitor:
        query = query.filter(ExtractionSession.competitor == competitor)
    
    sessions = query.order_by(ExtractionSession.started_at.desc()).offset(offset).limit(limit).all()
    
    return [
        ExtractionResponse(
            extraction_session_id=session.id,
            fingerprint_session_id=session.fingerprint_session_id,
            competitor=session.competitor,
            schema_version=session.schema_version,
            started_at=session.started_at,
            completed_at=session.completed_at,
            status="completed" if session.completed_at else "running",
            stats=ExtractionStats(
                total_pages=session.total_pages or 0,
                processed_pages=session.processed_pages or 0,
                skipped_pages=session.skipped_pages or 0,
                failed_pages=session.failed_pages or 0,
                cache_hits=session.cache_hits or 0,
                total_retries=session.total_retries or 0,
                companies_found=session.companies_found or 0,
                products_found=session.products_found or 0,
                capabilities_found=session.capabilities_found or 0,
                releases_found=session.releases_found or 0,
                documents_found=session.documents_found or 0,
                signals_found=session.signals_found or 0,
                changes_detected=session.changes_detected or 0
            ),
            error_summary=session.error_summary
        )
        for session in sessions
    ]


@router.post("/stop/{extraction_session_id}")
async def stop_extraction_session(
    extraction_session_id: int,
    db: Session = Depends(get_db)
):
    """
    Stop a running extraction session.
    
    This will mark the session as completed and stop any ongoing LLM requests
    to prevent unnecessary costs. The session will be marked as cancelled.
    """
    try:
        extraction_session = db.query(ExtractionSession).filter(
            ExtractionSession.id == extraction_session_id
        ).first()
        
        if not extraction_session:
            raise HTTPException(
                status_code=404,
                detail=f"Extraction session {extraction_session_id} not found"
            )
        
        # Check if session is already completed
        if extraction_session.completed_at:
            return {
                "message": f"Extraction session {extraction_session_id} is already completed",
                "status": "already_completed",
                "completed_at": extraction_session.completed_at.isoformat()
            }
        
        # Mark session as stopped/cancelled
        extraction_session.completed_at = datetime.utcnow()
        if not extraction_session.error_summary:
            extraction_session.error_summary = {}
        extraction_session.error_summary["system"] = "Session stopped by user request"
        
        db.commit()
        
        # Emit session finished event to notify any streaming clients
        from app.api.extract_stream import emit_session_finished, progress_tracker
        emit_session_finished(
            extraction_session_id,
            extraction_session.processed_pages or 0,
            extraction_session.processed_pages or 0,
            extraction_session.failed_pages or 0,
            extraction_session.changes_detected or 0
        )
        
        # Clean up progress tracking
        progress_tracker.cleanup_session(extraction_session_id)
        
        logger.info(f"Stopped extraction session {extraction_session_id} for competitor {extraction_session.competitor}")
        
        return {
            "message": f"Successfully stopped extraction session {extraction_session_id}",
            "status": "stopped",
            "competitor": extraction_session.competitor,
            "processed_pages": extraction_session.processed_pages or 0,
            "total_pages": extraction_session.total_pages or 0,
            "stopped_at": extraction_session.completed_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop extraction session {extraction_session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop extraction session: {e}")


@router.post("/stop-all")
async def stop_all_running_sessions(
    competitor: Optional[str] = Query(None, description="Only stop sessions for this competitor"),
    db: Session = Depends(get_db)
):
    """
    Stop all currently running extraction sessions.
    
    This is useful to prevent unnecessary LLM costs when starting fresh extractions.
    Optionally filter by competitor to only stop sessions for a specific competitor.
    """
    try:
        # Find all running sessions (those without completed_at)
        query = db.query(ExtractionSession).filter(
            ExtractionSession.completed_at.is_(None)
        )
        
        if competitor:
            query = query.filter(ExtractionSession.competitor == competitor)
        
        running_sessions = query.all()
        
        if not running_sessions:
            return {
                "message": "No running extraction sessions found",
                "status": "no_sessions",
                "stopped_count": 0
            }
        
        stopped_sessions = []
        
        # Stop each running session
        for session in running_sessions:
            session.completed_at = datetime.utcnow()
            if not session.error_summary:
                session.error_summary = {}
            session.error_summary["system"] = "Session stopped by bulk stop request"
            
            # Emit session finished event
            from app.api.extract_stream import emit_session_finished, progress_tracker
            emit_session_finished(
                session.id,
                session.processed_pages or 0,
                session.processed_pages or 0,
                session.failed_pages or 0,
                session.changes_detected or 0
            )
            
            # Clean up progress tracking
            progress_tracker.cleanup_session(session.id)
            
            stopped_sessions.append({
                "session_id": session.id,
                "competitor": session.competitor,
                "processed_pages": session.processed_pages or 0,
                "total_pages": session.total_pages or 0
            })
        
        db.commit()
        
        logger.info(f"Stopped {len(stopped_sessions)} extraction sessions")
        
        return {
            "message": f"Successfully stopped {len(stopped_sessions)} extraction sessions",
            "status": "stopped",
            "stopped_count": len(stopped_sessions),
            "stopped_sessions": stopped_sessions
        }
        
    except Exception as e:
        logger.error(f"Failed to stop all extraction sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop extraction sessions: {e}")


async def _run_batch_extraction_background(
    extraction_session_id: int,
    extraction_service: ExtractionService
):
    """
    Background task to run the batch extraction process using the restructured pipeline.
    
    New approach:
    - Step 1: Process each page individually to get basic extractions
    - Step 2A: ONE consolidated company LLM request with all company data  
    - Step 2B: ONE consolidated product LLM request with all product data (sequential after 2A)
    """
    # Create a new database session for the background task
    from app.core.db import SessionLocal
    db = SessionLocal()
    
    try:
        extraction_session = db.query(ExtractionSession).filter(
            ExtractionSession.id == extraction_session_id
        ).first()
        
        if not extraction_session:
            logger.error(f"Extraction session {extraction_session_id} not found")
            return
        
        # Get all page fingerprints for this session that have text
        fingerprints = db.query(PageFingerprint).filter(
            PageFingerprint.fingerprint_session_id == extraction_session.fingerprint_session_id,
            PageFingerprint.normalized_text_len > 0,
            PageFingerprint.extracted_text.isnot(None)
        ).all()
        
        extraction_session.total_pages = len(fingerprints)
        db.commit()
        
        logger.info(f"Starting BATCH extraction for {len(fingerprints)} pages")
        
        # Prepare page data for batch processing
        page_data_list = []
        for fingerprint in fingerprints:
            # Emit page queued event
            emit_page_queued(extraction_session_id, fingerprint.id, fingerprint.url)
            
            page_data_list.append({
                "text": fingerprint.extracted_text,
                "url": fingerprint.url,
                "page_type": fingerprint.page_type,
                "content_hash": fingerprint.content_hash,
                "fingerprint_id": fingerprint.id
            })
        
        start_time = datetime.utcnow()
        
        # Run batch extraction (Step 1 + consolidated Step 2A + Step 2B)
        batch_result = await extraction_service.extract_batch_from_pages(
            page_data_list=page_data_list,
            competitor=extraction_session.competitor,
            session_id=str(extraction_session_id)
        )
        
        if batch_result.success:
            logger.info(f"Batch extraction succeeded with confidence {batch_result.confidence:.2f}")
            
            # Emit extraction results for all pages (since they were processed as a batch)
            for page_data in page_data_list:
                emit_page_extracted(
                    extraction_session_id,
                    page_data["fingerprint_id"],
                    batch_result.method,
                    batch_result.confidence,
                    batch_result.tokens_input,
                    batch_result.tokens_output,
                    batch_result.cache_hit
                )
            
            # Normalize and store extracted entities (once for all pages)
            with competitor_lock(db, extraction_session.competitor) as lock_acquired:
                if lock_acquired:
                    normalization_service = NormalizationService(db)
                    
                    # Create consolidated source metadata
                    source_metadata = {
                        "extraction_session_id": extraction_session_id,
                        "competitor": extraction_session.competitor,
                        "method": batch_result.method,
                        "confidence": batch_result.confidence,
                        "processing_time_ms": batch_result.processing_time_ms,
                        "tokens_input": batch_result.tokens_input,
                        "tokens_output": batch_result.tokens_output,
                        "cache_hit": batch_result.cache_hit,
                        "pages_processed": len(page_data_list)
                    }
                    
                    # Normalize entities
                    changes = normalization_service.normalize_and_upsert(
                        extracted_entities=batch_result.entities,
                        competitor=extraction_session.competitor,
                        extraction_session_id=extraction_session_id,
                        source_metadata=source_metadata
                    )
                    
                    # Emit merge completion for all pages
                    for page_data in page_data_list:
                        emit_page_merged(extraction_session_id, page_data["fingerprint_id"], [], len(changes))
                    
                    # Update extraction session stats
                    extraction_session.processed_pages = len(page_data_list)
                    extraction_session.companies_found = len(batch_result.entities.get("Company", []))
                    extraction_session.products_found = len(batch_result.entities.get("Product", []))
                    extraction_session.capabilities_found = len(batch_result.entities.get("Capability", []))
                    extraction_session.releases_found = len(batch_result.entities.get("Release", []))
                    extraction_session.documents_found = len(batch_result.entities.get("Document", []))
                    extraction_session.signals_found = len(batch_result.entities.get("Signal", []))
                    extraction_session.changes_detected = len(changes)
                    extraction_session.cache_hits = 1 if batch_result.cache_hit else 0
                    
                    logger.info(f"Batch extraction completed: {extraction_session.companies_found} companies, "
                              f"{extraction_session.products_found} products, {extraction_session.capabilities_found} capabilities")
                else:
                    logger.warning(f"Could not acquire competitor lock for {extraction_session.competitor}")
                    extraction_session.failed_pages = len(page_data_list)
                    extraction_session.error_summary = {"lock_error": "Could not acquire competitor lock"}
        else:
            logger.error(f"Batch extraction failed: {batch_result.error}")
            extraction_session.failed_pages = len(page_data_list)
            extraction_session.error_summary = {"batch_error": batch_result.error}
            
            # Emit failure for all pages
            for page_data in page_data_list:
                emit_page_failed(extraction_session_id, page_data["fingerprint_id"], batch_result.error or "Batch extraction failed")
        
        # Complete the session
        extraction_session.completed_at = datetime.utcnow()
        db.commit()
        
        # Emit session finished event
        if batch_result.success:
            emit_session_finished(extraction_session_id, len(page_data_list), len(page_data_list), 0, extraction_session.changes_detected or 0)
        else:
            emit_session_finished(extraction_session_id, 0, 0, len(page_data_list), 0)
        
        # Export data
        try:
            await export_extraction_data(db, extraction_session_id)
            logger.info(f"Exported extraction data for session {extraction_session_id}")
        except Exception as e:
            logger.error(f"Failed to export extraction data: {e}")
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Batch extraction session {extraction_session_id} completed in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Batch extraction session {extraction_session_id} failed: {e}")
        
        # Update session with error
        try:
            extraction_session = db.query(ExtractionSession).filter(
                ExtractionSession.id == extraction_session_id
            ).first()
            if extraction_session:
                extraction_session.completed_at = datetime.utcnow()
                extraction_session.error_summary = {"system_error": str(e)}
                db.commit()
                
                emit_session_finished(extraction_session_id, 0, 0, 0, 0)
        except Exception as cleanup_error:
            logger.error(f"Failed to update session after error: {cleanup_error}")
    
    finally:
        db.close()


async def _run_extraction_background(
    extraction_session_id: int,
    extraction_service: ExtractionService
):
    """
    Background task to run the actual extraction process.
    """
    # Create a new database session for the background task
    from app.core.db import SessionLocal
    db = SessionLocal()
    
    try:
        extraction_session = db.query(ExtractionSession).filter(
            ExtractionSession.id == extraction_session_id
        ).first()
        
        if not extraction_session:
            logger.error(f"Extraction session {extraction_session_id} not found")
            return
        
        # Get all page fingerprints for this session that have text
        fingerprints = db.query(PageFingerprint).filter(
            PageFingerprint.fingerprint_session_id == extraction_session.fingerprint_session_id,
            PageFingerprint.normalized_text_len > 0,
            PageFingerprint.extracted_text.isnot(None)
        ).all()
        
        extraction_session.total_pages = len(fingerprints)
        db.commit()
        
        logger.info(f"Starting extraction for {len(fingerprints)} pages")
        
        # Process each page
        processed = 0
        skipped = 0
        failed = 0
        cache_hits = 0
        total_retries = 0
        error_summary = {}
        start_time = datetime.utcnow()
        
        for i, fingerprint in enumerate(fingerprints):
            try:
                # Emit page queued event
                emit_page_queued(extraction_session_id, fingerprint.id, fingerprint.url)
                
                # Check if already processed (hash-and-skip)
                # TODO: Implement hash-and-skip logic here
                
                # Emit page started event
                emit_page_started(extraction_session_id, fingerprint.id)
                
                # Extract from this page
                result = await extraction_service.extract_structured_from_text(
                    raw_text=fingerprint.extracted_text,
                    url=fingerprint.url,
                    page_type=fingerprint.page_type,
                    competitor=extraction_session.competitor,
                    content_hash=fingerprint.content_hash,
                    session_id=str(extraction_session_id)
                )
                
                # Emit extraction result
                emit_page_extracted(
                    extraction_session_id, 
                    fingerprint.id, 
                    result.method, 
                    result.confidence,
                    result.tokens_input,
                    result.tokens_output,
                    result.cache_hit
                )
                
                if result.success:
                    processed += 1
                    if result.cache_hit:
                        cache_hits += 1
                    
                    # Normalize and store extracted entities
                    with competitor_lock(db, extraction_session.competitor) as lock_acquired:
                        if lock_acquired:
                            normalization_service = NormalizationService(db)
                            
                            source_metadata = {
                                "url": fingerprint.url,
                                "content_hash": fingerprint.content_hash,
                                "page_type": fingerprint.page_type,
                                "method": result.method,
                                "ai_model": "deepseek_r1" if result.method == "ai" else None,
                                "confidence": result.confidence,
                                "tokens_input": result.tokens_input,
                                "tokens_output": result.tokens_output,
                                "processing_time_ms": result.processing_time_ms,
                                "cache_hit": result.cache_hit
                            }
                            
                            norm_result = normalization_service.normalize_and_upsert(
                                result.entities,
                                extraction_session.competitor,
                                extraction_session_id,
                                source_metadata
                            )
                            
                            # Update session stats with normalization results
                            extraction_session.companies_found += norm_result.get("entities_created", 0)
                            extraction_session.changes_detected += norm_result.get("changes_detected", 0)
                            
                            # Emit merge result
                            emit_page_merged(
                                extraction_session_id,
                                fingerprint.id,
                                list(result.entities.keys()),
                                norm_result.get("changes_detected", 0)
                            )
                            
                        else:
                            logger.warning(f"Could not acquire lock for competitor {extraction_session.competitor}, skipping normalization")
                    
                    logger.debug(f"Extracted from {fingerprint.url}: {result.method}, confidence={result.confidence:.2f}")
                else:
                    failed += 1
                    error_summary[str(fingerprint.id)] = result.error or "Unknown error"
                    emit_page_failed(extraction_session_id, fingerprint.id, result.error or "Unknown error")
                    logger.warning(f"Failed to extract from {fingerprint.url}: {result.error}")
                
            except Exception as e:
                failed += 1
                error_summary[str(fingerprint.id)] = str(e)
                emit_page_failed(extraction_session_id, fingerprint.id, str(e))
                logger.error(f"Error processing {fingerprint.url}: {e}")
            
            # Update progress periodically and emit metrics
            if (processed + skipped + failed) % 5 == 0 or i == len(fingerprints) - 1 or (processed + skipped + failed) == 1:
                extraction_session.processed_pages = processed
                extraction_session.skipped_pages = skipped
                extraction_session.failed_pages = failed
                extraction_session.cache_hits = cache_hits
                extraction_session.total_retries = total_retries
                extraction_session.error_summary = error_summary
                db.commit()
                
                # Calculate metrics
                elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
                pages_per_minute = ((processed + failed) / max(elapsed_seconds, 1)) * 60
                remaining = len(fingerprints) - (processed + skipped + failed)
                eta_seconds = int(remaining / max(pages_per_minute / 60, 0.1)) if remaining > 0 else 0
                
                # Emit metrics
                emit_metrics(
                    extraction_session_id,
                    processed + skipped + failed,
                    processed,
                    failed,
                    skipped,
                    cache_hits,
                    total_retries,
                    pages_per_minute,
                    eta_seconds if remaining > 0 else None
                )
        
        # Final update
        extraction_session.processed_pages = processed
        extraction_session.skipped_pages = skipped
        extraction_session.failed_pages = failed
        extraction_session.cache_hits = cache_hits
        extraction_session.total_retries = total_retries
        extraction_session.error_summary = error_summary
        extraction_session.completed_at = datetime.utcnow()
        
        db.commit()
        
        # Emit final session completion
        emit_session_finished(extraction_session_id, processed, processed, failed, extraction_session.changes_detected or 0)
        
        logger.info(f"Extraction completed: {processed} processed, {skipped} skipped, {failed} failed")
        
    except Exception as e:
        logger.error(f"Background extraction failed: {e}")
        
        # Mark session as failed
        if extraction_session:
            extraction_session.completed_at = datetime.utcnow()
            extraction_session.error_summary = {"system": str(e)}
            db.commit()
    
    finally:
        db.close()
