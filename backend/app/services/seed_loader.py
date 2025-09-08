"""
Seed data loader service.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.company import Company, CompanySummary
from app.models.product import Product, Capability, ProductCapability
from app.models.signal import Signal, Release, Source

logger = logging.getLogger(__name__)


def load_seed_data(db: Session, seed_file_path: str = "data/seed.json") -> Dict[str, int]:
    """
    Load seed data from JSON file into the database.
    
    Args:
        db: Database session
        seed_file_path: Path to the seed JSON file
        
    Returns:
        Dictionary with counts of loaded entities
    """
    try:
        # Load seed data from JSON file
        with open(seed_file_path, 'r') as f:
            seed_data = json.load(f)
        
        counts = {
            'companies': 0,
            'company_summaries': 0,
            'products': 0,
            'capabilities': 0,
            'product_capabilities': 0,
            'signals': 0,
            'releases': 0,
            'sources': 0
        }
        
        # Load companies
        for company_data in seed_data.get('companies', []):
            company = Company(
                id=company_data['id'],
                name=company_data['name'],
                aliases=company_data.get('aliases', []),
                hq_country=company_data.get('hq_country'),
                website=company_data.get('website'),
                status=company_data.get('status', 'active'),
                tags=company_data.get('tags', []),
                logo_url=company_data.get('logoUrl'),
                is_self=company_data.get('isSelf', False)
            )
            db.add(company)
            counts['companies'] += 1
        
        # Load company summaries (deduplicate by company_id)
        seen_company_ids = set()
        for summary_data in seed_data.get('company_summaries', []):
            company_id = summary_data['company_id']
            if company_id not in seen_company_ids:
                summary = CompanySummary(
                    company_id=company_id,
                    one_liner=summary_data['one_liner'],
                    founded_year=summary_data.get('founded_year'),
                    hq_city=summary_data.get('hq_city'),
                    employees=summary_data.get('employees'),
                    footprint=summary_data.get('footprint'),
                    sites=summary_data.get('sites', []),
                    sources=summary_data.get('sources', [])
                )
                db.add(summary)
                counts['company_summaries'] += 1
                seen_company_ids.add(company_id)
        
        # Load capabilities
        for capability_data in seed_data.get('capabilities', []):
            capability = Capability(
                id=capability_data['id'],
                name=capability_data['name'],
                definition=capability_data.get('definition'),
                tags=capability_data.get('tags', [])
            )
            db.add(capability)
            counts['capabilities'] += 1
        
        # Load products
        for product_data in seed_data.get('products', []):
            product = Product(
                id=product_data['id'],
                company_id=product_data['company_id'],
                name=product_data['name'],
                category=product_data['category'],
                stage=product_data['stage'],
                markets=product_data.get('markets', []),
                tags=product_data.get('tags', []),
                short_desc=product_data.get('short_desc'),
                product_url=product_data.get('product_url'),
                docs_url=product_data.get('docs_url'),
                media=product_data.get('media'),
                spec_profile=product_data.get('spec_profile'),
                specs=product_data.get('specs'),
                released_at=datetime.fromisoformat(product_data['released_at'].replace('Z', '+00:00')) if product_data.get('released_at') else None,
                eol_at=datetime.fromisoformat(product_data['eol_at'].replace('Z', '+00:00')) if product_data.get('eol_at') else None,
                compliance=product_data.get('compliance', [])
            )
            db.add(product)
            counts['products'] += 1
        
        # Load product capabilities
        for pc_data in seed_data.get('product_capabilities', []):
            product_capability = ProductCapability(
                id=pc_data['id'],
                product_id=pc_data['product_id'],
                capability_id=pc_data['capability_id'],
                maturity=pc_data['maturity'],
                details=pc_data.get('details'),
                metrics=pc_data.get('metrics'),
                observed_at=datetime.fromisoformat(pc_data['observed_at'].replace('Z', '+00:00')) if pc_data.get('observed_at') else None,
                source_id=pc_data.get('source_id'),
                method=pc_data.get('method')
            )
            db.add(product_capability)
            counts['product_capabilities'] += 1
        
        # Load sources
        for source_data in seed_data.get('sources', []):
            source = Source(
                id=source_data['id'],
                origin=source_data['origin'],
                author=source_data.get('author'),
                retrieved_at=datetime.fromisoformat(source_data['retrieved_at'].replace('Z', '+00:00')) if source_data.get('retrieved_at') else None,
                credibility=source_data.get('credibility')
            )
            db.add(source)
            counts['sources'] += 1
        
        # Load signals
        for signal_data in seed_data.get('signals', []):
            signal = Signal(
                id=signal_data['id'],
                type=signal_data['type'],
                headline=signal_data['headline'],
                summary=signal_data.get('summary'),
                published_at=datetime.fromisoformat(signal_data['published_at'].replace('Z', '+00:00')),
                url=signal_data['url'],
                company_ids=signal_data.get('company_ids', []),
                product_ids=signal_data.get('product_ids', []),
                capability_ids=signal_data.get('capability_ids', []),
                impact=signal_data['impact'],
                source_id=signal_data.get('source_id')
            )
            db.add(signal)
            counts['signals'] += 1
        
        # Load releases (skip those with empty product_id)
        for release_data in seed_data.get('releases', []):
            product_id = release_data.get('product_id', '').strip()
            if product_id:  # Only load releases with valid product_id
                release = Release(
                    id=release_data['id'],
                    company_id=release_data['company_id'],
                    product_id=product_id,
                    version=release_data.get('version'),
                    notes=release_data.get('notes'),
                    released_at=datetime.fromisoformat(release_data['released_at'].replace('Z', '+00:00')),
                    source_id=release_data.get('source_id')
                )
                db.add(release)
                counts['releases'] += 1
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Successfully loaded seed data: {counts}")
        return counts
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading seed data: {e}")
        raise


def is_database_empty(db: Session) -> bool:
    """
    Check if the database is empty (no companies).
    
    Args:
        db: Database session
        
    Returns:
        True if database is empty, False otherwise
    """
    try:
        count = db.query(Company).count()
        return count == 0
    except Exception as e:
        logger.error(f"Error checking if database is empty: {e}")
        return True
