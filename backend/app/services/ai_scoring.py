"""
AI-powered page scoring service for discovery stage.

Uses DeepSeek (via Theta EdgeCloud) to provide comprehensive scoring and classification
of pages based on their content relevance for competitive analysis.
"""

import json
import logging
import time
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
        Score a page using AI analysis with lightweight input.
        
        Args:
            url: Page URL
            title: Page title
            content: Page content (optional, not used in lightweight mode)
            h1_headings: H1 headings from the page
            competitor: Competitor name for context
            session_id: Session ID for rate limiting
            
        Returns:
            AIScoringResult with comprehensive scoring
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
                            ai_response_dict = {}
                    else:
                        ai_response_dict = {}
            else:
                ai_response_dict = ai_response
            
            result = self._parse_ai_response(ai_response_dict)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return AIScoringResult(
                success=True,
                score=result["score"],
                primary_category=result["primary_category"],
                secondary_categories=result["secondary_categories"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                signals=result["signals"],
                processing_time_ms=processing_time,
                tokens_input=estimated_tokens,
                tokens_output=len(json.dumps(ai_response)) // 4,  # Rough estimate
                cache_hit=False  # Theta client handles this internally
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
                error=str(e)
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
                error=str(e)
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
                            # Extract JSON from the message if it contains JSON
                            extracted_json = self._extract_json_from_text(message)
                            logger.debug(f"Extracted JSON: {extracted_json}")
                            return extracted_json
                
                # Fallback: try to extract from other possible locations
                if "message" in result:
                    logger.debug(f"Direct message content: {result['message'][:200]}...")
                    return self._extract_json_from_text(result["message"])
                elif "content" in result:
                    logger.debug(f"Direct content: {result['content'][:200]}...")
                    return self._extract_json_from_text(result["content"])
                else:
                    # Debug: Log the full response for analysis
                    logger.debug(f"Full API response: {json.dumps(result, indent=2)}")
                    # Return the raw response as JSON string
                    return json.dumps(result)
                    
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
        
        # If no JSON found, return the original text
        logger.warning(f"No valid JSON found in AI response: {text[:200]}...")
        return text

    def _build_scoring_prompt(self, analysis_text: str, competitor: str) -> str:
        """Build the AI prompt for lightweight page scoring."""
        return f"""You are an expert competitive intelligence analyst. Analyze the following webpage metadata and provide a comprehensive score and classification.

IMPORTANT: Respond ONLY in English. Do not use any other languages.

COMPETITOR CONTEXT: {competitor}

WEBPAGE METADATA TO ANALYZE:
{analysis_text}

SCORING CRITERIA:
Rate the page's relevance for competitive analysis on a scale of 0.0 to 1.0. Be precise and differentiate between similar pages based on their actual content and context.

HIGH VALUE (0.8-1.0): Pages with exceptional competitive intelligence value:
- Product specifications, technical details, or capabilities
- Pricing information, business models, or commercial offerings
- Technical documentation, datasheets, or detailed product data
- Strategic announcements, major product launches, or roadmap information
- Competitive positioning, market analysis, or business strategy

MEDIUM-HIGH VALUE (0.6-0.8): Pages with strong competitive intelligence value:
- Product overviews, feature descriptions, or product pages
- Company updates, press releases, or strategic announcements
- Case studies, customer success stories, or use cases
- Industry insights, thought leadership, or market positioning
- Partnership announcements or business developments

MEDIUM VALUE (0.4-0.6): Pages with moderate competitive intelligence value:
- General company information or about pages
- News articles, blog posts, or content marketing
- Product updates, releases, or changelogs
- Support documentation or help content
- Marketing materials or promotional content

LOW VALUE (0.1-0.4): Pages with limited competitive intelligence value:
- Generic company information or contact pages
- Basic news or blog content without strategic value
- Administrative or operational information
- Community or social media pages

MINIMAL VALUE (0.0-0.1): Pages with no competitive intelligence value:
- Careers, jobs, or hiring information
- Privacy policies, terms of service, or legal disclaimers
- Generic contact information or forms
- Cookie notices or accessibility statements
- Low-value marketing or promotional content

ASSESSMENT APPROACH:
- Analyze the URL structure, title, and headings for context clues
- Consider what specific competitive intelligence this page would provide
- Evaluate the depth and specificity of information likely to be present
- Assess the strategic importance for understanding the competitor's business
- Consider the target audience and business purpose
- Be precise in scoring - avoid giving identical scores to different pages
- Think about what a competitor analyst would find most valuable

OUTPUT FORMAT (JSON only):
{{
    "score": 0.85,
    "primary_category": "product",
    "secondary_categories": ["datasheet"],
    "confidence": 0.9,
    "reasoning": "High-value product specifications page with technical details that would provide significant competitive intelligence about product capabilities and positioning",
    "signals": ["product_specs", "pricing_info", "technical_details"]
}}

CATEGORIES: Use your judgment to assign the most appropriate category from: product, pricing, datasheet, release, news, company, other
SIGNALS: Identify relevant signals such as: product_specs, pricing_info, technical_details, release_notes, news_content, company_info, low_value, high_value, competitive_intel, strategic_info, market_analysis, business_model

Return ONLY valid JSON with no additional text. Use only English language."""
    
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
