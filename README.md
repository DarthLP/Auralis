# Auralis

## 🎵 Project Overview

Auralis is a full-stack audio processing and analysis application built as a monorepo. The project is designed as a single-tenant prototype with a modern, scalable architecture.

### 🏗️ Architecture

- **Backend**: FastAPI-based REST API with Python 3.11+
- **Frontend**: React/Next.js application (planned)
- **Infrastructure**: Docker Compose for local development and deployment
- **Database**: PostgreSQL (planned)
- **Authentication**: Single-tenant (no auth required for prototype)

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** - Backend runtime
- **Docker & Docker Compose** - Containerized services
- **Make** - Development commands
- **Git** - Version control

### Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/DarthLP/Auralis.git
   cd Auralis
   ```

2. **Start all services**
   ```bash
   make up
   ```

3. **Access the application**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Development Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services with Docker Compose |
| `make down` | Stop all services |
| `make logs` | View service logs in real-time |
| `make help` | Show all available commands |

## 📁 Project Structure

```
Auralis/
├── backend/           # FastAPI backend service
│   ├── app/          # Application code
│   ├── Dockerfile.backend  # Backend container config
│   ├── requirements.txt    # Python dependencies
│   └── .env          # Environment variables
├── frontend/          # React/Next.js frontend (planned)
├── infra/            # Infrastructure configuration
│   └── docker-compose.yml  # Service orchestration
├── Makefile          # Development automation
└── README.md         # This file
```

## 🔧 Backend API

The backend provides a RESTful API built with FastAPI:

### Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

### Features

- **CORS Enabled** - Configured for `http://localhost:3000`
- **Auto Documentation** - Swagger UI at `/docs`
- **Environment Configuration** - Via `.env` file
- **Docker Ready** - Containerized with Python 3.11-slim

## 🐳 Docker Services

### Backend Service

- **Image**: Custom build from `Dockerfile.backend`
- **Port**: 8000 (mapped to host)
- **Environment**: Loaded from `backend/.env`
- **Restart Policy**: `unless-stopped`

## 🛠️ Development

### Local Development

1. **Backend Only**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   python3 -m uvicorn app.main:app --reload
   ```

2. **Full Stack (Docker)**
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

## 📋 Roadmap

### Phase 1: Core Backend ✅
- [x] FastAPI setup with health endpoint
- [x] Docker containerization
- [x] CORS configuration
- [x] Environment management

### Phase 2: Frontend (Planned)
- [ ] React/Next.js application
- [ ] Audio processing UI
- [ ] Real-time audio visualization

### Phase 3: Audio Processing (Planned)
- [ ] Audio file upload/processing
- [ ] Audio analysis algorithms
- [ ] Real-time audio streaming

### Phase 4: Database & Storage (Planned)
- [ ] PostgreSQL integration
- [ ] Audio file storage
- [ ] User data persistence

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
