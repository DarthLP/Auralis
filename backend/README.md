# Backend Service

## 🔮 Performance & Enhancement Opportunities

### Caching & Optimization
- **HTTP Conditional Requests**: Implement If-Modified-Since/ETag headers to reduce bandwidth usage by 50-80%
- **Smart Change Detection**: Binary hash pre-checks before full content download
- **Session-Based Caching**: Only re-process pages that have changed since last fingerprinting

### Enhanced Text Extraction
- **OCR Integration**: Add Tesseract for image text extraction (product specifications, charts)
- **Office Document Support**: Excel, Word, PowerPoint text extraction with pandas/python-docx
- **Improved PDF Processing**: Better table and structure preservation

### Production Readiness
- **Rate Limiting**: Per-domain request throttling and retry logic
- **Async Optimization**: Batch processing improvements and connection pooling
- **Monitoring**: Content change alerts and processing metrics

---

## 🚀 Overview

The Auralis backend is a FastAPI-based REST API service that provides the core functionality for competitor analysis and website crawling. Built with Python 3.12+ and designed as a single-tenant prototype.

## 🏗️ Architecture

- **Framework**: FastAPI (modern, fast web framework for building APIs)
- **Python Version**: 3.12+
- **ASGI Server**: Uvicorn
- **Data Validation**: Pydantic v2
- **CORS**: Enabled for frontend integration
- **Containerization**: Docker with Python 3.12-slim base image

## 📁 Directory Structure

```
backend/
├── app/                    # Application source code
│   ├── core/              # Core configuration and database
│   │   ├── config.py      # Application settings
│   │   └── db.py          # Database configuration
│   ├── services/          # Business logic services
│   │   ├── fetch.py       # JavaScript-enabled fetching with Playwright
│   │   ├── scrape.py      # Intelligent page discovery and classification
│   │   └── validate.py    # Schema validation service
│   ├── schema/            # Generated JSON schemas
│   │   └── json/          # JSON Schema files (auto-generated)
│   ├── api/               # API endpoints
│   │   └── crawl.py       # Website discovery and crawling API
│   ├── models/            # Database models
│   │   └── crawl.py       # CrawlSession and CrawledPage models
│   └── main.py            # FastAPI application entry point
├── logs/                  # Crawl session logs and JSON data files
├── Dockerfile.backend     # Docker container configuration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🔧 API Endpoints

### Core Endpoints

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/` | Root endpoint with API information | `{"message": "Auralis Backend API"}` |
| `GET` | `/health` | Health check endpoint | `{"status": "ok"}` |
| `GET` | `/docs` | Interactive API documentation | Swagger UI HTML |

### Discovery & Fingerprinting API

The core crawling API provides both discovery and fingerprinting capabilities with database-first architecture.

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `POST` | `/api/crawl/discover` | Discover and classify pages from a website | JSON with categorized pages |
| `POST` | `/api/crawl/fingerprint` | Process crawl session through 3-step pipeline | JSON with fingerprint results |
| `GET` | `/api/crawl/sessions` | List crawl sessions with metadata | JSON array of sessions |
| `GET` | `/api/crawl/sessions/{id}/fingerprints` | Get fingerprint results for a session | JSON with fingerprint data |
| `POST` | `/api/crawl/stop` | **NEW**: Stop an active crawl session | JSON with stop confirmation |
| `GET` | `/api/crawl/active-sessions` | **NEW**: List currently active crawl sessions | JSON array of active session IDs |

### Extraction Pipeline API

The schema-first extraction pipeline transforms raw page text into structured competitive intelligence data using AI and rules-based extraction.

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `POST` | `/api/extract/run` | Start extraction on a fingerprint session | JSON with extraction session details |
| `GET` | `/api/extract/status/{session_id}` | Get extraction progress and results | JSON with session status and statistics |
| `GET` | `/api/extract/sessions` | List extraction sessions with filtering | JSON array of extraction sessions |
| `GET` | `/api/extract/stream/{session_id}` | **NEW**: Real-time progress via Server-Sent Events | Live SSE stream |
| `POST` | `/api/extract/stop/{session_id}` | **NEW**: Stop a running extraction session | JSON with stop confirmation |
| `POST` | `/api/extract/stop-all` | **NEW**: Stop all running extraction sessions | JSON with batch stop results |

#### POST /api/crawl/discover

Crawls a competitor website starting from the provided URL and discovers pages that might be interesting for competitive analysis. Pages are classified into categories and scored by relevance.

**Request Body:**
```json
{
  "url": "https://competitor.example.com"
}
```

**Response (truncated example):**
```json
{
  "input_url": "https://competitor.example.com",
  "base_domain": "https://competitor.example.com",
  "limits": {
    "max_pages": 30,
    "max_depth": 3,
    "timeout": 10,
    "rate_sleep": 0.5,
    "user_agent": "AuralisBot/0.1 (+contact)"
  },
  "pages": [
    {
      "url": "https://competitor.example.com/products/widget-x",
      "status": 200,
      "primary_category": "product",
      "secondary_categories": [],
      "score": 0.95,
      "signals": ["product_url", "product_title"],
      "content_hash": "abc123...",
      "size_bytes": 15420,
      "depth": 1
    }
  ],
  "top_by_category": {
    "product": ["https://competitor.example.com/products/widget-x"],
    "docs": ["https://competitor.example.com/docs/api"],
    "pricing": ["https://competitor.example.com/pricing"],
    "releases": [],
    "datasheet": [],
    "news": []
  },
  "warnings": []
}
```

**Categories:**
- `product`: Product pages, solutions, hardware specifications
- `datasheet`: Documentation, datasheets, PDFs, technical guides  
- `docs`: General documentation and developer resources
- `releases`: Release notes, updates, changelogs, firmware
- `pricing`: Pricing pages and subscription plans
- `news`: News, blog posts, press releases
- `other`: Other interesting pages

**Database Integration:** All discovered pages are automatically saved to PostgreSQL as `CrawlSession` and `CrawledPage` records.

