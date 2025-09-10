"""
Promotion service: upsert extracted entities into main operational tables
after a successful extraction run, so the frontend Companies/Products pages
reflect newly extracted data automatically.

This mirrors the logic from add_extraction_data.py but as importable functions
that can be used programmatically from the extraction flow.
"""

from typing import Dict, Any, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.company import Company, CompanySummary
from app.models.product import Product, ProductCapability, Capability


def _normalize_stage(stage: Optional[str]) -> str:
    if not stage:
        return 'alpha'
    s = stage.lower().strip()
    if 'alpha' in s:
        return 'alpha'
    if 'beta' in s:
        return 'beta'
    if 'ga' in s or 'general availability' in s or 'released' in s:
        return 'ga'
    if 'discontinued' in s or 'eol' in s or 'end of life' in s:
        return 'discontinued'
    if 'deprecated' in s:
        return 'deprecated'
    if 'pre-order' in s or 'preorder' in s:
        return 'beta'
    return 'alpha'


def _normalize_maturity(maturity: Optional[str]) -> str:
    if not maturity:
        return 'basic'
    m = maturity.lower().strip()
    if 'basic' in m:
        return 'basic'
    if 'intermediate' in m:
        return 'intermediate'
    if 'advanced' in m:
        return 'advanced'
    if 'expert' in m:
        return 'expert'
    if 'ga' in m or 'general availability' in m or 'released' in m:
        return 'ga'
    if 'reported' in m:
        return 'basic'
    return 'basic'


def _upsert_company(db: Session, company_data: Dict[str, Any]) -> Company:
    existing = db.query(Company).filter(Company.name == company_data.get('name')).first()
    if existing:
        existing.website = company_data.get('website')
        existing.hq_country = company_data.get('hq_country')
        existing.status = company_data.get('status') or 'active'
        existing.tags = company_data.get('tags') or []
        existing.aliases = company_data.get('aliases') or []
        company = existing
    else:
        company = Company(
            id=str(uuid.uuid4()),
            name=company_data.get('name') or 'Unknown',
            website=company_data.get('website'),
            hq_country=company_data.get('hq_country'),
            status=company_data.get('status') or 'active',
            tags=company_data.get('tags') or [],
            aliases=company_data.get('aliases') or []
        )
        db.add(company)
        db.flush()

    # Upsert summary short_desc and sources if present
    summary = db.query(CompanySummary).filter(CompanySummary.company_id == company.id).first()
    short_desc = company_data.get('short_desc') or ''
    sources = company_data.get('main_sources_used') or []
    if summary:
        summary.one_liner = short_desc
        summary.sources = sources
    else:
        db.add(CompanySummary(company_id=company.id, one_liner=short_desc, sources=sources))
    return company


def _upsert_capability(db: Session, cap_data: Dict[str, Any]) -> Capability:
    existing = db.query(Capability).filter(Capability.name == cap_data.get('name')).first()
    if existing:
        return existing
    cap = Capability(
        id=str(uuid.uuid4()),
        name=cap_data.get('name'),
        definition=cap_data.get('definition'),
        tags=cap_data.get('tags') or []
    )
    db.add(cap)
    db.flush()
    return cap


def _link_product_capability(db: Session, product: Product, capability: Capability, cap_data: Dict[str, Any]) -> None:
    existing = db.query(ProductCapability).filter(
        ProductCapability.product_id == product.id,
        ProductCapability.capability_id == capability.id
    ).first()
    if existing:
        return
    relation = ProductCapability(
        id=str(uuid.uuid4()),
        product_id=product.id,
        capability_id=capability.id,
        maturity=_normalize_maturity(cap_data.get('maturity')),
        details=(cap_data.get('details') or ''),
        metrics=cap_data.get('metrics'),
        observed_at=cap_data.get('observed_at'),
        source_id=(cap_data.get('source_id') or ''),
        method=cap_data.get('method')
    )
    db.add(relation)


def _upsert_product(db: Session, product_data: Dict[str, Any], company: Company) -> Product:
    existing = db.query(Product).filter(
        Product.name == product_data.get('name'),
        Product.company_id == company.id
    ).first()
    if existing:
        existing.category = product_data.get('category')
        existing.stage = _normalize_stage(product_data.get('stage'))
        existing.short_desc = product_data.get('short_desc')
        existing.product_url = product_data.get('product_url')
        existing.docs_url = product_data.get('docs_url')
        existing.tags = product_data.get('tags') or []
        existing.markets = product_data.get('markets') or []
        existing.specs = product_data.get('specs')
        existing.released_at = product_data.get('released_at')
        existing.eol_at = product_data.get('eol_at')
        existing.compliance = product_data.get('compliance') or []
        product = existing
    else:
        product = Product(
            id=str(uuid.uuid4()),
            company_id=company.id,
            name=product_data.get('name'),
            category=product_data.get('category'),
            stage=_normalize_stage(product_data.get('stage')),
            short_desc=product_data.get('short_desc'),
            product_url=product_data.get('product_url'),
            docs_url=product_data.get('docs_url'),
            tags=product_data.get('tags') or [],
            markets=product_data.get('markets') or [],
            specs=product_data.get('specs'),
            released_at=product_data.get('released_at'),
            compliance=product_data.get('compliance') or []
        )
        db.add(product)
        db.flush()
    # Link capabilities if provided
    for cap in (product_data.get('capabilities') or []):
        capability = _upsert_capability(db, cap)
        _link_product_capability(db, product, capability, cap)
    return product


def promote_extracted_entities_to_main(db: Session, extracted_entities: Dict[str, Any]) -> Dict[str, int]:
    """
    Promote extracted entities (Company/Product/Capability) to main tables.

    Args:
        db: SQLAlchemy session
        extracted_entities: dict like {"Company": [...], "Product": [...], ...}

    Returns:
        Counts of created/updated entities (best-effort; focuses on success path).
    """
    counts = {"companies": 0, "products": 0, "capabilities": 0}

    companies: List[Dict[str, Any]] = extracted_entities.get("Company") or []
    products: List[Dict[str, Any]] = extracted_entities.get("Product") or []

    company_obj: Optional[Company] = None
    if companies:
        # Assume single primary company in this flow
        company_obj = _upsert_company(db, companies[0])
        counts["companies"] += 1

    # Only proceed with products if we have a company to attach to
    if company_obj:
        for prod in products:
            _upsert_product(db, prod, company_obj)
            counts["products"] += 1
            # Capabilities counted approximately via product links
            counts["capabilities"] += len(prod.get('capabilities') or [])

    db.commit()
    return counts


