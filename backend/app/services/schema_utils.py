"""
Schema compaction utilities for efficient AI extraction prompts.

Provides dynamic schema trimming, field prioritization, and token counting
to stay within context limits while maintaining extraction quality.
"""

import json
import re
from typing import Dict, Any, List, Set, Optional
from pathlib import Path

from app.core.config import settings
from app.services.validate import load_schema, get_available_schemas

# Token estimation: ~4 chars per token for English text
CHARS_PER_TOKEN = 4

# Page type to entity mapping for dynamic schema selection
PAGE_TYPE_SCHEMAS = {
    "product": ["Product", "Company", "Capability"],
    "pricing": ["Product", "Company", "Signal"],
    "release": ["Release", "Product", "Company"],
    "docs": ["Document", "Product", "Company"],
    "news": ["Signal", "Company", "Product"],
    "about": ["Company"],
    "contact": ["Company"],
    "blog": ["Signal", "Document", "Company"],
    "api": ["Document", "Product", "Capability"],
    "whitepaper": ["Document", "Product", "Capability"],
    "datasheet": ["Document", "Product", "Capability"],
    "unknown": ["Product", "Company", "Document", "Signal"]  # Fallback
}

# High-value fields to prioritize in compact schemas
HIGH_VALUE_FIELDS = {
    "Product": {
        "required": ["id", "company_id", "name", "category", "stage", "markets", "tags"],
        "high_value": ["short_desc", "product_url", "docs_url", "specs", "released_at", "compliance"]
    },
    "Company": {
        "required": ["id", "name", "aliases", "status", "tags"], 
        "high_value": ["website", "hq_country"]
    },
    "Release": {
        "required": ["id", "name", "version", "date", "notes"],
        "high_value": ["product_refs", "release_url", "highlights"]
    },
    "Document": {
        "required": ["id", "title", "doc_type"],
        "high_value": ["url", "summary", "product_refs", "published_at"]
    },
    "Signal": {
        "required": ["id", "type", "title", "date"],
        "high_value": ["summary", "company_refs", "product_refs", "source_url"]
    },
    "Capability": {
        "required": ["id", "name", "tags"],
        "high_value": ["definition"]
    },
    "Source": {
        "required": ["id", "origin"],
        "high_value": ["author", "retrieved_at", "credibility"]
    }
}