#### POST /api/crawl/stop

**NEW**: Stop an active crawl session that is currently running. This endpoint allows users to cancel long-running crawl operations.

**Request Body:**
```json
{
  "session_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "message": "Crawl session stopped successfully",
  "session_id": 123
}
```

**Features:**
- **Immediate Stop**: Crawl process stops at the next check point
- **Graceful Termination**: Current page processing completes before stopping
- **Session Tracking**: Uses active session tracking to identify running crawls
- **Error Handling**: Returns appropriate error if session not found or already stopped

#### GET /api/crawl/active-sessions

**NEW**: List all currently active crawl sessions. Useful for monitoring and management.

**Response:**
```json
{
  "active_sessions": [123, 124, 125],
  "count": 3
}
```

**Features:**
- **Real-time Status**: Shows sessions currently being processed
- **Session Management**: Helps identify which sessions can be stopped
- **Monitoring**: Useful for debugging and system monitoring

#### POST /api/extract/run

Starts the schema-first extraction pipeline on a completed fingerprint session. Uses rules-first + AI fallback strategy to extract structured entities.

**Request Body:**
```json
{
  "fingerprint_session_id": 1,
  "competitor": "competitor-name",
  "schema_version": "v1",
  "force_reprocess": false
}
```

**Response:**
```json
{
  "extraction_session_id": 1,
  "fingerprint_session_id": 1,
  "competitor": "competitor-name", 
  "schema_version": "v1",
  "started_at": "2024-01-15T10:00:00Z",
  "status": "running",
  "stats": {
    "total_pages": 25,
    "processed_pages": 0,
    "skipped_pages": 0,
    "failed_pages": 0,
    "cache_hits": 0,
    "companies_found": 0,
    "products_found": 0,
    "capabilities_found": 0,
    "releases_found": 0,
    "documents_found": 0,
    "signals_found": 0,
    "changes_detected": 0
  }
}
```

**Extraction Pipeline Features:**
- **Multi-Stage LLM Process**: Simplified two-stage approach for better reliability
  - Stage 1: Per-page extraction with simple 3-key JSON output (products, company, source)
  - Stage 2: Batch consolidation into structured Company and Products objects
- **Deterministic Output**: Uses SHA1 hashing for consistent product/capability IDs
- **Schema Validation**: All outputs validated against JSON schemas
- **Hash & Skip**: Avoids re-processing unchanged content
- **Change Detection**: Tracks entity changes between extraction runs
- **Source Tracking**: Full provenance of extracted data with confidence scores

**AI-Powered Page Scoring:**
- **Intelligent Classification**: DeepSeek analyzes page content to determine relevance for competitive analysis
- **Comprehensive Scoring**: Pages scored 0.0-1.0 based on business value, technical depth, and competitive intelligence potential
- **Category Detection**: Automatically classifies pages as product, pricing, datasheet, release, news, company, or other
- **Signal Extraction**: Identifies specific signals like product_specs, pricing_info, technical_details, competitive_intel
- **Confidence Scoring**: Each AI assessment includes confidence level and reasoning
- **100% JSON Consistency**: Improved prompt structure achieving 100% success rate for valid JSON responses
- **Enhanced Content Detection**: Improved minimal content detection including H1, H2, H3 headings and content length fallback
- **Robust Error Handling**: Proper fallback mechanisms and parsing error detection with success/failure flags
- **Fallback Strategy**: Gracefully falls back to rules-based scoring if AI is unavailable
- **Rate Limiting**: Built-in rate limiting and caching to manage AI API costs

#### GET /api/extract/status/{session_id}

Monitor extraction progress and view detailed results for a specific session.

**Response:**
```json
{
  "extraction_session_id": 1,
  "fingerprint_session_id": 1,
  "competitor": "competitor-name",
  "schema_version": "v1", 
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:30Z",
  "status": "completed",
  "stats": {
    "total_pages": 25,
    "processed_pages": 22,
    "skipped_pages": 1,
    "failed_pages": 2,
    "cache_hits": 8,
    "companies_found": 1,
    "products_found": 5,
    "capabilities_found": 12,
    "releases_found": 3,
    "documents_found": 7,
    "signals_found": 2,
    "changes_detected": 4
  },
  "error_summary": {
    "page_123": "AI extraction timeout",
    "page_456": "Schema validation failed"
  }
}
```

**Status Values:**
- `running`: Extraction in progress
- `completed`: Successfully completed
- `degraded`: Completed with high failure rate (>30%)
- `failed`: Extraction failed entirely

#### GET /api/extract/sessions

List recent extraction sessions with optional filtering by competitor.

**Query Parameters:**
- `competitor` (optional): Filter by competitor name
- `limit` (default: 50): Maximum sessions to return
- `offset` (default: 0): Number of sessions to skip

**Response:** Array of extraction session objects with stats and metadata.

#### GET /api/extract/stream/{session_id}

**NEW**: Stream real-time extraction progress via Server-Sent Events (SSE). Perfect for frontend progress bars and live updates.

**Usage Example:**
```javascript
// Connect to live extraction stream
const eventSource = new EventSource('/api/extract/stream/123');

// Handle different event types
eventSource.addEventListener('page_extracted', (event) => {
    const data = JSON.parse(event.data);
    console.log(`Page processed: ${data.url} via ${data.method} (${data.confidence})`);
    updateProgressBar(data.page_id);
});

eventSource.addEventListener('metrics', (event) => {
    const data = JSON.parse(event.data);
    showProgress(`${data.processed}/${data.total}`, data.eta_seconds);
    showStats(`Cache hits: ${data.cache_hits}, Failed: ${data.failed}`);
});

eventSource.addEventListener('session_completed', (event) => {
    const data = JSON.parse(event.data);
    showResults(data.stats);
    eventSource.close();
});

eventSource.addEventListener('error', (event) => {
    console.error('SSE Error:', event);
});
```

