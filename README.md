# Auralis

## 🎯 Project Overview

Auralis is an AI-powered competitor analysis tool that helps businesses track and analyze their competitors' websites, products, and changes over time. Built as a simple but extensible prototype with a modern, scalable architecture.

### 🏗️ Architecture

- **Backend**: FastAPI-based REST API with Python 3.12+
- **Frontend**: React application with dashboard, drill-down views, and global search
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

- **Python 3.12+** - Backend runtime
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

### Docker Container Management

**Important**: When making code changes, you must rebuild containers for changes to take effect:

```bash
# Stop and remove containers
docker-compose down

# Rebuild and start containers with latest code
docker-compose up --build -d
```

**Why rebuild is necessary:**
- `docker-compose restart` only restarts containers with existing code
- Code changes require rebuilding the container image
- This ensures your latest changes are properly applied
- Always test endpoints after rebuild to verify changes are working

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
├── frontend/          # React + Vite frontend application
│   ├── src/          # Source code
│   │   ├── layouts/  # Layout components (AppLayout)
│   │   ├── pages/    # Page components with routing
│   │   ├── components/ # Reusable UI components
│   │   ├── lib/      # API client and utilities (includes mockData.ts)
│   │   └── hooks/    # Custom React hooks
│   ├── package.json  # Dependencies and scripts
│   ├── tailwind.config.js # Tailwind CSS configuration
│   └── vite.config.ts # Vite build configuration
├── data/             # Sample data and seed files
│   ├── seed.json     # Comprehensive mock data for development and demo
│   └── competitor_mock_data_pal_and_peers.json  # Additional competitor data
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

## 🎨 Frontend Application

The `frontend/` directory contains a modern React application built with Vite, featuring a professional design system and comprehensive routing.

### Key Features

- **React + Vite**: Fast development server with hot reload
- **Tailwind CSS**: Utility-first CSS framework for rapid styling
- **React Router**: Client-side routing with nested layouts
- **TanStack Query**: Powerful data fetching and caching
- **TypeScript**: Full type safety throughout the application
- **Responsive Design**: Mobile-first approach with responsive navigation
- **Mock Data System**: Comprehensive seed data with PAL Robotics example
- **Overview Dashboard**: Real-time signals and releases tracking
- **Loading States**: Comprehensive loading indicators and skeleton screens
- **Global Search**: Command palette style search across companies, products, signals, and releases
- **Empty States**: Friendly empty state components for better UX
- **Error Handling**: 404 pages and graceful error handling

### UI Components

The frontend includes several reusable components for consistent user experience:

- **LoadingSpinner**: Configurable loading spinner with different sizes
- **LoadingSkeleton**: Skeleton screens for table, grid, list, and card layouts
- **EmptyState**: Friendly empty state component with icons and actions
- **NotFound**: 404 page component for unknown routes
- **SourceDrawer**: Modal drawer for displaying source information
- **UrlInputWithValidate**: URL input with live validation and normalization
- **JobStatusBadge**: Status indicator for background jobs (queued, processing, done, error)
- **EditableTagInput**: Tag management component with add/remove functionality
- **ProductsEditor**: Product list editor with add/remove rows
- **SourcesList**: Read-only source information display
- **DedupAlert**: Duplicate company detection and warning component
- **Toast**: Transient notification component for success/error messages

### Architecture

- **AppLayout**: Main layout component with header and navigation
- **Nested Routing**: Clean URL structure with parameter support
- **Lazy Loading**: Code splitting for optimal performance
- **Suspense Boundaries**: Graceful loading states
- **API Integration**: Type-safe API client with schema validation

### Routes

- `/` - Overview dashboard with signals and releases
- `/companies` - Companies listing with search and filtering
- `/companies/:companyId` - Individual company details with products and recent activity
- `/companies/:companyId/products/:productId` - Product details with capabilities
- `/competitors/new` - Add new competitor via URL-based ingestion
- `/signals` - Advanced signals filtering and analysis
- `/releases` - Product releases tracking with company and date filtering

### Overview Dashboard

