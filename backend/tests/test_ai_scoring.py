"""
Tests for AI-powered page scoring service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.services.ai_scoring import AIScoringService, AIScoringResult


class TestAIScoringService:
    """Test cases for AI scoring service."""
    
    @pytest.fixture
    def mock_theta_client(self):
        """Mock Theta client for testing."""
        client = Mock()
        client.complete = AsyncMock()
        return client
    
    @pytest.fixture
    def ai_scoring_service(self, mock_theta_client):
        """Create AI scoring service with mocked dependencies."""
        return AIScoringService(mock_theta_client)
    
    @pytest.mark.asyncio
    async def test_score_product_page(self, ai_scoring_service, mock_theta_client):
        """Test scoring a product page."""
        # Mock AI response
        mock_response = {
            "score": 0.85,
            "primary_category": "product",
            "secondary_categories": ["datasheet"],
            "confidence": 0.9,
            "reasoning": "Detailed product specifications with technical details and pricing information",
            "signals": ["product_specs", "pricing_info", "technical_details"]
        }
        mock_theta_client.complete.return_value = mock_response
        
        # Test data
        url = "https://example.com/products/robot-arm-mt1"
        title = "MT1 Robot Arm - Advanced Cleaning Solution"
        content = """
        The MT1 Robot Arm is our flagship autonomous cleaning robot designed for commercial environments.
        
        Key Features:
        - Advanced AI navigation
        - 8-hour battery life
        - 99.9% cleaning efficiency
        - Price: $15,999
        
        Technical Specifications:
        - Weight: 45kg
        - Dimensions: 120cm x 80cm x 60cm
        - Operating temperature: -10°C to 40°C
        """
        
        # Score the page
        result = await ai_scoring_service.score_page(
            url=url,
            title=title,
            content=content,
            competitor="ExampleCorp"
        )
        
        # Assertions
        assert result.success is True
        assert result.score == 0.85
        assert result.primary_category == "product"
        assert "datasheet" in result.secondary_categories
        assert result.confidence == 0.9
        assert "product_specs" in result.signals
        assert result.processing_time_ms > 0
        
        # Verify AI client was called
        mock_theta_client.complete.assert_called_once()
        call_args = mock_theta_client.complete.call_args
        assert "competitor" in call_args.kwargs
        assert call_args.kwargs["competitor"] == "ExampleCorp"
    
    @pytest.mark.asyncio
    async def test_score_pricing_page(self, ai_scoring_service, mock_theta_client):
        """Test scoring a pricing page."""
        # Mock AI response
        mock_response = {
            "score": 0.75,
            "primary_category": "pricing",
            "secondary_categories": [],
            "confidence": 0.85,
            "reasoning": "Clear pricing information with multiple plans and subscription options",
            "signals": ["pricing_info", "competitive_intel"]
        }
        mock_theta_client.complete.return_value = mock_response
        
        # Test data
        url = "https://example.com/pricing"
        title = "Pricing Plans - ExampleCorp"
        content = """
        Choose the perfect plan for your business:
        
        Starter Plan: $99/month
        - Up to 5 robots
        - Basic support
        - Standard features
        
        Professional Plan: $299/month
        - Up to 20 robots
        - Priority support
        - Advanced analytics
        
        Enterprise Plan: $999/month
        - Unlimited robots
        - 24/7 support
        - Custom integrations
        """
        
        # Score the page
        result = await ai_scoring_service.score_page(
            url=url,
            title=title,
            content=content,
            competitor="ExampleCorp"
        )
        
        # Assertions
        assert result.success is True
        assert result.score == 0.75
        assert result.primary_category == "pricing"
        assert result.confidence == 0.85
        assert "pricing_info" in result.signals
    
    @pytest.mark.asyncio
    async def test_score_low_value_page(self, ai_scoring_service, mock_theta_client):
        """Test scoring a low-value page."""
        # Mock AI response
        mock_response = {
            "score": 0.15,
            "primary_category": "other",
            "secondary_categories": [],
            "confidence": 0.8,
            "reasoning": "Generic contact page with minimal business value for competitive analysis",
            "signals": ["low_value"]
        }
        mock_theta_client.complete.return_value = mock_response
        
        # Test data
        url = "https://example.com/contact"
        title = "Contact Us - ExampleCorp"
        content = """
        Get in touch with our team:
        
        Email: contact@example.com
        Phone: +1-555-0123
        Address: 123 Business St, City, State 12345
        
        Office Hours: Monday-Friday, 9AM-5PM
        """
        
        # Score the page
        result = await ai_scoring_service.score_page(
            url=url,
            title=title,
            content=content,
            competitor="ExampleCorp"
        )
        
        # Assertions
        assert result.success is True
        assert result.score == 0.15
        assert result.primary_category == "other"
        assert "low_value" in result.signals
    
    @pytest.mark.asyncio
    async def test_ai_scoring_failure(self, ai_scoring_service, mock_theta_client):
        """Test handling of AI scoring failures."""
        # Mock AI failure
        mock_theta_client.complete.side_effect = Exception("AI service unavailable")
        
        # Test data
        url = "https://example.com/products/test"
        title = "Test Product"
        content = "Some product content here"
        
        # Score the page
        result = await ai_scoring_service.score_page(
            url=url,
            title=title,
            content=content,
            competitor="ExampleCorp"
        )
        
        # Assertions
        assert result.success is False
        assert result.score == 0.0
        assert result.primary_category == "other"
        assert result.error is not None
        assert "ai_error" in result.signals
    
    @pytest.mark.asyncio
    async def test_ai_scoring_parse_failure(self, ai_scoring_service):
        """Test handling of AI response parsing failures."""
        # Mock AI response that will cause parsing failure
        with patch.object(ai_scoring_service, '_call_scoring_api') as mock_call:
            # Return an empty response that will cause "No content found" error
            mock_call.return_value = ""
            
            # Test data
            url = "https://example.com/products/test"
            title = "Test Product"
            h1_headings = "Test Headings"
            
            # Score the page
            result = await ai_scoring_service.score_page(
                url=url,
                title=title,
                h1_headings=h1_headings,
                competitor="ExampleCorp"
            )
            
            # Assertions - should be marked as failed due to parsing error
            assert result.success is False
            assert result.score == 0.1  # Fallback score
            assert result.primary_category == "other"
            assert result.confidence == 0.0
            assert "Failed to parse AI response" in result.reasoning
            assert "parse_error" in result.signals
            assert result.error is not None
    
    def test_category_priority(self, ai_scoring_service):
        """Test category priority system."""
        assert ai_scoring_service.get_category_priority("product") == 6
        assert ai_scoring_service.get_category_priority("pricing") == 5
        assert ai_scoring_service.get_category_priority("datasheet") == 4
        assert ai_scoring_service.get_category_priority("release") == 3
        assert ai_scoring_service.get_category_priority("news") == 2
        assert ai_scoring_service.get_category_priority("company") == 1
        assert ai_scoring_service.get_category_priority("other") == 0
        assert ai_scoring_service.get_category_priority("unknown") == 0
    
    def test_category_description(self, ai_scoring_service):
        """Test category descriptions."""
        assert "Product pages" in ai_scoring_service.get_category_description("product")
        assert "Pricing pages" in ai_scoring_service.get_category_description("pricing")
        assert "Technical documentation" in ai_scoring_service.get_category_description("datasheet")
        assert "Unknown category" == ai_scoring_service.get_category_description("unknown")


if __name__ == "__main__":
    # Run a simple test
    async def test_basic_functionality():
        """Basic functionality test."""
        mock_client = Mock()
        mock_client.complete = AsyncMock()
        mock_client.complete.return_value = {
            "score": 0.8,
            "primary_category": "product",
            "secondary_categories": [],
            "confidence": 0.9,
            "reasoning": "Test reasoning",
            "signals": ["test_signal"]
        }
        
        service = AIScoringService(mock_client)
        result = await service.score_page(
            url="https://test.com/product",
            title="Test Product",
            content="Test content",
            competitor="TestCorp"
        )
        
        print(f"Score: {result.score}")
        print(f"Category: {result.primary_category}")
        print(f"Confidence: {result.confidence}")
        print(f"Success: {result.success}")
    
    # Run the test
    asyncio.run(test_basic_functionality())
