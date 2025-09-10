#!/usr/bin/env python3
"""
Script to add extracted data from Step 2A and 2B to the database.
"""

import json
import sys
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.models.company import Company
from app.models.product import Product, ProductCapability, Capability
from app.models.signal import Signal, Source
# from app.models.signal import Release  # Removed - no longer exists

def get_db_session():
    """Create a database session."""
    engine = create_engine(settings.DATABASE_URL)
    return Session(engine)

def normalize_name(name):
    """Normalize a name for consistent comparison."""
    return name.lower().strip()

def normalize_stage(stage):
    """Normalize stage values to match the expected enum."""
    if not stage:
        return 'alpha'  # Default to alpha when no stage is specified
    
    stage_lower = stage.lower().strip()
    
    # Map various stage descriptions to enum values
    if 'alpha' in stage_lower:
        return 'alpha'
    elif 'beta' in stage_lower:
        return 'beta'
    elif 'ga' in stage_lower or 'general availability' in stage_lower or 'released' in stage_lower:
        return 'ga'
    elif 'discontinued' in stage_lower or 'eol' in stage_lower or 'end of life' in stage_lower:
        return 'discontinued'
    elif 'deprecated' in stage_lower:
        return 'deprecated'
    elif 'pre-order' in stage_lower or 'preorder' in stage_lower:
        return 'beta'  # Pre-order typically means beta stage
    else:
        return 'alpha'  # Default to alpha for unknown stages

def normalize_maturity(maturity):
    """Normalize maturity values to match the expected enum."""
    if not maturity:
        return 'basic'  # Default to basic when no maturity is specified
    
    maturity_lower = maturity.lower().strip()
    
    # Map various maturity descriptions to enum values
    if 'basic' in maturity_lower:
        return 'basic'
    elif 'intermediate' in maturity_lower:
        return 'intermediate'
    elif 'advanced' in maturity_lower:
        return 'advanced'
    elif 'expert' in maturity_lower:
        return 'expert'
    elif 'ga' in maturity_lower or 'general availability' in maturity_lower or 'released' in maturity_lower:
        return 'ga'
    elif 'reported' in maturity_lower:
        return 'basic'  # Map "reported" to basic
    else:
        return 'basic'  # Default to basic for unknown maturity levels

def add_company_data(db: Session, company_data):
    """Add company data to the database."""
    try:
        # Check if company already exists
        existing_company = db.query(Company).filter(
            Company.name == company_data['name']
        ).first()
        
        if existing_company:
            print(f"Company '{company_data['name']}' already exists, updating...")
            # Update existing company
            existing_company.website = company_data.get('website')
            existing_company.hq_country = company_data.get('hq_country')
            existing_company.status = company_data.get('status', 'active')
            existing_company.tags = company_data.get('tags', [])
            existing_company.aliases = company_data.get('aliases', [])
            company = existing_company
        else:
            # Create new company
            company = Company(
                id=str(uuid.uuid4()),
                name=company_data['name'],
                website=company_data.get('website'),
                hq_country=company_data.get('hq_country'),
                status=company_data.get('status', 'active'),
                tags=company_data.get('tags', []),
                aliases=company_data.get('aliases', [])
            )
            db.add(company)
            db.flush()  # Get the ID
        
        # Create or update company summary
        add_company_summary(db, company, company_data)
        
        print(f"✅ Company '{company.name}' processed successfully")
        return company
        
    except Exception as e:
        print(f"❌ Error processing company '{company_data['name']}': {e}")
        return None

def add_company_summary(db: Session, company, company_data):
    """Add company summary data to the database."""
    try:
        from app.models.company import CompanySummary
        
        # Check if summary already exists
        existing_summary = db.query(CompanySummary).filter(
            CompanySummary.company_id == company.id
        ).first()
        
        if existing_summary:
            # Update existing summary
            existing_summary.one_liner = company_data.get('short_desc', '')
            existing_summary.sources = company_data.get('main_sources_used', [])
            print(f"✅ Company summary updated for '{company.name}'")
        else:
            # Create new summary
            summary = CompanySummary(
                company_id=company.id,
                one_liner=company_data.get('short_desc', ''),
                sources=company_data.get('main_sources_used', [])
            )
            db.add(summary)
            print(f"✅ Company summary created for '{company.name}'")
        
    except Exception as e:
        print(f"❌ Error processing company summary for '{company.name}': {e}")
        raise

