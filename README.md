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

**Intelligent Lightweight Scoring**: AI scoring uses only URL, page title, and H1 headings but applies sophisticated business context analysis to assess competitive intelligence value, reducing API costs and processing time by ~90% while maintaining high accuracy.

**Enhanced Content Detection**: Improved minimal content detection now includes H1, H2, H3 headings and content length fallback, significantly reducing false "no content" classifications.

**Data Management**: Added options to clear old crawl data between jobs to prevent data persistence issues. Use `clear_old_data: true` in crawl requests or call the `/api/crawl/clear-data` endpoint.

**Automatic Database Import**: Fixed automatic import of extracted data into the main database after extraction completion. The system now automatically imports companies and products without manual intervention.

**URL Validation Fixes**: Resolved frontend ZodError validation issues by normalizing website URLs to include proper `https://` protocol in API responses.

## 🔄 Recent Improvements (Latest)

### Enhanced Discovery Process Visualization
- **Complete Sitemap Transparency**: Now shows all sitemap URLs found (e.g., 18 URLs) with visual filtering breakdown
- **Step-by-Step Processing**: Displays the complete discovery flow: sitemap → filtering → final pages
- **Visual Status Indicators**: Color-coded status for each URL (filtered, processed, queued)
- **No More Truncation**: Removed "... and X more pages" limits - shows complete lists
- **Filtering Details**: Clear breakdown of why URLs were filtered out (privacy, terms, etc.)

### Improved URL Filtering Logic
- **Context-Aware Filtering**: Fixed overly aggressive filtering that was removing valuable content
- **Product Announcement Support**: URLs like `/news/f-03-battery-development` now pass filtering
- **Refined Patterns**: Changed from `'development'` to `'/development/'` to avoid false positives
- **Better Content Discovery**: More pages now make it through the discovery process

### AI Scoring Fixes
- **Fixed "No Minimal Content" Issue**: Resolved frontend mapping that was missing content fields
- **Complete Content Field Mapping**: Added `has_minimal_content`, `title`, `h1`, `h2`, `h3`, `content_length`
- **Proper TypeScript Interfaces**: Updated type definitions for all content fields
- **Debug Logging**: Added detailed logging for content extraction troubleshooting
- **AI Scoring Now Works**: Pages with sufficient content now get proper AI scores instead of being skipped

**Dual Scoring Debug Mode**: For debugging purposes, the system now calculates both AI and rules-based scores for every page, allowing you to compare the effectiveness of both approaches. This data is included in the API response and detailed logs.

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
│   │   ├── lib/      # API client and utilities
│   │   └── hooks/    # Custom React hooks
│   ├── package.json  # Dependencies and scripts
│   ├── tailwind.config.js # Tailwind CSS configuration
│   └── vite.config.ts # Vite build configuration
├── data/             # Sample data and seed files
│   ├── seed.json     # Comprehensive seed data for development and demo
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

## 🎨 Frontend Application

The `frontend/` directory contains a modern React application built with Vite, featuring a professional design system and comprehensive routing.

### Key Features

- **React + Vite**: Fast development server with hot reload
- **Tailwind CSS**: Utility-first CSS framework for rapid styling
- **React Router**: Client-side routing with nested layouts
- **TanStack Query**: Powerful data fetching and caching
- **TypeScript**: Full type safety throughout the application
- **Responsive Design**: Mobile-first approach with responsive navigation
- **Seed Data System**: Comprehensive seed data with PAL Robotics example
- **Overview Dashboard**: Real-time signals tracking
- **Loading States**: Comprehensive loading indicators and skeleton screens
- **Global Search**: Command palette style search across companies, products, and signals
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

- `/` - Overview dashboard with signals
- `/companies` - Companies listing with search and filtering
- `/companies/:companyId` - Individual company details with products and recent activity
- `/companies/:companyId/products/:productId` - Product details with capabilities
- `/competitors/new` - Add new competitor via URL-based ingestion
- `/signals` - Advanced signals filtering and analysis


### Development

```bash
cd frontend
npm install
npm run dev
```

Access the application at http://localhost:3000

## 🔧 Backend API

The backend provides a RESTful API built with FastAPI for competitor analysis with **database-first architecture** and **full frontend integration**:

### Core Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

### 🚀 Website Discovery & Fingerprinting API

**`POST /api/crawl/discover`** - Advanced website crawling and page discovery 
**`POST /api/crawl/fingerprint`** - 3-step fingerprinting pipeline for content analysis with text extraction 
**`GET /api/crawl/sessions`** - List crawl sessions with metadata 
**`GET /api/crawl/sessions/{id}/fingerprints`** - Get fingerprint results with extracted text content 

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
- **AI-First Scoring**: Primary scoring uses AI analysis, falls back to rules-based scoring only on AI failure
- **Smart Download Filtering**: Pages with score ≥ 0.5 identified for detailed analysis (filters out noise)
- **Duplicate Detection**: URL canonicalization and content hash deduplication
- **Comprehensive Logging**: Detailed session logs and complete JSON data persistence

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
- **Capabilities**: Technical capabilities with maturity assessment
- **Sources**: Data provenance and credibility tracking


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


## 🛠️ Development

### Automatic Virtual Environment

The project includes automatic virtual environment setup for all collaborators:

#### Automatic Setup (Recommended)**
```bash
make setup  # One-time setup
make dev    # Start development server
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

## 🎯 Key Features

### Competitor Management
- **Add Competitors**: Enter name and website URL
- **Website Crawling**: Automated data collection from competitor sites
- **Data Extraction**: Overview text, products, features, documents
- **Change Detection**: Track updates and modifications over time

### Dashboard Views
- **Competitor Overview**: List all competitors with last crawl and changes
- **Competitor Detail**: Drill down into specific competitor information
- **Product Detail**: View features and documents for each product

### Data Architecture
- **Structured Models**: Competitor → Products → Features, Documents
- **Extensible Design**: Easy to add new artifact types (Pricing, News, etc.)
- **Snapshot System**: Track changes and maintain historical data

### AI Integration
- **Theta EdgeCloud**: AI-powered summaries and entity extraction with Llama

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
View Features, Documents
    ↓
Re-crawl → Detect Changes → Show What's New
```
