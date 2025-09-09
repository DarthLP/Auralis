"""
Page discovery and classification service.
Crawls websites to discover and score interesting pages for competitive analysis.
"""

import logging
import re
import time
from collections import deque
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .fetch import (
    fetch_url, get_robots_txt, get_sitemap_urls, normalize_url, 
    sha256_text, smart_delay, canonicalize_url, are_urls_duplicate
)

logger = logging.getLogger(__name__)


async def discover_interesting_pages(root_url: str, limits: Dict, enable_js: bool = True) -> Dict:
    """
    Discover and classify interesting pages from a website.
    
    Args:
        root_url: Starting URL to crawl from
        limits: Dictionary with crawling limits:
            - max_pages: Maximum pages to crawl
            - max_depth: Maximum crawl depth
            - timeout: Request timeout in seconds
            - rate_sleep: Sleep between requests
            - user_agent: User agent string
            
    Returns:
        Dictionary with discovered pages and metadata
    """
    parsed_root = urlparse(root_url)
    base_domain = f"{parsed_root.scheme}://{parsed_root.netloc}"
    
    # Initialize result structure
    result = {
        "input_url": root_url,
        "base_domain": base_domain,
        "limits": limits,
        "pages": [],
        "top_by_category": {
            "product": [],
            "datasheet": [],
            "docs": [],
            "releases": [],
            "pricing": [],
            "news": [],
            "other": []
        },
        "warnings": []
    }
    
    try:
        # Normalize root URL
        normalized_root = normalize_url(root_url, root_url)
        if not normalized_root:
            result["warnings"].append(f"Could not normalize root URL: {root_url}")
            return result
            
        # Fetch homepage first (with JavaScript if enabled)
        js_wait_time = limits.get('js_wait_time', 3)
        status, content = await fetch_url(
            normalized_root, 
            limits['timeout'], 
            limits['user_agent'],
            enable_js=enable_js,
            js_wait_time=js_wait_time
        )
        if status is None:
            return {
                "error": "HOMEPAGE_FETCH_FAILED",
                "warnings": [f"Could not fetch homepage: {normalized_root}"],
                "pages": []
            }
            
        # Track crawled URLs with canonical URLs for better duplicate detection
        crawled_urls: Set[str] = set()
        canonical_urls: Set[str] = set()
        url_queue = deque([(normalized_root, 0)])  # (url, depth)
        pages_found = []
        
        # Get robots.txt (best effort)
        robots_rules = get_robots_txt(base_domain)
        if robots_rules['disallow']:
            result["warnings"].append(f"Found {len(robots_rules['disallow'])} robots.txt disallow rules")
            
        # Get sitemap URLs (treat as depth 0 seeds)
        sitemap_urls = get_sitemap_urls(base_domain)
        if sitemap_urls:
            result["warnings"].append(f"Found {len(sitemap_urls)} URLs in sitemap")
            # Use up to 70% of our budget for sitemap URLs, prioritizing interesting ones
            sitemap_budget = int(limits['max_pages'] * 0.7)
            
            # Prioritize sitemap URLs that look interesting
            def sitemap_priority(url):
                url_lower = url.lower()
                if any(pattern in url_lower for pattern in ['/product', '/solution', '/item', '/model']):
                    return 0  # Highest priority
                elif any(pattern in url_lower for pattern in ['/docs', '/download', '/news', '/blog']):
                    return 1  # Medium priority
                else:
                    return 2  # Lower priority
            
            sitemap_urls.sort(key=sitemap_priority)
            
            for url in sitemap_urls[:sitemap_budget]:
                normalized = normalize_url(url, base_domain)
                if normalized:
                    canonical = canonicalize_url(normalized)
                    if canonical not in canonical_urls:
                        url_queue.append((normalized, 0))
        
        # BFS crawl
        while url_queue and len(pages_found) < limits['max_pages']:
            current_url, depth = url_queue.popleft()
            
            # Check for duplicates using canonical URLs
            canonical = canonicalize_url(current_url)
            if canonical in canonical_urls or depth > limits['max_depth']:
                continue
                
            crawled_urls.add(current_url)
            canonical_urls.add(canonical)
            
            # Smart rate limiting with randomization
            if len(crawled_urls) > 1:  # Skip sleep for first request
                smart_delay(1, limits['rate_sleep'])
                
            # Smart JavaScript usage - use JS for important pages only
            use_js_for_page = enable_js and _should_use_javascript(current_url, depth)
            
            # Fetch page (with JavaScript if needed)
            status, content = await fetch_url(
                current_url, 
                limits['timeout'], 
                limits['user_agent'],
                enable_js=use_js_for_page,
                js_wait_time=js_wait_time
            )
            
            # Log JS usage decision
            if use_js_for_page:
                logger.debug(f"Using JavaScript for {current_url}")
            else:
                logger.debug(f"Using requests for {current_url}")
            
            # Process page (even if failed - record the failure)
            page_info = _process_page(current_url, status, content, depth)
            pages_found.append(page_info)
            
            # Extract links if successful and not at max depth
            if status == 200 and depth < limits['max_depth'] and content:
                links = _extract_links(content, current_url)
                for link in links:
                    if len(url_queue) + len(crawled_urls) >= limits['max_pages']:
                        break
                    link_canonical = canonicalize_url(link)
                    if link_canonical not in canonical_urls:
                        url_queue.append((link, depth + 1))
        
        # Sort pages by score and categorize
        pages_found.sort(key=lambda p: p['score'], reverse=True)
        result["pages"] = pages_found
        
        # Build top_by_category
        for page in pages_found:
            category = page['primary_category']
            if category in result["top_by_category"]:
                if len(result["top_by_category"][category]) < 10:  # Top 10 per category
                    result["top_by_category"][category].append(page['url'])
        
        logger.info(f"Crawled {len(pages_found)} pages from {root_url}")
        
    except Exception as e:
        logger.error(f"Error during crawling: {e}")
        result["warnings"].append(f"Crawling error: {str(e)}")
        
    return result


