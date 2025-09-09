"""
Core crawl service implementing the 3-step fingerprinting pipeline:
1. Filter - Apply score threshold, canonicalize URLs, deduplicate, apply caps
2. Fetch - Download content with httpx, detect content types, size limits  
3. Fingerprint - Generate stable content hashes based on content type
"""

import asyncio
import hashlib
import logging
import re
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse, urlunparse

import httpx
import trafilatura
import filetype
from sqlalchemy.orm import Session
from pdfminer.high_level import extract_text as extract_pdf_text
from pdfminer.pdfparser import PDFSyntaxError

from app.core.config import settings
from app.models.crawl import CrawlSession, CrawledPage
from app.models.core_crawl import (
    FingerprintSession, PageFingerprint, 
    FingerprintRequest, FingerprintResponse, FingerprintResult, FetchMeta
)

logger = logging.getLogger(__name__)


class CoreCrawlService:
    """
    Service for processing crawl sessions through the 3-step fingerprinting pipeline.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.concurrency = settings.CORE_CRAWL_CONCURRENCY
        self.batch_size = settings.CORE_CRAWL_BATCH_SIZE
        self.max_content_size = settings.CORE_CRAWL_MAX_CONTENT_SIZE
        self.connect_timeout = settings.CORE_CRAWL_CONNECT_TIMEOUT
        self.read_timeout = settings.CORE_CRAWL_READ_TIMEOUT
    
    async def fingerprint_session(self, request: FingerprintRequest) -> FingerprintResponse:
        """
        Main orchestrator - processes a crawl session through the 3-step pipeline.
        """
        # Validate crawl session exists
        crawl_session = self.db.query(CrawlSession).filter(
            CrawlSession.id == request.crawl_session_id
        ).first()
        
        if not crawl_session:
            raise ValueError(f"Crawl session {request.crawl_session_id} not found")
        
        # Get pages from the crawl session
        crawled_pages = self.db.query(CrawledPage).filter(
            CrawledPage.session_id == request.crawl_session_id
        ).all()
        
        logger.info(f"Processing {len(crawled_pages)} pages from crawl session {request.crawl_session_id}")
        
        # Create fingerprint session
        fingerprint_session = FingerprintSession(
            crawl_session_id=request.crawl_session_id,
            competitor=request.competitor,
            started_at=datetime.utcnow()
        )
        self.db.add(fingerprint_session)
        self.db.flush()  # Get ID
        
        try:
            # Step 1: Filter and deduplicate
            filtered_pages = self._filter_and_dedupe(crawled_pages)
            logger.info(f"After filtering: {len(filtered_pages)} pages")
            
            # Step 2 & 3: Process in batches
            all_results = []
            total_processed = 0
            total_errors = 0
            
            for batch in self._batch(filtered_pages, self.batch_size):
                batch_results, batch_errors = await self._process_batch(batch, fingerprint_session.id)
                all_results.extend(batch_results)
                total_processed += len(batch_results)
                total_errors += batch_errors
                
                logger.info(f"Processed batch: {len(batch_results)} results, {batch_errors} errors")
            
            # Update fingerprint session
            fingerprint_session.completed_at = datetime.utcnow()
            fingerprint_session.total_processed = total_processed
            fingerprint_session.total_errors = total_errors
            
            self.db.commit()
            
            logger.info(f"Fingerprinting complete: {total_processed} processed, {total_errors} errors")
            
            return FingerprintResponse(
                fingerprint_session_id=fingerprint_session.id,
                crawl_session_id=request.crawl_session_id,
                competitor=request.competitor,
                started_at=fingerprint_session.started_at,
                completed_at=fingerprint_session.completed_at,
                total_processed=total_processed,
                total_errors=total_errors,
                fingerprints=all_results
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Fingerprinting failed: {e}")
            raise
    
    def _filter_and_dedupe(self, crawled_pages: List[CrawledPage]) -> List[CrawledPage]:
        """
        Step 1: Filter pages by score >= 0.5, canonicalize URLs, dedupe, apply caps.
        """
        logger.info(f"=== FINGERPRINTING FILTER DEBUG ===")
        logger.info(f"Total input pages: {len(crawled_pages)}")
        
        # Debug: Show all pages with their scores
        for i, page in enumerate(crawled_pages):
            logger.info(f"  Page {i+1}: {page.url} (score: {page.score:.2f})")
        
        # Filter by score threshold
        filtered = [page for page in crawled_pages if page.score >= 0.5]
        logger.info(f"After score filter (>= 0.5): {len(filtered)} pages")
        
        # Debug: Show which pages were filtered out by score
        filtered_out_by_score = [page for page in crawled_pages if page.score < 0.5]
        if filtered_out_by_score:
            logger.info(f"Pages filtered out by score threshold:")
            for page in filtered_out_by_score:
                logger.info(f"  FILTERED: {page.url} (score: {page.score:.2f})")
        
        # Deduplicate by canonical URL
        seen_urls = set()
        deduped = []
        duplicate_mapping = {}  # Track which URLs are considered duplicates
        
        for page in filtered:
            canonical = self._canonicalize_url(page.url)
            logger.debug(f"Canonicalization: {page.url} -> {canonical}")
            
            if canonical not in seen_urls:
                seen_urls.add(canonical)
                deduped.append(page)
                logger.info(f"  KEPT: {page.url} (canonical: {canonical})")
            else:
                # Find which page this is a duplicate of
                original_page = next((p for p in deduped if self._canonicalize_url(p.url) == canonical), None)
                duplicate_mapping[page.url] = original_page.url if original_page else "unknown"
                logger.info(f"  DUPLICATE: {page.url} -> duplicate of {duplicate_mapping[page.url]} (canonical: {canonical})")
        
        logger.info(f"After deduplication: {len(deduped)} pages")
        if duplicate_mapping:
            logger.info(f"Duplicate pages found: {len(duplicate_mapping)}")
            for dup_url, orig_url in duplicate_mapping.items():
                logger.info(f"  {dup_url} is duplicate of {orig_url}")
        
        # Apply caps: max 100 per domain, max 100 per category
        domain_counts = {}
        category_counts = {}
        capped = []
        capped_pages = []  # Track which pages were capped
        
        for page in deduped:
            domain = self._extract_domain(page.url)
            category = page.primary_category
            
            domain_count = domain_counts.get(domain, 0)
            category_count = category_counts.get(category, 0)
            
            if domain_count < 100 and category_count < 100:
                capped.append(page)
                domain_counts[domain] = domain_count + 1
                category_counts[category] = category_count + 1
                logger.debug(f"  KEPT (caps): {page.url} (domain: {domain_count+1}/100, category '{category}': {category_count+1}/100)")
            else:
                capped_pages.append((page.url, domain, category, domain_count, category_count))
                logger.info(f"  CAPPED: {page.url} (domain: {domain_count}/100, category '{category}': {category_count}/100)")
        
        logger.info(f"After caps (100/domain, 100/category): {len(capped)} pages")
        if capped_pages:
            logger.info(f"Pages filtered by caps: {len(capped_pages)}")
            for url, domain, category, d_count, c_count in capped_pages:
                logger.info(f"  {url} - domain {domain}: {d_count}/100, category '{category}': {c_count}/100")
        
        # Final summary
        logger.info(f"=== FILTERING SUMMARY ===")
        logger.info(f"Input: {len(crawled_pages)} pages")
        logger.info(f"After score filter: {len(filtered)} pages ({len(crawled_pages) - len(filtered)} filtered)")
        logger.info(f"After deduplication: {len(deduped)} pages ({len(filtered) - len(deduped)} duplicates)")
        logger.info(f"Final result: {len(capped)} pages ({len(deduped) - len(capped)} capped)")
        logger.info(f"=== END FILTER DEBUG ===")
        
        return capped
    
    async def _process_batch(self, batch: List[CrawledPage], fingerprint_session_id: int) -> Tuple[List[FingerprintResult], int]:
        """
        Process a batch of pages through fetch + fingerprint steps.
        """
        logger.info(f"=== PROCESSING BATCH DEBUG ===")
        logger.info(f"Batch size: {len(batch)} pages")
        for i, page in enumerate(batch):
            logger.info(f"  Batch page {i+1}: {page.url} (score: {page.score:.2f}, category: {page.primary_category})")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)
        
        # Process pages concurrently
        tasks = [
            self._process_single_page(page, fingerprint_session_id, semaphore)
            for page in batch
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate successful results from errors
        successful_results = []
        error_count = 0
        failed_urls = []
        
        for i, result in enumerate(results):
            page_url = batch[i].url
            if isinstance(result, Exception):
                error_count += 1
                failed_urls.append(page_url)
                logger.error(f"  FAILED: {page_url} - Error: {result}")
            else:
                successful_results.append(result)
                logger.info(f"  SUCCESS: {page_url} - Fingerprint: {result.content_hash[:8]}...")
        
        logger.info(f"=== BATCH PROCESSING RESULTS ===")
        logger.info(f"Successful: {len(successful_results)} pages")
        logger.info(f"Failed: {error_count} pages")
        if failed_urls:
            logger.info(f"Failed URLs: {', '.join(failed_urls)}")
        logger.info(f"=== END BATCH DEBUG ===")
        
        return successful_results, error_count
    
    async def _process_single_page(
        self, 
        page: CrawledPage, 
        fingerprint_session_id: int, 
        semaphore: asyncio.Semaphore
    ) -> FingerprintResult:
        """
        Process a single page: fetch content + generate fingerprint.
        """
        async with semaphore:
            start_time = time.time()
            
            try:
                # Step 2: Fetch content
                content_bytes, content_type, fetch_status, fetch_notes = await self._fetch_content(page.url)
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                # Step 3: Generate fingerprint
                key_url = self._detect_canonical_url(content_bytes, content_type, page.url)
                content_hash, normalized_text_len, low_text_pdf, needs_render = self._fingerprint_content(
                    content_bytes, content_type
                )
                
                # Create fetch metadata
                fetch_meta = FetchMeta(
                    status=fetch_status,
                    content_type=content_type,
                    content_length=len(content_bytes) if content_bytes else 0,
                    elapsed_ms=elapsed_ms,
                    notes=fetch_notes
                )
                
                # Create fingerprint result
                extracted_text = self._get_extracted_text(content_bytes, content_type)
                result = FingerprintResult(
                    url=page.url,
                    key_url=key_url,
                    page_type=page.primary_category,
                    content_hash=content_hash,
                    normalized_text_len=normalized_text_len,
                    extracted_text=extracted_text,
                    low_text_pdf=low_text_pdf,
                    needs_render=needs_render,
                    meta=fetch_meta
                )
                
                # Save to database
                page_fingerprint = PageFingerprint(
                    fingerprint_session_id=fingerprint_session_id,
                    crawled_page_id=page.id,
                    url=page.url,
                    key_url=key_url,
                    page_type=page.primary_category,
                    content_hash=content_hash,
                    normalized_text_len=normalized_text_len,
                    extracted_text=extracted_text,  # Store the actual text
                    low_text_pdf=low_text_pdf,
                    needs_render=needs_render,
                    fetch_status=fetch_status,
                    content_type=content_type,
                    content_length=len(content_bytes) if content_bytes else 0,
                    fetch_elapsed_ms=elapsed_ms,
                    fetch_notes=fetch_notes,
                    processed_at=datetime.utcnow()
                )
                self.db.add(page_fingerprint)
                
                return result
                
            except Exception as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.error(f"Failed to process page {page.url}: {e}")
                
                # Save error to database
                error_fingerprint = PageFingerprint(
                    fingerprint_session_id=fingerprint_session_id,
                    crawled_page_id=page.id,
                    url=page.url,
                    key_url=page.url,
                    page_type=page.primary_category,
                    content_hash="error",
                    normalized_text_len=0,
                    low_text_pdf=False,
                    needs_render=False,
                    fetch_status=None,
                    content_type=None,
                    content_length=0,
                    fetch_elapsed_ms=elapsed_ms,
                    fetch_notes=str(e),
                    processed_at=datetime.utcnow()
                )
                self.db.add(error_fingerprint)
                raise e
    
    async def _fetch_content(self, url: str) -> Tuple[Optional[bytes], Optional[str], Optional[int], Optional[str]]:
        """
        Step 2: Fetch content with httpx, detect content type, apply size limits.
        """
        try:
            timeout = httpx.Timeout(
                connect=self.connect_timeout, 
                read=self.read_timeout,
                write=5.0,  # Add write timeout
                pool=5.0    # Add pool timeout
            )
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, follow_redirects=True)
                
                # Check content length
                content_length = len(response.content)
                if content_length > self.max_content_size:
                    return None, None, response.status_code, f"Content too large: {content_length} bytes"
                
                # Detect content type
                content_type = response.headers.get('content-type', '').split(';')[0].strip()
                if not content_type:
                    # Use filetype detection as fallback
                    detected = filetype.guess(response.content[:1024])  # Check first 1KB
                    content_type = detected.mime if detected else 'application/octet-stream'
                
                return response.content, content_type, response.status_code, None
                
        except httpx.TimeoutException:
            return None, None, None, "Request timeout"
        except httpx.RequestError as e:
            return None, None, None, f"Request error: {e}"
        except Exception as e:
            return None, None, None, f"Fetch error: {e}"
    
    def _fingerprint_content(self, content_bytes: Optional[bytes], content_type: Optional[str]) -> Tuple[str, int, bool, bool]:
        """
        Step 3: Generate stable content hash based on content type.
        Returns: (content_hash, normalized_text_len, low_text_pdf, needs_render)
        """
        if not content_bytes:
            return "empty", 0, False, True
        
        try:
            if content_type and 'text/html' in content_type:
                return self._fingerprint_html(content_bytes)
            elif content_type and 'application/pdf' in content_type:
                return self._fingerprint_pdf(content_bytes)
            else:
                return self._fingerprint_binary(content_bytes)
        except Exception as e:
            logger.warning(f"Fingerprinting failed for content type {content_type}: {e}")
            return self._fingerprint_binary(content_bytes)
    
    def _fingerprint_html(self, content_bytes: bytes) -> Tuple[str, int, bool, bool]:
        """Fingerprint HTML content using trafilatura for text extraction."""
        try:
            # Decode HTML
            html_text = content_bytes.decode('utf-8', errors='ignore')
            
            # Extract main text with trafilatura
            extracted_text = trafilatura.extract(html_text)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                # Very little text extracted, might need JavaScript rendering
                return hashlib.sha256(content_bytes).hexdigest(), 0, False, True
            
            # Normalize text: collapse whitespace, strip, lowercase
            normalized_text = re.sub(r'\s+', ' ', extracted_text.strip().lower())
            content_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
            
            return content_hash, len(normalized_text), False, False
            
        except Exception as e:
            logger.warning(f"HTML fingerprinting failed: {e}")
            return hashlib.sha256(content_bytes).hexdigest(), 0, False, True
    
    def _fingerprint_pdf(self, content_bytes: bytes) -> Tuple[str, int, bool, bool]:
        """Fingerprint PDF content using pdfminer for text extraction."""
        try:
            # Extract text from PDF
            from io import BytesIO
            pdf_text = extract_pdf_text(BytesIO(content_bytes))
            
            if not pdf_text or len(pdf_text.strip()) < 100:
                # Very little text, likely image-based PDF
                return hashlib.sha256(content_bytes).hexdigest(), 0, True, False
            
            # Normalize text
            normalized_text = re.sub(r'\s+', ' ', pdf_text.strip().lower())
            content_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
            
            return content_hash, len(normalized_text), False, False
            
        except (PDFSyntaxError, Exception) as e:
            logger.warning(f"PDF fingerprinting failed: {e}")
            # Fall back to binary hash
            return hashlib.sha256(content_bytes).hexdigest(), 0, True, False
    
    def _fingerprint_binary(self, content_bytes: bytes) -> Tuple[str, int, bool, bool]:
        """Fingerprint binary content (images, videos, etc.) by hashing bytes directly."""
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        return content_hash, 0, False, False
    
    def _detect_canonical_url(self, content_bytes: Optional[bytes], content_type: Optional[str], original_url: str) -> str:
        """Detect canonical URL from HTML content."""
        if not content_bytes or not content_type or 'text/html' not in content_type:
            return original_url
        
        try:
            from bs4 import BeautifulSoup
            html_text = content_bytes.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # Look for canonical link
            canonical_link = soup.find('link', rel='canonical')
            if canonical_link and canonical_link.get('href'):
                return canonical_link['href']
                
        except Exception as e:
            logger.debug(f"Canonical URL detection failed: {e}")
        
        return original_url
    
    def _canonicalize_url(self, url: str) -> str:
        """Canonicalize URL for deduplication."""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            
            # Remove tracking parameters
            query_params = []
            if parsed.query:
                params = parsed.query.split('&')
                for param in params:
                    if '=' in param:
                        key = param.split('=')[0].lower()
                        if key not in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 
                                     'utm_term', 'gclid', 'fbclid', 'msclkid', '_ga', '_gl']:
                            query_params.append(param)
            
            clean_query = '&'.join(query_params) if query_params else ''
            clean_path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
            
            # Remove www prefix for canonicalization (treat www and non-www as same)
            clean_netloc = parsed.netloc.lower()
            if clean_netloc.startswith('www.'):
                clean_netloc = clean_netloc[4:]  # Remove 'www.'
            
            return urlunparse((
                parsed.scheme.lower(),
                clean_netloc,
                clean_path,
                parsed.params,
                clean_query,
                ''  # Remove fragment
            ))
            
        except Exception:
            return url
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return "unknown"
    
    def _get_extracted_text(self, content_bytes: Optional[bytes], content_type: Optional[str]) -> Optional[str]:
        """Extract and clean text content for AI analysis."""
        if not content_bytes:
            return None
        
        try:
            if content_type and 'text/html' in content_type:
                html_text = content_bytes.decode('utf-8', errors='ignore')
                extracted_text = trafilatura.extract(html_text)
                if extracted_text and len(extracted_text.strip()) >= 50:
                    return self._clean_extracted_text(extracted_text)
            elif content_type and 'application/pdf' in content_type:
                from io import BytesIO
                pdf_text = extract_pdf_text(BytesIO(content_bytes))
                if pdf_text and len(pdf_text.strip()) >= 100:
                    return self._clean_extracted_text(pdf_text)
        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")
        
        return None
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text for optimal LLM consumption."""
        # Remove excessive whitespace but preserve some structure
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n ', '\n', text)  # Remove spaces after newlines
        text = re.sub(r' \n', '\n', text)  # Remove spaces before newlines
        
        # Remove common web artifacts
        text = re.sub(r'(Cookie|Cookies?)\s+(Policy|Einstellungen|Settings)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(Alle\s+)?Cookies?\s+(akzeptieren|erlauben)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Browser\s+not\s+compatible', '', text, flags=re.IGNORECASE)
        
        # Clean up repeated navigation elements
        text = re.sub(r'(Return\s+)?Produkte\s+Branchenlösungen\s+Fallstudien\s+Ressourcen\s+News\s+Blogs', 'Navigation:', text)
        
        return text.strip()
    
    def _batch(self, items: List[Any], batch_size: int) -> List[List[Any]]:
        """Split items into batches."""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
