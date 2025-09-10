"""
Entity normalization and resolution service.

Handles natural key normalization, source ranking, conflict resolution,
entity deduplication, and snapshot/change detection for the extraction pipeline.
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from difflib import unified_diff

from sqlalchemy.orm import Session


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


from sqlalchemy import func

from app.models.extraction import (
    ExtractedCompany, ExtractedProduct, ExtractedCapability, ExtractedRelease, ExtractedDocument, ExtractedSignalEntity,
    ExtractionSource, EntitySnapshot, EntityChange, ExtractionSession
)
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class NormalizedEntity:
    """Normalized entity with resolved natural keys."""
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    natural_key: str
    confidence: float
    sources: List[str]  # URLs that contributed to this entity


@dataclass
class MergeResult:
    """Result of entity merge operation."""
    entity_id: str
    entity_type: str
    created: bool  # True if new entity, False if updated existing
    changes_detected: List[str]  # List of changed field names
    snapshot_id: Optional[str] = None
    change_id: Optional[str] = None


class EntityNormalizer:
    """Handles entity normalization and natural key generation."""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for consistent comparison."""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove punctuation except meaningful chars
        normalized = re.sub(r'[^\w\s+#./\-]', '', normalized)
        
        # Normalize common acronyms
        acronym_map = {
            'api': 'API',
            'sdk': 'SDK', 
            'sso': 'SSO',
            'saml': 'SAML',
            'oauth': 'OAuth',
            'ai': 'AI',
            'ml': 'ML',
            'ui': 'UI',
            'ux': 'UX'
        }
        
        words = normalized.split()
        normalized_words = []
        for word in words:
            if word in acronym_map:
                normalized_words.append(acronym_map[word])
            else:
                normalized_words.append(word)
        
        return ' '.join(normalized_words)
    
    @staticmethod
    def extract_version(name: str) -> Tuple[str, Optional[str]]:
        """Extract version from product name."""
        # Common version patterns
        version_patterns = [
            r'(.+?)\s+v?(\d+\.\d+(?:\.\d+)?)\s*$',  # "Product v2.1.0"
            r'(.+?)\s+(\d+\.\d+(?:\.\d+)?)\s*$',    # "Product 2.1.0"
            r'(.+?)\s+(v\d+)\s*$',                   # "Product v2"
        ]
        
        for pattern in version_patterns:
            match = re.match(pattern, name.strip(), re.IGNORECASE)
            if match:
                base_name = match.group(1).strip()
                version = match.group(2).strip()
                return base_name, version
        
        return name, None
    
    @staticmethod
    def detect_product_tier(name: str) -> Tuple[str, Optional[str]]:
        """Detect product tier/edition from name."""
        tier_patterns = [
            r'(.+?)\s+(Pro|Professional|Enterprise|Business|Premium|Plus|Lite|Basic|Standard|Free)\s*$'
        ]
        
        for pattern in tier_patterns:
            match = re.match(pattern, name.strip(), re.IGNORECASE)
            if match:
                base_name = match.group(1).strip()
                tier = match.group(2).strip().lower()
                return base_name, tier
        
        return name, None
    
    def generate_natural_key(self, entity_type: str, data: Dict[str, Any], competitor: str) -> str:
        """Generate natural key for entity deduplication."""
        if entity_type == "ExtractedCompany":
            # Use normalized name + website domain if available
            name = self.normalize_text(data.get("name", ""))
            website = data.get("website", "")
            domain = ""
            if website:
                domain_match = re.search(r"https?://(?:www\.)?([^/]+)", website)
                if domain_match:
                    domain = domain_match.group(1).lower()
            
            return f"{competitor}:company:{name}:{domain}"
        
        elif entity_type == "ExtractedProduct":
            name = data.get("name", "")
            base_name, version = self.extract_version(name)
            base_name, tier = self.detect_product_tier(base_name)
            
            normalized_name = self.normalize_text(base_name)
            company_ref = data.get("company_id", "unknown")
            
            key_parts = [competitor, "product", normalized_name]
            if company_ref != "unknown":
                key_parts.append(company_ref)
            if version:
                key_parts.append(f"v{version}")
            if tier:
                key_parts.append(f"tier_{tier}")
            
            return ":".join(key_parts)
        
        elif entity_type == "Release":
            name = self.normalize_text(data.get("name", ""))
            version = data.get("version", "")
            date = data.get("date", "")
            
            key_parts = [competitor, "release", name]
            if version:
                key_parts.append(f"v{version}")
            if date:
                # Use just the date part, not full timestamp
                date_part = date.split("T")[0] if "T" in date else date
                key_parts.append(date_part)
            
            return ":".join(key_parts)
        
        elif entity_type == "ExtractedDocument":
            title = self.normalize_text(data.get("title", ""))
            url = data.get("url", "")
            doc_type = data.get("doc_type", "")
            
            key_parts = [competitor, "document", title]
            if doc_type:
                key_parts.append(doc_type)
            if url:
                # Use URL path for uniqueness
                path = url.split("/")[-1] if "/" in url else url
                key_parts.append(path[:50])  # Limit length
            
            return ":".join(key_parts)
        
        elif entity_type == "ExtractedSignalEntity":
            title = self.normalize_text(data.get("title", ""))
            signal_type = data.get("signal_type", data.get("type", ""))
            date = data.get("date", "")
            
            key_parts = [competitor, "signal", signal_type, title]
            if date:
                date_part = date.split("T")[0] if "T" in date else date
                key_parts.append(date_part)
            
            return ":".join(key_parts)
        
        elif entity_type == "ExtractedCapability":
            name = self.normalize_text(data.get("name", ""))
            category = data.get("category", "")
            
            key_parts = [competitor, "capability", name]
            if category:
                key_parts.append(category)
            
            return ":".join(key_parts)
        
        else:
            # Fallback: use all string fields
            string_fields = [str(v) for v in data.values() if isinstance(v, str)]
            combined = self.normalize_text(" ".join(string_fields))
            return f"{competitor}:{entity_type.lower()}:{combined[:100]}"


