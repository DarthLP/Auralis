
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import init_db, get_db
from app.services.seed_loader import load_seed_data, is_database_empty
from app.api.crawl import router as crawl_router
from app.api.core_crawl import router as core_crawl_router
from app.api.extract import router as extract_router
from app.api.extract_stream import router as extract_stream_router
from app.api.companies import router as companies_router
from app.api.products import router as products_router
from app.api.capabilities import router as capabilities_router
from app.api.signals import router as signals_router
from app.api.releases import router as releases_router
from app.api.sources import router as sources_router

# Import all models to ensure they are registered with SQLAlchemy
from app.models.crawl import *  # noqa
from app.models.core_crawl import *  # noqa
from app.models.extraction import *  # noqa
from app.models.company import *  # noqa
from app.models.product import *  # noqa
from app.models.signal import *  # noqa

app = FastAPI(title="Auralis Backend", version="1.0.0")

logger = logging.getLogger(__name__)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(crawl_router)
app.include_router(core_crawl_router)
app.include_router(extract_router)
app.include_router(extract_stream_router)
app.include_router(companies_router)
app.include_router(products_router)
app.include_router(capabilities_router)
app.include_router(signals_router)
app.include_router(releases_router)
app.include_router(sources_router)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    init_db()
    
    # Load seed data if database is empty
    try:
        db = next(get_db())
        if is_database_empty(db):
            logger.info("Database is empty, loading seed data...")
            seed_file_path = "/data/seed.json"
            counts = load_seed_data(db, seed_file_path)
            logger.info(f"Loaded seed data: {counts}")
        else:
            logger.info("Database already contains data, skipping seed data loading")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Auralis Backend API"}