The main dashboard (`/`) provides a comprehensive overview of the latest industry activity:

- **This Week Signals**: Displays the top 5 most impactful signals from the past 7 days, sorted by impact score and recency
- **Recent Releases**: Shows the 8 most recent product releases from the past 90 days
- **Impact Scoring**: Visual indicators for signal impact levels (High, Medium, Neutral, Low, Very Low)
- **Interactive Navigation**: Click-through links to detailed views for signals and product releases
- **Loading States**: Skeleton loading animations for better user experience
- **Error Handling**: Graceful error states with user-friendly messages

### Companies Pages

The companies section provides comprehensive company management and analysis:

#### Companies Index (`/companies`)
- **Company Cards**: Display company name, website domain, HQ location, and tags
- **Search & Filter**: Real-time client-side filtering by company name and aliases
- **Responsive Grid**: Adaptive layout (1-3 columns based on screen size)
- **Navigation**: Click any company card to view detailed information

#### Company Detail (`/companies/:companyId`)
- **Company Header**: Name, one-liner description, meta information (founded year, HQ, employees), and website button
- **Products Grid**: All company products with name, description, category, markets, and tags
- **Recent Activity**: Mixed chronological list of signals (last 60 days) and releases (all), limited to 10 items
- **Interactive Elements**: 
  - Product cards navigate to product detail pages
  - Recent activity items navigate to signals or product pages based on type
  - Website button opens company website in new tab
- **Loading States**: Comprehensive skeleton loading for all sections
- **Error Handling**: Company not found, empty states, and data loading errors

#### Product Detail (`/companies/:companyId/products/:productId`)
- **Hero Section**: Product name, description, company chip (linking back to company), category, markets, and tags
- **Action Buttons**: Links to product page and documentation (when available)
- **Capabilities Section**: List of product capabilities with:
  - Capability name (looked up by capability ID)
  - Maturity pills with color coding (Basic, Intermediate, Advanced, Expert, GA, Alpha, Beta)
  - One-line details description
  - Source icons (ready for future Source Drawer implementation)
- **Data Validation**: Ensures product belongs to specified company (404 if mismatch)
- **Loading States**: Skeleton loading animations for hero and capabilities sections
- **Error Handling**: Product not found, company mismatch, and data loading errors
- **Navigation**: Breadcrumb-style navigation back to company page
- **Simplified Empty States**: Clean, minimal display for products without documented capabilities

### Add Competitor Page (`/competitors/new`)

The Add Competitor page provides a comprehensive URL-based competitor ingestion system with **auto-save functionality**:

#### **3-Phase Automated Pipeline**
- **Phase 1 - Discovery**: Crawls and classifies pages from competitor websites
- **Phase 2 - Fingerprinting**: Generates content hashes and extracts text from discovered pages
- **Phase 3 - Extraction**: Uses AI + rules to extract structured entities (companies, products, capabilities)
- **Auto-Save Mode**: Automatically saves extracted entities to database without user intervention

#### **Real-Time Progress Tracking**
- **Visual Progress Indicators**: Shows current phase with animated status dots
- **Progress Bars**: Tracks pages discovered, processed, and extracted
- **Live Metrics**: Displays processing speed (pages/min), ETA, cache hits, and retry counts
- **Server-Sent Events**: Real-time updates during extraction phase
- **Fallback Polling**: 10-second polling backup if SSE connection fails
- **Enhanced Metrics**: More frequent updates (every 5 pages + first page) for better responsiveness

#### **URL-Based Ingestion Flow**
- **Smart URL Validation**: Real-time validation with scheme handling, hostname normalization, and security checks
- **Domain Normalization**: Automatic eTLD+1 extraction for consistent domain matching
- **Reachability Testing**: Real reachability checks to ensure websites are accessible
- **Deduplication Logic**: Automatic detection of existing companies by domain and name matching
- **Visual Feedback**: Green highlighting for valid URLs, error messages for invalid ones

