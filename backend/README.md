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

### API Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

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

### Phase 2: Audio Processing (Planned)
- [ ] Audio file upload endpoint
- [ ] Audio analysis algorithms
- [ ] Real-time audio streaming
- [ ] Audio format conversion

### Phase 3: Database Integration (Planned)
- [ ] PostgreSQL integration
- [ ] Audio metadata storage
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
