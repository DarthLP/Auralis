"""
AI-powered page scoring service for discovery stage.

Uses DeepSeek (via Theta EdgeCloud) to provide comprehensive scoring and classification
of pages based on their content relevance for competitive analysis.
"""

import json
import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from app.core.config import settings
from app.services.theta_client import ThetaClient, ThetaClientError
from app.services.schema_utils import get_schema_compactor, TokenCounter

logger = logging.getLogger(__name__)


@dataclass
class AIScoringResult:
    """Result of AI scoring attempt."""
    success: bool
    score: float
    primary_category: str
    secondary_categories: List[str]
    confidence: float
    reasoning: str
    signals: List[str]
    processing_time_ms: int
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cache_hit: bool = False
    error: Optional[str] = None
    retry_count: int = 0
    retry_errors: List[str] = None


class AIScoringService:
    """
    AI-powered page scoring service using DeepSeek for comprehensive analysis.
    """
    
    def __init__(self, theta_client: ThetaClient):
        self.theta_client = theta_client
        self.schema_compactor = get_schema_compactor()
        self.token_counter = TokenCounter()
        
        # Define scoring categories with their priorities
        self.categories = {
            "product": {
                "priority": 6,
                "description": "Product pages, specifications, features, models",
                "keywords": ["product", "model", "specification", "feature", "hardware", "robot", "device"]
            },
            "pricing": {
                "priority": 5,
                "description": "Pricing pages, plans, costs, subscriptions",
                "keywords": ["price", "cost", "plan", "subscription", "billing", "purchase"]
            },
            "datasheet": {
                "priority": 4,
                "description": "Technical documentation, datasheets, manuals",
                "keywords": ["datasheet", "manual", "documentation", "spec", "technical"]
            },
            "release": {
                "priority": 3,
                "description": "Release notes, updates, changelogs, versions",
                "keywords": ["release", "update", "changelog", "version", "new", "announcement"]
            },
            "news": {
                "priority": 2,
                "description": "News, blog posts, press releases, announcements",
                "keywords": ["news", "blog", "press", "announcement", "article"]
            },
            "company": {
                "priority": 1,
                "description": "Company information, about, team, history",
                "keywords": ["about", "company", "team", "history", "mission", "vision"]
            },
            "other": {
                "priority": 0,
                "description": "Other content not fitting above categories",
                "keywords": []
            }
        }
    
    def _is_retryable_error(self, error: Exception, ai_response_dict: Optional[Dict] = None) -> bool:
        """
        Determine if an error should trigger a retry attempt.
        
        Args:
            error: The exception that occurred
            ai_response_dict: The parsed AI response (if available)
            
        Returns:
            True if the error is retryable, False otherwise
        """
        # Network/API errors are retryable
        if isinstance(error, ThetaClientError):
            error_str = str(error).lower()
            # Don't retry on authentication or quota errors
            if any(keyword in error_str for keyword in ['401', '403', 'unauthorized', 'quota', 'rate limit']):
                return False
            # Retry on timeout, connection, and temporary server errors
            if any(keyword in error_str for keyword in ['timeout', 'connection', 'temporary', '502', '503', '504']):
                return True
            # Retry other API errors (could be temporary)
            return True
        
        # JSON parsing errors are retryable (AI might produce better output on retry)
        if isinstance(error, json.JSONDecodeError):
            return True
        
        # Check for string-based error patterns that are retryable
        error_str = str(error).lower()
        retryable_patterns = [
            'failed to parse ai response',
            'no content found in ai response',
            'missing required field',
            'parse_error',
            'timeout',
            'connection',
            'temporary',
            '502', '503', '504',
            'empty message content',
            'empty direct message',
            'empty direct content',
            'does not contain valid json',
            'no recognizable content fields'
        ]
        
        if any(pattern in error_str for pattern in retryable_patterns):
            return True
        
        # Check for specific AI response issues that are retryable
        if ai_response_dict:
            # If we have a response but it's missing critical fields
            if isinstance(ai_response_dict, dict):
                # Check for parse_error signals (indicates malformed AI output)
                signals = ai_response_dict.get("signals", [])
                if "parse_error" in signals:
                    return True
                
                # Check for very low confidence with parse-related reasoning
                confidence = ai_response_dict.get("confidence", 1.0)
                reasoning = ai_response_dict.get("reasoning", "").lower()
                if confidence == 0.0 and "parse" in reasoning:
                    return True
        
        # Don't retry programming errors or other unexpected issues
        return False
    
    async def _score_page_with_retry(
        self, 
        url: str, 
        title: str, 
        content: str = "", 
        h1_headings: str = "",
        competitor: str = "unknown",
        session_id: Optional[str] = None,
        max_retries: int = 2
    ) -> AIScoringResult:
        """
        Score a page with automatic retry logic for transient failures.
        
        Args:
            url: Page URL
            title: Page title
            content: Page content (optional, not used in lightweight mode)
            h1_headings: H1 headings from the page
            competitor: Competitor name for context
            session_id: Session ID for rate limiting
            max_retries: Maximum number of retry attempts (default: 2)
            
        Returns:
            AIScoringResult with retry information included
        """
        retry_errors = []
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Add exponential backoff delay for retries
                if attempt > 0:
                    delay = min(2 ** (attempt - 1), 4)  # Cap at 4 seconds
                    logger.info(f"Retrying AI scoring for {url} (attempt {attempt + 1}/{max_retries + 1}) after {delay}s delay")
                    await asyncio.sleep(delay)
                
                # Attempt the scoring
                result = await self._score_page_single_attempt(
                    url=url,
                    title=title,
                    content=content,
                    h1_headings=h1_headings,
                    competitor=competitor,
                    session_id=session_id
                )
                
                # Add retry information to successful result
                result.retry_count = attempt
                result.retry_errors = retry_errors.copy() if retry_errors else []
                
                # If successful, return immediately
                if result.success:
                    if attempt > 0:
                        logger.info(f"AI scoring succeeded on retry attempt {attempt + 1} for {url}")
                    return result
                
                # If not successful, check if we should retry
                if attempt < max_retries:
                    # For unsuccessful results, check if the error is retryable
                    # Check for parsing errors or other retryable conditions
                    is_retryable = (
                        result.error and (
                            self._is_retryable_error(Exception(result.error)) or
                            "parse_error" in result.signals or
                            "Failed to parse AI response" in result.reasoning or
                            (result.confidence == 0.0 and "parse" in result.reasoning.lower())
                        )
                    )
                    
                    if is_retryable:
                        retry_errors.append(f"Attempt {attempt + 1}: {result.error}")
                        logger.warning(f"AI scoring failed (retryable), will retry: {result.error}")
                        continue
                    else:
                        # Non-retryable failure, return immediately
                        logger.warning(f"AI scoring failed (non-retryable): {result.error}")
                        result.retry_count = attempt
                        result.retry_errors = retry_errors.copy() if retry_errors else []
                        return result
                else:
                    # Max retries reached
                    logger.error(f"AI scoring failed after {max_retries + 1} attempts for {url}")
                    result.retry_count = attempt
                    result.retry_errors = retry_errors.copy() if retry_errors else []
                    # Add retry_exhausted signal if not already present
                    if "retry_exhausted" not in result.signals:
                        result.signals.append("retry_exhausted")
                    return result
                    
            except Exception as e:
                last_error = e
                logger.warning(f"AI scoring attempt {attempt + 1} failed for {url}: {e}")
                
                # Check if this error is retryable
                if attempt < max_retries and self._is_retryable_error(e):
                    retry_errors.append(f"Attempt {attempt + 1}: {str(e)}")
                    continue
                else:
                    # Non-retryable error or max retries reached
                    logger.error(f"AI scoring failed permanently for {url}: {e}")
                    break
        
        # If we get here, all attempts failed
        processing_time = 0  # We don't have timing info for failed attempts
        return AIScoringResult(
            success=False,
            score=0.0,
            primary_category="other",
            secondary_categories=[],
            confidence=0.0,
            reasoning=f"AI scoring failed after {max_retries + 1} attempts",
            signals=["retry_exhausted"],
            processing_time_ms=processing_time,
            error=str(last_error) if last_error else "All retry attempts failed",
            retry_count=max_retries,
            retry_errors=retry_errors
        )

    async def _score_page_single_attempt(
        self, 
        url: str, 
        title: str, 
        content: str = "", 
        h1_headings: str = "",
        competitor: str = "unknown",
        session_id: Optional[str] = None
    ) -> AIScoringResult:
        """
        Single attempt at scoring a page (extracted from original score_page method).
        
        This is the core scoring logic without retry handling.
        """
        start_time = time.time()
        
        try:
            # Prepare lightweight content for AI analysis
            analysis_text = self._prepare_lightweight_content_for_analysis(url, title, h1_headings)
            
            # Check token limits
            estimated_tokens = self.token_counter.estimate_tokens(analysis_text)
            if estimated_tokens > settings.EXTRACTOR_MAX_TEXT_CHARS // 4:  # Conservative limit
                analysis_text = self.schema_compactor.truncate_text(
                    analysis_text, 
                    settings.EXTRACTOR_MAX_TEXT_CHARS // 4
                )
                logger.warning(f"Truncated content for AI scoring: {estimated_tokens} -> {self.token_counter.estimate_tokens(analysis_text)} tokens")
            
            # Create AI prompt for scoring
            prompt = self._build_scoring_prompt(analysis_text, competitor)
            
            # Call AI service with custom scoring method
            ai_response = await self._call_scoring_api(
                prompt=prompt,
                competitor=competitor,
                session_id=session_id
            )
            
            # Parse and validate response
            # ai_response is a string (JSON content), parse it first
            if isinstance(ai_response, str):
                try:
                    ai_response_dict = json.loads(ai_response)
                    logger.debug(f"Parsed AI response: {ai_response_dict}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse AI response JSON: {e}")
                    logger.debug(f"Raw AI response: {ai_response[:500]}...")
                    # Try to extract JSON from the response
                    extracted_json = self._extract_json_from_text(ai_response)
                    if extracted_json != ai_response:
                        try:
                            ai_response_dict = json.loads(extracted_json)
                            logger.debug(f"Successfully extracted and parsed JSON: {ai_response_dict}")
                        except json.JSONDecodeError as e2:
                            logger.error(f"Failed to parse extracted JSON: {e2}")
                            # Create a fallback response with parse error
                            ai_response_dict = {
                                "score": 0.1,
                                "primary_category": "other",
                                "secondary_categories": [],
                                "confidence": 0.0,
                                "reasoning": f"Failed to parse AI response: {e2}",
                                "signals": ["parse_error"]
                            }
                    else:
                        # Create a fallback response with parse error
                        ai_response_dict = {
                            "score": 0.1,
                            "primary_category": "other",
                            "secondary_categories": [],
                            "confidence": 0.0,
                            "reasoning": "Failed to parse AI response: No content found in AI response",
                            "signals": ["parse_error"]
                        }
            else:
                ai_response_dict = ai_response
            
            result = self._parse_ai_response(ai_response_dict)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Check if parsing failed by looking for parse_error signal or specific error patterns
            parsing_failed = (
                "parse_error" in result.get("signals", []) or
                "Failed to parse AI response" in result.get("reasoning", "") or
                result.get("confidence", 0) == 0.0 and "parse" in result.get("reasoning", "").lower()
            )
            
            return AIScoringResult(
                success=not parsing_failed,
                score=result["score"],
                primary_category=result["primary_category"],
                secondary_categories=result["secondary_categories"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                signals=result["signals"],
                processing_time_ms=processing_time,
                tokens_input=estimated_tokens,
                tokens_output=len(json.dumps(ai_response)) // 4,  # Rough estimate
                cache_hit=False,  # Theta client handles this internally
                error=result.get("reasoning") if parsing_failed else None,
                retry_count=0,
                retry_errors=[]
            )
            
        except ThetaClientError as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"AI scoring failed for {url}: {e}")
            
            return AIScoringResult(
                success=False,
                score=0.0,
                primary_category="other",
                secondary_categories=[],
                confidence=0.0,
                reasoning="AI scoring failed",
                signals=["ai_error"],
                processing_time_ms=processing_time,
                error=str(e),
                retry_count=0,
                retry_errors=[]
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Unexpected error in AI scoring for {url}: {e}")
            
            return AIScoringResult(
                success=False,
                score=0.0,
                primary_category="other",
                secondary_categories=[],
                confidence=0.0,
                reasoning="Unexpected error",
                signals=["error"],
                processing_time_ms=processing_time,
                error=str(e),
                retry_count=0,
                retry_errors=[]
            )
    
    async def score_page(
        self, 
        url: str, 
        title: str, 
        content: str = "", 
        h1_headings: str = "",
        competitor: str = "unknown",
        session_id: Optional[str] = None
    ) -> AIScoringResult:
        """
        Score a page using AI analysis with automatic retry on failures.
        
        This method now includes automatic retry logic for transient failures
        such as JSON parsing errors, network timeouts, and temporary API issues.
        
        Args:
            url: Page URL
            title: Page title
            content: Page content (optional, not used in lightweight mode)
            h1_headings: H1 headings from the page
            competitor: Competitor name for context
            session_id: Session ID for rate limiting
            
        Returns:
            AIScoringResult with comprehensive scoring and retry information
        """
        return await self._score_page_with_retry(
            url=url,
            title=title,
            content=content,
            h1_headings=h1_headings,
            competitor=competitor,
            session_id=session_id,
            max_retries=2  # Allow up to 2 retries (3 total attempts)
        )
    
    def _prepare_lightweight_content_for_analysis(self, url: str, title: str, h1_headings: str) -> str:
        """Prepare lightweight content for AI analysis using URL, title, H1 headings, and URL structure."""
        analysis_parts = []
        
        # URL context with path analysis
        analysis_parts.append(f"URL: {url}")
        
        # Extract meaningful path segments for context
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path_segments = [seg for seg in parsed.path.split('/') if seg and seg not in ['', 'index', 'home']]
            if path_segments:
                analysis_parts.append(f"URL Path: /{'/'.join(path_segments)}")
        except:
            pass
        
        # Title
        if title and title.strip():
            analysis_parts.append(f"Title: {title.strip()}")
        
        # H1 headings
        if h1_headings and h1_headings.strip():
            analysis_parts.append(f"Main Headings: {h1_headings.strip()}")
        
        # Add URL-based context clues
        url_lower = url.lower()
        context_clues = []
        
        if any(keyword in url_lower for keyword in ['product', 'products', 'robot', 'robots']):
            context_clues.append("product-related URL")
        if any(keyword in url_lower for keyword in ['pricing', 'price', 'cost', 'plan', 'subscription']):
            context_clues.append("pricing-related URL")
        if any(keyword in url_lower for keyword in ['news', 'blog', 'press', 'announcement']):
            context_clues.append("news-related URL")
        if any(keyword in url_lower for keyword in ['docs', 'documentation', 'manual', 'guide']):
            context_clues.append("documentation-related URL")
        if any(keyword in url_lower for keyword in ['about', 'company', 'team', 'mission']):
            context_clues.append("company-related URL")
        if any(keyword in url_lower for keyword in ['careers', 'jobs', 'hiring']):
            context_clues.append("careers-related URL")
        if any(keyword in url_lower for keyword in ['privacy', 'terms', 'legal', 'cookies']):
            context_clues.append("legal-related URL")
        
        if context_clues:
            analysis_parts.append(f"URL Context: {', '.join(context_clues)}")
        
        return "\n\n".join(analysis_parts)
    
    def _prepare_content_for_analysis(self, url: str, title: str, content: str) -> str:
        """Prepare content for AI analysis by cleaning and structuring (legacy method)."""
        # Clean and structure the content
        analysis_parts = []
        
        # URL context
        analysis_parts.append(f"URL: {url}")
        
        # Title
        if title and title.strip():
            analysis_parts.append(f"Title: {title.strip()}")
        
        # Content (cleaned)
        if content and content.strip():
            # Truncate very long content
            max_content_length = 8000  # Conservative limit for scoring
            if len(content) > max_content_length:
                content = content[:max_content_length] + "... [truncated]"
            analysis_parts.append(f"Content:\n{content.strip()}")
        
        return "\n\n".join(analysis_parts)
    
    async def _call_scoring_api(self, prompt: str, competitor: str, session_id: Optional[str] = None) -> str:
        """Call the scoring API directly with raw text response."""
        import httpx
        import json
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.ON_DEMAND_API_ACCESS_TOKEN}"
        }
        
        url = "https://ondemand.thetaedgecloud.com/infer_request/deepseek_r1/completions"
        
        data = {
            "input": {
                "max_tokens": 500,  # Reduced for faster response
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert competitive intelligence analyst. Analyze webpage content and provide scoring in JSON format. IMPORTANT: Respond ONLY in English. Do not use any other languages."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "temperature": 0.2,  # Lower temperature for more consistent results
                "top_p": 0.8
            }
        }
        
        try:
            # Use shorter timeout for faster failure detection
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                
                # Debug: Log the response structure
                logger.debug(f"API Response structure: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                if isinstance(result, dict) and "body" in result:
                    logger.debug(f"Body structure: {list(result['body'].keys()) if isinstance(result['body'], dict) else 'Not a dict'}")
                
                # Extract content from Theta EdgeCloud response format
                if "body" in result and "infer_requests" in result["body"]:
                    infer_requests = result["body"]["infer_requests"]
                    if len(infer_requests) > 0:
                        infer_request = infer_requests[0]
                        logger.debug(f"Infer request structure: {list(infer_request.keys()) if isinstance(infer_request, dict) else 'Not a dict'}")
                        if "output" in infer_request and "message" in infer_request["output"]:
                            message = infer_request["output"]["message"]
                            logger.debug(f"Message content: {message[:200]}...")
                            logger.debug(f"Message content (last 500 chars): ...{message[-500:]}")
                            
                            # Check for empty or whitespace-only message
                            if not message or not message.strip():
                                logger.warning(f"AI API returned empty message content")
                                raise ThetaClientError("AI API returned empty message content")
                            
                            # Extract JSON from the message if it contains JSON
                            extracted_json = self._extract_json_from_text(message)
                            logger.debug(f"Extracted JSON: {extracted_json}")
                            
                            # Check if extraction actually found valid content
                            if extracted_json == message and not message.strip().startswith('{'):
                                logger.warning(f"AI API message does not contain JSON: {message[:100]}...")
                                raise ThetaClientError("AI API message does not contain valid JSON")
                            
                            return extracted_json
                
                # Fallback: try to extract from other possible locations
                if "message" in result:
                    message = result["message"]
                    logger.debug(f"Direct message content: {message[:200]}...")
                    if not message or not message.strip():
                        logger.warning(f"Direct message is empty")
                        raise ThetaClientError("AI API returned empty direct message")
                    return self._extract_json_from_text(message)
                elif "content" in result:
                    content = result["content"]
                    logger.debug(f"Direct content: {content[:200]}...")
                    if not content or not str(content).strip():
                        logger.warning(f"Direct content is empty")
                        raise ThetaClientError("AI API returned empty direct content")
                    return self._extract_json_from_text(str(content))
                else:
                    # Debug: Log the full response for analysis
                    logger.debug(f"Full API response: {json.dumps(result, indent=2)}")
                    logger.warning(f"No recognizable content found in API response")
                    raise ThetaClientError("AI API response contains no recognizable content fields")
                    
        except Exception as e:
            logger.error(f"Scoring API call failed: {e}")
            raise ThetaClientError(f"Scoring API call failed: {e}")

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text that may contain other content."""
        import re
        
        # Clean up the text first
        text = text.strip()
        
        # Look for JSON blocks in the text
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
            r'```\s*(\{.*?\})\s*```',      # JSON in generic code blocks
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Try to parse as JSON to validate
                    json.loads(match)
                    return match
                except json.JSONDecodeError:
                    continue
        
        # Try to find any JSON object in the text (more flexible approach)
        # Look for opening and closing braces
        start_pos = text.find('{')
        if start_pos != -1:
            # Find the matching closing brace
            brace_count = 0
            end_pos = start_pos
            for i, char in enumerate(text[start_pos:], start_pos):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            if brace_count == 0:  # Found matching braces
                json_candidate = text[start_pos:end_pos]
                try:
                    # Try to parse as JSON to validate
                    parsed = json.loads(json_candidate)
                    # Check if it has the expected fields
                    if 'score' in parsed or 'primary_category' in parsed or 'category' in parsed:
                        return json_candidate
                except json.JSONDecodeError:
                    pass
        
        # Try to find JSON at the end of the text (common pattern)
        # Look for the last occurrence of a complete JSON object
        json_objects = re.findall(r'\{[^{}]*\}', text)
        for json_obj in reversed(json_objects):  # Start from the end
            try:
                parsed = json.loads(json_obj)
                if 'score' in parsed or 'primary_category' in parsed or 'category' in parsed:
                    return json_obj
            except json.JSONDecodeError:
                continue
        
        # Try to find JSON with more complex nested structures
        # Look for JSON objects that might have nested objects/arrays
        complex_json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(complex_json_pattern, text, re.DOTALL)
        for match in reversed(matches):  # Start from the end
            try:
                parsed = json.loads(match)
                if 'score' in parsed or 'primary_category' in parsed or 'category' in parsed:
                    return match
            except json.JSONDecodeError:
                continue
        
        # Try to find incomplete JSON and attempt to complete it
        # Look for patterns like {"score": or {"primary_category":
        incomplete_json_patterns = [
            r'\{[^}]*"score"\s*:\s*[^}]*$',  # JSON ending with score field
            r'\{[^}]*"primary_category"\s*:\s*[^}]*$',  # JSON ending with category field
        ]
        
        for pattern in incomplete_json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                # Try to complete the JSON with reasonable defaults
                try:
                    # Add missing closing brace and try to parse
                    completed_json = match + '}'
                    parsed = json.loads(completed_json)
                    if 'score' in parsed or 'primary_category' in parsed or 'category' in parsed:
                        return completed_json
                except json.JSONDecodeError:
                    # Try adding more fields to make it valid
                    try:
                        completed_json = match + ', "primary_category": "other", "confidence": 0.0, "reasoning": "Incomplete AI response", "signals": ["parse_error"]}'
                        parsed = json.loads(completed_json)
                        return completed_json
                    except json.JSONDecodeError:
                        continue
        
        # Try to find JSON that starts with reasoning text and extract the JSON part
        # Look for patterns like "```json\n{...}\n```" or just "{...}" after reasoning
        reasoning_json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
            r'```\s*(\{.*?\})\s*```',      # JSON in generic code blocks
            r'(\{[^{}]*"score"[^{}]*\})',  # JSON with score field
            r'(\{[^{}]*"primary_category"[^{}]*\})',  # JSON with category field
        ]
        
        for pattern in reasoning_json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Try to parse as JSON to validate
                    parsed = json.loads(match)
                    if 'score' in parsed or 'primary_category' in parsed or 'category' in parsed:
                        return match
                except json.JSONDecodeError:
                    continue
        
        # Try to find any JSON object in the text, even if it's incomplete
        # Look for the most complete JSON object we can find
        json_candidates = []
        
        # Find all potential JSON objects
        for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL):
            json_candidates.append(match.group())
        
        # Also look for incomplete JSON at the end
        for match in re.finditer(r'\{[^}]*$', text, re.DOTALL):
            json_candidates.append(match.group())
        
        # Try to parse each candidate, prioritizing complete ones
        for candidate in json_candidates:
            try:
                parsed = json.loads(candidate)
                if 'score' in parsed or 'primary_category' in parsed or 'category' in parsed:
                    return candidate
            except json.JSONDecodeError:
                # Try to complete incomplete JSON
                if candidate.endswith('"') or candidate.endswith(','):
                    # Try adding missing closing brace and required fields
                    try:
                        completed = candidate.rstrip('",') + '}'
                        parsed = json.loads(completed)
                        if 'score' in parsed or 'primary_category' in parsed or 'category' in parsed:
                            return completed
                    except json.JSONDecodeError:
                        # Try adding more fields to make it valid
                        try:
                            completed = candidate.rstrip('",') + ', "primary_category": "other", "confidence": 0.0, "reasoning": "Incomplete AI response", "signals": ["parse_error"]}'
                            parsed = json.loads(completed)
                            return completed
                        except json.JSONDecodeError:
                            continue
                continue
        
        # If no JSON found, return the original text
        logger.warning(f"No valid JSON found in AI response: {text[:200]}...")
        return text

    def _build_scoring_prompt(self, analysis_text: str, competitor: str) -> str:
        """Build the AI prompt for lightweight page scoring."""
        return f"""
You are an expert competitive intelligence analyst. Your task is to evaluate the competitive relevance of the given webpage and output a single valid JSON object with a score and categorization.

TASK
- Assess how important the provided webpage is for competitive analysis of the competitor.
- Use the SCORING criteria to decide the numeric score and categories.
- Base your judgment ONLY on the provided metadata text. Do not invent extra details.

CRITICAL RULES
- Output must be ONLY a valid JSON object. 
- Do NOT include any explanations, reasoning outside the JSON, markdown, commentary, or internal thoughts.
- JSON must begin with {{ and end with }}.
- All strings must be properly quoted.
- All fields must be present; use null or [] if not applicable.
- Output language: English ONLY.

INPUT
  - COMPETITOR: {competitor}
  - WEBPAGE METADATA: {analysis_text}

SCORING
  - Score range: 0.0–1.0
    - High Value (0.9–1.0): product specs, pricing, datasheets, launches, strategies
    - Medium-High (0.7–0.9): product pages and updates, press releases, use cases, partnerships, general company info (what is the company doing)
    - Medium (0.4–0.7): other company info, blogs, product updates, support docs
    - Low (0.1–0.3): generic info, admin, social, basic marketing
    - Minimal (0.0–0.1): careers, legal, privacy, contact, cookie notices

OUTPUT FORMAT
{{
  "score": <float>,
  "primary_category": "<string>",
  "secondary_categories": ["<string>", ...],
  "confidence": <float>,
  "reasoning": "<string>",
  "signals": ["<string>", ...]
}}

OPTIONS
  - primary_category: ["product","pricing","datasheet","release","news","company","other"]
  - signals: ["product_specs","pricing_info","technical_details","release_notes","news_content","company_info","low_value","high_value","competitive_intel","strategic_info","market_analysis","business_model"]

Return JSON ONLY.
"""
    
    def _parse_ai_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate AI response."""
        try:
            # If response is already a parsed dictionary with the expected fields, use it directly
            if isinstance(response, dict) and "score" in response:
                result = response
            else:
                # Extract the actual content from the response
                if isinstance(response, dict):
                    # Handle different response formats
                    content = None
                    if "content" in response:
                        content = response["content"]
                    elif "text" in response:
                        content = response["text"]
                    elif "output" in response:
                        content = response["output"]
                    else:
                        # Try to find content in nested structures
                        content = self._extract_nested_content(response)
                    
                    if not content:
                        raise ValueError("No content found in AI response")
                    
                    # Parse JSON content
                    if isinstance(content, str):
                        result = json.loads(content)
                    else:
                        result = content
                else:
                    raise ValueError(f"Unexpected response type: {type(response)}")
            
            # Handle different field names
            if "category" in result and "primary_category" not in result:
                result["primary_category"] = result["category"]
            
            # Validate required fields
            required_fields = ["score", "primary_category", "confidence", "reasoning"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate score range - handle both 0-1 and 0-100 scales
            score = float(result["score"])
            if score > 1.0:  # Convert from 0-100 to 0-1 scale
                score = score / 100.0
                result["score"] = score
            
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Score out of range: {score}")
            
            # Validate category
            primary_category = result["primary_category"]
            if primary_category not in self.categories:
                logger.warning(f"Unknown category: {primary_category}, defaulting to 'other'")
                result["primary_category"] = "other"
            
            # Set defaults for optional fields
            result.setdefault("secondary_categories", [])
            result.setdefault("signals", [])
            
            return result
                
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Response content: {response}")
            
            # Return fallback result
            return {
                "score": 0.1,
                "primary_category": "other",
                "secondary_categories": [],
                "confidence": 0.0,
                "reasoning": f"Failed to parse AI response: {e}",
                "signals": ["parse_error"]
            }
    
    def _extract_nested_content(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract content from nested response structures."""
        # Common nested patterns in AI responses
        paths = [
            ["choices", 0, "message", "content"],
            ["choices", 0, "text"],
            ["output", "message"],
            ["result", "content"],
            ["data", "content"]
        ]
        
        for path in paths:
            try:
                current = response
                for key in path:
                    if isinstance(key, int):
                        current = current[key]
                    else:
                        current = current[key]
                if isinstance(current, str) and current.strip():
                    return current
            except (KeyError, IndexError, TypeError):
                continue
        
        return None
    
    def get_category_priority(self, category: str) -> int:
        """Get priority score for a category."""
        return self.categories.get(category, {}).get("priority", 0)
    
    def get_category_description(self, category: str) -> str:
        """Get description for a category."""
        return self.categories.get(category, {}).get("description", "Unknown category")


# Convenience function for dependency injection
def get_ai_scoring_service(theta_client: ThetaClient) -> AIScoringService:
    """Get AI scoring service instance."""
    return AIScoringService(theta_client)
