#!/usr/bin/env python3
"""
Export utilities for creating JSON files from database data.

This module provides functions to automatically export data from each stage 
of the extraction pipeline for testing and debugging purposes.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.db import get_db


def ensure_exports_directory() -> Path:
    """Ensure the exports directory structure exists."""
    exports_dir = Path(__file__).parent.parent / "exports"
    
    # Create main exports directory
    exports_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    for subdir in ["crawling", "fingerprinting", "extraction", "llm_responses"]:
        (exports_dir / subdir).mkdir(exist_ok=True)
    
    return exports_dir


def json_serial(obj) -> str:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def export_crawling_data(session_id: int, competitor: str = "unknown") -> Path:
    """Export crawling data to JSON file with automatic formatting."""
    exports_dir = ensure_exports_directory()
    
    db = next(get_db())
    try:
        # Get data directly as rows to avoid JSON parsing issues
        result = db.execute(text("""
            SELECT 
                session_id,
                url,
                canonical_url,
                status_code,
                primary_category,
                secondary_categories,
                score,
                signals,
                depth,
                size_bytes,
                mime_type,
                content_hash,
                crawled_at
            FROM crawl_data.crawled_pages 
            WHERE session_id = :session_id
            ORDER BY score DESC
        """), {"session_id": session_id})
        
        # Convert rows to dictionaries with proper serialization
        records = []
        for row in result:
            record = {
                'crawl_session_id': row[0],
                'url': row[1],
                'canonical_url': row[2],
                'status_code': row[3],
                'primary_category': row[4],
                'secondary_categories': row[5],
                'score': row[6],
                'signals': row[7],
                'depth': row[8],
                'size_bytes': row[9],
                'mime_type': row[10],
                'content_hash': row[11],
                'crawled_at': row[12]
            }
            records.append(record)
        
        filename = f"{competitor}_crawling_session_{session_id}.json"
        filepath = exports_dir / "crawling" / filename
        
        # Write with automatic JSON serialization handling
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False, default=json_serial)
        
        print(f"✅ Exported {len(records)} crawling records to {filepath}")
        return filepath
        
    finally:
        db.close()


def export_fingerprinting_data(fingerprint_session_id: int, competitor: str = "unknown") -> Path:
    """Export fingerprinting data to JSON file with automatic formatting."""
    exports_dir = ensure_exports_directory()
    
    db = next(get_db())
    try:
        # Get data directly as rows to avoid JSON parsing issues
        result = db.execute(text("""
            SELECT 
                fingerprint_session_id,
                url,
                key_url,
                page_type,
                content_hash,
                normalized_text_len,
                LEFT(extracted_text, 5000) as extracted_text_preview,
                low_text_pdf,
                needs_render,
                fetch_status,
                content_type,
                content_length,
                processed_at
            FROM crawl_data.page_fingerprints 
            WHERE fingerprint_session_id = :fingerprint_session_id
            ORDER BY normalized_text_len DESC
        """), {"fingerprint_session_id": fingerprint_session_id})
        
        # Convert rows to dictionaries with proper serialization
        records = []
        for row in result:
            record = {
                'fingerprint_session_id': row[0],
                'url': row[1],
                'key_url': row[2],
                'page_type': row[3],
                'content_hash': row[4],
                'normalized_text_len': row[5],
                'extracted_text_preview': row[6],
                'low_text_pdf': row[7],
                'needs_render': row[8],
                'fetch_status': row[9],
                'content_type': row[10],
                'content_length': row[11],
                'processed_at': row[12]
            }
            records.append(record)
        
        filename = f"{competitor}_fingerprinting_session_{fingerprint_session_id}.json"
        filepath = exports_dir / "fingerprinting" / filename
        
        # Write with automatic JSON serialization handling
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False, default=json_serial)
        
        print(f"✅ Exported {len(records)} fingerprinting records to {filepath}")
        return filepath
        
    finally:
        db.close()


def export_extraction_data(extraction_session_id: int, competitor: str = "unknown") -> Path:
    """Export extraction session data to JSON file with automatic formatting."""
    exports_dir = ensure_exports_directory()
    
    db = next(get_db())
    try:
        # Get data directly as row to avoid JSON parsing issues
        result = db.execute(text("""
            SELECT 
                id,
                fingerprint_session_id,
                competitor,
                schema_version,
                started_at,
                completed_at,
                total_pages,
                processed_pages,
                skipped_pages,
                failed_pages,
                cache_hits,
                companies_found,
                products_found,
                capabilities_found,
                releases_found,
                documents_found,
                signals_found,
                changes_detected,
                error_summary
            FROM crawl_data.extraction_sessions
            WHERE id = :extraction_session_id
        """), {"extraction_session_id": extraction_session_id})
        
        row = result.fetchone()
        if not row:
            raise ValueError(f"Extraction session {extraction_session_id} not found")
        
        # Convert row to dictionary with proper serialization
        record = {
            'extraction_session_id': row[0],
            'fingerprint_session_id': row[1],
            'competitor': row[2],
            'schema_version': row[3],
            'started_at': row[4],
            'completed_at': row[5],
            'total_pages': row[6],
            'processed_pages': row[7],
            'skipped_pages': row[8],
            'failed_pages': row[9],
            'cache_hits': row[10],
            'companies_found': row[11],
            'products_found': row[12],
            'capabilities_found': row[13],
            'releases_found': row[14],
            'documents_found': row[15],
            'signals_found': row[16],
            'changes_detected': row[17],
            'error_summary': row[18]
        }
        
        filename = f"{competitor}_extraction_session_{extraction_session_id}.json"
        filepath = exports_dir / "extraction" / filename
        
        # Write with automatic JSON serialization handling
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False, default=json_serial)
        
        print(f"✅ Exported extraction session to {filepath}")
        return filepath
        
    finally:
        db.close()


def auto_export_pipeline_data(competitor: str = "test_competitor"):
    """Automatically export data from the latest pipeline run."""
    exports_dir = ensure_exports_directory()
    
    db = next(get_db())
    try:
        # Get latest crawl session
        result = db.execute(text("""
            SELECT id FROM crawl_data.crawl_sessions 
            ORDER BY started_at DESC LIMIT 1
        """))
        crawl_session = result.fetchone()
        
        if crawl_session:
            export_crawling_data(crawl_session[0], competitor)
        
        # Get latest fingerprint session
        result = db.execute(text("""
            SELECT id FROM crawl_data.fingerprint_sessions 
            ORDER BY id DESC LIMIT 1
        """))
        fingerprint_session = result.fetchone()
        
        if fingerprint_session:
            export_fingerprinting_data(fingerprint_session[0], competitor)
        
        # Get latest extraction session
        result = db.execute(text("""
            SELECT id FROM crawl_data.extraction_sessions 
            ORDER BY started_at DESC LIMIT 1
        """))
        extraction_session = result.fetchone()
        
        if extraction_session:
            export_extraction_data(extraction_session[0], competitor)
        
        print(f"📁 All exports saved to: {exports_dir}")
        
    finally:
        db.close()


if __name__ == "__main__":
    # Run auto export when script is called directly
    auto_export_pipeline_data("pudu_robotics")
