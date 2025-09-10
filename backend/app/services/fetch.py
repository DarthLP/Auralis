"""
URL fetching utilities for web scraping.
Handles HTTP requests, robots.txt parsing, sitemap discovery, and URL normalization.
"""

import hashlib
import logging
import os
import random
import re
import time
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
import gzip

# Import Playwright for JavaScript support
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    PlaywrightTimeoutError = Exception

logger = logging.getLogger(__name__)

# Realistic User Agents for better bot detection evasion
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]


def get_realistic_headers(user_agent: Optional[str] = None) -> Dict[str, str]:
    """
    Generate realistic browser headers to evade bot detection.
    
    Args:
        user_agent: Optional custom user agent, otherwise picks random one
        
    Returns:
        Dictionary of HTTP headers
    """
    if not user_agent:
        user_agent = random.choice(USER_AGENTS)
    
    return {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }


def smart_delay(attempt: int = 1, base_delay: float = 0.5) -> None:
    """
    Apply smart delay with randomization and exponential backoff.
    
    Args:
        attempt: Attempt number (1-based)
        base_delay: Base delay in seconds
    """
    # Random delay between 0.3x and 1.5x base delay
    delay = base_delay * random.uniform(0.3, 1.5)
    
    # Exponential backoff for retries
    if attempt > 1:
        delay *= (2 ** (attempt - 1))
        
    # Cap maximum delay at 30 seconds
    delay = min(delay, 30.0)
    
    logger.debug(f"Sleeping for {delay:.2f}s (attempt {attempt})")
    time.sleep(delay)


async def fetch_url(url: str, timeout: int, user_agent: str, enable_js: bool = False, js_wait_time: int = 3) -> Tuple[Optional[int], str]:
    """
    Fetch a URL with enhanced anti-bot detection measures and optional JavaScript support.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        user_agent: User agent string (can be overridden by realistic headers)
        enable_js: Whether to use JavaScript rendering with Playwright
        js_wait_time: Seconds to wait for JavaScript to load
        
    Returns:
        Tuple of (status_code, response_text). Status is None if request failed.
    """
    if enable_js and PLAYWRIGHT_AVAILABLE:
        return await fetch_url_with_js(url, timeout, user_agent, js_wait_time)
    else:
        return fetch_url_with_retries(url, timeout, user_agent, max_retries=3)


