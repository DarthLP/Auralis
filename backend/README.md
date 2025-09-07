# Backend Service

## 🚀 Overview

The Auralis backend is a FastAPI-based REST API service that provides the core functionality for competitor analysis and website crawling. Built with Python 3.11+ and designed as a single-tenant prototype.

## 🏗️ Architecture

- **Framework**: FastAPI (modern, fast web framework for building APIs)
- **Python Version**: 3.11+
- **ASGI Server**: Uvicorn
- **Data Validation**: Pydantic v2
- **CORS**: Enabled for frontend integration
- **Containerization**: Docker with Python 3.11-slim base image

## 📁 Directory Structure

```
backend/
├── app/                    # Application source code
│   ├── core/              # Core configuration and database
│   │   ├── config.py      # Application settings
│   │   └── db.py          # Database configuration
│   ├── services/          # Business logic services
│   │   └── validate.py    # Schema validation service
│   ├── schema/            # Generated JSON schemas
│   │   └── json/          # JSON Schema files (auto-generated)
│   └── main.py            # FastAPI application entry point
├── Dockerfile.backend     # Docker container configuration
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
└── README.md             # This file
```

## 🔧 API Endpoints

### Core Endpoints

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/` | Root endpoint with API information | `{"message": "Auralis Backend API"}` |
| `GET` | `/health` | Health check endpoint | `{"status": "ok"}` |
| `GET` | `/docs` | Interactive API documentation | Swagger UI HTML |

### Discovery API

The Discovery API enables crawling and analysis of competitor websites to identify interesting pages for competitive analysis.

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `POST` | `/api/crawl/discover` | Discover and classify pages from a website | JSON with categorized pages |

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

**Note:** Discovery returns candidate pages only; no database writes occur. This is the first stage before normalization and storage.

#### Anti-Scraping Protection

The crawler includes several measures to avoid bot detection and respect website policies:

**🛡️ Bot Detection Evasion:**
- **Realistic Browser Headers**: Mimics real browser requests with proper Accept, Accept-Language, DNT, and Sec-Fetch headers
- **User Agent Rotation**: Randomly selects from pool of real browser user agents (Chrome, Firefox, Safari)
- **Session Management**: Uses persistent sessions for better connection handling

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

## 🛠️ Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

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

3. **Run the development server**
   ```bash
   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the API**
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

# Database (Future)
DATABASE_URL=postgresql://user:password@localhost:5432/auralis

# Security (Future)
SECRET_KEY=your-secret-key-here

# External APIs (Future)
# API_KEY=your-api-key
```

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
- [ ] User session management
- [ ] Data persistence layer

### Phase 4: Advanced Features (Planned)
- [ ] Authentication system
- [ ] Rate limiting
- [ ] Caching layer
- [ ] Background task processing

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

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Docker Python Best Practices](https://docs.docker.com/language/python/)
