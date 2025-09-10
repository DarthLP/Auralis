# Infrastructure

## 🏗️ Overview

The infrastructure directory contains Docker Compose configuration and deployment files for the Auralis competitor analysis application. This setup enables containerized development and deployment of all services.

## 📁 Directory Structure

```
infra/
├── docker-compose.yml    # Service orchestration configuration
└── README.md            # This file
```

## 🐳 Docker Compose Configuration

### Services

#### Backend Service

The backend service runs the FastAPI application in a containerized environment.

**Configuration:**
- **Build Context**: `../backend` (relative to docker-compose.yml)
- **Dockerfile**: `Dockerfile.backend`
- **Port Mapping**: `8000:8000` (host:container)
- **Environment File**: `../backend/.env`
- **Restart Policy**: `unless-stopped`

**Features:**
- Automatic rebuild on changes (`--build` flag)
- Environment variable loading from `.env` file
- Port forwarding for local access
- Automatic restart on failure

### Docker Compose File Structure

```yaml
services:
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    env_file:
      - ../backend/.env
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

## 🚀 Usage

### Development Commands

All commands are run from the project root using the Makefile:

| Command | Description | Docker Compose Equivalent |
|---------|-------------|---------------------------|
| `make up` | Start all services | `docker compose -f infra/docker-compose.yml up --build -d` |
| `make down` | Stop all services | `docker compose -f infra/docker-compose.yml down` |
| `make logs` | View service logs | `docker compose -f infra/docker-compose.yml logs -f` |

### Manual Docker Compose Commands

If you prefer to run Docker Compose commands directly:

```bash
# Start services (first time or after dependency changes)
docker compose -f infra/docker-compose.yml up --build -d

# Stop services
docker compose -f infra/docker-compose.yml down

# View logs
docker compose -f infra/docker-compose.yml logs -f

# View logs for specific service
docker compose -f infra/docker-compose.yml logs -f backend
```

### 🚀 **Optimized Rebuild Procedures**

**For Code Changes Only (Fast - ~30 seconds):**
```bash
# Quick restart without rebuilding (code changes only)
docker compose -f infra/docker-compose.yml restart backend

# Or if you need to rebuild just the code layer
docker compose -f infra/docker-compose.yml up -d --no-deps backend
```

**For Requirements Changes (Medium - ~2-3 minutes):**
```bash
# Rebuild only the backend service (preserves base layers)
docker compose -f infra/docker-compose.yml build backend
docker compose -f infra/docker-compose.yml up -d backend
```

**For System Dependencies (Slow - ~10+ minutes):**
```bash
# Full rebuild (only when Dockerfile changes)
docker compose -f infra/docker-compose.yml build --no-cache backend
docker compose -f infra/docker-compose.yml up -d backend
```

**Complete Clean Rebuild (Nuclear option):**
```bash
# Remove everything and rebuild from scratch
docker compose -f infra/docker-compose.yml down --volumes --remove-orphans
docker compose -f infra/docker-compose.yml build --no-cache
docker compose -f infra/docker-compose.yml up -d
```

### 🏗️ **Docker Layer Caching Strategy**

The Dockerfile is optimized for efficient rebuilds using layer caching:

```dockerfile
# Layer 1: Base image (rarely changes)
FROM python:3.12-slim

# Layer 2: System dependencies (changes rarely)
RUN apt-get update && apt-get install -y ...

# Layer 3: Python dependencies (changes when requirements.txt changes)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 4: Playwright browsers (changes rarely)
RUN playwright install chromium
RUN playwright install-deps chromium

# Layer 5: Application code (changes frequently)
COPY backend/ .
COPY data/ /data/
```

**Why This Works:**
- **Code changes** only rebuild Layer 5 (~30 seconds)
- **Requirements changes** rebuild Layers 3-5 (~2-3 minutes)
- **System changes** rebuild Layers 2-5 (~10+ minutes)
- **Base image changes** rebuild everything (~15+ minutes)

## 🔧 Configuration

### Environment Variables

The backend service loads environment variables from `../backend/.env`. This file should contain:

```env
# Application Settings
DEBUG=true
LOG_LEVEL=info

# Database (Future)
DATABASE_URL=postgresql://user:password@localhost:5432/auralis

# Security (Future)
SECRET_KEY=your-secret-key-here
```

### Port Configuration

- **Backend**: Port 8000 (mapped to host port 8000)
- **Future Services**: Additional ports will be added as services are developed

### Network Configuration

Docker Compose creates a default network for service communication:
- **Network Name**: `infra_default`
- **Services**: All services can communicate using service names as hostnames

## 🛠️ Development Workflow

### Starting Development

1. **Clone and navigate to project**
   ```bash
   git clone https://github.com/DarthLP/Auralis.git
   cd Auralis
   ```

2. **Start all services**
   ```bash
   make up
   ```

3. **Verify services are running**
   ```bash
   # Check container status
   docker compose -f infra/docker-compose.yml ps
   
   # Test backend health
   curl http://localhost:8000/health
   ```

4. **View logs**
   ```bash
   make logs
   ```

### Making Changes

1. **Code Changes**: Edit files in the respective service directories
2. **Rebuild**: Use `make up` to rebuild and restart services
3. **Environment Changes**: Edit `.env` files and restart with `make down && make up`

### Stopping Development

```bash
make down
```

## 🔍 Monitoring and Debugging

### Service Status

```bash
# Check running containers
docker compose -f infra/docker-compose.yml ps

# Check service health
docker compose -f infra/docker-compose.yml top
```

### Logs

```bash
# All services logs
make logs

# Specific service logs
docker compose -f infra/docker-compose.yml logs -f backend

# Logs with timestamps
docker compose -f infra/docker-compose.yml logs -f -t
```

### Container Inspection

```bash
# Enter backend container
docker compose -f infra/docker-compose.yml exec backend bash

# Check container resources
docker stats

# Inspect container configuration
docker compose -f infra/docker-compose.yml config
```

## 🚀 Production Considerations

### Security

- **Environment Variables**: Never commit sensitive data to version control
- **Network Security**: Configure proper firewall rules for production
- **Container Security**: Use non-root users in production containers

### Performance

- **Resource Limits**: Add CPU and memory limits for production
- **Health Checks**: Implement proper health check endpoints
- **Logging**: Configure centralized logging for production

### Scalability

- **Load Balancing**: Add reverse proxy (nginx) for multiple backend instances
- **Database**: Use external database service for production
- **Storage**: Use persistent volumes for data storage


### Cleanup Commands

```bash
# Remove all containers and networks
docker compose -f infra/docker-compose.yml down --volumes --remove-orphans

# Remove all images
docker system prune -a

# Remove specific service
docker compose -f infra/docker-compose.yml rm -f backend
```