class TokenCounter:
    """Utility for counting tokens in text."""
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count using character-based heuristic."""
        # More accurate estimation considering JSON structure
        # JSON has more punctuation/structure than plain text
        json_overhead = 1.2 if '{' in text or '[' in text else 1.0
        return int(len(text) / CHARS_PER_TOKEN * json_overhead)
    
    @staticmethod
    def truncate_to_tokens(text: str, max_tokens: int) -> str:
        """Truncate text to approximate token limit."""
        max_chars = int(max_tokens * CHARS_PER_TOKEN * 0.9)  # Safety margin
        if len(text) <= max_chars:
            return text
        
        # Try to truncate at sentence boundaries
        truncated = text[:max_chars]
        last_sentence = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?'),
            truncated.rfind('\n\n')
        )
        
        if last_sentence > max_chars * 0.8:  # If we found a good break point
            return truncated[:last_sentence + 1]
        else:
            return truncated + "..."


class SchemaCompactor:
    """Compacts JSON schemas for efficient AI prompts."""
    
    def __init__(self):
        self.full_schemas = {}
        self.compact_templates = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all available schemas."""
        try:
            available = get_available_schemas()
            for schema_name in available:
                self.full_schemas[schema_name] = load_schema(schema_name)
        except Exception as e:
            # Graceful fallback - log but don't crash
            print(f"Warning: Could not load schemas: {e}")
    
    def get_relevant_schemas(self, page_type: str) -> List[str]:
        """Get relevant schema names for a page type."""
        page_type_clean = page_type.lower().replace('-', '').replace('_', '')
        
        # Try exact match first
        if page_type_clean in PAGE_TYPE_SCHEMAS:
            return PAGE_TYPE_SCHEMAS[page_type_clean]
        
        # Try partial matches
        for pt, schemas in PAGE_TYPE_SCHEMAS.items():
            if page_type_clean in pt or pt in page_type_clean:
                return schemas
        
        # Fallback to unknown
        return PAGE_TYPE_SCHEMAS["unknown"]
    
    def compact_schema(self, schema_name: str, include_examples: bool = False) -> Dict[str, Any]:
        """Create a compact version of a schema."""
        if schema_name not in self.full_schemas:
            return {"error": f"Schema {schema_name} not found"}
        
        full_schema = self.full_schemas[schema_name]
        
        # Extract the main definition
        if "$ref" in full_schema and "definitions" in full_schema:
            # Handle $ref style schemas
            ref_path = full_schema["$ref"].replace("#/definitions/", "")
            definition = full_schema["definitions"][ref_path]
        else:
            definition = full_schema
        
        # Get field priorities for this schema
        field_config = HIGH_VALUE_FIELDS.get(schema_name, {})
        required_fields = set(field_config.get("required", []))
        high_value_fields = set(field_config.get("high_value", []))
        
        # Build compact schema
        compact = {
            "type": "object",
            "properties": {},
            "required": list(required_fields)
        }
        
        # Add required fields first
        if "properties" in definition:
            for field_name in required_fields:
                if field_name in definition["properties"]:
                    compact["properties"][field_name] = self._simplify_property(
                        definition["properties"][field_name]
                    )
        
        # Add high-value optional fields
        for field_name in high_value_fields:
            if field_name in definition["properties"] and field_name not in compact["properties"]:
                compact["properties"][field_name] = self._simplify_property(
                    definition["properties"][field_name]
                )
        
        # Add examples if requested (for complex fields)
        if include_examples:
            compact["_examples"] = self._generate_examples(schema_name)
        
        return compact
    
    def _simplify_property(self, prop: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify a property definition for compactness."""
        simplified = {"type": prop.get("type", "string")}
        
        # Keep essential constraints
        if "enum" in prop:
            simplified["enum"] = prop["enum"]
        if "format" in prop:
            simplified["format"] = prop["format"]
        if "items" in prop and prop.get("type") == "array":
            # Simplify array items
            if isinstance(prop["items"], dict):
                simplified["items"] = self._simplify_property(prop["items"])
            else:
                simplified["items"] = prop["items"]
        
        # For objects, include basic structure but not deep nesting
        if prop.get("type") == "object" and "properties" in prop:
            # Only include a few key properties to avoid explosion
            simplified["properties"] = {}
            for key, value in list(prop["properties"].items())[:3]:  # Limit to 3 props
                simplified["properties"][key] = self._simplify_property(value)
        
        return simplified
    
    def _generate_examples(self, schema_name: str) -> Dict[str, Any]:
        """Generate example values for complex schemas."""
        examples = {
            "Product": {
                "id": "prod_123",
                "name": "AI Analytics Platform",
                "category": "analytics",
                "stage": "ga",
                "markets": ["enterprise", "healthcare"],
                "tags": ["ai", "analytics", "saas"]
            },
            "Company": {
                "id": "comp_456", 
                "name": "DataCorp Inc",
                "aliases": ["DataCorp", "DC"],
                "status": "active",
                "tags": ["enterprise", "b2b"]
            },
            "Release": {
                "id": "rel_789",
                "name": "Version 2.1.0",
                "version": "2.1.0", 
                "date": "2024-01-15",
                "notes": "Added new ML models and improved performance"
            }
        }
        return examples.get(schema_name, {})
    
    def build_extraction_prompt(
        self,
        text: str,
        page_type: str,
        competitor: str,
        url: str,
        content_hash: str,
        schema_version: str = "v1"
    ) -> str:
        """Build complete extraction prompt with compact schemas."""
        
        # Get relevant schemas for this page type
        relevant_schemas = self.get_relevant_schemas(page_type)
        
        # Build compact schema definitions
        compact_schemas = {}
        for schema_name in relevant_schemas:
            compact_schemas[schema_name] = self.compact_schema(schema_name)
        
        # Always include Source schema for attribution
        compact_schemas["Source"] = {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "content_hash": {"type": "string"},
                "page_type": {"type": "string"},
                "method": {"type": "string", "enum": ["rules", "ai"]},
                "ai_model": {"type": "string"},
                "extracted_at": {"type": "string", "format": "date-time"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["url", "content_hash", "page_type", "method", "extracted_at"]
        }
        
        # Truncate text to fit within token budget
        # Reserve tokens for prompt structure and schemas
        prompt_overhead = 2000  # Estimated tokens for instructions + schemas
        max_text_tokens = (settings.EXTRACTOR_MAX_TEXT_CHARS // CHARS_PER_TOKEN) - prompt_overhead
        
        truncated_text = TokenCounter.truncate_to_tokens(text, max_text_tokens)
        
        # Build the prompt
        prompt = f"""Task: Extract structured entities from the following page text about products of a specific company.

Context:
- Competitor: {competitor}
- URL: {url}
- Page Type: {page_type}
- Content Hash: {content_hash}
- Schema Version: {schema_version}

Extraction Rules:
1. Output ONLY valid JSON matching the provided schemas!
2. Use null for missing optional fields, never omit required fields!
3. Never Hallucinate data, only use data that is explicitly provided in the text!
4. For product names/versions, use exact text when possible.
5. Include confidence scores (0-1) in Source objects.
6. If multiple entities of same type, return arrays.

Schemas (compact definitions):
{json.dumps(compact_schemas, indent=2)}

Required Output Format:
{{
  "entities": {{
    {', '.join(f'"{schema}": []' for schema in relevant_schemas)},
    "Source": {{}}
  }}
}}

Page Text:
{truncated_text}

Output (JSON only):"""

        return prompt
    
    def estimate_prompt_tokens(self, prompt: str) -> int:
        """Estimate total tokens in a prompt."""
        return TokenCounter.estimate_tokens(prompt)
    
    def validate_prompt_size(self, prompt: str, max_tokens: int = None) -> Dict[str, Any]:
        """Validate that prompt fits within token limits."""
        if max_tokens is None:
            max_tokens = settings.EXTRACTOR_MAX_TEXT_CHARS // CHARS_PER_TOKEN
        
        estimated_tokens = self.estimate_prompt_tokens(prompt)
        
        return {
            "estimated_tokens": estimated_tokens,
            "max_tokens": max_tokens,
            "within_limits": estimated_tokens <= max_tokens,
            "utilization": estimated_tokens / max_tokens,
            "headroom_tokens": max_tokens - estimated_tokens
        }


# Global instance
schema_compactor = SchemaCompactor()


def get_schema_compactor() -> SchemaCompactor:
    """Get the global schema compactor instance."""
    return schema_compactor
