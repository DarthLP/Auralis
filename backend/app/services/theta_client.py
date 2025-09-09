"""
Theta EdgeCloud client for DeepSeek-R1 inference with structured output support.

Implements JSON mode, rate limiting, caching, retry logic, and circuit breaker
for reliable AI extraction at scale.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Iterator
from dataclasses import dataclass, field
from enum import Enum

import httpx
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.config import settings
from app.core.db import get_db

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"


@dataclass
class TokenBucket:
    """Token bucket for rate limiting with burst support."""
    rate: float  # tokens per second
    capacity: int  # max tokens
    tokens: float = field(default_factory=lambda: 0)
    last_refill: float = field(default_factory=time.time)
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()
        
        # Refill tokens based on elapsed time
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time needed for tokens to be available."""
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.rate


@dataclass
class CircuitBreaker:
    """Circuit breaker for handling provider failures."""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # seconds
    failure_count: int = 0
    last_failure: Optional[float] = None
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    
    def call_succeeded(self):
        """Record successful call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        
    def call_failed(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def can_attempt(self) -> bool:
        """Check if we can attempt a call."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
            
        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure and time.time() - self.last_failure > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state")
                return True
            return False
            
        # HALF_OPEN state - allow one attempt
        return True


class ThetaClientError(Exception):
    """Base exception for Theta client errors."""
    pass


class ThetaRateLimitError(ThetaClientError):
    """Rate limit exceeded."""
    pass


class ThetaValidationError(ThetaClientError):
    """Response validation failed."""
    pass