def _process_page(url: str, status: Optional[int], content: str, depth: int) -> Dict:
    """
    Process a single page to extract metadata and classify it.
    
    Args:
        url: Page URL
        status: HTTP status code (None if failed)
        content: Page content
        depth: Crawl depth
        
    Returns:
        Page information dictionary
    """
    page_info = {
        "url": url,
        "status": status,
        "depth": depth,
        "primary_category": "other",
        "secondary_categories": [],
        "score": 0.0,
        "signals": [],
        "content_hash": None,
        "size_bytes": len(content) if content else 0,
        "mime_type": None
    }
    
    if status != 200 or not content:
        return page_info
        
    # Check if it's a PDF or binary file (HEAD request would be better, but we already have content)
    if url.lower().endswith('.pdf') or 'pdf' in url.lower():
        page_info["primary_category"] = "datasheet"
        page_info["mime_type"] = "application/pdf"
        page_info["score"] = 0.9
        page_info["signals"] = ["pdf_url"]
        return page_info
        
    # Hash content for text pages
    page_info["content_hash"] = sha256_text(content)
    
    # Parse HTML for classification
    try:
        soup = BeautifulSoup(content, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text().lower() if title else ""
        
        h1_tags = soup.find_all('h1')
        h1_text = " ".join([h1.get_text().lower() for h1 in h1_tags])
        
        # Classify and score
        category, score, signals = _classify_page(url, title_text, h1_text, content)
        
        # Apply depth penalty
        score *= (0.9 ** depth)
        
        # Apply noise penalty
        if any(noise in url.lower() for noise in ['careers', 'privacy', 'terms', 'cookies', 'legal']):
            score = min(score, 0.05)
            
        page_info["primary_category"] = category
        page_info["score"] = min(1.0, max(0.0, score))  # Clip to [0,1]
        page_info["signals"] = signals
        
    except Exception as e:
        logger.debug(f"Error processing page {url}: {e}")
        page_info["signals"] = ["parse_error"]
        
    return page_info


def _classify_page(url: str, title: str, h1_text: str, content: str) -> Tuple[str, float, List[str]]:
    """
    Classify a page into categories and assign a score.
    
    Args:
        url: Page URL
        title: Page title text (lowercase)
        h1_text: H1 headings text (lowercase)
        content: Full page content
        
    Returns:
        Tuple of (primary_category, score, signals)
    """
    url_lower = url.lower()
    content_lower = content.lower()
    
    categories = []
    signals = []
    
    # Product/Solutions patterns (highest priority)
    product_patterns = [
        r'/products?(?:/|$)', r'/solutions?(?:/|$)', r'/hardware(?:/|$)',
        r'/catalog(?:/|$)', r'/specs?(?:/|$)', r'/items?(?:/|$)',
        r'/models?(?:/|$)', r'/series(?:/|$)', r'/range(?:/|$)',
        r'/equipment(?:/|$)', r'/devices?(?:/|$)', r'/machines?(?:/|$)',
        r'/systems?(?:/|$)', r'/technology(?:/|$)'
    ]
    if any(re.search(pattern, url_lower) for pattern in product_patterns):
        categories.append(("product", 1.0))
        signals.append("product_url")
        
    # Enhanced product title detection
    product_keywords = [
        'product', 'solution', 'hardware', 'specification', 'model', 'series',
        'equipment', 'device', 'machine', 'system', 'robot', 'technology',
        'mt1', 'kehrroboter', 'cleaning', 'autonomous'  # Specific to robotics
    ]
    if any(keyword in title for keyword in product_keywords):
        categories.append(("product", 1.0))
        signals.append("product_title")
        
    # Check H1 headings for product indicators
    if any(keyword in h1_text for keyword in product_keywords):
        categories.append(("product", 1.0))
        signals.append("product_h1")
        
    # Datasheet/Docs patterns
    doc_patterns = [
        r'/docs?(?:/|$)', r'/documentation(?:/|$)', r'/datasheet(?:/|$)',
        r'/downloads?(?:/|$)', r'\.pdf$'
    ]
    if any(re.search(pattern, url_lower) for pattern in doc_patterns):
        categories.append(("datasheet", 0.9))
        signals.append("docs_url")
        
    if any(keyword in title for keyword in ['documentation', 'datasheet', 'manual', 'guide']):
        categories.append(("docs", 0.9))
        signals.append("docs_title")
        
    # Pricing patterns
    if '/pricing' in url_lower or '/plans' in url_lower:
        categories.append(("pricing", 0.7))
        signals.append("pricing_url")
        
    if any(keyword in title for keyword in ['pricing', 'plans', 'cost']):
        categories.append(("pricing", 0.7))
        signals.append("pricing_title")
        
    # Releases/Updates patterns
    release_patterns = [
        r'/releases?(?:/|$)', r'/updates?(?:/|$)', r'/changelog(?:/|$)',
        r'/firmware(?:/|$)', r'/versions?(?:/|$)'
    ]
    if any(re.search(pattern, url_lower) for pattern in release_patterns):
        categories.append(("releases", 0.7))
        signals.append("releases_url")
        
    if any(keyword in title for keyword in ['release', 'update', 'changelog', 'version']):
        categories.append(("releases", 0.7))
        signals.append("releases_title")
        
    # News/Blog patterns
    news_patterns = [r'/news(?:/|$)', r'/blog(?:/|$)', r'/press(?:/|$)']
    if any(re.search(pattern, url_lower) for pattern in news_patterns):
        categories.append(("news", 0.4))
        signals.append("news_url")
        
    if any(keyword in title for keyword in ['news', 'blog', 'press', 'announcement']):
        categories.append(("news", 0.4))
        signals.append("news_title")
    
    # Apply hierarchy: product > datasheet > docs > releases > pricing > news > other
    category_priority = {
        "product": 6, "datasheet": 5, "docs": 4, "releases": 3, 
        "pricing": 2, "news": 1, "other": 0
    }
    
    if categories:
        # Sort by priority, then by score
        categories.sort(key=lambda x: (category_priority.get(x[0], 0), x[1]), reverse=True)
        primary_category, base_score = categories[0]
        
        # Adjust score with signals
        signal_bonus = len(signals) * 0.05  # Small bonus for multiple signals
        final_score = min(1.0, base_score + signal_bonus)
        
        return primary_category, final_score, signals
    else:
        return "other", 0.1, ["no_classification"]


def _extract_links(content: str, base_url: str) -> List[str]:
    """
    Extract and normalize links from HTML content with enhanced discovery.
    
    Args:
        content: HTML content
        base_url: Base URL for resolving relative links
        
    Returns:
        List of normalized URLs
    """
    try:
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        
        # Extract from standard <a> tags
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            normalized = normalize_url(href, base_url)
            if normalized:
                links.append(normalized)
        
        # Extract from navigation menus (common patterns)
        nav_selectors = [
            'nav a[href]',
            '.nav a[href]',
            '.navigation a[href]',
            '.menu a[href]',
            '.header a[href]',
            '.navbar a[href]',
            '[role="navigation"] a[href]'
        ]
        
        for selector in nav_selectors:
            try:
                nav_links = soup.select(selector)
                for link in nav_links:
                    if link.get('href'):
                        normalized = normalize_url(link['href'], base_url)
                        if normalized:
                            links.append(normalized)
            except Exception:
                continue
        
        # Extract from common product/content containers
        content_selectors = [
            '.product a[href]',
            '.products a[href]',
            '.item a[href]',
            '.card a[href]',
            '.content a[href]',
            '[class*="product"] a[href]',
            '[class*="item"] a[href]'
        ]
        
        for selector in content_selectors:
            try:
                content_links = soup.select(selector)
                for link in content_links:
                    if link.get('href'):
                        normalized = normalize_url(link['href'], base_url)
                        if normalized:
                            links.append(normalized)
            except Exception:
                continue
                
        # Look for data-href, data-url attributes (JavaScript navigation)
        for element in soup.find_all(attrs={'data-href': True}):
            href = element.get('data-href')
            if href:
                normalized = normalize_url(href, base_url)
                if normalized:
                    links.append(normalized)
                    
        for element in soup.find_all(attrs={'data-url': True}):
            href = element.get('data-url')
            if href:
                normalized = normalize_url(href, base_url)
                if normalized:
                    links.append(normalized)
        
        # Deduplicate and prioritize interesting links
        unique_links = list(set(links))
        
        # Sort links to prioritize product/content pages
        def link_priority(url):
            url_lower = url.lower()
            # Higher priority for product-related URLs
            if any(pattern in url_lower for pattern in ['/product', '/solution', '/item', '/category']):
                return 0
            # Medium priority for content URLs  
            elif any(pattern in url_lower for pattern in ['/docs', '/download', '/news', '/blog']):
                return 1
            # Lower priority for other pages
            else:
                return 2
        
        unique_links.sort(key=link_priority)
        return unique_links
        
    except Exception as e:
        logger.debug(f"Error extracting links: {e}")
        return []


def _should_use_javascript(url: str, depth: int) -> bool:
    """
    Determine if JavaScript should be used for this URL.
    Use JS for important pages, regular requests for simple navigation.
    
    Args:
        url: URL to evaluate
        depth: Crawl depth of the URL
        
    Returns:
        True if JavaScript should be used
    """
    url_lower = url.lower()
    
    # Always use JS for homepage (depth 0)
    if depth == 0:
        return True
    
    # Use JS for product pages and important content
    important_patterns = [
        '/product', '/solution', '/item', '/model', '/series',
        '/catalog', '/spec', '/datasheet', '/download',
        '/pricing', '/plans', '/releases', '/changelog'
    ]
    
    if any(pattern in url_lower for pattern in important_patterns):
        return True
    
    # Use JS for pages that likely have dynamic content
    dynamic_indicators = [
        'shop', 'store', 'buy', 'cart', 'search', 'filter',
        'dashboard', 'portal', 'app', 'tool'
    ]
    
    if any(indicator in url_lower for indicator in dynamic_indicators):
        return True
    
    # Skip JS for simple pages
    simple_patterns = [
        '/about', '/contact', '/privacy', '/terms', '/legal',
        '/careers', '/jobs', '/team', '/history', '/faq'
    ]
    
    if any(pattern in url_lower for pattern in simple_patterns):
        return False
    
    # Use JS for depth 1 (direct links from homepage), skip for deeper pages
    return depth <= 1
