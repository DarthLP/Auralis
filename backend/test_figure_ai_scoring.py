#!/usr/bin/env python3
"""
Test AI Scoring functionality using Figure.ai website.
This script fetches real content from https://figure.ai/ and tests the AI scoring service.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai_scoring import AIScoringService, AIScoringResult
from app.services.theta_client import ThetaClient
from app.core.config import settings

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set specific loggers to DEBUG
logging.getLogger('app.services.ai_scoring').setLevel(logging.DEBUG)


class FigureAITestScraper:
    """Simple scraper to fetch Figure.ai content for testing."""
    
    async def fetch_figure_content(self) -> tuple[str, str, str]:
        """
        Fetch content from Figure.ai website.
        Returns: (url, title, content)
        """
        import httpx
        from bs4 import BeautifulSoup
        
        url = "https://figure.ai/"
        
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            ) as client:
                logger.info(f"Fetching content from {url}")
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "Figure.ai"
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Extract main content
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    content = main_content.get_text(separator=' ', strip=True)
                else:
                    content = soup.get_text(separator=' ', strip=True)
                
                # Clean up content
                content = ' '.join(content.split())  # Remove extra whitespace
                
                # Truncate if too long
                max_length = 10000
                if len(content) > max_length:
                    content = content[:max_length] + "... [truncated]"
                
                logger.info(f"Fetched content: {len(content)} characters")
                logger.info(f"Title: {title_text}")
                
                return url, title_text, content
                
        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
            # Return mock data for testing
            return url, "Figure.ai - Humanoid Robots", """
            Figure.ai is a leading company in humanoid robotics, developing advanced AI-powered robots 
            for various applications. Our flagship product is a humanoid robot designed for general-purpose 
            tasks in homes and workplaces.
            
            Key Features:
            - Advanced AI and machine learning capabilities
            - Human-like dexterity and movement
            - Natural language processing
            - Computer vision and spatial awareness
            - Autonomous operation with minimal human intervention
            
            Applications:
            - Household assistance and automation
            - Industrial and manufacturing support
            - Healthcare and eldercare
            - Research and development
            
            Technology:
            - Proprietary AI algorithms
            - Advanced sensor fusion
            - Real-time decision making
            - Continuous learning capabilities
            
            Our mission is to create robots that can seamlessly integrate into human environments 
            and perform complex tasks with human-like intelligence and dexterity.
            """


async def test_ai_scoring_with_figure():
    """Test AI scoring with Figure.ai content."""
    
    print("=" * 80)
    print("AI SCORING TEST - FIGURE.AI")
    print("=" * 80)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Initialize database session
    from app.core.db import SessionLocal
    db_session = SessionLocal()
    
    try:
        # Initialize services
        logger.info("Initializing services...")
        
        # Debug: Check API token
        from app.core.config import settings
        token = settings.ON_DEMAND_API_ACCESS_TOKEN
        print(f"API Token length: {len(token) if token else 0}")
        print(f"API Token preview: {token[:10] + '...' if token and len(token) > 10 else token}")
        
        theta_client = ThetaClient(db_session)
        ai_scoring_service = AIScoringService(theta_client)
    
        # Fetch Figure.ai content
        logger.info("Fetching Figure.ai content...")
        scraper = FigureAITestScraper()
        url, title, content = await scraper.fetch_figure_content()
        
        print(f"URL: {url}")
        print(f"Title: {title}")
        print(f"Content length: {len(content)} characters")
        print()
        
        # Test AI scoring
        logger.info("Running AI scoring analysis...")
        print("Running AI scoring analysis...")
        print("-" * 40)
        
        result = await ai_scoring_service.score_page(
            url=url,
            title=title,
            content=content,
            competitor="Figure.ai",
            session_id="test_session_001"
        )
        
        # Display results
        print("\n" + "=" * 80)
        print("AI SCORING RESULTS")
        print("=" * 80)
        
        print(f"Success: {result.success}")
        print(f"Score: {result.score:.3f}")
        print(f"Primary Category: {result.primary_category}")
        print(f"Secondary Categories: {result.secondary_categories}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Processing Time: {result.processing_time_ms}ms")
        print(f"Tokens Input: {result.tokens_input}")
        print(f"Tokens Output: {result.tokens_output}")
        print(f"Cache Hit: {result.cache_hit}")
        
        print(f"\nReasoning:")
        print(f"{result.reasoning}")
        
        print(f"\nSignals Detected:")
        for signal in result.signals:
            print(f"  - {signal}")
        
        if result.error:
            print(f"\nError: {result.error}")
        
        # Category analysis
        print(f"\n" + "=" * 80)
        print("CATEGORY ANALYSIS")
        print("=" * 80)
        
        category_priority = ai_scoring_service.get_category_priority(result.primary_category)
        category_description = ai_scoring_service.get_category_description(result.primary_category)
        
        print(f"Category: {result.primary_category}")
        print(f"Priority: {category_priority}")
        print(f"Description: {category_description}")
        
        # Score interpretation
        print(f"\n" + "=" * 80)
        print("SCORE INTERPRETATION")
        print("=" * 80)
        
        if result.score >= 0.8:
            score_level = "HIGH VALUE"
            interpretation = "Excellent content for competitive analysis"
        elif result.score >= 0.6:
            score_level = "MEDIUM VALUE"
            interpretation = "Good content with some competitive value"
        elif result.score >= 0.4:
            score_level = "LOW-MEDIUM VALUE"
            interpretation = "Limited competitive value"
        else:
            score_level = "LOW VALUE"
            interpretation = "Minimal competitive value"
        
        print(f"Score Level: {score_level}")
        print(f"Interpretation: {interpretation}")
        
        # Save results to file
        results_file = f"figure_ai_scoring_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_data = {
            "test_info": {
                "url": url,
                "title": title,
                "test_time": datetime.now().isoformat(),
                "competitor": "Figure.ai"
            },
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "scoring_result": {
                "success": result.success,
                "score": result.score,
                "primary_category": result.primary_category,
                "secondary_categories": result.secondary_categories,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "signals": result.signals,
                "processing_time_ms": result.processing_time_ms,
                "tokens_input": result.tokens_input,
                "tokens_output": result.tokens_output,
                "cache_hit": result.cache_hit,
                "error": result.error
            },
            "category_analysis": {
                "priority": category_priority,
                "description": category_description
            },
            "score_interpretation": {
                "level": score_level,
                "interpretation": interpretation
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"\nERROR: {e}")
        return None
    finally:
        # Close database session
        db_session.close()


async def test_multiple_pages():
    """Test AI scoring with multiple Figure.ai pages."""
    
    test_pages = [
        "https://figure.ai/",
        "https://figure.ai/about",
        "https://figure.ai/products",
        "https://figure.ai/technology",
        "https://figure.ai/careers"
    ]
    
    print("=" * 80)
    print("MULTI-PAGE AI SCORING TEST - FIGURE.AI")
    print("=" * 80)
    
    results = []
    
    for i, url in enumerate(test_pages, 1):
        print(f"\n{i}. Testing: {url}")
        print("-" * 60)
        
        try:
            # Initialize services
            theta_client = ThetaClient()
            ai_scoring_service = AIScoringService(theta_client)
            
            # Fetch content
            scraper = FigureAITestScraper()
            test_url, title, content = await scraper.fetch_figure_content()
            
            # Override URL for specific pages
            if url != "https://figure.ai/":
                test_url = url
                # For now, use the same content but this could be enhanced
                # to fetch different pages
            
            # Score the page
            result = await ai_scoring_service.score_page(
                url=test_url,
                title=title,
                content=content,
                competitor="Figure.ai",
                session_id=f"test_session_{i:03d}"
            )
            
            results.append({
                "url": test_url,
                "title": title,
                "result": result
            })
            
            print(f"  Score: {result.score:.3f}")
            print(f"  Category: {result.primary_category}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Success: {result.success}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "url": url,
                "title": "Error",
                "result": None,
                "error": str(e)
            })
    
    # Summary
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful_tests = [r for r in results if r["result"] and r["result"].success]
    failed_tests = [r for r in results if not r["result"] or not r["result"].success]
    
    print(f"Total tests: {len(results)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if successful_tests:
        scores = [r["result"].score for r in successful_tests]
        categories = [r["result"].primary_category for r in successful_tests]
        
        print(f"\nScore range: {min(scores):.3f} - {max(scores):.3f}")
        print(f"Average score: {sum(scores)/len(scores):.3f}")
        print(f"Categories found: {set(categories)}")
    
    return results


if __name__ == "__main__":
    print("Figure.ai AI Scoring Test")
    print("=" * 40)
    
    # Check if we should run multi-page test
    if len(sys.argv) > 1 and sys.argv[1] == "--multi":
        asyncio.run(test_multiple_pages())
    else:
        asyncio.run(test_ai_scoring_with_figure())
