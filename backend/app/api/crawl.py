"""
Crawling API endpoints for website discovery and analysis.
"""

import logging
import os
from datetime import datetime
from typing import Dict

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
        crawl_logger.info(f"JavaScript enabled: {settings.SCRAPER_ENABLE_JAVASCRIPT}")
        crawl_logger.info(f"Limits: {limits}")
        crawl_logger.info(f"Log file: {log_file}")
        
        # Perform discovery with JavaScript support
        result = await discover_interesting_pages(
            str(request.url), 
            limits, 
            enable_js=settings.SCRAPER_ENABLE_JAVASCRIPT
        )
        
        # Log detailed results
        crawl_logger.info(f"=== CRAWL RESULTS ===")
        crawl_logger.info(f"Total pages found: {len(result.get('pages', []))}")
        crawl_logger.info(f"Warnings: {len(result.get('warnings', []))}")
        
        # Log category breakdown
        if result.get('pages'):
            category_counts = {}
            for page in result['pages']:
                cat = page.get('primary_category', 'unknown')
                category_counts[cat] = category_counts.get(cat, 0) + 1
            crawl_logger.info(f"Category breakdown: {category_counts}")
            
            # Log top pages
            crawl_logger.info("=== TOP PAGES ===")
            top_pages = sorted(result['pages'], key=lambda x: x.get('score', 0), reverse=True)[:10]
            for i, page in enumerate(top_pages, 1):
                crawl_logger.info(f"{i:2d}. {page.get('primary_category', 'unknown'):10s} | "
                                f"{page.get('score', 0):4.2f} | {page.get('url', 'N/A')}")
        
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
