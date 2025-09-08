"""
Server-Sent Events (SSE) endpoint for real-time extraction progress tracking.

Provides live updates on extraction session progress including page counts,
entity discoveries, errors, and completion estimates.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.extraction import ExtractionSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extract", tags=["extraction-streaming"])


class ProgressTracker:
    """Tracks and broadcasts extraction progress via SSE."""
    
    def __init__(self):
        self._sessions: Dict[int, Dict[str, Any]] = {}
        self._subscribers: Dict[int, list] = {}
    
    def update_session_progress(self, session_id: int, progress_data: Dict[str, Any]):
        """Update progress for a session and notify subscribers."""
        self._sessions[session_id] = {
            **self._sessions.get(session_id, {}),
            **progress_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Notify all subscribers for this session
        if session_id in self._subscribers:
            for queue in self._subscribers[session_id]:
                try:
                    queue.put_nowait(progress_data)
                except asyncio.QueueFull:
                    logger.warning(f"Progress queue full for session {session_id}")
    
    def subscribe(self, session_id: int) -> asyncio.Queue:
        """Subscribe to progress updates for a session."""
        if session_id not in self._subscribers:
            self._subscribers[session_id] = []
        
        queue = asyncio.Queue(maxsize=100)
        self._subscribers[session_id].append(queue)
        return queue
    
    def unsubscribe(self, session_id: int, queue: asyncio.Queue):
        """Unsubscribe from progress updates."""
        if session_id in self._subscribers:
            try:
                self._subscribers[session_id].remove(queue)
                if not self._subscribers[session_id]:
                    del self._subscribers[session_id]
            except ValueError:
                pass
    
    def get_current_progress(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get current progress for a session."""
        return self._sessions.get(session_id)
    
    def cleanup_session(self, session_id: int):
        """Clean up session data and subscribers."""
        self._sessions.pop(session_id, None)
        if session_id in self._subscribers:
            # Close all queues
            for queue in self._subscribers[session_id]:
                try:
                    queue.put_nowait({"type": "session_ended"})
                except asyncio.QueueFull:
                    pass
            del self._subscribers[session_id]


# Global progress tracker instance
progress_tracker = ProgressTracker()


def format_sse_message(event_type: str, data: Dict[str, Any]) -> str:
    """Format data as Server-Sent Events message."""
    json_data = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {json_data}\n\n"


async def generate_progress_stream(session_id: int, db: Session):
    """Generate SSE stream for extraction progress."""
    # Verify session exists
    session = db.query(ExtractionSession).filter(
        ExtractionSession.id == session_id
    ).first()
    
    if not session:
        yield format_sse_message("error", {"message": f"Session {session_id} not found"})
        return
    
    # Subscribe to progress updates
    queue = progress_tracker.subscribe(session_id)
    
    try:
        # Send initial session info
        initial_data = {
            "type": "session_started",
            "session_id": session_id,
            "competitor": session.competitor,
            "schema_version": session.schema_version,
            "started_at": session.started_at.isoformat(),
            "total_pages": session.total_pages or 0
        }
        yield format_sse_message("session_started", initial_data)
        
        # Send current progress if available
        current_progress = progress_tracker.get_current_progress(session_id)
        if current_progress:
            yield format_sse_message("progress", current_progress)
        
        # Stream live updates
        while True:
            try:
                # Wait for progress update with timeout
                progress_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                if progress_data.get("type") == "session_ended":
                    break
                
                # Determine event type based on progress data
                event_type = progress_data.get("type", "progress")
                yield format_sse_message(event_type, progress_data)
                
                # Check if session is completed
                if progress_data.get("completed", False):
                    break
                    
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                heartbeat_data = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield format_sse_message("heartbeat", heartbeat_data)
                
                # Check if session is still active
                db.refresh(session)
                if session.completed_at:
                    final_data = {
                        "type": "session_completed",
                        "session_id": session_id,
                        "completed_at": session.completed_at.isoformat(),
                        "stats": {
                            "total_pages": session.total_pages or 0,
                            "processed_pages": session.processed_pages or 0,
                            "skipped_pages": session.skipped_pages or 0,
                            "failed_pages": session.failed_pages or 0,
                            "companies_found": session.companies_found or 0,
                            "products_found": session.products_found or 0,
                            "capabilities_found": session.capabilities_found or 0,
                            "releases_found": session.releases_found or 0,
                            "documents_found": session.documents_found or 0,
                            "signals_found": session.signals_found or 0,
                            "changes_detected": session.changes_detected or 0
                        }
                    }
                    yield format_sse_message("session_completed", final_data)
                    break
    
    except Exception as e:
        logger.error(f"Error in progress stream for session {session_id}: {e}")
        error_data = {
            "type": "error",
            "message": str(e)
        }
        yield format_sse_message("error", error_data)
    
    finally:
        # Cleanup subscription
        progress_tracker.unsubscribe(session_id, queue)


