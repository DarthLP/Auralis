# Auralis

## 🎯 Project Overview

Auralis is an AI-powered competitor analysis tool that helps businesses track and analyze their competitors' websites, products, and changes over time. Built as a simple but extensible prototype with a modern, scalable architecture.

### 🏗️ Architecture

- **Backend**: FastAPI-based REST API with Python 3.11+
- **Frontend**: Next.js application with dashboard and drill-down views
- **Database**: PostgreSQL with structured data models
- **Scraping**: Hybrid JavaScript-enabled crawler (Playwright + Requests) with anti-bot protection
- **AI Layer**: Theta EdgeCloud integration with local fallback
- **Infrastructure**: Docker Compose for local development and deployment
- **Authentication**: Single-tenant prototype (no auth required)

## 🔮 Future Enhancements

### Performance Optimizations
- **Smart Caching**: HTTP conditional requests (If-Modified-Since, ETags) to reduce bandwidth by 50-80%
- **Binary Hash Pre-check**: Quick change detection before full content download
- **Incremental Processing**: Only process changed pages between fingerprinting sessions

### Enhanced Content Analysis  
- **OCR Integration**: Text extraction from images using Tesseract (product specs, infographics)
- **Office Document Support**: Excel (.xlsx/.xls), Word (.docx), PowerPoint (.pptx) text extraction
- **Advanced File Processing**: Enhanced PDF handling with table/structure preservation

### Scalability & Production
- **Distributed Processing**: Multi-worker fingerprinting with job queues
- **Rate Limiting**: Intelligent request throttling per domain
- **Monitoring & Alerts**: Content change notifications and system health monitoring

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** - Backend runtime
- **Docker & Docker Compose** - Containerized services
- **Make** - Development commands
- **Git** - Version control
- **PostgreSQL** - Database (via Docker)

### Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/DarthLP/Auralis.git
   cd Auralis
   ```

2. **Set up the development environment**
   ```bash
   make setup
   ```
   This will:
   - Create a Python virtual environment
   - Install all dependencies
   - Create necessary configuration files

3. **Start the backend (development mode)**
   ```bash
   make dev
   ```
   Or start all services with Docker:
   ```bash
   make up
   ```

4. **Access the application**
   - Frontend Dashboard: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Development Commands

| Command | Description |
|---------|-------------|
| `make setup` | Set up virtual environment and install dependencies |
| `make dev` | Start backend in development mode (requires venv) |
| `make up` | Start all services with Docker Compose |
| `make down` | Stop all services |
| `make logs` | View service logs in real-time |
| `make help` | Show all available commands |

#### Schema Development

| Command | Description |
|---------|-------------|
| `cd schema && npm install` | Install schema build dependencies |
| `cd schema && npm run build` | Build JSON schemas for backend validation |
| `cd schema && npm run build:watch` | Watch for schema changes and rebuild automatically |

## 📁 Project Structure

```
Auralis/
├── backend/           # FastAPI backend service
│   ├── app/          # Application code
│   │   ├── models/   # Database models (Competitor, Product, CrawlSession, etc.)
│   │   ├── services/ # Business logic (hybrid scraping, AI, validation)
│   │   │   ├── fetch.py    # JavaScript-enabled fetching with Playwright
│   │   │   ├── scrape.py   # Intelligent page discovery and classification
│   │   │   ├── validate.py # Schema validation service
│   │   │   └── export_utils.py # Automated JSON export system ✅
│   │   ├── schema/   # Generated JSON schemas for validation
│   │   │   └── json/ # JSON Schema files (auto-generated)
│   │   ├── api/      # API endpoints
│   │   │   ├── crawl.py    # Website discovery and crawling API
│   │   │   ├── core_crawl.py # Fingerprinting pipeline API
│   │   │   └── extract.py  # Extraction pipeline API (JSON bug ❌)
│   │   └── main.py   # FastAPI application
│   ├── exports/      # Automated JSON data exports ✅
│   │   ├── crawling/     # Crawl session results
│   │   ├── fingerprinting/ # Fingerprint results with text content
│   │   └── extraction/   # Extraction session metadata
│   ├── logs/         # Crawl session logs and JSON data files
│   ├── Dockerfile.backend  # Backend container config
│   ├── requirements.txt    # Python dependencies
│   └── .env          # Environment variables
├── frontend/          # Next.js frontend application
│   ├── src/          # Source code
│   ├── pages/        # Dashboard and detail pages
│   └── components/   # Reusable UI components
├── schema/           # Shared data models and validation
│   ├── enums.ts      # Core enumeration types
│   ├── specs.ts      # Flexible specification value types
│   ├── types.ts      # TypeScript interface definitions
│   ├── zod.ts        # Runtime validation schemas
│   ├── index.ts      # Re-exports all types and schemas
│   ├── build-json-schema.ts  # JSON Schema build script
│   ├── package.json  # NPM package configuration
│   ├── tsconfig.json # TypeScript configuration
│   └── README.md     # Schema documentation
├── infra/            # Infrastructure configuration
│   └── docker-compose.yml  # Service orchestration with volume mounting
├── venv/             # Python virtual environment (auto-created)
├── .python-version   # Python version specification
├── .envrc            # Automatic environment activation (direnv)
├── setup.sh          # Automated setup script
├── Makefile          # Development automation
└── README.md         # This file
```

## 📊 Data Schema

The `schema/` directory contains shared TypeScript data models and validation schemas for the Auralis platform. These schemas define the structure for tech industry intelligence data including companies, products, capabilities, signals, and more.

### Key Features

- **Type Safety**: Full TypeScript interfaces with proper optional fields
- **Runtime Validation**: Zod schemas for data validation
- **Flexible Specifications**: Support for various product specification types
- **Source Tracking**: Data provenance and credibility tracking
- **Impact Scoring**: Signal impact analysis with -2 to +2 scale

### Core Entities

- **Company**: Technology companies with status tracking
- **Product**: Product lifecycle management with specifications
- **Capability**: Technical capabilities with maturity assessment
- **Signal**: News/events with impact scoring and entity associations
- **Source**: Data provenance and credibility tracking

### Schema Validation System

The project includes a comprehensive schema validation system that ensures type safety between frontend and backend:

- **TypeScript/Zod Schemas**: Single source of truth in `/schema/zod.ts`
- **JSON Schema Generation**: Automatic conversion to JSON Schema for backend validation
- **Python Validation Service**: Backend validation using `jsonschema` library
- **Build Pipeline**: `npm run build` generates JSON schemas for backend

#### Usage

**Frontend (TypeScript):**
```typescript
// Import types
import { Company, Product, Signal } from './schema';

// Runtime validation
import { zCompany, zProduct, zSignal } from './schema';
const company = zCompany.parse(rawData);
```

**Backend (Python):**
```python
from app.services.validate import validate_company, validate_product