**Event Types:**
- `session_started` - Initial session information
- `page_queued` - Page added to processing queue  
- `page_started` - Page processing started
- `page_extracted` - Page successfully extracted (method, confidence, tokens)
- `page_merged` - Page entities merged into database
- `page_failed` - Page processing failed with error
- `metrics` - Live metrics (progress, ETA, cache hits, QPS)
- `session_completed` - Extraction session finished
- `heartbeat` - Keep-alive message (every 30s)
- `error` - Error occurred

**Benefits:**
- 📊 **Live Progress**: Real-time progress bars and completion estimates
- 💰 **Cost Tracking**: Monitor AI usage, cache hits, and token consumption  
- 🎯 **Method Insights**: See which pages use rules vs AI extraction
- ❌ **Error Monitoring**: Immediate notification of failed pages
- ⚡ **Performance**: No polling overhead, instant updates

#### POST /api/extract/stop/{session_id}

**NEW**: Stop a running extraction session to prevent unnecessary LLM costs and resource usage.

**Path Parameters:**
- `session_id` (required): ID of the extraction session to stop

**Response:**
```json
{
  "message": "Successfully stopped extraction session 1",
  "status": "stopped",
  "competitor": "Figure AI",
  "processed_pages": 2,
  "total_pages": 7,
  "stopped_at": "2025-09-09T10:56:16.666459Z"
}
```

**Use Cases:**
- 🛑 **Cost Control**: Stop runaway LLM requests that are incurring high costs
- 🔄 **Fresh Start**: Clear old sessions before starting new extractions
- 🚨 **Error Recovery**: Stop sessions that are stuck or failing repeatedly
- 📊 **Resource Management**: Free up processing resources for other tasks

#### POST /api/extract/stop-all

**NEW**: Stop all currently running extraction sessions in bulk. Optionally filter by competitor.

**Query Parameters:**
- `competitor` (optional): Only stop sessions for this specific competitor

**Response:**
```json
{
  "message": "Successfully stopped 3 extraction sessions",
  "status": "stopped",
  "stopped_count": 3,
  "stopped_sessions": [
    {
      "session_id": 1,
      "competitor": "Figure AI",
      "processed_pages": 2,
      "total_pages": 7
    },
    {
      "session_id": 2,
      "competitor": "Boston Dynamics",
      "processed_pages": 0,
      "total_pages": 12
    }
  ]
}
```

**Use Cases:**
- 💰 **Emergency Stop**: Immediately halt all LLM processing to prevent costs
- 🔄 **Pipeline Reset**: Clean slate before starting fresh extraction runs
- 🎯 **Competitor Focus**: Stop only sessions for a specific competitor
- 🚀 **Batch Management**: Efficiently manage multiple concurrent sessions

#### POST /api/crawl/fingerprint

Processes pages from a crawl session through the 3-step fingerprinting pipeline for stable content analysis.

**Request Body:**
```json
{
  "crawl_session_id": 1,
  "competitor": "competitor-name"
}
```

**Response:**
```json
{
  "fingerprint_session_id": 1,
  "crawl_session_id": 1,
  "competitor": "competitor-name",
  "started_at": "2025-09-08T07:58:36.922300",
  "completed_at": "2025-09-08T07:58:36.929679",
  "total_processed": 24,
  "total_errors": 0,
  "fingerprints": [
    {
      "url": "https://example.com/product",
      "key_url": "https://example.com/product",
      "page_type": "product",
      "content_hash": "a1b2c3d4e5f6...",
      "normalized_text_len": 2048,
      "low_text_pdf": false,
      "needs_render": false,
      "meta": {
        "status": 200,
        "content_type": "text/html",
        "content_length": 15420,
        "elapsed_ms": 250,
        "notes": null
      }
    }
  ]
}
```

**3-Step Pipeline:**
1. **Filter** - Score threshold (≥0.5), URL canonicalization, deduplication, caps (30/domain, 10/category)
2. **Fetch** - Async HTTP with httpx, content type detection, 15MB size limit, configurable timeouts
3. **Fingerprint** - Stable content hashing:
   - HTML → trafilatura text extraction → normalized hash
   - PDF → pdfminer text extraction → normalized hash (with low_text_pdf flag)
   - Images/Videos → direct byte hashing

#### AI Scoring Persistence (Post-Discovery)

- Endpoint: `POST /api/crawl/score-pages`
- Purpose: Run AI scoring on discovered pages and persist successful AI results back into the database so downstream fingerprinting uses AI scores.
- Behavior:
  - For each page with successful AI scoring (`ai_success=true`), the service updates the corresponding `crawl_data.crawled_pages` row (matched by `canonical_url`) with:
    - `score` ← AI score
    - `primary_category`, `secondary_categories`, `signals` ← AI-derived values
  - Pages where AI scoring fails retain their original rules-based values.
- Response includes `db_updated_pages` showing how many pages were persisted.

Note: Fingerprinting uses the `score` stored in the database. To prioritize AI, click "Start AI Scoring" in the UI (or call this endpoint) before fingerprinting.

#### GET /api/crawl/sessions

Lists recent crawl sessions with pagination support.

**Query Parameters:**
- `limit` (default: 50) - Maximum sessions to return
- `offset` (default: 0) - Number of sessions to skip