class SourceRanker:
    """Handles source ranking and conflict resolution."""
    
    # Source ranking hierarchy (higher number = higher authority)
    PAGE_TYPE_RANKS = {
        "product": 10,      # Official product pages
        "pricing": 9,       # Pricing tables
        "datasheet": 8,     # Technical datasheets
        "api": 8,           # API documentation
        "release": 7,       # Release notes
        "docs": 6,          # General documentation
        "whitepaper": 5,    # Whitepapers
        "manual": 5,        # User manuals
        "blog": 4,          # Blog posts
        "news": 3,          # News articles
        "about": 2,         # About pages
        "unknown": 1        # Unknown page types
    }
    
    def rank_source(self, url: str, page_type: str, method: str, confidence: float) -> float:
        """Calculate source ranking score."""
        base_rank = self.PAGE_TYPE_RANKS.get(page_type.lower(), 1)
        
        # Page depth bonus (closer to root = higher authority)
        path_parts = url.split("/")[3:]  # Skip protocol and domain
        depth_penalty = min(len(path_parts) * 0.1, 0.5)  # Max 50% penalty
        
        # Method bonus
        method_bonus = 0.1 if method == "rules" else 0.0  # Rules slightly preferred for structured data
        
        # Confidence weight
        confidence_weight = confidence
        
        # URL pattern bonuses
        url_bonus = 0.0
        if "/products/" in url.lower():
            url_bonus += 0.2
        if "/pricing" in url.lower():
            url_bonus += 0.15
        if "/docs/" in url.lower() or "/documentation/" in url.lower():
            url_bonus += 0.1
        
        final_score = (base_rank + method_bonus + url_bonus - depth_penalty) * confidence_weight
        return max(final_score, 0.1)  # Minimum score
    
    def resolve_conflicts(self, field_name: str, values: List[Tuple[Any, float]]) -> Tuple[Any, float]:
        """
        Resolve conflicts between field values from different sources.
        
        Args:
            field_name: Name of the field
            values: List of (value, source_rank) tuples
            
        Returns:
            (resolved_value, confidence)
        """
        if not values:
            return None, 0.0
        
        if len(values) == 1:
            return values[0][0], values[0][1]
        
        # Sort by source rank (highest first)
        values.sort(key=lambda x: x[1], reverse=True)
        
        # For volatile fields, prefer newer sources (would need timestamp)
        volatile_fields = {"pricing", "stage", "status", "released_at"}
        
        if field_name in volatile_fields:
            # Take highest ranked value
            return values[0][0], values[0][1]
        
        # For descriptive fields, check for substantial differences
        if field_name in {"description", "summary", "notes"}:
            # If top two sources have similar rank, flag for review
            if len(values) > 1 and abs(values[0][1] - values[1][1]) < 0.2:
                # Values differ materially, keep highest ranked but lower confidence
                return values[0][0], values[0][1] * 0.8
            else:
                return values[0][0], values[0][1]
        
        # For list fields, merge unique values
        if field_name in {"tags", "markets", "features", "compliance"}:
            merged_list = []
            seen = set()
            total_confidence = 0.0
            
            for value, confidence in values:
                if isinstance(value, list):
                    for item in value:
                        item_str = str(item).lower()
                        if item_str not in seen:
                            merged_list.append(item)
                            seen.add(item_str)
                            total_confidence += confidence
            
            avg_confidence = total_confidence / len(values) if values else 0.0
            return merged_list, min(avg_confidence, 1.0)
        
        # Default: take highest ranked value
        return values[0][0], values[0][1]