# Validate data against schema
validate_company(company_data)
validate_product(product_data)
```

#### Building Schemas

```bash
cd schema
npm install
npm run build  # Generates JSON schemas in /backend/app/schema/json/
```

For detailed schema documentation, see [`schema/README.md`](schema/README.md).

## 🔧 Backend API

The backend provides a RESTful API built with FastAPI for competitor analysis with **database-first architecture**:

### Core Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

### 🚀 Website Discovery & Fingerprinting API

**`POST /api/crawl/discover`** - Advanced website crawling and page discovery ✅
**`POST /api/crawl/fingerprint`** - 3-step fingerprinting pipeline for content analysis with text extraction ✅
**`GET /api/crawl/sessions`** - List crawl sessions with metadata ✅
**`GET /api/crawl/sessions/{id}/fingerprints`** - Get fingerprint results with extracted text content ✅

### 🤖 Extraction Pipeline API

**`POST /api/extract/run`** - AI-powered structured data extraction ❌ (JSON serialization bug)
**`GET /api/extract/status/{session_id}`** - Monitor extraction progress ✅
**`GET /api/extract/sessions`** - List extraction sessions ✅

### 📁 Automated Data Export System

**Automatic JSON Export** - All pipeline stages automatically export structured JSON files ✅
- **Location**: `backend/exports/{stage}/{competitor}_{stage}_session_{id}.json`
- **Stages**: crawling, fingerprinting, extraction
- **Features**: 5,000 character text previews, proper JSON formatting, all records included

#### 🎯 3-Step Fingerprinting Pipeline

1. **Filter**: Score threshold (≥0.5), URL canonicalization, deduplication, caps (100/domain, 100/category)
2. **Fetch**: Async HTTP with content type detection, 15MB size limit, 5s/20s timeouts
3. **Fingerprint**: Stable content hashing with text extraction:
   - **HTML** → trafilatura text extraction → cleaned, normalized hash
   - **PDF** → pdfminer text extraction → normalized hash (with low_text_pdf flag)
   - **Images/Videos** → direct byte hashing (no text extraction)

**Features:**
- **JavaScript-Enabled Crawling**: Full browser automation with Playwright for modern websites
- **Hybrid Performance Mode**: Smart JavaScript usage for important pages, fast requests for simple pages
- **Anti-Bot Protection**: Realistic browser headers, user agent rotation, smart delays
- **Intelligent Classification**: Automatic categorization (product, docs, pricing, news, etc.)
- **Smart Download Filtering**: Pages with score ≥ 0.5 identified for detailed analysis (filters out noise)
- **Duplicate Detection**: URL canonicalization and content hash deduplication
- **Comprehensive Logging**: Detailed session logs and complete JSON data persistence

**Request:**
```json
{
  "url": "https://competitor.example.com"
}
```

**Response:**
```json
{
  "input_url": "https://competitor.example.com",
  "base_domain": "https://competitor.example.com",
  "pages": [
    {
      "url": "https://competitor.example.com/products/widget",
      "primary_category": "product",
      "score": 0.95,
      "signals": ["product_url", "product_title"],
      "status": 200,
      "content_hash": "abc123...",
      "size_bytes": 15420
    }
  ],
  "top_by_category": {
    "product": ["https://competitor.example.com/products/widget"],
    "docs": ["https://competitor.example.com/docs/api"],
    "pricing": ["https://competitor.example.com/pricing"]
  },
  "log_file": "logs/crawl_20250907_161900.log",
  "crawl_session_id": 1,
  "pages_saved_to_db": 45
}
```

### 🧬 Core Crawl Fingerprinting API

**`POST /api/crawl/fingerprint`** - Process crawl sessions through 3-step fingerprinting pipeline

**Request:**
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

**Session Management:**
- `GET /api/crawl/sessions` - List all crawl sessions
- `GET /api/crawl/sessions/{id}/fingerprints` - Get fingerprint results for a session

### Competitor Management (Planned)

- `POST /api/competitors` - Add a new competitor
- `GET /api/competitors` - List all competitors
- `GET /api/competitors/{id}` - Get competitor details
- `POST /api/competitors/{id}/crawl` - Trigger website crawl

### Data Access (Planned)

- `GET /api/competitors/{id}/products` - Get competitor's products
- `GET /api/products/{id}` - Get product details
- `GET /api/products/{id}/changes` - Get product change history

### Features

- **CORS Enabled** - Configured for `http://localhost:3000`
- **Auto Documentation** - Swagger UI at `/docs`
- **Environment Configuration** - Via `.env` file
- **Docker Ready** - Containerized with Python 3.11-slim
- **Database Integration** - PostgreSQL with structured models
- **AI Integration** - Theta EdgeCloud with local fallback

## 🐳 Docker Services & Database Integration

### Backend Service

- **Image**: Custom build from `Dockerfile.backend`
- **Port**: 8000 (mapped to host)
- **Environment**: Loaded from `backend/.env`
- **Database Connection**: `postgresql+psycopg://postgres:postgres@db:5432/auralis`
- **Restart Policy**: `unless-stopped`

### Database Service (PostgreSQL 15)