class ThetaClient:
    """
    Theta EdgeCloud client with robust error handling and caching.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.base_url = "https://ondemand.thetaedgecloud.com"
        self.model = "deepseek_r1"
        self.timeout = settings.THETA_REQUEST_TIMEOUT
        self.max_retries = settings.THETA_MAX_RETRIES
        
        # Rate limiting: global and per-session buckets
        self.global_limiter = TokenBucket(
            rate=settings.THETA_RATE_PER_MIN / 60.0,  # convert to per-second
            capacity=settings.THETA_RATE_BURST or 10
        )
        self.session_limiters: Dict[str, TokenBucket] = {}
        
        # Circuit breaker for provider failures
        self.circuit_breaker = CircuitBreaker()
        
        # HTTP client with proper timeouts
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
        )
    
    def _get_session_limiter(self, session_id: str) -> TokenBucket:
        """Get or create rate limiter for session."""
        if session_id not in self.session_limiters:
            self.session_limiters[session_id] = TokenBucket(
                rate=settings.THETA_SESSION_RATE_PER_MIN / 60.0,
                capacity=settings.THETA_SESSION_RATE_BURST or 5
            )
        return self.session_limiters[session_id]
    
    def _compute_cache_key(self, prompt: str, schema_version: str, page_type: str, competitor: str) -> str:
        """Compute deterministic cache key for request."""
        # Include all parameters that affect the response
        key_data = f"{self.model}:{schema_version}:{settings.EXTRACTOR_PROMPT_VERSION}:{page_type}:{competitor}:{prompt}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if valid."""
        try:
            from app.models.extraction import AICache  # Import here to avoid circular imports
            
            cache_entry = self.db.query(AICache).filter(
                AICache.cache_key == cache_key,
                AICache.expires_at > datetime.utcnow()
            ).first()
            
            if cache_entry:
                # Update last_used_at for LRU tracking
                cache_entry.last_used_at = datetime.utcnow()
                self.db.commit()
                
                logger.debug(f"Cache hit for key {cache_key[:16]}...")
                return json.loads(cache_entry.response_json)
                
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            
        return None
    
    def _cache_response(self, cache_key: str, response: Dict[str, Any], ttl_hours: int = 24 * 30):
        """Cache response with TTL."""
        try:
            from app.models.extraction import AICache
            
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            
            # Generate prompt hash for caching (use cache_key as it already contains the prompt info)
            import hashlib
            prompt_hash = hashlib.sha256(cache_key.encode()).hexdigest()
            
            cache_entry = AICache(
                cache_key=cache_key,
                model_name=self.model,
                schema_version=settings.SCHEMA_VERSION,
                prompt_hash=prompt_hash,
                response_json=json.dumps(response),
                created_at=datetime.utcnow(),
                last_used_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            # Use merge to handle potential duplicates
            self.db.merge(cache_entry)
            self.db.commit()
            
            logger.debug(f"Cached response for key {cache_key[:16]}...")
            
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    async def _wait_for_rate_limit(self, session_id: Optional[str] = None):
        """Wait for rate limit availability."""
        # Check global rate limit
        if not self.global_limiter.consume():
            wait_time = self.global_limiter.wait_time()
            logger.info(f"Global rate limit hit, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            self.global_limiter.consume()  # Should succeed now
        
        # Check session rate limit if provided
        if session_id:
            session_limiter = self._get_session_limiter(session_id)
            if not session_limiter.consume():
                wait_time = session_limiter.wait_time()
                logger.info(f"Session {session_id} rate limit hit, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                session_limiter.consume()  # Should succeed now
    
    def _build_request_payload(self, prompt: str, use_json_mode: bool = True) -> Dict[str, Any]:
        """Build request payload for Theta EdgeCloud."""
        messages = [
            {
                "role": "system",
                "content": "You are a structured data extractor for competitive intelligence. Output ONLY valid JSON matching the provided JSON Schema. If uncertain, use null but keep required fields. No markdown, no explanations, pure JSON only."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        payload = {
            "input": {
                "max_tokens": settings.THETA_MAX_OUTPUT_TOKENS,
                "messages": messages,
                "stream": False,  # Never stream for structured output
                "temperature": 0.1,  # Very low for consistency
                "top_p": 0.5
            }
        }
        
        # Add JSON mode if supported and requested
        if use_json_mode and settings.THETA_JSON_MODE:
            payload["input"]["response_format"] = {"type": "json_object"}
            
        return payload
    
    async def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Theta EdgeCloud."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.ON_DEMAND_API_ACCESS_TOKEN}"
        }
        
        url = f"{self.base_url}/infer_request/{self.model}/completions"
        
        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            self.circuit_breaker.call_succeeded()
            return result
            
        except httpx.HTTPStatusError as e:
            self.circuit_breaker.call_failed()
            
            if e.response.status_code == 429:
                raise ThetaRateLimitError(f"Rate limit exceeded: {e}")
            elif e.response.status_code >= 500:
                raise ThetaClientError(f"Server error {e.response.status_code}: {e}")
            else:
                raise ThetaClientError(f"HTTP error {e.response.status_code}: {e}")
                
        except httpx.TimeoutException:
            self.circuit_breaker.call_failed()
            raise ThetaClientError("Request timeout")
            
        except Exception as e:
            self.circuit_breaker.call_failed()
            raise ThetaClientError(f"Unexpected error: {e}")
    
    def _extract_content(self, response: Dict[str, Any]) -> str:
        """Extract content from Theta EdgeCloud response."""
        try:
            content = None
            
            # Handle Theta EdgeCloud response format
            if "body" in response and "infer_requests" in response["body"]:
                infer_requests = response["body"]["infer_requests"]
                if len(infer_requests) > 0:
                    infer_request = infer_requests[0]
                    if "output" in infer_request and "message" in infer_request["output"]:
                        content = infer_request["output"]["message"]
            
            # Handle standard OpenAI-style response formats
            if not content and "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                elif "text" in choice:
                    content = choice["text"]
            
            # Fallback - look for common content fields
            if not content:
                for field in ["content", "text", "output", "result"]:
                    if field in response:
                        content = response[field]
                        break
            
            if not content:
                raise ThetaClientError(f"Could not extract content from response: {response}")
            
            # Extract JSON from markdown code blocks if present
            import re
            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                return json_match.group(1).strip()
            
            # If no markdown, return the content as-is
            return content.strip()
            
        except Exception as e:
            raise ThetaClientError(f"Response parsing failed: {e}")
    
    async def complete(
        self, 
        prompt: str, 
        schema_version: str = "v1",
        page_type: str = "unknown",
        competitor: str = "unknown",
        session_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Complete a prompt with structured JSON output.
        
        Args:
            prompt: The prompt to complete
            schema_version: Schema version for caching
            page_type: Page type for caching and optimization
            competitor: Competitor name for caching
            session_id: Session ID for rate limiting
            use_cache: Whether to use caching
            
        Returns:
            Parsed JSON response
            
        Raises:
            ThetaClientError: On various failures
            ThetaRateLimitError: On rate limit issues
            ThetaValidationError: On validation failures
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_attempt():
            raise ThetaClientError("Circuit breaker open - too many recent failures")
        
        # Check cache first
        cache_key = None
        if use_cache:
            cache_key = self._compute_cache_key(prompt, schema_version, page_type, competitor)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        # Wait for rate limits
        await self._wait_for_rate_limit(session_id)
        
        # Attempt request with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                payload = self._build_request_payload(prompt, use_json_mode=True)
                response = await self._make_request(payload)
                content = self._extract_content(response)
                
                # Parse JSON response
                try:
                    result = json.loads(content)
                except json.JSONDecodeError as e:
                    # Try corrective retry on first attempt
                    if attempt == 0:
                        logger.warning(f"JSON parsing failed, attempting corrective retry: {e}")
                        corrective_prompt = f"{prompt}\n\nIMPORTANT: Your previous response was invalid JSON. Return ONLY valid JSON with no additional text or formatting."
                        payload = self._build_request_payload(corrective_prompt, use_json_mode=True)
                        response = await self._make_request(payload)
                        content = self._extract_content(response)
                        result = json.loads(content)  # This will raise if still invalid
                    else:
                        raise ThetaValidationError(f"Invalid JSON response: {e}")
                
                # Cache successful response
                if use_cache and cache_key:
                    self._cache_response(cache_key, result)
                
                return result
                
            except (ThetaRateLimitError, ThetaValidationError):
                # Don't retry these specific errors
                raise
                
            except ThetaClientError as e:
                last_error = e
                if attempt < self.max_retries:
                    # Exponential backoff with jitter
                    base_delay = 0.8 * (2 ** attempt)
                    jitter = base_delay * 0.1 * (0.5 - hash(str(e)) % 100 / 100)
                    delay = min(base_delay + jitter, 10.0)  # Cap at 10s
                    
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts: {e}")
        
        # All retries exhausted
        raise last_error or ThetaClientError("Request failed after all retries")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def health_check(self) -> Dict[str, Any]:
        """Return client health status."""
        return {
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
            "global_rate_limit_tokens": self.global_limiter.tokens,
            "active_session_limiters": len(self.session_limiters),
            "cache_enabled": True
        }


# Convenience function for dependency injection
def get_theta_client(db: Session = Depends(get_db)) -> ThetaClient:
    """Get Theta client instance."""
    return ThetaClient(db)
