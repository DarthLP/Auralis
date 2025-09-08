#!/usr/bin/env python3
"""
Script to analyze text statistics from extracted webpage content.
Provides total text volume and per-page metrics including highest and lowest character counts.
"""

import sys
import os
from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create direct database connection for analysis
DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/auralis"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from models.crawl import CrawlSession, CrawledPage  # Import first to avoid circular dependency
from models.core_crawl import PageFingerprint, FingerprintSession


def analyze_text_stats():
    """Analyze text statistics from the PageFingerprint table."""
    
    with SessionLocal() as db:
        # Get basic statistics
        total_pages = db.query(PageFingerprint).count()
        pages_with_text = db.query(PageFingerprint).filter(
            PageFingerprint.extracted_text.isnot(None),
            PageFingerprint.extracted_text != ""
        ).count()
        
        print(f"📊 Text Statistics Analysis")
        print(f"=" * 50)
        print(f"Total pages in database: {total_pages:,}")
        print(f"Pages with extracted text: {pages_with_text:,}")
        print(f"Pages without text: {total_pages - pages_with_text:,}")
        
        if pages_with_text == 0:
            print("\n❌ No pages with extracted text found!")
            return
        
        # Calculate total text volume
        total_chars_result = db.query(
            func.sum(func.length(PageFingerprint.extracted_text))
        ).filter(
            PageFingerprint.extracted_text.isnot(None),
            PageFingerprint.extracted_text != ""
        ).scalar()
        
        total_chars = total_chars_result or 0
        
        # Get min and max text lengths with page details
        min_result = db.query(
            PageFingerprint.url,
            PageFingerprint.page_type,
            func.length(PageFingerprint.extracted_text).label('text_length')
        ).filter(
            PageFingerprint.extracted_text.isnot(None),
            PageFingerprint.extracted_text != ""
        ).order_by(asc(func.length(PageFingerprint.extracted_text))).first()
        
        max_result = db.query(
            PageFingerprint.url,
            PageFingerprint.page_type,
            func.length(PageFingerprint.extracted_text).label('text_length')
        ).filter(
            PageFingerprint.extracted_text.isnot(None),
            PageFingerprint.extracted_text != ""
        ).order_by(desc(func.length(PageFingerprint.extracted_text))).first()
        
        # Calculate average text length
        avg_chars_result = db.query(
            func.avg(func.length(PageFingerprint.extracted_text))
        ).filter(
            PageFingerprint.extracted_text.isnot(None),
            PageFingerprint.extracted_text != ""
        ).scalar()
        
        avg_chars = avg_chars_result or 0
        
        print(f"\n📈 Volume Statistics")
        print(f"=" * 30)
        print(f"Total characters: {total_chars:,}")
        print(f"Total words (approx): {total_chars // 5:,}")  # Rough estimate: avg 5 chars per word
        print(f"Total KB: {total_chars / 1024:.1f}")
        print(f"Total MB: {total_chars / (1024 * 1024):.2f}")
        
        print(f"\n📏 Per-Page Statistics")
        print(f"=" * 30)
        print(f"Average characters per page: {avg_chars:.0f}")
        print(f"Average words per page (approx): {avg_chars / 5:.0f}")
        
        if min_result:
            print(f"\n🔻 Shortest Page")
            print(f"URL: {min_result.url}")
            print(f"Type: {min_result.page_type or 'Unknown'}")
            print(f"Characters: {min_result.text_length:,}")
            print(f"Words (approx): {min_result.text_length // 5:,}")
        
        if max_result:
            print(f"\n🔺 Longest Page")
            print(f"URL: {max_result.url}")
            print(f"Type: {max_result.page_type or 'Unknown'}")
            print(f"Characters: {max_result.text_length:,}")
            print(f"Words (approx): {max_result.text_length // 5:,}")
        
        # Get distribution by page type
        type_stats = db.query(
            PageFingerprint.page_type,
            func.count(PageFingerprint.id).label('count'),
            func.sum(func.length(PageFingerprint.extracted_text)).label('total_chars'),
            func.avg(func.length(PageFingerprint.extracted_text)).label('avg_chars')
        ).filter(
            PageFingerprint.extracted_text.isnot(None),
            PageFingerprint.extracted_text != ""
        ).group_by(PageFingerprint.page_type).order_by(desc('total_chars')).all()
        
        if type_stats:
            print(f"\n📊 Distribution by Page Type")
            print(f"=" * 50)
            print(f"{'Type':<15} {'Pages':<8} {'Total Chars':<15} {'Avg Chars':<10}")
            print(f"{'-' * 15} {'-' * 8} {'-' * 15} {'-' * 10}")
            
            for stat in type_stats:
                page_type = stat.page_type or 'Unknown'
                total_chars_type = stat.total_chars or 0
                avg_chars_type = stat.avg_chars or 0
                print(f"{page_type:<15} {stat.count:<8,} {total_chars_type:<15,} {avg_chars_type:<10.0f}")
        
        # Get top 5 longest and shortest pages
        print(f"\n🏆 Top 5 Longest Pages")
        print(f"=" * 60)
        longest_pages = db.query(
            PageFingerprint.url,
            PageFingerprint.page_type,
            func.length(PageFingerprint.extracted_text).label('text_length')
        ).filter(
            PageFingerprint.extracted_text.isnot(None),
            PageFingerprint.extracted_text != ""
        ).order_by(desc(func.length(PageFingerprint.extracted_text))).limit(5).all()
        
        for i, page in enumerate(longest_pages, 1):
            print(f"{i}. {page.text_length:,} chars - {page.page_type or 'Unknown'}")
            print(f"   {page.url}")
        
        print(f"\n🎯 Top 5 Shortest Pages")
        print(f"=" * 60)
        shortest_pages = db.query(
            PageFingerprint.url,
            PageFingerprint.page_type,
            func.length(PageFingerprint.extracted_text).label('text_length')
        ).filter(
            PageFingerprint.extracted_text.isnot(None),
            PageFingerprint.extracted_text != ""
        ).order_by(asc(func.length(PageFingerprint.extracted_text))).limit(5).all()
        
        for i, page in enumerate(shortest_pages, 1):
            print(f"{i}. {page.text_length:,} chars - {page.page_type or 'Unknown'}")
            print(f"   {page.url}")


if __name__ == "__main__":
    try:
        analyze_text_stats()
    except Exception as e:
        print(f"❌ Error analyzing text stats: {e}")
        sys.exit(1)
