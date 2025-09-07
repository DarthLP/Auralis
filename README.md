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
├── frontend/          # Next.js frontend application
│   ├── src/          # Source code
│   ├── pages/        # Dashboard and detail pages
│   └── components/   # Reusable UI components
├── infra/            # Infrastructure configuration
│   └── docker-compose.yml  # Service orchestration
├── venv/             # Python virtual environment (auto-created)
├── .python-version   # Python version specification
├── .envrc            # Automatic environment activation (direnv)
├── setup.sh          # Automated setup script
├── Makefile          # Development automation
└── README.md         # This file
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

### Phase 2: Database & Models (In Progress)
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
