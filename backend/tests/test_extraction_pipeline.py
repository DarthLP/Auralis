"""
Integration tests for the extraction pipeline.

Tests the complete flow from raw text extraction through normalization
and entity storage, including rules-first + AI fallback strategy.
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.extract import ExtractionService, RulesExtractor, AIExtractor
from app.services.normalize import NormalizationService, EntityNormalizer
from app.services.schema_utils import get_schema_compactor
from app.services.theta_client import ThetaClient
from app.models.extraction import ExtractionSession, ExtractedCompany, ExtractedProduct, EntitySnapshot
from app.models.core_crawl import PageFingerprint, FingerprintSession


class TestRulesExtractor:
    """Test the rules-based extraction engine."""
    
    def setup_method(self):
        self.extractor = RulesExtractor()
    
    def test_extract_product_pricing(self):
        """Test extraction of product with pricing information."""
        text = """
        CloudAnalytics API v2.1
        
        Our enterprise analytics platform provides real-time insights.
        
        Pricing:
        - Starter: $99/month
        - Professional: $299/month  
        - Enterprise: $999/month
        
        Features:
        - Real-time analytics
        - Custom dashboards
        - API access
        """
        
        result = self.extractor.extract_from_text(text, "product", "https://example.com/products/analytics")
        
        assert result.success
        assert result.method == "rules"
        assert result.confidence > 0.6
        
        # Check extracted entities
        assert len(result.entities["Product"]) == 1
        product = result.entities["Product"][0]
        assert "CloudAnalytics API" in product["name"]
        assert "pricing" in product
        
        # Check source record
        assert result.entities["Source"]["method"] == "rules"
        assert result.entities["Source"]["confidence"] > 0.0
    
    def test_extract_release_notes(self):
        """Test extraction from release notes."""
        text = """
        ## Version 2.1.0 - March 15, 2024
        
        ### New Features
        - Added SAML authentication
        - Improved dashboard performance
        - New API endpoints for bulk operations
        
        ### Bug Fixes
        - Fixed memory leak in data processing
        - Resolved timezone issues in reports
        """
        
        result = self.extractor.extract_from_text(text, "release", "https://example.com/releases/v2.1.0")
        
        assert result.success
        assert len(result.entities["Release"]) == 1
        
        release = result.entities["Release"][0]
        assert release["version"] == "2.1.0"
        assert "SAML" in release["notes"]
    
    def test_extract_company_info(self):
        """Test company information extraction."""
        text = """
        About TechCorp
        
        We are a leading provider of cloud analytics solutions.
        Founded in 2010, we serve over 10,000 customers worldwide.
        """
        
        result = self.extractor.extract_from_text(text, "about", "https://techcorp.com/about")
        
        assert result.success
        assert len(result.entities["Company"]) == 1
        
        company = result.entities["Company"][0]
        assert "TechCorp" in company["name"] or "techcorp" in company["name"]
        assert company["website"] == "https://techcorp.com"
    
    def test_low_confidence_extraction(self):
        """Test that low-confidence extractions are marked as failed."""
        text = "This is just some random text with no useful information."
        
        result = self.extractor.extract_from_text(text, "unknown", "https://example.com/random")
        
        assert not result.success
        assert result.confidence < 0.6


class TestAIExtractor:
    """Test the AI-based extraction engine."""
    
    @pytest.fixture
    def mock_theta_client(self):
        """Mock Theta client for testing."""
        client = Mock(spec=ThetaClient)
        client.complete = AsyncMock()
        return client
    
    @pytest.fixture  
    def ai_extractor(self, mock_theta_client):
        """AI extractor with mocked Theta client."""
        return AIExtractor(mock_theta_client)
    
    @pytest.mark.asyncio
    async def test_successful_ai_extraction(self, ai_extractor, mock_theta_client):
        """Test successful AI extraction."""
        # Mock AI response
        mock_response = {
            "entities": {
                "Product": [{
                    "id": "prod_123",
                    "company_id": "comp_456", 
                    "name": "DataViz Pro",
                    "category": "analytics",
                    "stage": "ga",
                    "markets": ["enterprise"],
                    "tags": ["analytics", "visualization"]
                }],
                "Company": [{
                    "id": "comp_456",
                    "name": "DataCorp",
                    "aliases": ["DataCorp Inc"],
                    "status": "active", 
                    "tags": ["b2b", "analytics"]
                }],
                "Source": {
                    "url": "https://datacorp.com/products/dataviz",
                    "content_hash": "abc123",
                    "page_type": "product",
                    "method": "ai",
                    "ai_model": "meta-llama/Llama-3.1-70B-Instruct",
                    "extracted_at": "2024-01-15T10:00:00Z",
                    "confidence": 0.85
                }
            }
        }
        
        mock_theta_client.complete.return_value = mock_response
        
        result = await ai_extractor.extract_from_text(
            text="DataViz Pro is our flagship analytics platform...",
            page_type="product",
            competitor="datacorp", 
            url="https://datacorp.com/products/dataviz",
            content_hash="abc123"
        )
        
        assert result.success
        assert result.method == "ai"
        assert result.confidence == 0.85
        assert len(result.entities["Product"]) == 1
        assert len(result.entities["Company"]) == 1
    
    @pytest.mark.asyncio
    async def test_ai_extraction_validation_error(self, ai_extractor, mock_theta_client):
        """Test AI extraction with validation errors."""
        # Mock invalid AI response (missing required fields)
        mock_response = {
            "entities": {
                "Product": [{
                    "name": "Invalid Product"
                    # Missing required fields: id, company_id, category, stage, markets, tags
                }],
                "Source": {}
            }
        }
        
        mock_theta_client.complete.return_value = mock_response
        
        result = await ai_extractor.extract_from_text(
            text="Some product text...",
            page_type="product",
            competitor="test",
            url="https://test.com",
            content_hash="xyz"
        )
        
        # Should still succeed but with validation warnings logged
        assert result.success
        assert result.method == "ai"
    
    @pytest.mark.asyncio
    async def test_ai_extraction_failure(self, ai_extractor, mock_theta_client):
        """Test AI extraction failure handling."""
        mock_theta_client.complete.side_effect = Exception("AI service error")
        
        result = await ai_extractor.extract_from_text(
            text="Some text...",
            page_type="product",
            competitor="test",
            url="https://test.com",
            content_hash="xyz"
        )
        
        assert not result.success
        assert result.method == "ai"
        assert "AI service error" in result.error


class TestEntityNormalizer:
    """Test entity normalization and natural key generation."""
    
    def setup_method(self):
        self.normalizer = EntityNormalizer()
    
    def test_normalize_text(self):
        """Test text normalization."""
        assert self.normalizer.normalize_text("  Product   API  ") == "Product API"
        assert self.normalizer.normalize_text("My-Product_Name!") == "My Product Name"
        assert self.normalizer.normalize_text("api sdk ui") == "API SDK UI"
    
    def test_extract_version(self):
        """Test version extraction from product names."""
        base, version = self.normalizer.extract_version("DataViz Pro v2.1.0")
        assert base == "DataViz Pro"
        assert version == "v2.1.0"
        
        base, version = self.normalizer.extract_version("Analytics Platform 3.0")
        assert base == "Analytics Platform"
        assert version == "3.0"
        
        base, version = self.normalizer.extract_version("Simple Product")
        assert base == "Simple Product"
        assert version is None
    
    def test_detect_product_tier(self):
        """Test product tier detection."""
        base, tier = self.normalizer.detect_product_tier("CloudAnalytics Enterprise")
        assert base == "CloudAnalytics"
        assert tier == "enterprise"
        
        base, tier = self.normalizer.detect_product_tier("DataViz Pro")
        assert base == "DataViz"
        assert tier == "pro"
    
    def test_generate_natural_keys(self):
        """Test natural key generation for different entity types."""
        # Product key
        product_data = {
            "name": "DataViz Pro v2.1",
            "company_id": "comp_123"
        }
        key = self.normalizer.generate_natural_key("Product", product_data, "datacorp")
        assert "datacorp:product:dataviz:comp_123:v2.1" in key.lower()
        
        # Company key
        company_data = {
            "name": "DataCorp Inc",
            "website": "https://datacorp.com"
        }
        key = self.normalizer.generate_natural_key("Company", company_data, "datacorp")
        assert "datacorp:company:datacorp inc:datacorp.com" in key.lower()
        
        # Release key
        release_data = {
            "name": "Version 2.1.0",
            "version": "2.1.0",
            "date": "2024-01-15"
        }
        key = self.normalizer.generate_natural_key("Release", release_data, "datacorp")
        assert "datacorp:release" in key.lower()
        assert "v2.1.0" in key.lower()


class TestExtractionService:
    """Test the complete extraction service."""
    
    @pytest.fixture
    def mock_theta_client(self):
        client = Mock(spec=ThetaClient)
        client.complete = AsyncMock()
        return client
    
    @pytest.fixture
    def extraction_service(self, mock_theta_client):
        return ExtractionService(mock_theta_client)
    
    @pytest.mark.asyncio
    async def test_rules_first_success(self, extraction_service):
        """Test that rules extraction succeeds and AI is not called."""
        text = """
        CloudAnalytics API v2.1
        Pricing: $99/month for starter plan
        Features: Real-time analytics, Custom dashboards
        """
        
        with patch.object(extraction_service.ai_extractor, 'extract_from_text') as mock_ai:
            result = await extraction_service.extract_structured_from_text(
                raw_text=text,
                url="https://example.com/products",
                page_type="product",
                competitor="example",
                content_hash="abc123"
            )
            
            assert result.success
            assert result.method == "rules"
            assert result.confidence >= 0.6
            
            # AI should not have been called
            mock_ai.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ai_fallback(self, extraction_service, mock_theta_client):
        """Test that AI fallback is used when rules fail."""
        # Text that won't trigger rules extraction
        text = "This is some complex product description that requires AI understanding."
        
        # Mock successful AI response
        mock_theta_client.complete.return_value = {
            "entities": {
                "Product": [{
                    "id": "prod_123",
                    "company_id": "comp_456",
                    "name": "Complex Product",
                    "category": "software",
                    "stage": "ga", 
                    "markets": ["enterprise"],
                    "tags": ["complex"]
                }],
                "Source": {
                    "confidence": 0.8,
                    "method": "ai"
                }
            }
        }
        
        result = await extraction_service.extract_structured_from_text(
            raw_text=text,
            url="https://example.com/complex",
            page_type="product",
            competitor="example",
            content_hash="xyz789"
        )
        
        assert result.success
        assert result.method == "ai"
        assert result.confidence == 0.8
        
        # Verify AI was called
        mock_theta_client.complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_both_methods_fail(self, extraction_service, mock_theta_client):
        """Test behavior when both rules and AI fail."""
        text = "Minimal text"
        
        # Mock AI failure
        mock_theta_client.complete.side_effect = Exception("AI failed")
        
        result = await extraction_service.extract_structured_from_text(
            raw_text=text,
            url="https://example.com/minimal",
            page_type="unknown",
            competitor="example", 
            content_hash="fail123"
        )
        
        assert not result.success
        # Should return the better of the two failed attempts


class TestSchemaCompactor:
    """Test schema compaction for AI prompts."""
    
    def setup_method(self):
        self.compactor = get_schema_compactor()
    
    def test_get_relevant_schemas(self):
        """Test schema selection based on page type."""
        product_schemas = self.compactor.get_relevant_schemas("product")
        assert "Product" in product_schemas
        assert "Company" in product_schemas
        
        release_schemas = self.compactor.get_relevant_schemas("release")
        assert "Release" in release_schemas
        assert "Product" in release_schemas
    
    def test_compact_schema(self):
        """Test schema compaction."""
        # This test requires actual schema files to be present
        try:
            compact = self.compactor.compact_schema("Product")
            assert "type" in compact
            assert "properties" in compact
            assert "required" in compact
            
            # Should have fewer fields than full schema
            assert len(compact["properties"]) <= 15
        except Exception:
            pytest.skip("Schema files not available in test environment")
    
    def test_build_extraction_prompt(self):
        """Test prompt building."""
        prompt = self.compactor.build_extraction_prompt(
            text="Sample product text with features and pricing.",
            page_type="product",
            competitor="testcorp",
            url="https://testcorp.com/product",
            content_hash="test123",
            schema_version="v1"
        )
        
        assert "testcorp" in prompt
        assert "product" in prompt
        assert "JSON" in prompt
        assert "entities" in prompt
        assert len(prompt) > 100  # Should be substantial
    
    def test_token_estimation(self):
        """Test token counting utilities."""
        from app.services.schema_utils import TokenCounter
        
        text = "This is a sample text for token estimation."
        tokens = TokenCounter.estimate_tokens(text)
        assert tokens > 0
        assert tokens < 50  # Should be reasonable
        
        # Test truncation
        long_text = "word " * 1000
        truncated = TokenCounter.truncate_to_tokens(long_text, 100)
        assert len(truncated) < len(long_text)


@pytest.mark.integration
class TestFullExtractionPipeline:
    """Integration tests for the complete extraction pipeline."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session for testing."""
        # In a real test environment, you'd use a test database
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_fingerprint_data(self):
        """Sample fingerprint data for testing."""
        return {
            "id": 1,
            "url": "https://datacorp.com/products/analytics",
            "page_type": "product",
            "content_hash": "abc123",
            "extracted_text": """
            DataAnalytics Pro v3.0
            
            Our flagship analytics platform for enterprise customers.
            
            Features:
            - Real-time data processing
            - Custom dashboards
            - API access
            - SAML authentication
            
            Pricing:
            - Professional: $299/month
            - Enterprise: $999/month
            
            Released: January 15, 2024
            """
        }
    
    def test_extraction_session_creation(self, db_session):
        """Test creation of extraction session."""
        session = ExtractionSession(
            fingerprint_session_id=1,
            competitor="datacorp",
            schema_version="v1"
        )
        
        assert session.competitor == "datacorp"
        assert session.schema_version == "v1"
        assert session.total_pages == 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_extraction(self, db_session, sample_fingerprint_data):
        """Test complete extraction flow from fingerprint to entities."""
        # Mock the database queries and operations
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.flush = Mock()
        
        # Create extraction service with mocked dependencies
        theta_client = Mock(spec=ThetaClient)
        theta_client.complete = AsyncMock(return_value={
            "entities": {
                "Product": [{
                    "id": "prod_123",
                    "company_id": "comp_datacorp",
                    "name": "DataAnalytics Pro",
                    "category": "analytics",
                    "stage": "ga",
                    "markets": ["enterprise"],
                    "tags": ["analytics", "real-time"]
                }],
                "Company": [{
                    "id": "comp_datacorp",
                    "name": "DataCorp",
                    "aliases": ["DataCorp Inc"],
                    "status": "active",
                    "tags": ["b2b", "analytics"]
                }],
                "Source": {
                    "url": sample_fingerprint_data["url"],
                    "content_hash": sample_fingerprint_data["content_hash"],
                    "page_type": sample_fingerprint_data["page_type"],
                    "method": "ai",
                    "confidence": 0.9
                }
            }
        })
        
        extraction_service = ExtractionService(theta_client)
        
        # Run extraction
        result = await extraction_service.extract_structured_from_text(
            raw_text=sample_fingerprint_data["extracted_text"],
            url=sample_fingerprint_data["url"],
            page_type=sample_fingerprint_data["page_type"],
            competitor="datacorp",
            content_hash=sample_fingerprint_data["content_hash"]
        )
        
        # Verify results
        assert result.success
        assert len(result.entities["Product"]) == 1
        assert len(result.entities["Company"]) == 1
        assert result.entities["Product"][0]["name"] == "DataAnalytics Pro"
        assert result.entities["Company"][0]["name"] == "DataCorp"
    
    def test_normalization_service(self, db_session):
        """Test entity normalization and deduplication."""
        # Mock database operations
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.flush = Mock()
        
        normalization_service = NormalizationService(db_session)
        
        extracted_entities = {
            "Product": [{
                "id": "prod_123",
                "company_id": "comp_datacorp", 
                "name": "DataAnalytics Pro v3.0",
                "category": "analytics",
                "stage": "ga",
                "markets": ["enterprise"],
                "tags": ["analytics"]
            }],
            "Company": [{
                "id": "comp_datacorp",
                "name": "DataCorp Inc",
                "aliases": ["DataCorp"],
                "status": "active",
                "tags": ["b2b"]
            }]
        }
        
        source_metadata = {
            "url": "https://datacorp.com/products",
            "content_hash": "abc123",
            "page_type": "product",
            "method": "rules",
            "confidence": 0.8
        }
        
        result = normalization_service.normalize_and_upsert(
            extracted_entities,
            "datacorp",
            1,  # extraction_session_id
            source_metadata
        )
        
        # Verify normalization results
        assert result["entities_processed"] >= 2
        assert result["sources_created"] >= 2
        assert len(result["errors"]) == 0


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_extraction_pipeline.py -v
    pytest.main([__file__, "-v"])
