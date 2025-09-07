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
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

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


def get_sitemap_urls(base_url: str) -> List[str]:
    """
    Fetch sitemap.xml and extract URLs.
    
    Args:
        base_url: Base URL of the site
        
    Returns:
        List of URLs found in sitemap
    """
    sitemap_url = urljoin(base_url, '/sitemap.xml')
    
    try:
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.content, 'xml')
        urls = []
        
        # Handle sitemap index files
        sitemap_tags = soup.find_all('sitemap')
        if sitemap_tags:
            for sitemap in sitemap_tags[:5]:  # Limit to first 5 sitemaps
                loc = sitemap.find('loc')
                if loc:
                    sub_urls = get_sitemap_urls(loc.text)
                    urls.extend(sub_urls)
        
        # Handle direct URL entries
        url_tags = soup.find_all('url')
        for url_tag in url_tags:
            loc = url_tag.find('loc')
            if loc:
                urls.append(loc.text)
                
        return urls[:100]  # Cap at 100 URLs to prevent overload
        
    except Exception as e:
        logger.warning(f"Could not fetch sitemap from {sitemap_url}: {e}")
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
            
        # Remove fragment, normalize path
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path or '/',
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