- **Image**: PostgreSQL 15
- **Port**: 5432 (mapped to host)
- **Database**: `auralis`
- **Username/Password**: `postgres/postgres`
- **Persistent Storage**: Docker volume `postgres_data` for data persistence
- **Schema**: `crawl_data` for all crawling and fingerprinting tables

### 🗄️ Database Schema & Access

**Database Tables:**
- `crawl_data.crawl_sessions` - Discovery results and metadata
- `crawl_data.crawled_pages` - Individual discovered pages with scores
- `crawl_data.fingerprint_sessions` - Fingerprinting operations
- `crawl_data.page_fingerprints` - Stable content hashes and metadata

**Accessing the Database:**

1. **Via Docker Desktop:**
   - Open Docker Desktop app
   - Go to Containers → `infra-db-1`
   - Click "Open in Terminal" to access PostgreSQL container
   - Run: `psql -U postgres -d auralis`

2. **Via Terminal:**
   ```bash
   # Connect to PostgreSQL container
   docker exec -it infra-db-1 psql -U postgres -d auralis
   
   # View tables
   \dt crawl_data.*
   
   # Query crawl sessions
   SELECT id, target_url, total_pages, started_at FROM crawl_data.crawl_sessions;
   
   # Query fingerprint results
   SELECT url, page_type, content_hash FROM crawl_data.page_fingerprints LIMIT 5;
   ```

3. **Via Database Client (e.g., pgAdmin, DBeaver):**
   - Host: `localhost`
   - Port: `5432`
   - Database: `auralis`
   - Username: `postgres`
   - Password: `postgres`

**Database Migrations:**
```bash
# Run migrations (from backend directory)
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

### Frontend Service (Planned)

- **Image**: Custom build from `Dockerfile.frontend`
- **Port**: 3000 (mapped to host)
- **Environment**: Next.js development server

## 🛠️ Development

### Automatic Virtual Environment

The project includes automatic virtual environment setup for all collaborators:

#### **Option 1: Automatic Setup (Recommended)**
```bash
make setup  # One-time setup
make dev    # Start development server
```

#### **Option 2: Manual Activation**
```bash
source venv/bin/activate
cd backend
python -m uvicorn app.main:app --reload
```

#### **Option 3: Automatic Activation with direnv**
Install [direnv](https://direnv.net/docs/installation.html) for automatic virtual environment activation:
```bash
# Install direnv (macOS)
brew install direnv

# Allow direnv in this directory
direnv allow

# Virtual environment activates automatically when you cd into the project
```

### Development Modes

1. **Local Development (Virtual Environment)**
   ```bash
   make dev  # Uses virtual environment
   ```

2. **Docker Development**
   ```bash
   make up
   make logs  # View logs
   ```

### Environment Variables

Create `backend/.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/auralis

# Security
SECRET_KEY=your-secret-key-here