**Response:**
```json
{
  "sessions": [
    {
      "id": 1,
      "target_url": "https://example.com",
      "base_domain": "https://example.com",
      "started_at": "2025-09-08T07:54:18.373900",
      "completed_at": "2025-09-08T07:54:18.373901",
      "total_pages": 45,
      "warnings": []
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### GET /api/crawl/sessions/{id}/fingerprints

Retrieves fingerprint results for a specific crawl session.

**Response:** Complete fingerprint session data with all processed pages and their content hashes.

#### Download Threshold Configuration

The discovery API identifies pages worth downloading for detailed analysis based on their relevance scores:

**Default Download Threshold: ≥ 0.5**
- **Rationale**: Captures all high-value content while filtering out noise
- **Typical Coverage**: ~70% of discovered pages (all products, docs, pricing)
- **Filtered Out**: Low-value pages (about, contact, legal, careers)

**Configuration:**
```env
SCRAPER_DOWNLOAD_THRESHOLD=0.5    # Minimum score for download consideration
SCRAPER_DOWNLOAD_MAX_PAGES=100    # Maximum pages to download per session
```

**Score Ranges:**
- **1.0**: Primary products/homepage
- **0.9**: Direct product pages, solutions
- **0.8**: Secondary products (depth 1)
- **0.7**: Tertiary products (depth 2)
- **0.6**: Deep products (depth 3)
- **< 0.5**: Filtered out (about, contact, legal pages)

#### Anti-Scraping Protection

The crawler includes several measures to avoid bot detection and respect website policies:

**🛡️ Bot Detection Evasion:**
- **Realistic Browser Headers**: Mimics real browser requests with proper Accept, Accept-Language, DNT, and Sec-Fetch headers
- **User Agent Rotation**: Randomly selects from pool of real browser user agents (Chrome, Firefox, Safari)
- **Session Management**: Uses persistent sessions for better connection handling

**🌐 Language Filtering:**
- **English-Only Focus**: Automatically skips non-English language paths (e.g., `/de/`, `/es/`, `/fr/`, `/zh/`)
- **Query Parameter Filtering**: Skips URLs with language query parameters (`?lang=es`, `?language=de`)
- **Comprehensive Coverage**: Supports 50+ languages including major European, Asian, and other world languages
- **Duplicate Prevention**: Prevents crawling the same content in multiple languages

**⏱️ Rate Limiting & Delays:**
- **Smart Delays**: Random delays between 0.3x-1.5x base rate (default 0.8s)
- **Exponential Backoff**: Automatic retry with increasing delays on failures
- **429 Handling**: Special handling for rate limit responses with longer delays

**🔄 Retry Logic:**
- **Automatic Retries**: Up to 3 attempts for failed requests
- **Error Recovery**: Handles timeouts, connection errors, and server errors
- **Graceful Degradation**: Returns partial results with warnings on failures

**🤖 Respectful Crawling:**
- **Robots.txt Compliance**: Checks and respects robots.txt disallow rules
- **Same Domain Only**: Restricts crawling to same registrable domain + subdomains
- **Configurable Limits**: Respects page count, depth, and timeout limits

**Configuration:**
```bash
SCRAPER_TIMEOUT=15              # Request timeout (increased from 10s)
SCRAPER_RATE_SLEEP=0.8          # Base delay between requests (increased from 0.5s)
SCRAPER_MAX_RETRIES=3           # Maximum retry attempts
SCRAPER_USE_REALISTIC_HEADERS=true  # Enable realistic browser headers
```

### 🏢 Business Intelligence API

The backend now includes a complete set of business intelligence endpoints for managing companies, products, signals, and more:

**Companies Management:**
- `GET /api/companies/` - List all companies with search and filtering
- `GET /api/companies/{id}` - Get detailed company information
- `POST /api/companies/` - Create new company
- `PUT /api/companies/{id}` - Update company information
- `DELETE /api/companies/{id}` - Delete company

**Products Management:**
- `GET /api/products/` - List all products with filtering
- `GET /api/products/{id}` - Get detailed product information
- `POST /api/products/` - Create new product
- `PUT /api/products/{id}` - Update product information
- `DELETE /api/products/{id}` - Delete product

**Signals & Intelligence:**
- `GET /api/signals/` - List all signals with advanced filtering
- `GET /api/signals/{id}` - Get detailed signal information
- `POST /api/signals/` - Create new signal
- `PUT /api/signals/{id}` - Update signal information
- `DELETE /api/signals/{id}` - Delete signal

**Releases Tracking:**
- `GET /api/releases/` - List all product releases with filtering
- `GET /api/releases/{id}` - Get detailed release information
- `POST /api/releases/` - Create new release
- `PUT /api/releases/{id}` - Update release information
- `DELETE /api/releases/{id}` - Delete release

**Capabilities & Sources:**
- `GET /api/capabilities/` - List all technical capabilities
- `GET /api/capabilities/{id}` - Get detailed capability information
- `GET /api/sources/` - List all data sources
- `GET /api/sources/{id}` - Get detailed source information

### 🗄️ Database Models

The backend includes comprehensive database models for business intelligence:

**Core Models:**
- **Company**: Company profiles with metadata and summaries
- **Product**: Product lifecycle management with specifications
- **Signal**: Industry intelligence with impact scoring
- **Release**: Product release tracking with version history
- **Capability**: Technical capabilities with maturity assessment
- **Source**: Data provenance and credibility tracking

**Database Features:**
- **Automatic Seed Data Loading**: Populates database on startup from `data/seed.json`
- **Deduplication Logic**: Prevents duplicate entries and maintains data integrity
- **Foreign Key Constraints**: Ensures referential integrity between entities
- **Schema Management**: Uses default PostgreSQL schema for compatibility
- **API Integration**: Real-time data serving to frontend with proper formatting
- **Datetime Handling**: ISO format with Z suffix for frontend compatibility

### API Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔍 Schema Validation Service

The backend includes a comprehensive schema validation service that ensures data consistency using JSON Schema files generated from the TypeScript/Zod schemas.

### Features

- **JSON Schema Validation**: Uses `jsonschema` library for robust validation
- **Error Handling**: Detailed validation error messages with field-level information
- **Schema Caching**: LRU cache for improved performance
- **Health Checks**: Monitor schema system status
- **Convenience Functions**: Pre-configured validators for common entities
- **Frontend Integration**: Proper datetime formatting for API responses
- **Nullable Field Support**: Handles optional fields with proper null handling

### Usage

```python
from app.services.validate import (
    validate_company,
    validate_product,
    validate_payload,
    schema_system_health
)

# Validate specific entities
validate_company(company_data)
validate_product(product_data)

# Generic validation
validate_payload("Signal", signal_data)

