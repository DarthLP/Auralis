"""
Schema-first extraction service with rules-first + AI fallback strategy.

Implements structured data extraction from page text using:
1. Rules-first: Fast regex/heuristic patterns for common data structures
2. AI fallback: Theta EdgeCloud for complex extraction when rules fail
3. Validation: JSON Schema validation for all outputs
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from app.core.config import settings
from app.services.theta_client import ThetaClient
from app.services.schema_utils import get_schema_compactor, TokenCounter
from app.services.validate import validate_payload, SchemaValidationError

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of extraction attempt."""
    success: bool
    method: str  # "rules" or "ai"
    entities: Dict[str, Any]
    confidence: float
    processing_time_ms: int
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cache_hit: bool = False
    error: Optional[str] = None


class RulesExtractor:
    """
    Rules-based extraction using regex patterns and heuristics.
    Fast, deterministic extraction for common patterns.
    """
    
    def __init__(self):
        self.pricing_patterns = self._build_pricing_patterns()
        self.product_patterns = self._build_product_patterns()
        self.release_patterns = self._build_release_patterns()
        self.spec_patterns = self._build_spec_patterns()
    
    def _build_pricing_patterns(self) -> List[Dict[str, Any]]:
        """Build regex patterns for pricing detection."""
        return [
            {
                "name": "currency_amount",
                "pattern": r"[\$€£¥]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
                "confidence": 0.9,
                "field": "pricing"
            },
            {
                "name": "per_month_pricing",
                "pattern": r"(\d+(?:\.\d{2})?)\s*(?:per|/)\s*month",
                "confidence": 0.85,
                "field": "pricing"
            },
            {
                "name": "pricing_table",
                "pattern": r"(?:plan|tier|package).*?(\$\d+)",
                "confidence": 0.8,
                "field": "pricing"
            }
        ]
    
    def _build_product_patterns(self) -> List[Dict[str, Any]]:
        """Build regex patterns for product detection."""
        return [
            {
                "name": "api_product",
                "pattern": r"(?:^|\s)([A-Z][a-zA-Z0-9\s]+(?:API|SDK|Service))",
                "confidence": 0.85,
                "field": "name"
            },
            {
                "name": "version_pattern",
                "pattern": r"(?:version|v\.?|release)\s*(\d+(?:\.\d+)*(?:\.\d+)*)",
                "confidence": 0.9,
                "field": "version"
            },
            {
                "name": "feature_list",
                "pattern": r"(?:features?|capabilities?):\s*(.+?)(?:\n\n|\.|$)",
                "confidence": 0.7,
                "field": "features"
            }
        ]
    
    def _build_release_patterns(self) -> List[Dict[str, Any]]:
        """Build regex patterns for release detection."""
        return [
            {
                "name": "release_version",
                "pattern": r"(?:released?|launched?)\s+(?:version\s+)?(\d+\.\d+(?:\.\d+)?)",
                "confidence": 0.9,
                "field": "version"
            },
            {
                "name": "release_date",
                "pattern": r"(?:released?|launched?|available)\s+(?:on\s+)?(\w+\s+\d{1,2},?\s+\d{4})",
                "confidence": 0.85,
                "field": "date"
            },
            {
                "name": "changelog_entry",
                "pattern": r"##?\s*(?:version\s+)?(\d+\.\d+(?:\.\d+)?)\s*(?:-\s*)?(.+?)(?=##?|\Z)",
                "confidence": 0.8,
                "field": "notes"
            }
        ]
    
    def _build_spec_patterns(self) -> List[Dict[str, Any]]:
        """Build regex patterns for specification detection."""
        return [
            {
                "name": "memory_spec",
                "pattern": r"(\d+(?:\.\d+)?)\s*(GB|MB|TB)\s*(?:RAM|memory)",
                "confidence": 0.9,
                "field": "specs.memory"
            },
            {
                "name": "storage_spec",
                "pattern": r"(\d+(?:\.\d+)?)\s*(GB|TB|PB)\s*(?:storage|disk)",
                "confidence": 0.9,
                "field": "specs.storage"
            },
            {
                "name": "cpu_spec",
                "pattern": r"(\d+)\s*(?:core|CPU|processor)",
                "confidence": 0.85,
                "field": "specs.cpu_cores"
            }
        ]
    
    def extract_from_text(self, text: str, page_type: str, url: str) -> ExtractionResult:
        """
        Extract structured data using rules-based patterns.
        
        Args:
            text: The page text to extract from
            page_type: Type of page (product, pricing, release, etc.)
            url: Source URL for context
            
        Returns:
            ExtractionResult with extracted entities
        """
        start_time = datetime.now()
        
        try:
            entities = {
                "Company": [],
                "Product": [],
                "Capability": [],
                "Release": [],
                "Document": [],
                "Signal": [],
                "Source": {}
            }
            
            confidence_scores = []
            
            # Extract based on page type
            if page_type.lower() in ["product", "pricing"]:
                product_data, product_confidence = self._extract_product(text, url)
                if product_data:
                    entities["Product"].append(product_data)
                    confidence_scores.append(product_confidence)
            
            elif page_type.lower() in ["release", "changelog"]:
                release_data, release_confidence = self._extract_release(text, url)
                if release_data:
                    entities["Release"].append(release_data)
                    confidence_scores.append(release_confidence)
            
            elif page_type.lower() in ["docs", "documentation"]:
                doc_data, doc_confidence = self._extract_document(text, url)
                if doc_data:
                    entities["Document"].append(doc_data)
                    confidence_scores.append(doc_confidence)
            
            # Always try to extract company info
            company_data, company_confidence = self._extract_company(text, url)
            if company_data:
                entities["Company"].append(company_data)
                confidence_scores.append(company_confidence)
            
            # Create source record
            entities["Source"] = {
                "url": url,
                "page_type": page_type,
                "method": "rules",
                "extracted_at": datetime.now().isoformat(),
                "confidence": max(confidence_scores) if confidence_scores else 0.0
            }
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # Only return success if we extracted something meaningful
            success = overall_confidence >= 0.6 and any(
                len(entities[key]) > 0 for key in ["Company", "Product", "Release", "Document"]
            )
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ExtractionResult(
                success=success,
                method="rules",
                entities=entities,
                confidence=overall_confidence,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Rules extraction failed: {e}")
            
            return ExtractionResult(
                success=False,
                method="rules",
                entities={},
                confidence=0.0,
                processing_time_ms=processing_time,
                error=str(e)
            )
    
    def _extract_product(self, text: str, url: str) -> Tuple[Optional[Dict], float]:
        """Extract product information from text."""
        product = {}
        confidence_scores = []
        
        # Extract product name
        for pattern_info in self.product_patterns:
            if pattern_info["field"] == "name":
                matches = re.findall(pattern_info["pattern"], text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Take the first substantial match
                    name = max(matches, key=len).strip()
                    if len(name) > 3:  # Avoid short false positives
                        product["name"] = name
                        confidence_scores.append(pattern_info["confidence"])
                        break
        
        # Extract pricing information
        pricing_data = {}
        for pattern_info in self.pricing_patterns:
            matches = re.findall(pattern_info["pattern"], text, re.IGNORECASE)
            if matches:
                pricing_data[pattern_info["name"]] = matches[0] if len(matches) == 1 else matches
                confidence_scores.append(pattern_info["confidence"])
        
        if pricing_data:
            product["pricing"] = pricing_data
        
        # Extract specifications
        specs = {}
        for pattern_info in self.spec_patterns:
            matches = re.findall(pattern_info["pattern"], text, re.IGNORECASE)
            if matches:
                field_parts = pattern_info["field"].split(".")
                if len(field_parts) == 2 and field_parts[0] == "specs":
                    specs[field_parts[1]] = {
                        "type": "text",
                        "value": f"{matches[0][0]} {matches[0][1]}" if isinstance(matches[0], tuple) else matches[0]
                    }
                    confidence_scores.append(pattern_info["confidence"])
        
        if specs:
            product["specs"] = specs
        
        # Add required fields with defaults
        if product:
            product.update({
                "id": f"prod_{hash(product.get('name', url)) % 100000}",
                "company_id": "unknown",  # Will be resolved later
                "category": "unknown",
                "stage": "unknown",
                "markets": [],
                "tags": []
            })
        
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return product if product else None, overall_confidence
    
    def _extract_release(self, text: str, url: str) -> Tuple[Optional[Dict], float]:
        """Extract release information from text."""
        release = {}
        confidence_scores = []
        
        # Extract version
        for pattern_info in self.release_patterns:
            if pattern_info["field"] == "version":
                matches = re.findall(pattern_info["pattern"], text, re.IGNORECASE)
                if matches:
                    release["version"] = matches[0]
                    release["name"] = f"Version {matches[0]}"
                    confidence_scores.append(pattern_info["confidence"])
                    break
        
        # Extract release date
        for pattern_info in self.release_patterns:
            if pattern_info["field"] == "date":
                matches = re.findall(pattern_info["pattern"], text, re.IGNORECASE)
                if matches:
                    release["date"] = matches[0]
                    confidence_scores.append(pattern_info["confidence"])
                    break
        
        # Extract release notes
        for pattern_info in self.release_patterns:
            if pattern_info["field"] == "notes":
                matches = re.findall(pattern_info["pattern"], text, re.IGNORECASE | re.DOTALL)
                if matches:
                    if isinstance(matches[0], tuple):
                        release["version"] = matches[0][0]
                        release["notes"] = matches[0][1].strip()
                    else:
                        release["notes"] = matches[0].strip()
                    confidence_scores.append(pattern_info["confidence"])
                    break
        
        # Add required fields
        if release:
            release.update({
                "id": f"rel_{hash(release.get('version', url)) % 100000}",
                "name": release.get("name", f"Release {release.get('version', 'Unknown')}")
            })
        
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return release if release else None, overall_confidence
    
    def _extract_company(self, text: str, url: str) -> Tuple[Optional[Dict], float]:
        """Extract company information from text."""
        company = {}
        confidence = 0.0
        
        # Extract company name from URL domain
        domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
        if domain_match:
            domain = domain_match.group(1)
            # Convert domain to company name (heuristic)
            company_name = domain.split('.')[0].replace('-', ' ').title()
            company.update({
                "id": f"comp_{hash(domain) % 100000}",
                "name": company_name,
                "aliases": [domain],
                "website": f"https://{domain}",
                "status": "active",
                "tags": []
            })
            confidence = 0.7  # Medium confidence for domain-based extraction
        
        return company if company else None, confidence
    
    def _extract_document(self, text: str, url: str) -> Tuple[Optional[Dict], float]:
        """Extract document information from text."""
        # Extract title from first heading or URL
        title_match = re.search(r"^#\s*(.+)$", text, re.MULTILINE)
        if not title_match:
            title_match = re.search(r"<h1[^>]*>([^<]+)</h1>", text, re.IGNORECASE)
        
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Fallback to URL-based title
            title = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        
        # Determine document type from URL patterns
        doc_type = "unknown"
        if any(pattern in url.lower() for pattern in ["api", "reference"]):
            doc_type = "api"
        elif any(pattern in url.lower() for pattern in ["whitepaper", "white-paper"]):
            doc_type = "whitepaper"
        elif any(pattern in url.lower() for pattern in ["datasheet", "spec"]):
            doc_type = "datasheet"
        elif any(pattern in url.lower() for pattern in ["manual", "guide"]):
            doc_type = "manual"
        elif any(pattern in url.lower() for pattern in ["blog", "news"]):
            doc_type = "blog"
        
        document = {
            "id": f"doc_{hash(url) % 100000}",
            "title": title,
            "doc_type": doc_type,
            "url": url
        }
        
        return document, 0.8  # High confidence for document extraction


class AIExtractor:
    """
    AI-based extraction using Theta EdgeCloud.
    Fallback for complex extraction when rules fail.
    """
    
    def __init__(self, theta_client: ThetaClient):
        self.theta_client = theta_client
        self.schema_compactor = get_schema_compactor()
    
    async def extract_from_text(
        self, 
        text: str, 
        page_type: str, 
        competitor: str, 
        url: str, 
        content_hash: str,
        session_id: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract structured data using AI.
        
        Args:
            text: The page text to extract from
            page_type: Type of page for schema selection
            competitor: Competitor name for caching
            url: Source URL
            content_hash: Content hash for caching
            session_id: Session ID for rate limiting
            
        Returns:
            ExtractionResult with extracted entities
        """
        start_time = datetime.now()
        
        try:
            # Build extraction prompt
            prompt = self.schema_compactor.build_extraction_prompt(
                text=text,
                page_type=page_type,
                competitor=competitor,
                url=url,
                content_hash=content_hash,
                schema_version=settings.SCHEMA_VERSION
            )
            
            # Validate prompt size
            prompt_validation = self.schema_compactor.validate_prompt_size(prompt)
            if not prompt_validation["within_limits"]:
                logger.warning(f"Prompt exceeds token limit: {prompt_validation}")
                # Truncate text more aggressively
                max_text_tokens = int(prompt_validation["max_tokens"] * 0.7)  # Leave more headroom
                truncated_text = TokenCounter.truncate_to_tokens(text, max_text_tokens)
                prompt = self.schema_compactor.build_extraction_prompt(
                    text=truncated_text,
                    page_type=page_type,
                    competitor=competitor,
                    url=url,
                    content_hash=content_hash,
                    schema_version=settings.SCHEMA_VERSION
                )
            
            # Make AI request
            response = await self.theta_client.complete(
                prompt=prompt,
                schema_version=settings.SCHEMA_VERSION,
                page_type=page_type,
                competitor=competitor,
                session_id=session_id,
                use_cache=True
            )
            
            # Validate response structure
            if "entities" not in response:
                raise ValueError("AI response missing 'entities' field")
            
            entities = response["entities"]
            
            # Validate each entity type against schemas
            validation_errors = []
            for entity_type, entity_list in entities.items():
                if entity_type == "Source":
                    # Source is a single object, not a list
                    if isinstance(entity_list, dict):
                        try:
                            validate_payload("Source", entity_list, strict=False)
                        except SchemaValidationError as e:
                            validation_errors.append(f"Source validation: {e}")
                elif isinstance(entity_list, list):
                    for i, entity in enumerate(entity_list):
                        try:
                            validate_payload(entity_type, entity, strict=False)
                        except SchemaValidationError as e:
                            validation_errors.append(f"{entity_type}[{i}] validation: {e}")
            
            if validation_errors:
                logger.warning(f"Validation errors in AI response: {validation_errors}")
            
            # Extract confidence from Source
            source_confidence = entities.get("Source", {}).get("confidence", 0.5)
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ExtractionResult(
                success=True,
                method="ai",
                entities=entities,
                confidence=source_confidence,
                processing_time_ms=processing_time,
                tokens_input=prompt_validation.get("estimated_tokens"),
                tokens_output=None,  # Would need to parse from Theta response
                cache_hit=False  # Would need to track in theta_client
            )
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"AI extraction failed: {e}")
            
            return ExtractionResult(
                success=False,
                method="ai",
                entities={},
                confidence=0.0,
                processing_time_ms=processing_time,
                error=str(e)
            )


class ExtractionService:
    """
    Main extraction service coordinating rules-first + AI fallback strategy.
    """
    
    def __init__(self, theta_client: ThetaClient):
        self.rules_extractor = RulesExtractor()
        self.ai_extractor = AIExtractor(theta_client)
        self.confidence_threshold = 0.6  # Threshold for rules success
    
    async def extract_structured_from_text(
        self,
        raw_text: str,
        url: str,
        page_type: str,
        competitor: str,
        content_hash: str,
        session_id: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract structured data using rules-first + AI fallback strategy.
        
        Args:
            raw_text: Raw page text to extract from
            url: Source URL
            page_type: Page type classification
            competitor: Competitor name
            content_hash: Content hash for caching
            session_id: Session ID for rate limiting
            
        Returns:
            ExtractionResult with extracted entities and metadata
        """
        logger.info(f"Starting extraction for {url} (type: {page_type}, competitor: {competitor})")
        
        # Step 1: Try rules-first extraction
        rules_result = self.rules_extractor.extract_from_text(raw_text, page_type, url)
        
        if rules_result.success and rules_result.confidence >= self.confidence_threshold:
            logger.info(f"Rules extraction succeeded with confidence {rules_result.confidence:.2f}")
            return rules_result
        
        # Step 2: Fallback to AI extraction
        logger.info(f"Rules extraction failed/low confidence ({rules_result.confidence:.2f}), falling back to AI")
        
        ai_result = await self.ai_extractor.extract_from_text(
            text=raw_text,
            page_type=page_type,
            competitor=competitor,
            url=url,
            content_hash=content_hash,
            session_id=session_id
        )
        
        if ai_result.success:
            logger.info(f"AI extraction succeeded with confidence {ai_result.confidence:.2f}")
            return ai_result
        
        # Step 3: Both failed, return the better of the two
        if rules_result.confidence > ai_result.confidence:
            logger.warning(f"Both extractions failed, returning rules result (confidence: {rules_result.confidence:.2f})")
            return rules_result
        else:
            logger.warning(f"Both extractions failed, returning AI result (confidence: {ai_result.confidence:.2f})")
            return ai_result