@router.get("/stream/{session_id}")
async def stream_extraction_progress(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Stream real-time extraction progress via Server-Sent Events.
    
    **Event Types:**
    - `session_started`: Initial session information
    - `page_queued`: Page added to processing queue
    - `page_started`: Page processing started
    - `page_extracted`: Page successfully extracted
    - `page_validated`: Page validation completed
    - `page_merged`: Page entities merged into database
    - `page_failed`: Page processing failed
    - `metrics`: Current processing metrics and ETA
    - `heartbeat`: Keep-alive message (every 30s)
    - `session_completed`: Extraction session finished
    - `error`: Error occurred
    
    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/extract/stream/123');
    
    eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress:', data);
    });
    
    eventSource.addEventListener('session_completed', (event) => {
        const data = JSON.parse(event.data);
        console.log('Completed:', data.stats);
        eventSource.close();
    });
    ```
    """
    async def check_client_connected():
        """Check if client is still connected."""
        return not await request.is_disconnected()
    
    # Verify session exists
    session = db.query(ExtractionSession).filter(
        ExtractionSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Extraction session {session_id} not found")
    
    return StreamingResponse(
        generate_progress_stream(session_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


# Helper functions for updating progress from extraction process
def emit_page_queued(session_id: int, page_id: int, url: str):
    """Emit page queued event."""
    progress_tracker.update_session_progress(session_id, {
        "type": "page_queued",
        "page_id": page_id,
        "url": url
    })


def emit_page_started(session_id: int, page_id: int):
    """Emit page processing started event."""
    progress_tracker.update_session_progress(session_id, {
        "type": "page_started", 
        "page_id": page_id
    })


def emit_page_extracted(session_id: int, page_id: int, method: str, confidence: float, 
                       tokens_in: Optional[int] = None, tokens_out: Optional[int] = None,
                       cache_hit: bool = False):
    """Emit page extracted event."""
    progress_tracker.update_session_progress(session_id, {
        "type": "page_extracted",
        "page_id": page_id,
        "method": method,
        "confidence": confidence,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cache_hit": cache_hit
    })


def emit_page_validated(session_id: int, page_id: int, valid: bool, errors: Optional[list] = None):
    """Emit page validation event."""
    progress_tracker.update_session_progress(session_id, {
        "type": "page_validated",
        "page_id": page_id,
        "valid": valid,
        "errors": errors or []
    })


def emit_page_merged(session_id: int, page_id: int, entity_refs: list, changes: int):
    """Emit page merged event.""" 
    progress_tracker.update_session_progress(session_id, {
        "type": "page_merged",
        "page_id": page_id,
        "entity_refs": entity_refs,
        "changes": changes
    })


def emit_page_failed(session_id: int, page_id: int, reason: str, retried: int = 0):
    """Emit page failed event."""
    progress_tracker.update_session_progress(session_id, {
        "type": "page_failed",
        "page_id": page_id,
        "reason": reason,
        "retried": retried
    })


def emit_metrics(session_id: int, processed: int, succeeded: int, failed: int, 
                skipped: int, cache_hits: int, retries: int, qps: float, eta_seconds: Optional[int] = None):
    """Emit current processing metrics."""
    progress_tracker.update_session_progress(session_id, {
        "type": "metrics",
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
        "skipped": skipped,
        "cache_hits": cache_hits,
        "retries": retries,
        "qps": qps,
        "eta_seconds": eta_seconds
    })


def emit_session_finished(session_id: int, processed: int, succeeded: int, failed: int, changes_total: int):
    """Emit session finished event."""
    progress_tracker.update_session_progress(session_id, {
        "type": "session_finished",
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
        "changes_total": changes_total,
        "completed": True
    })
    
    # Clean up after a delay to allow final message delivery
    asyncio.create_task(cleanup_session_delayed(session_id))


async def cleanup_session_delayed(session_id: int):
    """Clean up session after delay to allow final message delivery."""
    await asyncio.sleep(5)  # Allow time for final messages
    progress_tracker.cleanup_session(session_id)


# Health check for SSE system
def sse_health_check() -> Dict[str, Any]:
    """Check health of SSE progress tracking system."""
    return {
        "status": "healthy",
        "active_sessions": len(progress_tracker._sessions),
        "active_subscribers": sum(len(subs) for subs in progress_tracker._subscribers.values()),
        "tracked_sessions": list(progress_tracker._sessions.keys())
    }