def add_product_data(db: Session, product_data, company):
    """Add product data to the database."""
    try:
        # Check if product already exists for this company
        existing_product = db.query(Product).filter(
            Product.name == product_data['name'],
            Product.company_id == company.id
        ).first()
        
        if existing_product:
            print(f"Product '{product_data['name']}' already exists for company '{company.name}', updating...")
            # Update existing product
            existing_product.category = product_data.get('category')
            existing_product.stage = normalize_stage(product_data.get('stage'))
            existing_product.short_desc = product_data.get('short_desc')
            existing_product.product_url = product_data.get('product_url')
            existing_product.tags = product_data.get('tags', [])
            existing_product.markets = product_data.get('markets', [])
            product = existing_product
        else:
            # Create new product
            product = Product(
                id=str(uuid.uuid4()),
                name=product_data['name'],
                company_id=company.id,
                category=product_data.get('category'),
                stage=normalize_stage(product_data.get('stage')),
                short_desc=product_data.get('short_desc'),
                product_url=product_data.get('product_url'),
                tags=product_data.get('tags', []),
                markets=product_data.get('markets', [])
            )
            db.add(product)
            db.flush()  # Get the ID
        
        # Add capabilities
        if 'capabilities' in product_data:
            for cap_data in product_data['capabilities']:
                add_capability_data(db, cap_data, product)
        
        print(f"✅ Product '{product.name}' processed successfully")
        return product
        
    except Exception as e:
        print(f"❌ Error processing product '{product_data['name']}': {e}")
        return None

def add_capability_data(db: Session, capability_data, product):
    """Add capability data to the database."""
    try:
        # Check if capability already exists
        existing_capability = db.query(Capability).filter(
            Capability.name == capability_data['name']
        ).first()
        
        if not existing_capability:
            # Create new capability
            capability = Capability(
                id=str(uuid.uuid4()),
                name=capability_data['name'],
                definition=capability_data.get('definition'),
                tags=capability_data.get('tags', [])
            )
            db.add(capability)
            db.flush()
        else:
            capability = existing_capability
        
        # Check if product-capability relationship already exists
        existing_relation = db.query(ProductCapability).filter(
            ProductCapability.product_id == product.id,
            ProductCapability.capability_id == capability.id
        ).first()
        
        if not existing_relation:
            # Create product-capability relationship with normalized values
            relation = ProductCapability(
                id=str(uuid.uuid4()),
                product_id=product.id,
                capability_id=capability.id,
                maturity=normalize_maturity(capability_data.get('maturity', 'basic')),
                details=capability_data.get('details') or '',  # Convert null to empty string
                metrics=capability_data.get('metrics'),
                observed_at=capability_data.get('observed_at'),
                source_id=capability_data.get('source_id') or '',  # Convert null to empty string
                method=capability_data.get('method')
            )
            db.add(relation)
        
        print(f"✅ Capability '{capability.name}' linked to product '{product.name}'")
        
    except Exception as e:
        print(f"❌ Error processing capability '{capability_data['name']}': {e}")

def fix_existing_capabilities(db: Session):
    """Fix existing ProductCapability records to meet validation requirements."""
    try:
        # Get all ProductCapability records with invalid maturity values
        invalid_capabilities = db.query(ProductCapability).filter(
            ProductCapability.maturity.notin_(['basic', 'intermediate', 'advanced', 'expert', 'ga'])
        ).all()
        
        for cap in invalid_capabilities:
            cap.maturity = normalize_maturity(cap.maturity)
            if cap.details is None:
                cap.details = ''
            if cap.source_id is None:
                cap.source_id = ''
        
        db.commit()
        print(f"✅ Fixed {len(invalid_capabilities)} capability records")
        
    except Exception as e:
        print(f"❌ Error fixing existing capabilities: {e}")
        db.rollback()
        raise

def main():
    """Main function to process the extraction data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import extraction data into main database')
    parser.add_argument('--company-file', required=True, help='Path to company extraction file')
    parser.add_argument('--products-file', required=True, help='Path to products extraction file')
    args = parser.parse_args()
    
    print("🚀 Starting extraction data import...")
    
    # Load company data
    with open(args.company_file, 'r') as f:
        company_data = json.load(f)
    
    # Load product data
    with open(args.products_file, 'r') as f:
        products_data = json.load(f)
    
    # Create database session
    db = get_db_session()
    
    try:
        # Add company
        print("\n📊 Processing company data...")
        company = add_company_data(db, company_data['llm_response']['company'])
        
        if not company:
            print("❌ Failed to process company data")
            return
        
        # Add products
        print("\n📦 Processing products data...")
        for product_name, product_data in products_data['llm_response']['products'].items():
            add_product_data(db, product_data, company)
        
        # Fix existing capability records
        print("\n🔧 Fixing existing capability records...")
        fix_existing_capabilities(db)
        
        # Commit all changes
        db.commit()
        print("\n✅ All data imported successfully!")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
