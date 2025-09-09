"""
Crawling API endpoints for website discovery and analysis.
"""

import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, Set, List, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl, validator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.crawl import CrawlSession, CrawledPage
from app.services.scrape import discover_interesting_pages
from app.services.export_utils import export_crawling_data, export_fingerprinting_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crawl", tags=["crawl"])

# Global store for active crawl sessions that can be stopped
active_crawl_sessions: Set[int] = set()


def _extract_competitor_name(url: str) -> str:
    """
    Extract competitor name from URL for AI scoring context.
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove common prefixes and suffixes
        domain = domain.replace('www.', '').replace('www2.', '').replace('www3.', '')
        
        # Extract the main domain name
        if '.' in domain:
            main_domain = domain.split('.')[0]
            # Capitalize first letter for better AI context
            return main_domain.capitalize()
        
        return domain.capitalize()
        
    except Exception:
        return "Unknown"


def _canonicalize_url(url: str) -> str:
    """
    Simple URL canonicalization for deduplication.
    """
    if not url:
        return ""
    
    try:
        from urllib.parse import urlparse, urlunparse
        
        parsed = urlparse(url)
        
        # Remove common tracking parameters
        query_params = []
        if parsed.query:
            params = parsed.query.split('&')
            for param in params:
                if '=' in param:
                    key = param.split('=')[0].lower()
                    # Skip common tracking parameters
                    if key not in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 
                                 'utm_term', 'gclid', 'fbclid', 'msclkid', '_ga', '_gl']:
                        query_params.append(param)
        
        # Rebuild query string
        clean_query = '&'.join(query_params) if query_params else ''
        
        # Normalize path (remove trailing slash except for root)
        clean_path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
        
        # Rebuild URL
        canonical = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            clean_path,
            parsed.params,
            clean_query,
            ''  # Remove fragment
        ))
        
        return canonical
        
    except Exception:
        return url


class CrawlRequest(BaseModel):
    """Request model for crawl discovery endpoint."""
    url: HttpUrl
    clear_old_data: bool = False  # Whether to clear old crawl data before starting
    
    @validator('url')
    def validate_url_scheme(cls, v):
        """Ensure URL has http or https scheme."""
        if v.scheme not in ['http', 'https']:
            raise ValueError('URL must use http or https scheme')
        return v


class CrawlResponse(BaseModel):
    """Response model for crawl discovery endpoint."""
    input_url: str
    base_domain: str
    limits: Dict
    pages: list
    top_by_category: Dict
    warnings: list = []
    error: str = None
    crawl_session_id: int = None
    sitemap_urls: list = []
    filtered_sitemap_urls: list = []
    sitemap_filtered_count: int = 0
    sitemap_processed_count: int = 0
    skipped_urls_details: list = []


class StopCrawlRequest(BaseModel):
    """Request model for stopping a crawl session."""
    crawl_session_id: int


class StopCrawlResponse(BaseModel):
    """Response model for stopping a crawl session."""
    success: bool
    message: str


def setup_detailed_logging(log_file: str) -> logging.Logger:
    """Setup detailed logging for crawling operations."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Create a specific logger for crawling
    crawl_logger = logging.getLogger('crawl_operations')
    crawl_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    crawl_logger.handlers.clear()
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    crawl_logger.addHandler(file_handler)
    
    return crawl_logger