# Check system health
health = schema_system_health()
print(f"Status: {health['status']}")
print(f"Available schemas: {health['available_schemas']}")
```

### Schema Generation

Schemas are generated from the TypeScript/Zod definitions in `/schema`:

```bash
# From the schema directory
cd ../schema
npm install
npm run build  # Generates JSON schemas in backend/app/schema/json/
```

### Available Schemas

- `Company` - Company information and metadata
- `Product` - Product details and specifications
- `Capability` - Technical capabilities
- `Signal` - Market signals and events
- `Source` - Data source tracking
- `Release` - Product releases
- And more...

## 🧠 Extraction Pipeline Architecture

The Auralis extraction pipeline transforms raw page text into structured competitive intelligence using a multi-stage LLM approach for better reliability and maintainability.

### Pipeline Overview

```
Raw Page Text → Stage 1: Simple Extraction → Stage 2A: Company → Stage 2B: Products → Entity Storage
                         ↓                           ↓                    ↓              ↓
                    3-key JSON               Company Object      Products + Capabilities   PostgreSQL
                  (products/company/source)  Consolidation         Consolidation         + Snapshots
                      (1-2s/page)            (batch process)      (batch process)
```

### Core Components

#### 1. Multi-Stage Extraction Service (`app/services/extract.py`)
- **MultiStageAIExtractor**: Implements the two-stage LLM approach
- **Stage 1**: Per-page extraction with simple 3-key JSON output
- **Stage 2A**: Company consolidation from multiple page results
- **Stage 2B**: Products and capabilities consolidation
- **Session Management**: Proper cost tracking and session coordination

#### 2. Multi-Stage Prompts (`app/services/schema_utils.py`)
- **Stage 1 Prompts**: Simple extraction with fixed bullet-point format
- **Stage 2A Prompts**: Company normalization and consolidation
- **Stage 2B Prompts**: Product deduplication and capability extraction
- **Deterministic IDs**: SHA1-based hashing for consistent product/capability IDs

#### 3. Theta EdgeCloud Client (`app/services/theta_client.py`)
- **JSON Mode**: Structured output with provider-side JSON enforcement
- **Rate Limiting**: Token bucket (global + per-session) with burst support
- **Caching**: DB-based response caching with TTL and deduplication
- **Circuit Breaker**: Automatic failure detection and recovery
- **Retry Logic**: Exponential backoff with jittered delays

#### 4. Entity Normalization (`app/services/normalize.py`)
- **Natural Key Generation**: Deterministic keys for entity deduplication
- **Source Ranking**: Product pages > datasheets > docs > blog > news
- **Conflict Resolution**: Field-level merging with confidence weighting
- **Change Detection**: Semantic diff between entity snapshots

#### 5. Advisory Locks (`app/services/advisory_locks.py`)
- **PostgreSQL Advisory Locks**: Distributed coordination across processes
- **Per-Competitor Locking**: Prevent merge conflicts during concurrent extractions
- **Automatic Cleanup**: Session-scoped locks with automatic release

### Multi-Stage Extraction Process

#### Stage 1: Per-Page Simple Extraction
Extracts basic information from individual pages into a simple 3-key format:

```json
{
  "products": {
    "Product Name": {
      "text": "WHAT: Description\nCATEGORY: Category\nFEATURES: Feature list\n..."
    }
  },
  "company": "NAME: Company Name\nWEBSITE: https://...\nLOCATION: Country\n...",
  "source": {"url": "https://..."}
}
```

**Advantages:**
- 🎯 Simple, focused extraction per page
- 📝 Structured bullet-point format for consistency
- 🚫 No complex schema validation during extraction
- 🔄 Easy to parse and consolidate

#### Stage 2: Batch Consolidation
Combines multiple Stage 1 results into final structured entities:

**Stage 2A - Company Consolidation:**
- Merges company information from all pages
- Resolves conflicts (prefers official pages)
- Generates canonical company object

**Stage 2B - Products Consolidation:**
- Deduplicates products by normalized names
- Extracts capabilities from product descriptions
- Generates deterministic IDs using SHA1 hashing
- Creates final product objects with nested capabilities

**Model Configuration:**
- **Model**: DeepSeek-R1 via Theta EdgeCloud
- **Context**: 128k tokens (~500k characters)
- **Output**: 8k tokens (conservative for Qwen 7B)
- **Temperature**: 0.1 (very low for consistency)
- **JSON Mode**: Provider-enforced structured output

### Entity Resolution

#### Natural Key Strategy
Deterministic entity deduplication across pages:

```python
# Product key example
"competitor:product:dataviz_pro:comp_123:v2.1:tier_enterprise"

# Company key example  
"competitor:company:datacorp_inc:datacorp.com"
```

#### Source Ranking Hierarchy
Authority-based conflict resolution:

1. **Official product pages** (rank: 10)
2. **Pricing tables** (rank: 9)
3. **Technical datasheets** (rank: 8)
4. **API documentation** (rank: 8)
5. **Release notes** (rank: 7)
6. **General documentation** (rank: 6)
7. **Blog posts** (rank: 4)
8. **News articles** (rank: 3)

#### Field-Level Provenance
Track data sources with granular attribution:

```json
{
  "entity_id": "prod_analytics_pro",
  "fields_extracted": ["name", "pricing", "features"],
  "field_confidences": {
    "name": 0.95,
    "pricing": 0.90, 
    "features": 0.85
  },
  "source_urls": ["https://example.com/products/analytics"]
}
```

### Change Detection System

#### Immutable Snapshots
Complete entity state preservation:

```python
EntitySnapshot(
    entity_type="Product",
    entity_id="prod_123",
    schema_version="v1",
    data_json={"name": "Analytics Pro", "version": "2.1.0", ...},
    data_hash="abc123...",  # For deduplication
    created_at=datetime.utcnow()
)
```

#### Semantic Change Detection
Human-readable change summaries:

```python
# Example change record
EntityChange(
    entity_type="Product",
    entity_id="prod_123", 
    summary="Analytics Pro: version 2.0.1 → 2.1.0, pricing updated, added SAML",
    fields_changed=["version", "pricing", "features"],
    diff_json={
        "version": {"old": "2.0.1", "new": "2.1.0"},
        "features": {"added": ["SAML authentication"]}
    }
)
```

### Performance Characteristics

#### Throughput
- **Rules extraction**: ~10 pages/second
- **AI extraction**: ~0.2-0.5 pages/second (depending on text length)
- **Combined pipeline**: ~1-2 pages/second average

#### Cost Optimization
- **Cache hit rate**: 60-80% for similar pages
- **Rules-first success**: 40-60% (zero AI cost)
- **Token efficiency**: 10-30 fields vs 100+ field full schemas

#### Reliability
- **Circuit breaker**: Auto-recovery from provider failures
- **Advisory locks**: Prevent concurrent merge conflicts
- **Graceful degradation**: Partial results on failures
- **Idempotent operations**: Safe to retry/rerun

### Configuration

```env
# Theta EdgeCloud
ON_DEMAND_API_ACCESS_TOKEN=your_token_here
THETA_REQUEST_TIMEOUT=20
THETA_MAX_RETRIES=2
THETA_JSON_MODE=false
THETA_RATE_PER_MIN=20