# Debug
DEBUG=true
LOG_LEVEL=info
```

## 🎯 Key Features

### Competitor Management
- **Add Competitors**: Enter name and website URL
- **Website Crawling**: Automated data collection from competitor sites
- **Data Extraction**: Overview text, products, features, releases, documents
- **Change Detection**: Track updates and modifications over time

### Dashboard Views
- **Competitor Overview**: List all competitors with last crawl and changes
- **Competitor Detail**: Drill down into specific competitor information
- **Product Detail**: View features, releases, and documents for each product
- **Change History**: Track and visualize changes over time

### Data Architecture
- **Structured Models**: Competitor → Products → Features, Releases, Documents
- **Extensible Design**: Easy to add new artifact types (Pricing, News, etc.)
- **Snapshot System**: Track changes and maintain historical data
- **Clean Interfaces**: Swappable scraping engines (Requests/BeautifulSoup → Playwright)

### AI Integration
- **Theta EdgeCloud**: AI-powered summaries and entity extraction
- **Local Fallback**: Dummy results when AI service unavailable
- **Stubbed Service**: Clean interface in `app/services/ai.py`

## 🔄 Main User Flow

The primary workflow demonstrates the complete competitor analysis process:

1. **Create Competitor** → Add competitor name and website URL
2. **Crawl Website** → Automated scraping collects structured data
3. **View Dashboard** → Overview of all competitors and their status
4. **Drill Down** → Explore competitor details, products, and features
5. **Detect Changes** → Track updates and modifications over time

### Example Flow
```
Add Competitor (Acme Corp, https://acme.com)
    ↓
Trigger Crawl (collects products, features, documents)
    ↓
View Dashboard (see Acme Corp with last crawl date)
    ↓
Click Competitor → Product List → Product Detail
    ↓
View Features, Releases, Documents
    ↓
Re-crawl → Detect Changes → Show What's New
```

## 📋 Development Roadmap

### Phase 1: Core Backend ✅
- [x] FastAPI setup with health endpoint
- [x] Docker containerization
- [x] CORS configuration
- [x] Environment management
- [x] Virtual environment setup

### Phase 2: Data Schema & Models ✅
- [x] TypeScript data models and interfaces
- [x] Zod validation schemas
- [x] Flexible specification system
- [x] Source tracking and provenance
- [ ] PostgreSQL integration
- [ ] Database models (Competitor, Product, Feature, Release, Document)
- [ ] Database migrations and seeding
- [ ] Change tracking system

### Phase 3: Advanced Scraping Engine ✅
- [x] **JavaScript-enabled crawling** with Playwright browser automation
- [x] **Hybrid performance mode** (JS for important pages, requests for simple pages)
- [x] **Anti-bot protection** with realistic headers and smart delays
- [x] **Intelligent page classification** with scoring (product, docs, pricing, news, etc.)
- [x] **Advanced duplicate detection** with URL canonicalization
- [x] **Comprehensive logging** with JSON data persistence
- [x] **Error handling and retry logic** with exponential backoff
- [x] **Volume-mounted logs** accessible on host filesystem

### Phase 4: API Development
- [x] **Website Discovery API** (`POST /api/crawl/discover`) with full feature set
- [x] **Fingerprinting Pipeline API** (`POST /api/crawl/fingerprint`) with 3-step processing
- [x] **Extraction Pipeline API** (`POST /api/extract/run`) with AI-powered extraction
- [x] **Comprehensive response format** with pages, categories, and metadata
- [x] **Automated JSON Export System** with proper formatting and all records
- [x] **Data persistence** (PostgreSQL database + JSON exports)
- [ ] Competitor CRUD endpoints
- [ ] Product and feature endpoints
- [ ] Change detection endpoints

### Phase 5: Frontend Dashboard
- [ ] Next.js application setup
- [ ] Competitor overview dashboard
- [ ] Competitor detail pages
- [ ] Product detail pages
- [ ] Change visualization

### Phase 6: AI Integration
- [ ] Theta EdgeCloud integration
- [ ] AI service stubbing
- [ ] Entity extraction and summarization
- [ ] Local fallback implementation

### Phase 7: Change Detection
- [ ] Snapshot comparison system
- [ ] Change notification system
- [ ] Historical data visualization
- [ ] Automated re-crawling

## ⚠️ Known Issues

### JSON Serialization Bug (Extraction Pipeline)
- **Status**: ❌ Blocking extraction pipeline
- **Error**: `Object of type datetime is not JSON serializable`
- **Impact**: 100% extraction failure rate
- **Location**: Entity data processing during AI extraction
- **Workaround**: Crawling and fingerprinting work perfectly; structured data available in exports
- **Details**: See `backend/exports/JSON_SERIALIZATION_BUG_ANALYSIS.md`

### Current Pipeline Status
- ✅ **Crawling**: Fully functional with 62 pages discovered
- ✅ **Fingerprinting**: Fully functional with 42 pages processed
- ❌ **Extraction**: Blocked by datetime serialization issue
- ✅ **Data Export**: All stages export clean JSON automatically

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at http://localhost:8000/docs
- Review the service logs with `make logs`