@router.delete("/clear-data")
async def clear_crawl_data(db: Session = Depends(get_db)):
    """
    Clear all crawl data from the database.
    
    This endpoint removes all crawl sessions and their associated pages.
    Use with caution as this action cannot be undone.
    
    Returns:
        Dict with success status and count of cleared sessions
    """
    try:
        # Count sessions before deletion
        session_count = db.query(CrawlSession).count()
        
        # Delete all crawl sessions and their pages (cascade will handle pages)
        db.query(CrawlSession).delete()
        db.commit()
        
        logger.info(f"Cleared {session_count} crawl sessions and their pages")
        
        return {
            "success": True,
            "message": f"Cleared {session_count} crawl sessions and their associated pages",
            "sessions_cleared": session_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear crawl data: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear crawl data: {str(e)}")


@router.post("/discover", response_model=CrawlResponse)
async def discover_pages(request: CrawlRequest, db: Session = Depends(get_db)) -> CrawlResponse:
    """
    Discover and classify interesting pages from a competitor website.
    
    This endpoint crawls a website starting from the provided URL and discovers
    pages that might be interesting for competitive analysis. Pages are classified
    into categories (product, docs, pricing, etc.) and scored by relevance.
    
    Args:
        request: CrawlRequest with the target URL
        
    Returns:
        CrawlResponse with discovered pages and metadata
        
    Raises:
        HTTPException: 400 for invalid URL, 502 for homepage fetch failure
    """
    try:
        # Setup detailed logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/crawl_{timestamp}.log"
        crawl_logger = setup_detailed_logging(log_file)
        
        # Prepare crawling limits from settings
        limits = {
            'max_pages': settings.SCRAPER_MAX_PAGES,
            'max_depth': settings.SCRAPER_MAX_DEPTH,
            'timeout': settings.SCRAPER_TIMEOUT,
            'rate_sleep': settings.SCRAPER_RATE_SLEEP,
            'user_agent': settings.SCRAPER_USER_AGENT,
            'js_wait_time': settings.SCRAPER_JS_WAIT_TIME
        }
        
        logger.info(f"Starting crawl discovery for {request.url}")
        crawl_logger.info(f"=== CRAWL SESSION STARTED ===")
        crawl_logger.info(f"Target URL: {request.url}")
        crawl_logger.info(f"Clear old data: {request.clear_old_data}")
        crawl_logger.info(f"JavaScript enabled: {settings.SCRAPER_ENABLE_JAVASCRIPT}")
        crawl_logger.info(f"Limits: {limits}")
        crawl_logger.info(f"Log file: {log_file}")
        
        # Clear old crawl data if requested
        if request.clear_old_data:
            try:
                logger.info("Clearing old crawl data...")
                crawl_logger.info("Clearing old crawl data...")
                
                # Delete in correct order to handle foreign key constraints
                # First delete page fingerprints, then crawled pages, then crawl sessions
                try:
                    # Delete page fingerprints first
                    from app.models.core_crawl import PageFingerprint
                    db.query(PageFingerprint).delete()
                    db.flush()
                    
                    # Then delete crawled pages
                    db.query(CrawledPage).delete()
                    db.flush()
                    
                    # Finally delete crawl sessions
                    old_sessions = db.query(CrawlSession).all()
                    for session in old_sessions:
                        db.delete(session)
                    
                    db.commit()
                    logger.info(f"Cleared {len(old_sessions)} old crawl sessions and related data")
                    crawl_logger.info(f"Cleared {len(old_sessions)} old crawl sessions and related data")
                    
                except Exception as fk_error:
                    # If foreign key deletion fails, try a simpler approach
                    logger.warning(f"Foreign key deletion failed, trying simpler approach: {fk_error}")
                    db.rollback()
                    
                    # Just delete crawl sessions and let cascade handle the rest
                    old_sessions = db.query(CrawlSession).all()
                    for session in old_sessions:
                        db.delete(session)
                    
                    db.commit()
                    logger.info(f"Cleared {len(old_sessions)} old crawl sessions (cascade delete)")
                    crawl_logger.info(f"Cleared {len(old_sessions)} old crawl sessions (cascade delete)")
                
            except Exception as e:
                logger.warning(f"Failed to clear old data: {e}")
                crawl_logger.warning(f"Failed to clear old data: {e}")
                db.rollback()  # Ensure clean state
        
        # Extract competitor name from URL for AI scoring context
        competitor = _extract_competitor_name(str(request.url))
        
        # Create a temporary crawl session ID for tracking
        # We'll create the actual session after crawling is complete
        temp_session_id = int(datetime.utcnow().timestamp() * 1000)  # Use timestamp as temp ID
        
        # Register as active session
        active_crawl_sessions.add(temp_session_id)
        
        try:
            # Perform fast discovery without AI scoring
            result = await discover_interesting_pages(
                str(request.url), 
                limits, 
                enable_js=settings.SCRAPER_ENABLE_JAVASCRIPT,
                competitor=competitor,
                crawl_logger=crawl_logger,
                stop_check=lambda: temp_session_id not in active_crawl_sessions,
                skip_ai_scoring=True  # Fast discovery mode
            )
        finally:
            # Always remove from active sessions when done
            active_crawl_sessions.discard(temp_session_id)
        
        # Log detailed results
        crawl_logger.info(f"=== CRAWL RESULTS ===")
        crawl_logger.info(f"Total pages found: {len(result.get('pages', []))}")
        crawl_logger.info(f"Warnings: {len(result.get('warnings', []))}")
        
        # Log category breakdown and scoring method statistics
        if result.get('pages'):
            category_counts = {}
            scoring_method_counts = {}
            ai_scores = []
            rules_scores = []
            ai_success_count = 0
            ai_failed_count = 0
            
            for page in result['pages']:
                cat = page.get('primary_category', 'unknown')
                category_counts[cat] = category_counts.get(cat, 0) + 1
                
                method = page.get('scoring_method', 'unknown')
                scoring_method_counts[method] = scoring_method_counts.get(method, 0) + 1
                
                # Track AI scoring success/failure
                if page.get('ai_success') is True:
                    ai_success_count += 1
                    if page.get('ai_score') is not None:
                        ai_scores.append(page.get('ai_score', 0.0))
                elif page.get('ai_success') is False:
                    ai_failed_count += 1
                
                # Track rules scores
                if page.get('rules_score') is not None:
                    rules_scores.append(page.get('rules_score', 0.0))
            
            crawl_logger.info(f"Category breakdown: {category_counts}")
            crawl_logger.info(f"Scoring method breakdown: {scoring_method_counts}")
            crawl_logger.info(f"AI scoring success: {ai_success_count} pages, failed: {ai_failed_count} pages")
            
            if ai_scores:
                avg_ai_score = sum(ai_scores) / len(ai_scores)
                crawl_logger.info(f"AI scores: {len(ai_scores)} pages, avg score: {avg_ai_score:.3f}")
            
            if rules_scores:
                avg_rules_score = sum(rules_scores) / len(rules_scores)
                crawl_logger.info(f"Rules scores: {len(rules_scores)} pages, avg score: {avg_rules_score:.3f}")
            
            # Log top pages with dual scoring
            crawl_logger.info("=== TOP PAGES (with dual scoring) ===")
            top_pages = sorted(result['pages'], key=lambda x: x.get('score', 0), reverse=True)[:10]
            for i, page in enumerate(top_pages, 1):
                primary_score = page.get('score', 0)
                ai_score = page.get('ai_score', 'N/A')
                rules_score = page.get('rules_score', 'N/A')
                method = page.get('scoring_method', 'unknown')
                
                # Format scores for display
                ai_display = f"{ai_score:.2f}" if isinstance(ai_score, (int, float)) else str(ai_score)
                rules_display = f"{rules_score:.2f}" if isinstance(rules_score, (int, float)) else str(rules_score)
                
                crawl_logger.info(f"{i:2d}. {page.get('primary_category', 'unknown'):10s} | "
                                f"Primary: {primary_score:.2f} ({method}) | "
                                f"AI: {ai_display} | Rules: {rules_display} | "
                                f"{page.get('url', 'N/A')}")
            
            # Log AI scoring debugging information (if available)
            if result.get('ai_scoring_debug'):
                debug_info = result['ai_scoring_debug']
                stats = debug_info.get('stats', {})
                crawl_logger.info("=== AI SCORING DEBUG INFO ===")
                crawl_logger.info(f"AI Scoring Stats: {stats.get('attempted', 0)} attempted, "
                                f"{stats.get('successful', 0)} successful, "
                                f"{stats.get('failed', 0)} failed, "
                                f"{stats.get('skipped', 0)} skipped")
                
                # Log detailed reasons
                reasons = stats.get('reasons', {})
                for reason, count in reasons.items():
                    crawl_logger.info(f"  - {reason}: {count} pages")
        
        # Add log file path to response
        result['log_file'] = log_file
        
        # Save crawl session and pages to database
        try:
            # Create crawl session
            crawl_session = CrawlSession(
                target_url=str(request.url),
                base_domain=result["base_domain"],
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                total_pages=len(result.get("pages", [])),
                limits=limits,
                warnings=result.get("warnings", []),
                log_file=log_file,
                json_file=None  # We're not saving JSON files anymore
            )
            db.add(crawl_session)
            db.flush()  # Get the ID without committing
            
            # Update the temp session ID with the real one
            if temp_session_id in active_crawl_sessions:
                active_crawl_sessions.discard(temp_session_id)
                active_crawl_sessions.add(crawl_session.id)
            
            crawl_logger.info(f"Created crawl session with ID: {crawl_session.id}")
            
            # Save pages to database
            pages_saved = 0
            for page_data in result.get("pages", []):
                try:
                    # Canonicalize URL for deduplication
                    canonical_url = _canonicalize_url(page_data.get("url", ""))
                    
                    crawled_page = CrawledPage(
                        session_id=crawl_session.id,
                        url=page_data.get("url", ""),
                        canonical_url=canonical_url,
                        content_hash=page_data.get("content_hash"),
                        status_code=page_data.get("status"),
                        depth=page_data.get("depth", 0),
                        size_bytes=page_data.get("size_bytes", 0),
                        mime_type=page_data.get("mime_type"),
                        crawled_at=datetime.utcnow(),
                        primary_category=page_data.get("primary_category", "other"),
                        secondary_categories=page_data.get("secondary_categories", []),
                        score=page_data.get("score", 0.0),
                        signals=page_data.get("signals", [])
                    )
                    db.add(crawled_page)
                    pages_saved += 1
                except Exception as page_error:
                    crawl_logger.warning(f"Failed to save page {page_data.get('url', 'unknown')}: {page_error}")
                    continue
            
            # Commit all changes
            db.commit()
            crawl_logger.info(f"Saved crawl session and {pages_saved} pages to database")
            
            # Automatically export crawling data
            try:
                export_crawling_data(crawl_session.id, result["base_domain"])
                crawl_logger.info(f"✅ Automatically exported crawling data for session {crawl_session.id}")
            except Exception as export_error:
                crawl_logger.warning(f"Failed to auto-export crawling data: {export_error}")
            
            # Add database info to response
            result['crawl_session_id'] = crawl_session.id
            result['pages_saved_to_db'] = pages_saved
            
        except Exception as db_error:
            db.rollback()
            crawl_logger.error(f"Failed to save to database: {db_error}")
            # Continue with the response even if DB save fails
            result['db_error'] = str(db_error)
        
        # Check for homepage fetch failure
        if "error" in result and result["error"] == "HOMEPAGE_FETCH_FAILED":
            logger.error(f"Homepage fetch failed for {request.url}")
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "HOMEPAGE_FETCH_FAILED",
                    "message": f"Could not fetch the homepage at {request.url}",
                    "warnings": result.get("warnings", [])
                }
            )
        
        logger.info(f"Crawl completed: found {len(result['pages'])} pages")
        
        return CrawlResponse(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during crawl: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during crawling",
                "warnings": [str(e)]
            }
        )