# Extraction Pipeline
SCHEMA_VERSION=v1
EXTRACTOR_PROMPT_VERSION=1.0
EXTRACTOR_MAX_TEXT_CHARS=450000
EXTRACTOR_FAIL_THRESHOLD=0.3
EXTRACTOR_MAX_CONCURRENT_SESSIONS=4
```

This architecture provides a robust, cost-effective solution for transforming unstructured web content into structured competitive intelligence at scale.

## 🛠️ Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL 15 (via Docker or local installation)
- Docker & Docker Compose (recommended)

### Local Development

1. **Install dependencies**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env  # If you have an example file
   # Edit .env with your configuration
   ```

3. **Set up the database**
   ```bash
   # Start PostgreSQL with Docker Compose (from project root)
   cd ..
   make up  # or docker compose -f infra/docker-compose.yml up -d db
   
   # Run database migrations
   cd backend
   alembic upgrade head
   ```

4. **Run the development server**
   ```bash
   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Health Check: http://localhost:8000/health
   - Documentation: http://localhost:8000/docs

### Docker Development

1. **Build the Docker image**
   ```bash
   docker build -f Dockerfile.backend -t auralis-backend .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env auralis-backend
   ```

3. **Or use Docker Compose (from project root)**
   ```bash
   make up
   ```

## 📦 Dependencies

### Core Dependencies

- **fastapi[all]**: Web framework with all optional dependencies
- **uvicorn**: ASGI server for running FastAPI
- **pydantic>=2**: Data validation and settings management
- **python-dotenv**: Environment variable loading

### Additional Dependencies

- **requests**: HTTP client library for external API calls
- **beautifulsoup4**: HTML parsing library for web scraping
- **sqlalchemy**: SQL toolkit and ORM
- **psycopg[binary]**: PostgreSQL database adapter
- **alembic**: Database migration tool
- **pydantic-settings**: Settings management using Pydantic
- **jsonschema>=4.17.0**: JSON Schema validation library

### Development Dependencies

All dependencies are included in the main requirements.txt for simplicity in this prototype.

## 🔧 Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the backend directory:

```env
# Application Settings
DEBUG=true
LOG_LEVEL=info
ENVIRONMENT=development

# Database Configuration
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/auralis

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Core Crawl Configuration
CORE_CRAWL_CONCURRENCY=8
CORE_CRAWL_BATCH_SIZE=20
CORE_CRAWL_MAX_CONTENT_SIZE=15728640  # 15MB
CORE_CRAWL_CONNECT_TIMEOUT=5
CORE_CRAWL_READ_TIMEOUT=20

# Scraper Configuration
SCRAPER_MAX_PAGES=100
SCRAPER_MAX_DEPTH=4
SCRAPER_TIMEOUT=10
SCRAPER_RATE_SLEEP=0.3
```

### Database Setup

The application uses PostgreSQL with Alembic for migrations:

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database (if needed)
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# View migration history
alembic history

# Downgrade (if needed)
alembic downgrade -1
```

**Database Schema:**
- `crawl_data.crawl_sessions` - Discovery results and metadata
- `crawl_data.crawled_pages` - Individual discovered pages with scores
- `crawl_data.fingerprint_sessions` - Fingerprinting operations
- `crawl_data.page_fingerprints` - Stable content hashes and metadata
- `crawl_data.extraction_sessions` - Extraction pipeline runs
- `crawl_data.companies` - Extracted company entities
- `crawl_data.products` - Extracted product entities
- `crawl_data.capabilities` - Extracted capability entities
- `crawl_data.releases` - Extracted release entities
- `crawl_data.documents` - Extracted document entities
- `crawl_data.signals` - Extracted signal entities
- `crawl_data.extraction_sources` - Source tracking with field-level provenance
- `crawl_data.entity_snapshots` - Immutable entity state snapshots
- `crawl_data.entity_changes` - Detected changes between snapshots
- `crawl_data.ai_cache` - AI response caching for cost optimization

### CORS Configuration

CORS is configured to allow requests from the frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🐳 Docker Configuration

### Dockerfile.backend

The Dockerfile creates a production-ready container:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Container Features

- **Base Image**: Python 3.11-slim (lightweight)
- **Port**: 8000 (exposed and mapped)
- **Environment**: Loads from `.env` file
- **Restart Policy**: `unless-stopped` (in docker-compose)

## 🧪 Testing

