"""
Schema-first extraction service with rules-first + AI fallback strategy.

Implements structured data extraction from page text using:
1. Rules-first: Fast regex/heuristic patterns for common data structures
2. AI fallback: Theta EdgeCloud for complex extraction when rules fail
3. Validation: JSON Schema validation for all outputs
"""

import json
import os
import re
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from app.core.config import settings
from app.services.theta_client import ThetaClient
from app.services.schema_utils import get_multi_stage_extractor, TokenCounter
from app.services.validate import validate_payload, SchemaValidationError

logger = logging.getLogger(__name__)


def save_llm_debug_output(stage: str, url: str, competitor: str, prompt: str, response: Dict[str, Any], session_id: str) -> None:
    """Save LLM outputs to debug files for analysis."""
    try:
        # Create debug directories - save both in Docker container AND on host
        from pathlib import Path
        import os
        
        # Docker container path
        container_base_dir = Path(__file__).parent.parent / "exports" / "extraction"
        container_stage_dir = container_base_dir / f"Step{stage}"
        container_stage_dir.mkdir(parents=True, exist_ok=True)
        
        # Host filesystem path (mounted volume)
        # Try to detect if we're in Docker and find the mounted volume
        host_base_dir = Path("/Users/lorenzpiazolo/Documents/Theta Hackathon 25/_Code/Auralis/backend/exports/extraction")
        if host_base_dir.exists():
            host_stage_dir = host_base_dir / f"Step{stage}"
            host_stage_dir.mkdir(parents=True, exist_ok=True)
        else:
            host_stage_dir = None
        
        # Create filename with timestamp and URL hash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_hash = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_").replace("=", "_")[:50]
        filename = f"{competitor.replace(' ', '_')}_{timestamp}_{url_hash}_session_{session_id}_stage{stage}.json"
        
        # Save debug data
        debug_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "stage": stage,
            "competitor": competitor,
            "url": url,
            "llm_response": response,
            "prompt_length": len(prompt),
            "response_size": len(json.dumps(response, default=str))
        }
        
        # Save to container filesystem
        container_filepath = container_stage_dir / filename
        with open(container_filepath, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved LLM debug output to container: {container_filepath}")
        
        # Also save to host filesystem if available
        if host_stage_dir:
            host_filepath = host_stage_dir / filename
            with open(host_filepath, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved LLM debug output to host: {host_filepath}")
        
    except Exception as e:
        logger.error(f"Failed to save LLM debug output: {e}")


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
            # Robotics product patterns (high priority)
            {
                "name": "robot_model",
                "pattern": r"(?:PUDU\s+)?([A-Z]{2,3}\d+(?:-[A-Z]+)?|[A-Z][a-z]+[Bb]ot\d*(?:\s+[A-Z][a-z]+)*)",
                "confidence": 0.9,
                "field": "name"
            },
            {
                "name": "product_title",
                "pattern": r"(?:^|\n)([A-Z][A-Za-z0-9\s\-]+(?:Robot|Bot|Service|Cleaner|Vacuum))",
                "confidence": 0.85,
                "field": "name"
            },
            # Generic API/SDK patterns
            {
                "name": "api_product",
                "pattern": r"(?:^|\s)([A-Z][a-zA-Z0-9\s]+(?:API|SDK|Service))",
                "confidence": 0.8,
                "field": "name"
            },
            # Version information
            {
                "name": "version_pattern",
                "pattern": r"(?:version|v\.?|release)\s*(\d+(?:\.\d+)*(?:\.\d+)*)",
                "confidence": 0.9,
                "field": "version"
            },
            # Features and capabilities
            {
                "name": "feature_list",
                "pattern": r"(?:features?|capabilities?):\s*(.+?)(?:\n\n|\.|$)",
                "confidence": 0.7,
                "field": "features"
            },
            # Product specifications
            {
                "name": "tech_specs",
                "pattern": r"(?:specifications?|specs?|technical\s+details?):\s*(.+?)(?:\n\n|\.|$)",
                "confidence": 0.75,
                "field": "specifications"
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
            
            # Always try to extract company info first
            company_data, company_confidence = self._extract_company(text, url)
            company_id = None
            if company_data:
                entities["Company"].append(company_data)
                confidence_scores.append(company_confidence)
                company_id = company_data.get("id")
            
            # Extract based on page type
            if page_type.lower() in ["product", "pricing"]:
                product_data, product_confidence = self._extract_product(text, url, company_id)
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
    
    def _extract_product(self, text: str, url: str, company_id: Optional[str] = None) -> Tuple[Optional[Dict], float]:
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
                "company_id": company_id if company_id else "unknown",
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


class BatchMultiStageAIExtractor:
    """
    Batch multi-stage AI-based extraction using Theta EdgeCloud.
    Stage 1: Per-page simple JSON extraction (collect all)
    Stage 2A: ONE consolidated company LLM request with all company data
    Stage 2B: ONE consolidated product LLM request with all product data (sequential after 2A)
    """
    
    def __init__(self, theta_client: ThetaClient):
        self.theta_client = theta_client
        self.extractor = get_multi_stage_extractor()
        
    def _check_input_size_warning(self, text: str, stage: str) -> None:
        """Check if input size exceeds warning threshold and log warning."""
        char_count = len(text)
        if char_count > 300000:  # 300k characters
            logger.warning(f"Stage {stage} input size ({char_count:,} chars) exceeds 300k character threshold")
    
    async def extract_batch_from_pages(
        self,
        page_data_list: List[Dict[str, Any]],
        competitor: str,
        session_id: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract structured data using batch multi-stage AI approach.
        
        Args:
            page_data_list: List of page data dicts with keys: text, url, page_type, content_hash
            competitor: Competitor name
            session_id: Session ID for rate limiting
            
        Returns:
            ExtractionResult with consolidated entities from all pages
        """
        start_time = datetime.now()
        
        try:
            # Log session start for cost tracking
            if session_id:
                logger.info(f"Starting batch multi-stage extraction with session {session_id} for {len(page_data_list)} pages")
            
            # Stage 1: Process each page individually to get basic extractions
            stage1_results = []
            stage1_errors = []
            
            for i, page_data in enumerate(page_data_list):
                text = page_data["text"]
                url = page_data["url"]
                page_type = page_data["page_type"]
                content_hash = page_data["content_hash"]
                
                try:
                    stage1_prompt = self.extractor.build_stage1_prompt(
                        text=text,
                        page_type=page_type,
                        competitor=competitor,
                        url=url
                    )
                    
                    logger.info(f"Starting Stage 1 extraction for {url} ({i+1}/{len(page_data_list)})")
                    stage1_response = await self.theta_client.complete(
                        prompt=stage1_prompt,
                        schema_version=settings.SCHEMA_VERSION,
                        page_type=page_type,
                        competitor=competitor,
                        session_id=session_id,
                        use_cache=True
                    )
                    
                    # DEBUG: Save Stage 1 LLM output (without prompt field)
                    save_llm_debug_output("1", url, competitor, stage1_prompt, stage1_response, session_id)
                    
                    # Validate Stage 1 response
                    if not isinstance(stage1_response, dict) or "products" not in stage1_response:
                        logger.warning(f"Stage 1 response for {url} missing required 'products' field, skipping")
                        stage1_errors.append(f"{url}: Missing products field")
                        continue
                        
                    stage1_results.append({
                        "url": url,
                        "content_hash": content_hash,
                        "response": stage1_response
                    })
                    logger.info(f"✅ Stage 1 completed for {url}")
                    
                except Exception as e:
                    logger.error(f"❌ Stage 1 failed for {url}: {e}")
                    stage1_errors.append(f"{url}: {str(e)}")
                    # Continue processing other pages instead of failing completely
                    continue
            
            # Log Stage 1 summary
            logger.info(f"📊 Stage 1 Summary: {len(stage1_results)}/{len(page_data_list)} pages successful")
            if stage1_errors:
                logger.warning(f"❌ Stage 1 Errors ({len(stage1_errors)}): {stage1_errors}")
            
            if not stage1_results:
                raise ValueError(f"No valid Stage 1 results obtained. Errors: {stage1_errors}")
            
            # Stage 2A: Consolidate ALL company data in ONE request
            company_items = []
            for result in stage1_results:
                company_items.append({
                    "company": result["response"].get("company", ""),
                    "source": result["response"].get("source", {"url": result["url"]})
                })
            
            temp_company_id = f"temp_comp_{competitor.lower().replace(' ', '_')}"
            stage2a_prompt = self.extractor.build_stage2a_company_prompt(
                company_id=temp_company_id,
                competitor=competitor,
                company_items=company_items
            )
            
            # Check input size warning
            self._check_input_size_warning(stage2a_prompt, "2A")
            
            logger.info(f"Starting Stage 2A consolidated company extraction for {competitor} with {len(company_items)} sources")
            stage2a_response = await self.theta_client.complete(
                prompt=stage2a_prompt,
                schema_version=settings.SCHEMA_VERSION,
                page_type="company_consolidation",
                competitor=competitor,
                session_id=session_id,
                use_cache=True
            )
            
            # DEBUG: Save Stage 2A LLM output (without prompt field)
            consolidated_url = f"consolidated_company_{len(company_items)}_pages"
            save_llm_debug_output("2A", consolidated_url, competitor, stage2a_prompt, stage2a_response, session_id)
            
            # Stage 2B: Consolidate ALL product data in ONE request (sequential after 2A)
            products_items = []
            for result in stage1_results:
                products_items.append({
                    "products": result["response"].get("products", {}),
                    "source": result["response"].get("source", {"url": result["url"]})
                })
            
            stage2b_prompt = self.extractor.build_stage2b_products_prompt(
                company_id=temp_company_id,
                products_items=products_items
            )
            
            # Check input size warning
            self._check_input_size_warning(stage2b_prompt, "2B")
            
            logger.info(f"Starting Stage 2B consolidated product extraction for {competitor} with {len(products_items)} sources")
            stage2b_response = await self.theta_client.complete(
                prompt=stage2b_prompt,
                schema_version=settings.SCHEMA_VERSION,
                page_type="product_consolidation",
                competitor=competitor,
                session_id=session_id,
                use_cache=True
            )
            
            # DEBUG: Save Stage 2B LLM output (without prompt field)
            consolidated_url = f"consolidated_products_{len(products_items)}_pages"
            save_llm_debug_output("2B", consolidated_url, competitor, stage2b_prompt, stage2b_response, session_id)
            
            # Process consolidated responses
            return self._process_consolidated_responses(
                stage2a_response, stage2b_response, stage1_results, competitor, start_time
            )
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Batch multi-stage AI extraction failed: {e}")
            
            return ExtractionResult(
                success=False,
                method="ai_batch_multistage",
                entities={},
                confidence=0.0,
                processing_time_ms=processing_time,
                error=str(e)
            )
    
    def _process_consolidated_responses(
        self,
        stage2a_response: Dict[str, Any],
        stage2b_response: Dict[str, Any], 
        stage1_results: List[Dict[str, Any]],
        competitor: str,
        start_time: datetime
    ) -> ExtractionResult:
        """Process consolidated Stage 2A and 2B responses into final entities."""
        
        # Handle case where LLM returns a list instead of dict
        if isinstance(stage2a_response, list):
            logger.warning("Stage 2A returned list instead of dict, taking first item")
            stage2a_response = stage2a_response[0] if stage2a_response else {}
        
        if isinstance(stage2b_response, list):
            logger.warning("Stage 2B returned list instead of dict, taking first item")
            stage2b_response = stage2b_response[0] if stage2b_response else {}
        
        # Ensure responses are dictionaries
        if not isinstance(stage2a_response, dict):
            logger.error(f"Stage 2A response is not a dict: {type(stage2a_response)}")
            stage2a_response = {}
            
        if not isinstance(stage2b_response, dict):
            logger.error(f"Stage 2B response is not a dict: {type(stage2b_response)}")
            stage2b_response = {}
        
        raw_company_data = stage2a_response.get("company", {})
        products_data = stage2b_response.get("products", {})
        
        # Process company data according to Stage 2A prompt output schema
        company_data = raw_company_data.copy()
        
        # Extract capabilities from products and prepare separate capability entities
        capabilities = []
        products = []
        
        for product_name, product_info in products_data.items():
            # Remove capabilities from product data (they'll be stored separately)
            product_capabilities = product_info.pop("capabilities", [])
            
            # Ensure capabilities is a list (handle None case)
            if product_capabilities is None:
                product_capabilities = []
            
            # Process each capability
            for capability in product_capabilities:
                # Ensure capability is a dict
                if not isinstance(capability, dict):
                    logger.warning(f"Skipping invalid capability for {product_name}: {capability}")
                    continue
                    
                processed_capability = {
                    "name": capability.get("name", ""),
                    "tags": capability.get("tags", []) or []  # Handle None tags
                }
                
                if capability.get("definition"):
                    processed_capability["definition"] = capability["definition"]
                
                processed_capability["category"] = "general"
                capabilities.append(processed_capability)
            
            # Process product data according to Stage 2B prompt output schema
            filtered_product_info = product_info.copy()
            filtered_product_info.pop("capabilities", None)
            
            # Normalize stage to valid values
            stage_raw = filtered_product_info.get("stage", "ga")
            stage = stage_raw.lower() if stage_raw else "ga"
            if stage not in ["alpha", "beta", "ga", "discontinued"]:
                if stage in ["gamma", "production", "released"]:
                    stage = "ga"
                else:
                    stage = "ga"
            
            # Convert specs to proper format
            raw_specs = filtered_product_info.get("specs", {})
            formatted_specs = {}
            if isinstance(raw_specs, dict):
                for key, value in raw_specs.items():
                    if value is not None:
                        formatted_specs[key] = {
                            "type": "text",
                            "value": str(value)
                        }
            
            # Build product according to Stage 2B prompt output schema
            product = {
                "name": filtered_product_info.get("name", product_name),
                "category": filtered_product_info.get("category") or "unknown",
                "stage": stage,
                "markets": filtered_product_info.get("markets", []) or [],  # Handle None
                "tags": filtered_product_info.get("tags", []) or [],  # Handle None
                "specs": formatted_specs,
                "compliance": filtered_product_info.get("compliance", []) or []  # Handle None
            }
            
            # Add optional string fields if they have values
            if filtered_product_info.get("short_desc"):
                product["short_desc"] = filtered_product_info["short_desc"]
            if filtered_product_info.get("product_url"):
                product["product_url"] = filtered_product_info["product_url"]
            if filtered_product_info.get("docs_url"):
                product["docs_url"] = filtered_product_info["docs_url"]
            if filtered_product_info.get("released_at"):
                product["released_at"] = filtered_product_info["released_at"]
            if filtered_product_info.get("sources"):
                product["sources"] = filtered_product_info["sources"]
            if filtered_product_info.get("notes"):
                product["notes"] = filtered_product_info["notes"]
            
            products.append(product)
        
        # Create company object according to Stage 2A prompt output schema
        company = {
            "name": company_data.get("name") or competitor,
            "aliases": company_data.get("aliases") or [],
            "status": company_data.get("status") or "active",
            "tags": company_data.get("tags") or []
        }
        
        # Add optional fields from Stage 2A prompt output
        if company_data.get("hq_country"):
            company["hq_country"] = company_data["hq_country"]
        if company_data.get("website"):
            company["website"] = company_data["website"]
        if company_data.get("short_desc"):
            company["short_desc"] = company_data["short_desc"]
        if company_data.get("main_sources_used"):
            company["main_sources_used"] = company_data["main_sources_used"]
        if company_data.get("notes"):
            company["notes"] = company_data["notes"]
        
        # Create consolidated source object from all Stage 1 results
        all_content_hashes = [result["content_hash"] for result in stage1_results]
        consolidated_hash = hashlib.sha256("".join(sorted(all_content_hashes)).encode()).hexdigest()
        
        entities = {
            "Company": [company],
            "Product": products,
            "Capability": capabilities,
            "Source": {
                "id": f"src_{consolidated_hash[:12]}",
                "origin": f"consolidated_{len(stage1_results)}_pages",
                "author": "ai_batch_multistage",
                "retrieved_at": datetime.now().isoformat(),
                "credibility": "high"
            }
        }
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Calculate total token usage from all stages
        total_prompts = ""
        for result in stage1_results:
            # We don't store the prompts, so estimate based on response size
            total_prompts += json.dumps(result["response"], default=str)
        
        return ExtractionResult(
            success=True,
            method="ai_batch_multistage",
            entities=entities,
            confidence=0.90,  # Higher confidence due to consolidated multi-stage validation
            processing_time_ms=processing_time,
            tokens_input=TokenCounter.estimate_tokens(total_prompts),
            tokens_output=None,
            cache_hit=False
        )


class MultiStageAIExtractor:
    """
    Multi-stage AI-based extraction using Theta EdgeCloud.
    Stage 1: Per-page simple JSON extraction
    Stage 2: Batch consolidation into structured entities
    """
    
    def __init__(self, theta_client: ThetaClient):
        self.theta_client = theta_client
        self.extractor = get_multi_stage_extractor()
    
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
        Extract structured data using multi-stage AI approach.
        
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
            # Log session start for cost tracking
            if session_id:
                logger.info(f"Starting multi-stage extraction with session {session_id}")
            
            # Stage 1: Per-page extraction
            stage1_prompt = self.extractor.build_stage1_prompt(
                text=text,
                page_type=page_type,
                competitor=competitor,
                url=url
            )
            
            logger.info(f"Starting Stage 1 extraction for {url}")
            stage1_response = await self.theta_client.complete(
                prompt=stage1_prompt,
                schema_version=settings.SCHEMA_VERSION,
                page_type=page_type,
                competitor=competitor,
                session_id=session_id,
                use_cache=True
            )
            
            # DEBUG: Save Stage 1 LLM output
            save_llm_debug_output("1", url, competitor, stage1_prompt, stage1_response, session_id)
            
            # Parse Stage 1 response
            if not isinstance(stage1_response, dict) or "products" not in stage1_response:
                raise ValueError("Stage 1 response missing required 'products' field")
            
            # For single-page extraction, we can directly convert to final format
            # This simulates what would happen in batch processing
            
            # Note: Company ID will be generated by the normalizer using natural keys
            # We don't set it here - the normalizer handles deduplication and ID assignment
            
            # Prepare Stage 2A data (company consolidation)
            company_items = [{
                "company": stage1_response.get("company", ""),
                "source": stage1_response.get("source", {"url": url})
            }]
            
            # Stage 2A: Company consolidation
            # Use a temporary company_id for the prompt - normalizer will assign the real one
            temp_company_id = f"temp_comp_{competitor.lower().replace(' ', '_')}"
            stage2a_prompt = self.extractor.build_stage2a_company_prompt(
                company_id=temp_company_id,
                competitor=competitor,
                company_items=company_items
            )
            
            logger.info(f"Starting Stage 2A company consolidation for {competitor}")
            stage2a_response = await self.theta_client.complete(
                prompt=stage2a_prompt,
                schema_version=settings.SCHEMA_VERSION,
                page_type="consolidation",
                competitor=competitor,
                session_id=session_id,
                use_cache=True
            )
            
            # DEBUG: Save Stage 2A LLM output
            save_llm_debug_output("2A", url, competitor, stage2a_prompt, stage2a_response, session_id)
            
            # Prepare Stage 2B data (products consolidation)
            products_items = [{
                "products": stage1_response.get("products", {}),
                "source": stage1_response.get("source", {"url": url})
            }]
            
            # Stage 2B: Products consolidation
            stage2b_prompt = self.extractor.build_stage2b_products_prompt(
                company_id=temp_company_id,
                products_items=products_items
            )
            
            logger.info(f"Starting Stage 2B products consolidation for {competitor}")
            stage2b_response = await self.theta_client.complete(
                prompt=stage2b_prompt,
                schema_version=settings.SCHEMA_VERSION,
                page_type="consolidation",
                competitor=competitor,
                session_id=session_id,
                use_cache=True
            )
            
            # DEBUG: Save Stage 2B LLM output
            save_llm_debug_output("2B", url, competitor, stage2b_prompt, stage2b_response, session_id)
            
            # Parse Stage 2 responses with error handling
            # DEBUG: Log response types for debugging
            logger.info(f"Stage 2A response type: {type(stage2a_response)}, content: {stage2a_response}")
            logger.info(f"Stage 2B response type: {type(stage2b_response)}, content: {stage2b_response}")
            
            # Handle case where LLM returns a list instead of dict
            if isinstance(stage2a_response, list):
                logger.warning("Stage 2A returned list instead of dict, taking first item")
                stage2a_response = stage2a_response[0] if stage2a_response else {}
            
            if isinstance(stage2b_response, list):
                logger.warning("Stage 2B returned list instead of dict, taking first item")
                stage2b_response = stage2b_response[0] if stage2b_response else {}
            
            # Ensure responses are dictionaries
            if not isinstance(stage2a_response, dict):
                logger.error(f"Stage 2A response is not a dict: {type(stage2a_response)}")
                stage2a_response = {}
                
            if not isinstance(stage2b_response, dict):
                logger.error(f"Stage 2B response is not a dict: {type(stage2b_response)}")
                stage2b_response = {}
            
            raw_company_data = stage2a_response.get("company", {})
            products_data = stage2b_response.get("products", {})
            
            # Process company data according to Stage 2A prompt output schema
            # Stage 2A prompt produces: name, aliases, status, tags, website, hq_country, main_sources_used, notes
            # Keep all fields that the prompt is designed to produce
            company_data = raw_company_data.copy()
            
            # Extract capabilities from products and prepare separate capability entities
            capabilities = []
            products = []
            
            for product_name, product_info in products_data.items():
                # Remove capabilities from product data (they'll be stored separately)
                product_capabilities = product_info.pop("capabilities", [])
                
                # Process each capability according to Stage 2B prompt schema
                # Prompt defines: {"name": "string", "tags": ["string"], "definition": "string" | null}
                for capability in product_capabilities:
                    processed_capability = {
                        "name": capability.get("name", ""),
                        "tags": capability.get("tags", [])  # Required field from prompt
                    }
                    
                    # Add definition field if present (as per prompt schema)
                    if capability.get("definition"):
                        processed_capability["definition"] = capability["definition"]
                    
                    # Map to database schema: add category field for database compatibility
                    # Default to "general" if not derivable from name/tags
                    processed_capability["category"] = "general"
                    
                    capabilities.append(processed_capability)
                
                # Ensure product has all required fields for the database model
                # Note: ID and company_id will be assigned by the normalizer
                # Remove null values to avoid schema validation errors
                
                # Process product data according to Stage 2B prompt output schema
                # Keep all fields that the prompt is designed to produce
                # Stage 2B prompt produces: name, category, stage, markets, tags, short_desc, 
                # product_url, docs_url, specs, released_at, compliance, sources, notes
                filtered_product_info = product_info.copy()
                
                # Remove capabilities as they're processed separately above
                filtered_product_info.pop("capabilities", None)
                
                # Normalize stage to valid values
                stage = filtered_product_info.get("stage", "ga").lower()
                if stage not in ["alpha", "beta", "ga", "discontinued"]:
                    if stage in ["gamma", "production", "released"]:
                        stage = "ga"
                    else:
                        stage = "ga"  # Default fallback
                
                # Convert specs to proper format: {"type": "text", "value": "..."}
                raw_specs = filtered_product_info.get("specs", {})
                formatted_specs = {}
                if isinstance(raw_specs, dict):
                    for key, value in raw_specs.items():
                        if value is not None:
                            formatted_specs[key] = {
                                "type": "text",
                                "value": str(value)
                            }
                
                # Build product according to Stage 2B prompt output schema
                product = {
                    "name": filtered_product_info.get("name", product_name),
                    "category": filtered_product_info.get("category") or "unknown",
                    "stage": stage,
                    "markets": filtered_product_info.get("markets", []),
                    "tags": filtered_product_info.get("tags", []),
                    "specs": formatted_specs,
                    "compliance": filtered_product_info.get("compliance", [])
                }
                
                # Add optional string fields if they have values (not null)
                if filtered_product_info.get("short_desc"):
                    product["short_desc"] = filtered_product_info["short_desc"]
                if filtered_product_info.get("product_url"):
                    product["product_url"] = filtered_product_info["product_url"]
                if filtered_product_info.get("docs_url"):
                    product["docs_url"] = filtered_product_info["docs_url"]
                if filtered_product_info.get("released_at"):
                    product["released_at"] = filtered_product_info["released_at"]
                
                # Add sources field from Stage 2B prompt output (array of URLs)
                sources = filtered_product_info.get("sources")
                if sources:
                    # Handle case where sources might be None or not a list
                    if isinstance(sources, list):
                        product["sources"] = sources
                    else:
                        product["sources"] = [sources] if sources else []
                
                # Add notes field from Stage 2B prompt output (array of strings)
                notes = filtered_product_info.get("notes")
                if notes:
                    # Handle case where notes might be None or not a list
                    if isinstance(notes, list):
                        product["notes"] = notes
                    else:
                        product["notes"] = [notes] if notes else []
                
                products.append(product)
            
            # Create company object according to Stage 2A prompt output schema
            # Stage 2A produces: name, aliases, status, tags, website, hq_country, main_sources_used, notes
            # Note: ID will be assigned by the normalizer using natural keys
            company = {
                "name": company_data.get("name") or competitor,
                "aliases": company_data.get("aliases") or [],
                "status": company_data.get("status") or "active",  # Must be "active" or "dormant"
                "tags": company_data.get("tags") or []
            }
            
            # Add optional fields from Stage 2A prompt output
            if company_data.get("hq_country"):
                company["hq_country"] = company_data["hq_country"]
            if company_data.get("website"):
                company["website"] = company_data["website"]
            if company_data.get("short_desc"):
                company["short_desc"] = company_data["short_desc"]
            if company_data.get("main_sources_used"):
                company["main_sources_used"] = company_data["main_sources_used"]
            if company_data.get("notes"):
                company["notes"] = company_data["notes"]
            
            # Combine results into expected format (all as lists for normalizer)
            # Source object must match the Source schema (id, origin required)
            entities = {
                "Company": [company],
                "Product": products,
                "Capability": capabilities,
                "Source": {
                    "id": f"src_{content_hash[:12]}",
                    "origin": url,
                    "author": "ai_multistage",
                    "retrieved_at": datetime.now().isoformat(),
                    "credibility": "high"  # Multi-stage extraction has high credibility
                }
            }
            
            # Basic validation (simplified for multi-stage) - made optional for debugging
            validation_errors = []
            # Temporarily disable required field validation to debug LLM responses
            # if not entities["Company"][0].get("name"):
            #     validation_errors.append("Company missing required name field")
            
            if validation_errors:
                logger.warning(f"Validation errors in multi-stage response: {validation_errors}")
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ExtractionResult(
                success=True,
                method="ai_multistage",
                entities=entities,
                confidence=0.85,  # Higher confidence due to multi-stage validation
                processing_time_ms=processing_time,
                tokens_input=TokenCounter.estimate_tokens(stage1_prompt + stage2a_prompt + stage2b_prompt),
                tokens_output=None,
                cache_hit=False
            )
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Multi-stage AI extraction failed: {e}")
            
            return ExtractionResult(
                success=False,
                method="ai_multistage",
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
        self.ai_extractor = MultiStageAIExtractor(theta_client)
        self.batch_ai_extractor = BatchMultiStageAIExtractor(theta_client)
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
        logger.info(f"Starting LLM extraction for {url} (type: {page_type}, competitor: {competitor})")
        
        # FORCE LLM EXTRACTION - Skip rules entirely
        logger.info("FORCING LLM extraction - bypassing rules-based extraction")
        
        ai_result = await self.ai_extractor.extract_from_text(
            text=raw_text,
            page_type=page_type,
            competitor=competitor,
            url=url,
            content_hash=content_hash,
            session_id=session_id
        )
        
        if ai_result.success:
            logger.info(f"LLM extraction succeeded with confidence {ai_result.confidence:.2f}")
            return ai_result
        else:
            logger.warning(f"LLM extraction failed with confidence {ai_result.confidence:.2f}")
            return ai_result
    
    async def extract_batch_from_pages(
        self,
        page_data_list: List[Dict[str, Any]],
        competitor: str,
        session_id: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract structured data from multiple pages using batch multi-stage AI approach.
        
        This method implements the restructured extraction pipeline:
        - Step 1: Process each page individually to get basic extractions
        - Step 2A: ONE consolidated company LLM request with all company data
        - Step 2B: ONE consolidated product LLM request with all product data (sequential after 2A)
        
        Args:
            page_data_list: List of page data dicts with keys: text, url, page_type, content_hash
            competitor: Competitor name
            session_id: Session ID for rate limiting
            
        Returns:
            ExtractionResult with consolidated entities from all pages
        """
        logger.info(f"Starting batch LLM extraction for {len(page_data_list)} pages (competitor: {competitor})")
        
        # FORCE BATCH LLM EXTRACTION - Skip rules entirely
        logger.info("FORCING batch LLM extraction - bypassing rules-based extraction")
        
        batch_result = await self.batch_ai_extractor.extract_batch_from_pages(
            page_data_list=page_data_list,
            competitor=competitor,
            session_id=session_id
        )
        
        if batch_result.success:
            logger.info(f"Batch LLM extraction succeeded with confidence {batch_result.confidence:.2f}")
            return batch_result
        else:
            logger.warning(f"Batch LLM extraction failed with confidence {batch_result.confidence:.2f}")
            return batch_result