class SnapshotManager:
    """Handles entity snapshots and change detection."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_snapshot(
        self, 
        entity_type: str, 
        entity_id: str, 
        data: Dict[str, Any],
        extraction_session_id: int,
        schema_version: str = "v1"
    ) -> str:
        """Create a new entity snapshot."""
        # Compute data hash for deduplication
        data_json = json.dumps(data, sort_keys=True, default=json_serial)
        data_hash = hashlib.sha256(data_json.encode()).hexdigest()
        
        # Check if identical snapshot already exists
        existing = self.db.query(EntitySnapshot).filter(
            EntitySnapshot.entity_type == entity_type,
            EntitySnapshot.entity_id == entity_id,
            EntitySnapshot.data_hash == data_hash
        ).first()
        
        if existing:
            logger.debug(f"Identical snapshot already exists for {entity_type}:{entity_id}")
            return existing.id
        
        # Create new snapshot
        snapshot = EntitySnapshot(
            entity_type=entity_type,
            entity_id=entity_id,
            schema_version=schema_version,
            data_json=json.loads(data_json),  # Use the properly serialized JSON
            data_hash=data_hash,
            extraction_session_id=extraction_session_id
        )
        
        self.db.add(snapshot)
        self.db.flush()  # Get the ID
        
        logger.debug(f"Created snapshot {snapshot.id} for {entity_type}:{entity_id}")
        return snapshot.id
    
    def detect_changes(
        self,
        entity_type: str,
        entity_id: str,
        new_data: Dict[str, Any],
        extraction_session_id: int
    ) -> Optional[str]:
        """
        Detect changes between current and previous entity state.
        
        Returns:
            Change ID if changes detected, None otherwise
        """
        # Get the most recent snapshot for this entity
        previous_snapshot = self.db.query(EntitySnapshot).filter(
            EntitySnapshot.entity_type == entity_type,
            EntitySnapshot.entity_id == entity_id
        ).order_by(EntitySnapshot.created_at.desc()).first()
        
        if not previous_snapshot:
            # No previous state, this is a new entity
            return None
        
        # Compare data
        old_data = previous_snapshot.data_json
        diff_result = self._compute_diff(old_data, new_data)
        
        if not diff_result["has_changes"]:
            return None
        
        # Create new snapshot first
        new_snapshot_id = self.create_snapshot(
            entity_type, entity_id, new_data, extraction_session_id
        )
        
        # Create change record
        change_summary = self._generate_change_summary(
            entity_type, diff_result["changes"], old_data, new_data
        )
        
        change_hash = hashlib.sha256(
            f"{entity_type}:{entity_id}:{previous_snapshot.id}:{new_snapshot_id}".encode()
        ).hexdigest()
        
        change = EntityChange(
            entity_type=entity_type,
            entity_id=entity_id,
            change_hash=change_hash,
            summary=change_summary,
            change_type="updated",
            diff_json=json.loads(json.dumps(diff_result["diff"], default=json_serial)),
            fields_changed=diff_result["changed_fields"],
            previous_snapshot_id=previous_snapshot.id,
            current_snapshot_id=new_snapshot_id,
            extraction_session_id=extraction_session_id
        )
        
        self.db.add(change)
        self.db.flush()
        
        logger.info(f"Detected changes for {entity_type}:{entity_id}: {change_summary}")
        return change.id
    
    def _compute_diff(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute detailed diff between two data dictionaries."""
        changes = {}
        changed_fields = []
        has_changes = False
        
        # Check all fields in new data
        for field, new_value in new_data.items():
            old_value = old_data.get(field)
            
            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value,
                    "type": "modified" if field in old_data else "added"
                }
                changed_fields.append(field)
                has_changes = True
        
        # Check for removed fields
        for field in old_data:
            if field not in new_data:
                changes[field] = {
                    "old": old_data[field],
                    "new": None,
                    "type": "removed"
                }
                changed_fields.append(field)
                has_changes = True
        
        return {
            "has_changes": has_changes,
            "changes": changes,
            "changed_fields": changed_fields,
            "diff": changes
        }
    
    def _generate_change_summary(
        self,
        entity_type: str,
        changes: Dict[str, Any],
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> str:
        """Generate human-readable change summary."""
        if not changes:
            return "No changes"
        
        # Get entity name for context
        entity_name = new_data.get("name", old_data.get("name", "Unknown"))
        
        # Prioritize important changes
        important_changes = []
        
        # Version/release changes
        if "version" in changes:
            old_ver = changes["version"]["old"]
            new_ver = changes["version"]["new"]
            important_changes.append(f"version {old_ver} → {new_ver}")
        
        # Status changes
        if "status" in changes or "stage" in changes:
            field = "status" if "status" in changes else "stage"
            old_val = changes[field]["old"]
            new_val = changes[field]["new"]
            important_changes.append(f"{field} {old_val} → {new_val}")
        
        # Pricing changes
        if "pricing" in changes:
            important_changes.append("pricing updated")
        
        # New features/capabilities
        if "features" in changes or "tags" in changes:
            important_changes.append("features updated")
        
        # URL changes
        if any(field.endswith("_url") for field in changes):
            important_changes.append("URLs updated")
        
        # Build summary
        if important_changes:
            summary = f"{entity_name}: {', '.join(important_changes[:3])}"
        else:
            # Fallback to field count
            field_count = len(changes)
            summary = f"{entity_name}: {field_count} field{'s' if field_count > 1 else ''} updated"
        
        return summary[:200]  # Limit length


class NormalizationService:
    """Main service for entity normalization and upsert operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.normalizer = EntityNormalizer()
        self.source_ranker = SourceRanker()
        self.snapshot_manager = SnapshotManager(db)
    
    def normalize_and_upsert(
        self,
        extracted_entities: Dict[str, Any],
        competitor: str,
        extraction_session_id: int,
        source_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize and upsert extracted entities with change detection.
        
        Args:
            extracted_entities: Raw entities from extraction
            competitor: Competitor name
            extraction_session_id: Current extraction session ID
            source_metadata: Source information (url, page_type, method, etc.)
            
        Returns:
            Dictionary with upsert results and statistics
        """
        results = {
            "entities_processed": 0,
            "entities_created": 0,
            "entities_updated": 0,
            "changes_detected": 0,
            "sources_created": 0,
            "snapshots_created": 0,
            "errors": []
        }
        
        try:
            # Process entities in dependency order: Company -> Product -> Capability -> others
            # This ensures foreign key constraints are satisfied
            processing_order = ["Company", "Product", "Capability", "Release", "ExtractedDocument", "Signal"]
            
            # Process entities in the correct order
            for entity_type in processing_order:
                if entity_type not in extracted_entities:
                    continue
                    
                entities = extracted_entities[entity_type]
                if entity_type == "Source":
                    continue  # Handle separately
                
                if not isinstance(entities, list):
                    continue
                
                for entity_data in entities:
                    try:
                        merge_result = self._process_single_entity(
                            entity_type, entity_data, competitor, 
                            extraction_session_id, source_metadata
                        )
                        
                        results["entities_processed"] += 1
                        if merge_result.created:
                            results["entities_created"] += 1
                        else:
                            results["entities_updated"] += 1
                        
                        if merge_result.changes_detected:
                            results["changes_detected"] += len(merge_result.changes_detected)
                        
                        if merge_result.snapshot_id:
                            results["snapshots_created"] += 1
                        
                        # Create source record
                        self._create_source_record(
                            merge_result.entity_type,
                            merge_result.entity_id,
                            extraction_session_id,
                            source_metadata,
                            list(entity_data.keys())  # fields extracted
                        )
                        results["sources_created"] += 1
                        
                    except Exception as e:
                        # Handle constraint violations gracefully
                        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                            logger.warning(f"Duplicate entity detected for {entity_type}, skipping: {e}")
                            # Rollback current transaction and start fresh
                            self.db.rollback()
                            self.db.begin()
                            results["entities_processed"] += 1  # Count as processed
                            continue
                        else:
                            error_msg = f"Failed to process {entity_type}: {e}"
                            logger.error(error_msg)
                            results["errors"].append(error_msg)
                            # Rollback and restart transaction for next entity
                            self.db.rollback()
                            self.db.begin()
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Normalization failed: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            raise
        
        return results
    
    def _process_single_entity(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        competitor: str,
        extraction_session_id: int,
        source_metadata: Dict[str, Any]
    ) -> MergeResult:
        """Process a single entity with normalization and deduplication."""
        
        # Generate natural key
        natural_key = self.normalizer.generate_natural_key(entity_type, entity_data, competitor)
        
        # Look for existing entity with same natural key
        existing_entity = self._find_existing_entity(entity_type, natural_key)
        
        if existing_entity:
            # Update existing entity
            entity_id = existing_entity.id
            
            # Merge data with source ranking
            merged_data = self._merge_entity_data(
                existing_entity, entity_data, source_metadata
            )
            
            # Update entity in database
            self._update_entity_in_db(entity_type, entity_id, merged_data)
            
            # Detect changes
            change_id = self.snapshot_manager.detect_changes(
                entity_type, entity_id, merged_data, extraction_session_id
            )
            
            return MergeResult(
                entity_id=entity_id,
                entity_type=entity_type,
                created=False,
                changes_detected=["data_updated"] if change_id else [],
                change_id=change_id
            )
        
        else:
            # Create new entity
            entity_id = self._create_new_entity(entity_type, entity_data, natural_key, competitor)
            
            # Create initial snapshot
            snapshot_id = self.snapshot_manager.create_snapshot(
                entity_type, entity_id, entity_data, extraction_session_id
            )
            
            return MergeResult(
                entity_id=entity_id,
                entity_type=entity_type,
                created=True,
                changes_detected=[],
                snapshot_id=snapshot_id
            )
    
    def _find_existing_entity(self, entity_type: str, natural_key: str):
        """Find existing entity by natural key."""
        model_map = {
            "ExtractedCompany": ExtractedCompany,
            "ExtractedProduct": ExtractedProduct,
            "ExtractedCapability": ExtractedCapability,
            "ExtractedRelease": ExtractedRelease,
            "ExtractedDocument": ExtractedDocument,
            "ExtractedSignalEntity": ExtractedSignalEntity
        }
        
        model = model_map.get(entity_type)
        if not model:
            return None
        
        # For now, use a simple approach - store natural_key in normalized_name field
        # In production, you'd want a proper natural_key field
        if hasattr(model, 'normalized_name'):
            return self.db.query(model).filter(model.normalized_name == natural_key).first()
        
        return None
    
    def _create_new_entity(self, entity_type: str, entity_data: Dict[str, Any], natural_key: str, competitor: str) -> str:
        """Create new entity in database."""
        model_map = {
            "ExtractedCompany": ExtractedCompany,
            "ExtractedProduct": ExtractedProduct,
            "ExtractedCapability": ExtractedCapability,
            "ExtractedRelease": ExtractedRelease,
            "ExtractedDocument": ExtractedDocument,
            "ExtractedSignalEntity": ExtractedSignalEntity,
            # Handle both short and long entity type names for backward compatibility
            "Company": ExtractedCompany,
            "Product": ExtractedProduct,
            "Capability": ExtractedCapability,
            "Release": ExtractedRelease,
            "ExtractedDocument": ExtractedDocument,
            "Signal": ExtractedSignalEntity
        }
        
        model = model_map.get(entity_type)
        if not model:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Handle field mapping for specific entity types
        mapped_data = entity_data.copy()
        if entity_type in ["Capability", "ExtractedCapability"] and "definition" in mapped_data:
            # Map "definition" field to "description" for capabilities
            mapped_data["description"] = mapped_data.pop("definition")
        
        # Create entity instance
        entity = model(**mapped_data)
        
        # Set natural key in normalized_name field (temporary approach)
        if hasattr(entity, 'normalized_name'):
            entity.normalized_name = natural_key
        
        # Set competitor if field exists
        if hasattr(entity, 'competitor'):
            entity.competitor = competitor
        
        self.db.add(entity)
        self.db.flush()  # Get the ID
        
        return entity.id
    
    def _update_entity_in_db(self, entity_type: str, entity_id: str, merged_data: Dict[str, Any]):
        """Update existing entity in database."""
        model_map = {
            "ExtractedCompany": ExtractedCompany,
            "ExtractedProduct": ExtractedProduct,
            "ExtractedCapability": ExtractedCapability,
            "ExtractedRelease": ExtractedRelease,
            "ExtractedDocument": ExtractedDocument,
            "ExtractedSignalEntity": ExtractedSignalEntity
        }
        
        model = model_map.get(entity_type)
        if not model:
            return
        
        entity = self.db.query(model).filter(model.id == entity_id).first()
        if entity:
            # Update fields
            for field, value in merged_data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)
            
            entity.last_updated = datetime.utcnow()
    
    def _merge_entity_data(self, existing_entity, new_data: Dict[str, Any], source_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Merge new data with existing entity using source ranking."""
        # For now, simple merge - take new data
        # In production, implement proper source ranking and field-level merging
        
        merged = {}
        
        # Copy existing data
        for column in existing_entity.__table__.columns:
            field_name = column.name
            if hasattr(existing_entity, field_name):
                merged[field_name] = getattr(existing_entity, field_name)
        
        # Override with new data (simple strategy for now)
        merged.update(new_data)
        
        return merged
    
    def _create_source_record(
        self,
        entity_type: str,
        entity_id: str,
        extraction_session_id: int,
        source_metadata: Dict[str, Any],
        fields_extracted: List[str]
    ):
        """Create source record for provenance tracking."""
        source = ExtractionSource(
            extraction_session_id=extraction_session_id,
            entity_type=entity_type,
            entity_id=entity_id,
            url=source_metadata.get("url", ""),
            content_hash=source_metadata.get("content_hash", ""),
            page_type=source_metadata.get("page_type", ""),
            method=source_metadata.get("method", ""),
            ai_model=source_metadata.get("ai_model"),
            confidence=source_metadata.get("confidence", 0.0),
            fields_extracted=fields_extracted,
            tokens_input=source_metadata.get("tokens_input"),
            tokens_output=source_metadata.get("tokens_output"),
            processing_time_ms=source_metadata.get("processing_time_ms"),
            cache_hit=source_metadata.get("cache_hit", False)
        )
        
        self.db.add(source)