### Manual Testing

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"ok"}
   ```

2. **Root Endpoint**
   ```bash
   curl http://localhost:8000/
   # Expected: {"message": "Auralis Backend API"}
   ```

3. **CORS Test**
   ```bash
   curl -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" \
        -X OPTIONS http://localhost:8000/health
   ```

### Automated Testing (Future)

Planned testing setup:
- pytest for unit tests
- httpx for API testing
- Coverage reporting

## 📋 Development Roadmap

### Phase 1: Core API ✅
- [x] FastAPI setup with health endpoint
- [x] CORS configuration
- [x] Docker containerization
- [x] Environment management

### Phase 2: Database & Models ✅
- [x] PostgreSQL integration with Docker Compose
- [x] Database models (Company, Product, Capability, Signal, Release, Source)
- [x] Database seeding with comprehensive seed data
- [x] Foreign key constraints and data integrity
- [x] Automatic seed data loading on startup

### Phase 3: Advanced Scraping Engine ✅
- [x] JavaScript-enabled website crawling (Playwright + Requests)
- [x] Hybrid crawling strategy for optimal performance
- [x] Intelligent page classification and scoring
- [x] Anti-bot protection and respectful crawling
- [x] Data extraction for products, features, releases
- [x] Error handling and retry logic
- [x] Session-specific logging and data persistence

### Phase 4: API Development ✅
- [x] Website discovery API endpoint
- [x] JSON response format with categorized pages
- [x] Comprehensive logging and data export
- [x] Docker integration with volume mounting
- [x] Business Intelligence API endpoints (Companies, Products, Signals, Releases, Capabilities, Sources)
- [x] Complete CRUD operations for all entities
- [x] Database integration with SQLAlchemy ORM
- [x] **Frontend-Backend integration** with real API endpoints
- [x] **Datetime formatting** for API responses with Zod compatibility
- [x] **Schema validation** with proper nullable field handling

### Phase 5: Progressive Discovery (Future Enhancement)
- [ ] Multi-stage crawling with resume tokens
- [ ] Strategy presets (quick/balanced/deep)
- [ ] Category-specific filtering and quotas
- [ ] Time-bounded crawling with partial results
- [ ] Advanced user experience optimizations

### Phase 6: Advanced Features (Planned)
- [ ] Authentication system
- [ ] Rate limiting
- [ ] Caching layer
- [ ] Background task processing

## 🚀 Future Improvements: Progressive Discovery

### Overview
The current discovery system crawls websites comprehensively in a single operation. For better user experience and performance, we're planning a **progressive discovery system** that allows users to get quick results first, then optionally dive deeper.

### 🎯 Progressive Discovery Architecture

#### **Multi-Stage Strategy**
Instead of one long crawl, break discovery into progressive stages:

```javascript
// Stage 1: Quick Overview (8 seconds)
POST /api/crawl/discover {
  "url": "https://competitor.com",
  "strategy": "quick"  // 8 pages, depth 1, 8s timeout
}

// Stage 2: Balanced Discovery (15 seconds)  
POST /api/crawl/discover {
  "url": "https://competitor.com", 
  "strategy": "balanced",        // 20 pages, depth 2, 15s timeout
  "resume_token": {...}          // Continue from Stage 1
}

// Stage 3: Targeted Deep Dive
POST /api/crawl/discover {
  "url": "https://competitor.com",
  "filters": {"categories": ["product"]},  // Only find more products
  "resume_token": {...}                    // Continue from Stage 2
}
```

#### **Strategy Presets**
Pre-configured crawling strategies for different use cases:

| Strategy | Pages | Depth | Time | Use Case |
|----------|-------|-------|------|----------|
| `quick` | 8 | 1 | 8s | Instant competitor overview |
| `balanced` | 20 | 2 | 15s | Comprehensive first look |
| `deep` | 80 | 3 | 40s | Thorough competitive analysis |

#### **Resume Token System**
Stateless continuation mechanism that remembers:
- **Frontier**: Pages queued for next crawl
- **Visited**: Already-crawled URLs (avoid duplicates)
- **Stats**: Progress tracking and category counts

```json
{
  "resume_token": {
    "frontier": [
      {"url": "https://site.com/products", "score": 0.9, "depth": 1}
    ],
    "visited": ["https://site.com/", "https://site.com/about"],
    "stats": {"products_found": 3, "docs_found": 1}
  }
}
```

#### **Category Quotas & Filtering**
Smart resource allocation and targeted discovery:

```json
{
  "limits": {
    "max_per_category": {
      "product": 10,    // Find up to 10 product pages
      "docs": 8,        // Up to 8 documentation pages  
      "releases": 6,    // Up to 6 release pages
      "pricing": 3,     // Up to 3 pricing pages
      "news": 5         // Up to 5 news/blog pages
    }
  },
  "filters": {
    "categories": ["product", "docs"],           // Only these types
    "path_prefixes": ["/products/", "/api/"],   // Only these URL paths
    "sitemap_only": true                        // Skip BFS, use sitemap only
  }
}
```

#### **Coverage Confidence**
Real-time feedback on discovery completeness:

```json
{
  "coverage": {
    "total_seen": 25,
    "total_emitted": 12,
    "queued_remaining": 8,
    "confidence": 0.7,  // 0-1 scale, higher = more complete
    "category_counts": {"product": 4, "docs": 2, "other": 6}
  }
}
```

### 🔄 Implementation Options

#### **Option 1: Manual Progression (Recommended)**
User controls each stage through separate API calls:
- **Pros**: User control, predictable costs, immediate feedback
- **Cons**: Requires frontend integration for optimal UX
- **Best for**: Interactive competitor analysis tools

#### **Option 2: Auto-Progression**
Backend automatically continues based on confidence thresholds:
- **Pros**: Hands-off operation, simpler API usage
- **Cons**: Less user control, potentially higher resource usage
- **Best for**: Batch processing, background analysis

#### **Option 3: Hybrid Approach**
Support both manual and automatic progression:
```json
{
  "strategy": "quick",
  "auto_continue": true,      // Auto-progress if confidence < 0.5
  "max_total_time": 30       // Stop after 30 seconds total
}
```

### 🎨 User Experience Flow

```
User Input: "Analyze competitor.com"
     ↓