#### **User Experience Features**
- **One-Click Analysis**: Simply enter URL and click "Analyze" - everything else is automated
- **User-Controlled Completion**: No forced redirects - users choose their next action
- **Completion Actions**: "View Companies" button to see results or "Add Another" to start over
- **Error Handling**: Graceful error states with helpful messages and retry options
- **Entry Points**: Multiple ways to access (floating button, empty state CTA, companies grid)

#### **Technical Implementation**
- **Backend Integration**: Full integration with crawling, fingerprinting, and extraction APIs
- **Type Safety**: Full TypeScript integration with validation schemas
- **Real-Time Updates**: WebSocket-like experience with Server-Sent Events
- **Component Reusability**: Modular components for URL input, progress tracking, and status display
- **Robust Completion Detection**: Dual mechanism (SSE + polling) ensures reliable completion handling

### Crawling & Extraction API

The backend provides a comprehensive 3-phase pipeline for competitor analysis:

#### **Discovery API (`/api/crawl/discover`)**
- **Purpose**: Discover and classify interesting pages from competitor websites
- **Input**: Target URL
- **Output**: List of discovered pages with categories, scores, and metadata
- **Features**: JavaScript-enabled crawling, sitemap discovery, content classification

#### **Fingerprinting API (`/api/crawl/fingerprint`)**
- **Purpose**: Generate content hashes and extract text from discovered pages
- **Input**: Crawl session ID and competitor name
- **Output**: Fingerprint session with processed pages and content hashes
- **Features**: Content deduplication, text extraction, change detection

#### **Extraction API (`/api/extract/run`)**
- **Purpose**: Extract structured entities using AI + rules-based extraction
- **Input**: Fingerprint session ID and competitor name
- **Output**: Extraction session with found entities (companies, products, capabilities)
- **Features**: AI-powered entity extraction, real-time progress tracking, auto-save to database

#### **Real-Time Progress (`/api/extract/stream/{session_id}`)**
- **Purpose**: Stream real-time progress updates during extraction
- **Format**: Server-Sent Events (SSE)
- **Updates**: Processing speed (pages/min), ETA, cache hits, retries, entity counts
- **Enhanced Metrics**: More frequent updates (every 5 pages + first page) for better responsiveness

### Signals Page (`/signals`)

The signals page provides advanced filtering and analysis capabilities for industry signals and news:

#### **Advanced Filtering System**
- **Signal Type Filter**: Multi-select checkboxes for news, job postings, research papers, funding announcements, releases, and social media
- **Company Filter**: Multi-select dropdown with all companies in the dataset
- **Product Filter**: Multi-select dropdown with "Only with results" toggle to show only products that have associated signals
- **Impact Filter**: Multiple selection buttons for all 5 impact levels (Very Low, Low, Neutral, Medium, High) with "All" reset option
- **Date Filter**: Preset buttons (7d, 30d, YTD, All) with visual feedback showing selected date range

#### **Responsive Table Layout**
- **Optimized Column Widths**: Headline column is prominently sized (320px) while other columns are compact
- **Column Order**: Date, Headline, Impact, Type, Companies, Products
- **Product Names**: Displays actual product names (TIAGo, ARI, StockBot) instead of IDs
- **Interactive Elements**: 
  - Clickable headlines open source drawer or direct URLs
  - Company/product tags are clickable filters
  - Impact badges with color coding
- **Pagination**: 25 signals per page with navigation controls

#### **Filter Management**
- **URL Persistence**: All filter selections are saved in URL parameters for bookmarking and sharing
- **Real-time Updates**: Results update immediately as filters are applied
- **Clear All Filters**: One-click reset to default state
- **Debounced Updates**: Smooth performance with 250ms debounce on filter changes

#### **Data Integration**
- **20 Diverse Signals**: Comprehensive seed data covering all signal types and impact levels
- **Source Integration**: Source drawer for detailed source information and credibility
- **Date Range**: Signals span 4+ months (May 2025 - September 2025) for testing date filtering
- **Entity Relationships**: Full integration with companies, products, and capabilities

#### **User Experience**
- **Compact Sidebar**: 256px width with optimized spacing for efficient filtering
- **Responsive Design**: Filters stack vertically on mobile, horizontal layout on desktop
- **Loading States**: Skeleton loading animations during data fetching
- **Empty States**: Helpful messages when no signals match filters
- **Error Handling**: Graceful error states with retry options