@router.post("/stop", response_model=StopCrawlResponse)
async def stop_crawl(request: StopCrawlRequest) -> StopCrawlResponse:
    """
    Stop an active crawl session.
    
    This endpoint stops a crawl session that is currently running.
    The session will be marked as stopped and any ongoing crawling will be terminated.
    
    Args:
        request: StopCrawlRequest with the crawl session ID to stop
        
    Returns:
        StopCrawlResponse indicating success or failure
    """
    try:
        crawl_session_id = request.crawl_session_id
        
        # Check if the session is active
        if crawl_session_id not in active_crawl_sessions:
            return StopCrawlResponse(
                success=False,
                message=f"Crawl session {crawl_session_id} is not active or does not exist"
            )
        
        # Remove from active sessions
        active_crawl_sessions.discard(crawl_session_id)
        
        logger.info(f"Stopped crawl session {crawl_session_id}")
        
        return StopCrawlResponse(
            success=True,
            message=f"Crawl session {crawl_session_id} has been stopped"
        )
        
    except Exception as e:
        logger.error(f"Error stopping crawl session {request.crawl_session_id}: {e}")
        return StopCrawlResponse(
            success=False,
            message=f"Failed to stop crawl session: {str(e)}"
        )


@router.get("/active-sessions")
async def get_active_sessions() -> Dict[str, list]:
    """
    Get list of active crawl sessions.
    
    Returns:
        Dictionary with list of active session IDs
    """
    return {"active_sessions": list(active_crawl_sessions)}