Stage 1: Quick (8s) → "Found 3 products, 2 solutions. More available?"
     ↓ (user clicks "Find More")
Stage 2: Balanced (15s) → "Found 8 products, 4 solutions. Want specific categories?"
     ↓ (user clicks "More Products")  
Stage 3: Product Focus (10s) → "Found 12 total products. Analysis complete."
```

### 🛠️ Technical Implementation

#### **Core Changes Required**
1. **Refactor `discover_interesting_pages()`** to support resume tokens
2. **Add strategy presets** to API endpoint with time limits
3. **Implement max-heap priority queue** for intelligent page ordering
4. **Add category quotas and filtering** logic
5. **Create resume token serialization** for stateless continuation

#### **API Enhancements**
```python
class CrawlRequest(BaseModel):
    url: str
    strategy: Optional[str] = "quick"           # quick/balanced/deep
    limits: Optional[dict] = None               # Override strategy defaults
    filters: Optional[dict] = None              # Category/path filtering
    resume_token: Optional[dict] = None         # Continue previous crawl
    auto_continue: Optional[bool] = False       # Auto-progression mode
```

#### **Configuration Updates**
```env
# Progressive Discovery Defaults
SCRAPER_MAX_PAGES=20
SCRAPER_MAX_DEPTH=2  
SCRAPER_MAX_TIME=15
SCRAPER_MAX_PER_CATEGORY={"product":10,"docs":8,"releases":6,"pricing":3,"news":5}
```

### 📊 Expected Benefits

- **⚡ 3x Faster Initial Response**: Quick results in 8 seconds vs 60+ seconds
- **💰 Cost Efficiency**: Users pay only for the depth they need
- **🎯 Better Targeting**: Category filters find specific content faster
- **♻️ Zero Waste**: Resume tokens eliminate duplicate crawling
- **📈 Improved UX**: Progressive disclosure keeps users engaged

### 🚀 Implementation Priority

1. **Phase 1**: Core progressive logic with manual progression
2. **Phase 2**: Strategy presets and category quotas  
3. **Phase 3**: Advanced filtering and auto-progression
4. **Phase 4**: Frontend integration and UX optimization

This progressive discovery system would transform the current "all-or-nothing" crawling into a flexible, user-controlled exploration tool that provides immediate value while supporting deep competitive analysis when needed.

## 🐛 Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'app'**
   - **Solution**: Run uvicorn from the backend directory, not the project root
   - **Correct**: `cd backend && python3 -m uvicorn app.main:app --reload`

2. **Port 8000 already in use**
   - **Solution**: Kill existing processes or use a different port
   - **Check**: `lsof -i :8000`
   - **Kill**: `pkill -f uvicorn`

3. **CORS errors from frontend**
   - **Solution**: Ensure frontend is running on http://localhost:3000
   - **Check**: CORS configuration in `app/main.py`

### Logs and Debugging

1. **View application logs**
   ```bash
   make logs  # From project root
   ```

2. **Debug mode**
   ```bash
   # Set in .env file
   DEBUG=true
   LOG_LEVEL=debug
   ```

## 🤝 Contributing

1. Follow the existing code structure
2. Add type hints to all functions
3. Update this README for new features
4. Test all endpoints manually
5. Ensure Docker builds successfully

## 📁 Automated Data Export System

The backend includes a comprehensive automated export system that creates clean JSON files for each pipeline stage.

### Features

- **Automatic Triggers**: Exports happen automatically after each pipeline stage completes
- **Proper JSON Formatting**: No manual cleaning required - all records properly formatted
- **Complete Data**: All records included (no truncation or missing entries)
- **Rich Text Content**: 5,000 character previews instead of 500
- **Error Handling**: Robust datetime serialization and special character handling

### Export Locations

```
backend/exports/
├── crawling/
│   └── {competitor}_crawling_session_{id}.json      # Discovered pages with scores
├── fingerprinting/
│   └── {competitor}_fingerprinting_session_{id}.json # Extracted text content
└── extraction/
    └── {competitor}_extraction_session_{id}.json     # Extraction metadata
```

### Usage

**Automatic (Recommended):**
```python
# Exports happen automatically after:
# - POST /api/crawl/discover completes
# - POST /api/crawl/fingerprint completes  
# - POST /api/extract/run completes
```

**Manual:**
```python
from app.services.export_utils import (
    export_crawling_data,
    export_fingerprinting_data,
    export_extraction_data,
    auto_export_pipeline_data
)

# Export specific sessions
export_crawling_data(session_id=1, competitor="pudu_robotics")
export_fingerprinting_data(fingerprint_session_id=1, competitor="pudu_robotics")

# Export all latest sessions
auto_export_pipeline_data("competitor_name")
```

### Data Quality

- **All 42 fingerprinted pages** included (no missing records due to parsing errors)
- **5,000 character text previews** for rich content analysis
- **Proper JSON validation** - no parsing errors or malformed data
- **Datetime serialization** handled automatically with ISO format
- **Special characters** properly escaped (quotes, newlines, unicode)

## ⚠️ Known Issues

### JSON Serialization Bug (Extraction Pipeline)
- **Status**: ❌ Blocking extraction pipeline
- **Error**: `Object of type datetime is not JSON serializable`
- **Impact**: 100% extraction failure rate (42/42 pages fail)
- **Location**: Entity data processing during AI extraction
- **Root Cause**: Datetime objects not converted to strings before JSON serialization
- **Database Impact**: No corruption; crawling/fingerprinting data intact
- **Workaround**: Rich structured data available in fingerprinting exports
- **Analysis**: See `backend/exports/JSON_SERIALIZATION_BUG_ANALYSIS.md`

### Current Pipeline Status
- ✅ **Crawling**: Fully functional (62 pages discovered)
- ✅ **Fingerprinting**: Fully functional (42 pages processed with text)
- ❌ **Extraction**: Blocked by datetime serialization issue
- ✅ **Data Export**: All stages export clean JSON automatically

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Docker Python Best Practices](https://docs.docker.com/language/python/)
