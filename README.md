# Auralis

## 🎯 Project Overview

Auralis is an AI-powered competitor analysis tool that helps businesses track and analyze their competitors' websites, products, and changes over time. Built as a simple but extensible prototype with a modern, scalable architecture.

### 🏗️ Architecture

- **Backend**: FastAPI-based REST API with Python 3.11+
- **Frontend**: Next.js application with dashboard and drill-down views
- **Database**: PostgreSQL with structured data models
- **Scraping**: Requests + BeautifulSoup (extensible to Playwright)
- **AI Layer**: Theta EdgeCloud integration with local fallback
- **Infrastructure**: Docker Compose for local development and deployment
- **Authentication**: Single-tenant prototype (no auth required)

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

## 📁 Project Structure

```
Auralis/
├── backend/           # FastAPI backend service
│   ├── app/          # Application code
│   │   ├── models/   # Database models (Competitor, Product, etc.)
│   │   ├── services/ # Business logic (scraping, AI, etc.)
│   │   ├── api/      # API endpoints
│   │   └── main.py   # FastAPI application
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
│   └── seed.json     # Mock data for development and demo
├── schema/           # Shared data models and validation
│   ├── enums.ts      # Core enumeration types
│   ├── specs.ts      # Flexible specification value types
│   ├── types.ts      # TypeScript interface definitions
│   ├── zod.ts        # Runtime validation schemas
│   ├── index.ts      # Re-exports all types and schemas
│   └── README.md     # Schema documentation
├── infra/            # Infrastructure configuration
│   └── docker-compose.yml  # Service orchestration
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

### Usage

```typescript
// Import types
import { Company, Product, Signal } from './schema';

// Runtime validation
import { zCompany, zProduct, zSignal } from './schema';
const company = zCompany.parse(rawData);
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
- `/signals` - Industry signals and news
- `/releases` - Product releases tracking

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

The `data/seed.json` file contains realistic sample data based on PAL Robotics, a Barcelona-based robotics company:

- **Companies**: Complete company profiles with metadata
- **Products**: Multiple product lines (TIAGo, TIAGo Pro, ARI, StockBot) with specifications
- **Capabilities**: Technical capabilities with maturity assessments
- **Signals**: Industry news and events with impact scoring
- **Releases**: Product release history with version tracking
- **Sources**: Data provenance and credibility tracking

### Mock API (`frontend/src/lib/mockData.ts`)

The mock data system provides:

- **Realistic Delays**: Simulated network latency for authentic user experience
- **Data Validation**: Zod schema validation for type safety
- **Filtered Queries**: Specialized functions for dashboard views (recent signals, releases)
- **Company-Specific Data**: Functions to fetch company products, summaries, and recent activity
- **Product-Specific Data**: Functions to fetch individual products and their capabilities
- **Capability Lookup**: Functions to fetch all capabilities for name resolution
- **Error Simulation**: Proper error handling and edge cases
- **Type Safety**: Full TypeScript integration with schema types

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
  capabilities
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
```

## 🔧 Backend API

The backend provides a RESTful API built with FastAPI for competitor analysis:

### Core Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

### Competitor Management

- `POST /api/competitors` - Add a new competitor
- `GET /api/competitors` - List all competitors
- `GET /api/competitors/{id}` - Get competitor details
- `POST /api/competitors/{id}/crawl` - Trigger website crawl

### Data Access

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

## 🐳 Docker Services

### Backend Service

- **Image**: Custom build from `Dockerfile.backend`
- **Port**: 8000 (mapped to host)
- **Environment**: Loaded from `backend/.env`
- **Restart Policy**: `unless-stopped`

### Database Service

- **Image**: PostgreSQL 15
- **Port**: 5432 (mapped to host)
- **Database**: `auralis`
- **Persistent Storage**: Docker volume for data persistence

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

### Phase 3: Scraping Engine
- [ ] Website crawling with Requests + BeautifulSoup
- [ ] Data extraction for products, features, releases
- [ ] Clean scraping interface for future Playwright integration
- [ ] Error handling and retry logic

### Phase 4: API Development
- [ ] Competitor CRUD endpoints
- [ ] Product and feature endpoints
- [ ] Crawling trigger endpoints
- [ ] Change detection endpoints

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