### Releases Page (`/releases`)

The releases page provides comprehensive tracking and filtering of product releases across the industry:

#### **Simplified Filtering System**
- **Company Filter**: Multi-select checkboxes for all companies in the dataset
- **Date Filter**: Preset buttons (7d, 30d, YTD, All) with visual feedback showing selected date range
- **Clear Filters**: One-click reset to default state

#### **Releases Table Layout**
- **Chronological Ordering**: Releases sorted by date (newest first)
- **Column Structure**: Date, Product & Version, Company, Notes, Source
- **Product Links**: Clickable product names that navigate to nested product detail pages
- **Company Tags**: Clickable company names that filter by that company
- **Source Integration**: Source icons that open the Source Drawer for detailed source information
- **Pagination**: 25 releases per page with navigation controls

#### **Data Integration**
- **Release Tracking**: Comprehensive product release history with version information
- **Company Association**: Each release linked to its company and product
- **Source Attribution**: Source tracking for release announcements
- **Notes Field**: Short descriptions of release contents and changes

#### **User Experience**
- **Consistent Layout**: Matches SignalsPage design with sidebar filters and main content area
- **Responsive Design**: Sidebar collapses on mobile, full-width on desktop
- **Loading States**: Skeleton loading animations during data fetching
- **Empty States**: Helpful messages when no releases match filters
- **Navigation**: Seamless integration with product detail pages

#### **Key Features**
- **Product Navigation**: Direct links from release entries to product detail pages
- **Source Verification**: Source drawer integration for release credibility
- **Time-based Filtering**: Quick access to recent releases with preset date ranges
- **Company Focus**: Easy filtering to track releases from specific companies

### Development

```bash
cd frontend
npm install
npm run dev
```

Access the application at http://localhost:3000

## 📊 Mock Data System

The application includes a comprehensive mock data system for development and demonstration purposes:

### Seed Data (`data/seed.json`)

The `data/seed.json` file contains comprehensive sample data based on PAL Robotics and industry peers:

- **Companies**: Complete company profiles with metadata including PAL Robotics as "Your Company" and industry competitors
- **Products**: Multiple product lines (TIAGo, TIAGo Pro, ARI, StockBot) with detailed specifications and capabilities
- **Capabilities**: Technical capabilities with maturity assessments across robotics, AI, and automation domains
- **Signals**: Industry news and events with impact scoring spanning multiple months
- **Releases**: Product release history with version tracking and detailed notes
- **Sources**: Data provenance and credibility tracking with comprehensive source attribution
- **Spec Profiles**: Flexible specification schemas for robotics, AI platforms, and general automation products

### Mock API (`frontend/src/lib/mockData.ts`)

The mock data system provides:

- **Realistic Delays**: Simulated network latency for authentic user experience
- **Data Validation**: Zod schema validation for type safety
- **Filtered Queries**: Specialized functions for dashboard views (recent signals, releases)
- **Company-Specific Data**: Functions to fetch company products, summaries, and recent activity
- **Product-Specific Data**: Functions to fetch individual products and their capabilities
- **Capability Lookup**: Functions to fetch all capabilities for name resolution
- **Scraper Job System**: Mock scraper jobs with status tracking (queued, processing, done)
- **Data Extraction**: Heuristic company data extraction from URLs
- **Deduplication**: Smart duplicate detection using domain and name matching
- **Error Simulation**: Proper error handling and edge cases
- **Type Safety**: Full TypeScript integration with schema types
- **Extended Spec Profiles**: Support for AI platforms, general robotics, mobile humanoids, cobots, and service robots

### Usage