def fetch_url_with_retries(url: str, timeout: int, user_agent: str, max_retries: int = 3) -> Tuple[Optional[int], str]:
    """
    Fetch a URL with retry logic and enhanced headers.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        user_agent: User agent string
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (status_code, response_text). Status is None if all retries failed.
    """
    for attempt in range(1, max_retries + 1):
        try:
            # Use realistic headers instead of just user agent
            headers = get_realistic_headers(user_agent)
            
            # Create session for better connection handling
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, timeout=timeout, allow_redirects=True)
            
            # Handle rate limiting
            if response.status_code == 429:
                logger.warning(f"Rate limited on {url}, attempt {attempt}/{max_retries}")
                if attempt < max_retries:
                    smart_delay(attempt + 1, base_delay=2.0)  # Longer delay for rate limits
                    continue
                return 429, ""
            
            # Handle other client/server errors with retry
            if response.status_code >= 500 and attempt < max_retries:
                logger.warning(f"Server error {response.status_code} on {url}, retrying...")
                smart_delay(attempt)
                continue
                
            return response.status_code, response.text
            
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout fetching {url} (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                smart_delay(attempt)
                
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error fetching {url} (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                smart_delay(attempt)
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error fetching {url} (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                smart_delay(attempt)
    
    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None, ""


async def fetch_url_with_js(url: str, timeout: int, user_agent: str, js_wait_time: int = 3) -> Tuple[Optional[int], str]:
    """
    Fetch a URL using Playwright with JavaScript rendering support.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        user_agent: User agent string
        js_wait_time: Seconds to wait for JavaScript to load
        
    Returns:
        Tuple of (status_code, response_text). Status is None if request failed.
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning(f"Playwright not available, falling back to requests for {url}")
        return fetch_url_with_retries(url, timeout, user_agent)
    
    try:
        async with async_playwright() as p:
            # Launch browser with realistic settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                ]
            )
            
            # Create context with realistic settings
            context = await browser.new_context(
                user_agent=user_agent or random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            # Set extra headers
            await context.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            page = await context.new_page()
            
            # Navigate to page with timeout
            response = await page.goto(url, timeout=timeout * 1000, wait_until='domcontentloaded')
            
            if response is None:
                await browser.close()
                return None, ""
            
            # Wait for JavaScript to load and execute
            await page.wait_for_timeout(js_wait_time * 1000)
            
            # Wait for network to be mostly idle
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
            except PlaywrightTimeoutError:
                # Network didn't become idle, but continue anyway
                pass
            
            # Get the final rendered content
            content = await page.content()
            status_code = response.status
            
            await browser.close()
            
            logger.debug(f"Successfully fetched {url} with JavaScript (status: {status_code}, size: {len(content)} bytes)")
            return status_code, content
            
    except PlaywrightTimeoutError as e:
        logger.warning(f"Playwright timeout fetching {url}: {e}")
        return None, ""
    except Exception as e:
        logger.warning(f"Playwright error fetching {url}: {e}")
        return None, ""


def get_robots_txt(base_url: str) -> Dict[str, List[str]]:
    """
    Fetch and parse robots.txt for basic allow/deny patterns.
    
    Args:
        base_url: Base URL of the site
        
    Returns:
        Dict with 'allow' and 'disallow' lists of patterns
    """
    robots_url = urljoin(base_url, '/robots.txt')
    
    try:
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        # Extract disallowed patterns for * user agent
        disallow_patterns = []
        for line in rp.entries:
            if line.useragent == '*' or 'AuralisBot' in line.useragent:
                disallow_patterns.extend(line.rulelines)
        
        return {
            'allow': [],  # Simplified - assume allowed unless explicitly disallowed
            'disallow': [rule.path for rule in disallow_patterns if not rule.allowance]
        }
    except Exception as e:
        logger.warning(f"Could not fetch robots.txt from {robots_url}: {e}")
        return {'allow': [], 'disallow': []}


def get_sitemap_urls(base_url: str, visited: Optional[Set[str]] = None, depth: int = 0, max_depth: int = 5) -> List[str]:
    """
    Fetch sitemap.xml and extract URLs.
    
    Args:
        base_url: Either the base domain (e.g., https://example.com) or a direct sitemap URL
        visited: Internal set to avoid revisiting the same sitemap URLs (prevents cycles)
        depth: Current recursion depth (internal)
        max_depth: Maximum allowed depth for nested sitemap indexes
        
    Returns:
        List of URLs found in sitemap
    """
    # Initialize visited set
    if visited is None:
        visited = set()
    
    # Determine the actual sitemap URL: if the input already looks like a sitemap, use as-is
    try:
        parsed = urlparse(base_url)
        path_lower = (parsed.path or '').lower()
        looks_like_sitemap = (
            path_lower.endswith('.xml') or path_lower.endswith('.xml.gz') or 'sitemap' in path_lower
        )
        sitemap_url = base_url if looks_like_sitemap else urljoin(base_url, '/sitemap.xml')
    except Exception:
        # Fallback to original behavior on any parsing error
        sitemap_url = urljoin(base_url, '/sitemap.xml')
    
    # Helper to normalize sitemap URLs to a scheme-agnostic, www-less key
    def _sitemap_key(u: str) -> str:
        try:
            p = urlparse(u)
            netloc = p.netloc.lower()
            if netloc.startswith('www.'):
                netloc = netloc[4:]
            path = p.path or '/sitemap.xml'
            if path == '' or path == '/':
                path = '/sitemap.xml'
            return f"{netloc}{path}"
        except Exception:
            return u
    
    current_key = _sitemap_key(sitemap_url)
    
    # Stop if we've seen this sitemap already (prevents infinite loops on self/cyclic references)
    if current_key in visited:
        return []
    visited.add(current_key)
    
    # Enforce a reasonable maximum depth to avoid excessive recursion on deeply nested indexes
    if depth >= max_depth:
        logger.warning(f"Sitemap index depth exceeded for {sitemap_url} (depth={depth}, max={max_depth})")
        return []
    
    try:
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code != 200:
            logger.debug(f"Sitemap fetch non-200: url={sitemap_url} status={response.status_code}")
            return []
            
        raw_content = response.content or b''
        # Detect and decompress gzip by magic header
        if len(raw_content) >= 2 and raw_content[:2] == b'\x1f\x8b':
            try:
                raw_content = gzip.decompress(raw_content)
                logger.debug(f"Sitemap gzip decompressed: url={sitemap_url} bytes={len(raw_content)}")
            except Exception as gz_e:
                logger.debug(f"Sitemap gzip decompress failed: url={sitemap_url} err={gz_e}")
        
        logger.debug(f"Sitemap fetch ok: url={sitemap_url} depth={depth} visited={len(visited)} bytes={len(raw_content)}")
        
        # Parse XML with defensive fallback on recursion errors
        try:
            soup = BeautifulSoup(raw_content, 'xml')
        except RecursionError as re_err:
            logger.warning(f"XML parser recursion on sitemap: url={sitemap_url} err={re_err}. Falling back to regex extraction.")
            # Fallback: extract <loc> values via regex
            try:
                import re as _re
                loc_bytes = _re.findall(b'<loc[^>]*>(.*?)</loc>', raw_content, flags=_re.IGNORECASE | _re.DOTALL)
                urls = []
                for lb in loc_bytes:
                    try:
                        urls.append(lb.decode('utf-8', errors='replace').strip())
                    except Exception:
                        pass
                # Dedup and cap
                seen_fallback: Set[str] = set()
                deduped_fallback: List[str] = []
                for u in urls:
                    if u and u not in seen_fallback:
                        seen_fallback.add(u)
                        deduped_fallback.append(u)
                logger.debug(f"Sitemap regex extracted {len(deduped_fallback)} URLs: url={sitemap_url}")
                return deduped_fallback[:100]
            except Exception as rex_e:
                logger.debug(f"Sitemap regex extraction failed: url={sitemap_url} err={rex_e}")
                return []
        urls: List[str] = []
        
        # Handle sitemap index files
        is_index = soup.find('sitemapindex') is not None
        sitemap_tags = soup.find_all('sitemap')
        if is_index and sitemap_tags:
            for sitemap in sitemap_tags[:5]:  # Limit to first 5 sitemaps
                loc = sitemap.find('loc')
                if loc:
                    next_url = (loc.text or '').strip()
                    next_key = _sitemap_key(next_url)
                    # Skip if same as current or already visited
                    if next_url and next_key not in visited:
                        sub_urls = get_sitemap_urls(next_url, visited=visited, depth=depth + 1, max_depth=max_depth)
                        urls.extend(sub_urls)
        logger.debug(f"Sitemap index={is_index} sitemaps_found={len(sitemap_tags)} urls_in_index_accum={len(urls)} url={sitemap_url}")
        
        # Handle direct URL entries
        url_tags = soup.find_all('url')
        for url_tag in url_tags:
            loc = url_tag.find('loc')
            if loc and loc.text:
                urls.append(loc.text.strip())
        logger.debug(f"Sitemap urlset urls_found={len(url_tags)} total_urls={len(urls)} url={sitemap_url}")
        
        # Deduplicate while preserving order, then cap to prevent overload
        seen: Set[str] = set()
        deduped: List[str] = []
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped[:100]
        
    except Exception as e:
        logger.exception(f"Could not fetch sitemap from {sitemap_url}: {e}")
        return []


def normalize_url(link: str, base_url: str) -> Optional[str]:
    """
    Normalize and canonicalize URLs, filtering to same registrable domain.
    
    Args:
        link: Raw link to normalize
        base_url: Base URL for resolving relative links
        
    Returns:
        Normalized URL if valid and same domain, None otherwise
    """
    if not link:
        return None
        
    # Resolve relative URLs
    try:
        full_url = urljoin(base_url, link)
        parsed = urlparse(full_url)
        base_parsed = urlparse(base_url)
        
        # Must have same scheme and registrable domain
        if parsed.scheme != base_parsed.scheme:
            return None
            
        # Extract registrable domain (simplified - just check if domains match)
        if not _same_registrable_domain(parsed.netloc, base_parsed.netloc):
            return None
            
        # Remove fragment, normalize path (add trailing slash for root URLs)
        if not parsed.path or parsed.path == '':
            clean_path = '/'  # Root URL should have trailing slash
        elif parsed.path == '/':
            clean_path = '/'  # Already correct
        else:
            clean_path = parsed.path.rstrip('/')  # Remove trailing slash from non-root paths
        
        # Remove www prefix for consistency (same as canonicalize_url)
        clean_netloc = parsed.netloc.lower()
        if clean_netloc.startswith('www.'):
            clean_netloc = clean_netloc[4:]  # Remove 'www.'
        
        normalized = urlunparse((
            parsed.scheme,
            clean_netloc,
            clean_path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        
        return normalized
        
    except Exception as e:
        logger.debug(f"Failed to normalize URL {link}: {e}")
        return None


def _same_registrable_domain(domain1: str, domain2: str) -> bool:
    """
    Check if two domains belong to the same registrable domain.
    Simplified implementation - allows subdomains of the same base domain.
    """
    # Remove port numbers
    domain1 = domain1.split(':')[0].lower()
    domain2 = domain2.split(':')[0].lower()
    
    if domain1 == domain2:
        return True
        
    # Check if one is subdomain of the other
    parts1 = domain1.split('.')
    parts2 = domain2.split('.')
    
    if len(parts1) >= 2 and len(parts2) >= 2:
        # Compare last two parts (registrable domain)
        return parts1[-2:] == parts2[-2:]
    
    return False


def sha256_text(text: str) -> str:
    """
    Generate SHA256 hash of text content.
    
    Args:
        text: Text to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL for duplicate detection.
    
    Args:
        url: URL to canonicalize
        
    Returns:
        Canonicalized URL string
    """
    if not url:
        return ""
    
    try:
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
                                 'utm_term', 'gclid', 'fbclid', 'msclkid', '_ga', '_gl', 
                                 'gad_source', 'gad_campaignid', 'gbraid']:
                        query_params.append(param)
        
        # Rebuild query string
        clean_query = '&'.join(query_params) if query_params else ''
        
        # Normalize path (same logic as normalize_url for consistency)
        if not parsed.path or parsed.path == '':
            clean_path = '/'  # Root URL should have trailing slash
        elif parsed.path == '/':
            clean_path = '/'  # Already correct
        else:
            clean_path = parsed.path.rstrip('/')  # Remove trailing slash from non-root paths
        
        # Remove www prefix for canonicalization (treat www and non-www as same)
        clean_netloc = parsed.netloc.lower()
        if clean_netloc.startswith('www.'):
            clean_netloc = clean_netloc[4:]  # Remove 'www.'
        
        # Rebuild URL
        canonical = urlunparse((
            parsed.scheme.lower(),
            clean_netloc,
            clean_path,
            parsed.params,
            clean_query,
            ''  # Remove fragment
        ))
        
        return canonical
        
    except Exception as e:
        logger.debug(f"Failed to canonicalize URL {url}: {e}")
        return url


def are_urls_duplicate(url1: str, url2: str) -> bool:
    """
    Check if two URLs are duplicates after canonicalization.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if URLs are duplicates
    """
    return canonicalize_url(url1) == canonicalize_url(url2)