# Request model for AI scoring
class ScorePagesRequest(BaseModel):
    pages: List[Dict[str, Any]]
    competitor: str


@router.post("/score-pages")
async def score_pages_with_ai(
    request: ScorePagesRequest,
    db: Session = Depends(get_db)
):
    """Score discovered pages with AI analysis."""
    try:
        # Initialize AI scoring service
        from app.services.theta_client import ThetaClient
        from app.services.ai_scoring import AIScoringService
        
        theta_client = ThetaClient(db)
        ai_scoring_service = AIScoringService(theta_client)
        
        scored_pages = []
        
        for page in request.pages:
            # Skip pages that don't qualify for AI scoring
            if not page.get("has_minimal_content", False):
                page["ai_scoring_reason"] = "No minimal content"
                page["ai_score"] = None
                page["ai_category"] = None
                page["ai_signals"] = []
                page["ai_success"] = False
                scored_pages.append(page)
                continue
            
            # Skip obvious noise pages
            noise_patterns = ['careers', 'privacy', 'terms', 'cookies', 'legal', 'accessibility', 'contact', 'support', 'help', 'faq', 'sitemap']
            if any(noise in page["url"].lower() for noise in noise_patterns):
                page["ai_scoring_reason"] = "Smart filtering: URL contains noise patterns"
                page["ai_score"] = None
                page["ai_category"] = None
                page["ai_signals"] = []
                page["ai_success"] = False
                scored_pages.append(page)
                continue
            
            try:
                # Perform AI scoring
                ai_result = await ai_scoring_service.score_page(
                    url=page["url"],
                    title=page.get("title", ""),
                    content="",  # No full content for lightweight scoring
                    h1_headings=page.get("h1", ""),
                    competitor=request.competitor
                )
                
                # Update page with AI results
                page["ai_score"] = ai_result.score
                page["ai_category"] = ai_result.primary_category
                page["ai_signals"] = ai_result.signals
                page["ai_confidence"] = ai_result.confidence
                page["ai_reasoning"] = ai_result.reasoning
                page["ai_success"] = ai_result.success
                page["ai_scoring_reason"] = "AI scoring completed"
                
                # Use AI score if successful, otherwise fall back to rules score
                if ai_result.success and ai_result.score > 0:
                    page["score"] = ai_result.score
                    page["primary_category"] = ai_result.primary_category
                    page["secondary_categories"] = ai_result.secondary_categories
                    page["signals"] = ai_result.signals
                    page["scoring_method"] = "ai"
                else:
                    page["scoring_method"] = "rules"
                    page["ai_error"] = ai_result.error
                
            except Exception as e:
                logger.error(f"AI scoring failed for {page['url']}: {e}")
                page["ai_scoring_reason"] = f"AI scoring failed: {str(e)}"
                page["ai_score"] = None
                page["ai_category"] = None
                page["ai_signals"] = []
                page["ai_success"] = False
                page["ai_error"] = str(e)
                page["scoring_method"] = "rules"
            
            scored_pages.append(page)
        
        return {
            "success": True,
            "pages": scored_pages,
            "total_pages": len(scored_pages),
            "ai_scored_pages": len([p for p in scored_pages if p.get("ai_success", False)])
        }
        
    except Exception as e:
        logger.error(f"Error in AI scoring: {e}")
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {str(e)}")