```typescript
// Import mock API functions
import { 
  getThisWeekSignals, 
  getRecentReleases, 
  companies, 
  company, 
  companySummaries, 
  productsByCompany, 
  getCompanyRecentActivity,
  product,
  productCapabilities,
  capabilities,
  startScraperJob,
  getScraperJob,
  saveCompetitor
} from '@/lib/mockData';

// Use in components
const signals = await getThisWeekSignals(); // Top 5 signals from past week
const releases = await getRecentReleases(); // Top 8 releases from past 90 days
const companiesList = await companies(); // All companies
const companyData = await company('cmp_pal'); // Specific company
const products = await productsByCompany('cmp_pal'); // Company products
const activity = await getCompanyRecentActivity('cmp_pal'); // Recent activity
const productData = await product('prd_tiago'); // Specific product
const productCaps = await productCapabilities('prd_tiago'); // Product capabilities
const allCapabilities = await capabilities(); // All capabilities for lookup

// Scraper job system
const job = await startScraperJob('https://example.com'); // Start scraping job
const jobStatus = await getScraperJob(job.id); // Check job status
const newCompany = await saveCompetitor(jobResult); // Save extracted data
```

## 🔧 Backend API

The backend provides a RESTful API built with FastAPI for competitor analysis with **database-first architecture** and **full frontend integration**:

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

### 🏢 Business Intelligence API

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

### 🗄️ Database Integration

The backend now includes a complete database schema with:
- **Companies**: Company profiles with metadata and summaries
- **Products**: Product lifecycle management with specifications
- **Signals**: Industry intelligence with impact scoring
- **Releases**: Product release tracking with version history
- **Capabilities**: Technical capabilities with maturity assessment
- **Sources**: Data provenance and credibility tracking

**Seed Data Loading:**
- Automatic database population on startup
- Comprehensive seed data from `data/seed.json`
- Deduplication logic for data integrity
- Foreign key constraint handling

### Features

- **CORS Enabled** - Configured for `http://localhost:3000`
- **Auto Documentation** - Swagger UI at `/docs`
- **Environment Configuration** - Via `.env` file
- **Docker Ready** - Containerized with Python 3.11-slim
- **Database Integration** - PostgreSQL with structured models
- **Frontend Integration** - Real API endpoints with proper datetime formatting
- **Schema Validation** - JSON Schema validation with Zod compatibility
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

### Phase 4: API Development ✅
- [x] **Website Discovery API** (`POST /api/crawl/discover`) with full feature set
- [x] **Fingerprinting Pipeline API** (`POST /api/crawl/fingerprint`) with 3-step processing
- [x] **Extraction Pipeline API** (`POST /api/extract/run`) with AI-powered extraction
- [x] **Comprehensive response format** with pages, categories, and metadata
- [x] **Automated JSON Export System** with proper formatting and all records
- [x] **Data persistence** (PostgreSQL database + JSON exports)
- [x] **Data persistence** (JSON files with complete crawl data)
- [x] **Business Intelligence API endpoints** (Companies, Products, Signals, Releases, Capabilities, Sources)
- [x] **Complete CRUD operations** for all entities
- [x] **Database integration** with SQLAlchemy ORM
- [x] **Frontend-Backend integration** with real API endpoints
- [x] **Datetime formatting** for API responses with Zod compatibility
- [ ] Change detection endpoints
- [ ] Competitor CRUD endpoints
- [ ] Product and feature endpoints

### Phase 5: Frontend Dashboard ✅
- [x] React + Vite application setup
- [x] Tailwind CSS styling system
- [x] React Router with nested routes
- [x] AppLayout with navigation and header
- [x] TanStack Query for data fetching
- [x] Lazy loading and Suspense boundaries
- [x] Responsive design and mobile support
- [x] Overview dashboard with signals and releases
- [x] Mock data system with seed data
- [x] Companies index page with search and filtering
- [x] Company detail pages with products and recent activity
- [x] Product detail pages with capabilities and maturity tracking
- [x] Advanced signals page with comprehensive filtering and analysis
- [x] Add Competitor page with URL-based ingestion
- [x] URL validation and normalization system
- [x] Mock scraper job system with status tracking
- [x] Deduplication logic for existing companies
- [x] Reusable UI components for competitor addition
- [x] **Frontend-Backend API integration** with real data fetching
- [x] **Real-time data processing** with proper filtering and sorting
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
