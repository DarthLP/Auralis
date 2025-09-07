# Infrastructure

## 🏗️ Overview

The infrastructure directory contains Docker Compose configuration and deployment files for the Auralis application. This setup enables containerized development and deployment of all services.

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
# Start services
docker compose -f infra/docker-compose.yml up --build -d

# Stop services
docker compose -f infra/docker-compose.yml down

# View logs
docker compose -f infra/docker-compose.yml logs -f

# View logs for specific service
docker compose -f infra/docker-compose.yml logs -f backend

# Rebuild and restart
docker compose -f infra/docker-compose.yml up --build --force-recreate -d
```

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

## 📋 Future Infrastructure Plans

### Phase 1: Core Services ✅
- [x] Backend service containerization
- [x] Docker Compose orchestration
- [x] Environment management

### Phase 2: Database Integration (Planned)
- [ ] PostgreSQL service
- [ ] Database initialization scripts
- [ ] Data persistence volumes

### Phase 3: Frontend Integration (Planned)
- [ ] Frontend service containerization
- [ ] Nginx reverse proxy
- [ ] Static file serving

### Phase 4: Production Deployment (Planned)
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline configuration
- [ ] Monitoring and observability
- [ ] SSL/TLS termination

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Kill process or change port in docker-compose.yml
   ```

2. **Container Won't Start**
   ```bash
   # Check logs for errors
   docker compose -f infra/docker-compose.yml logs backend
   
   # Rebuild container
   docker compose -f infra/docker-compose.yml build --no-cache backend
   ```

3. **Environment Variables Not Loading**
   ```bash
   # Verify .env file exists and has correct format
   cat backend/.env
   
   # Check container environment
   docker compose -f infra/docker-compose.yml exec backend env
   ```

4. **Network Issues**
   ```bash
   # Check Docker networks
   docker network ls
   
   # Inspect network configuration
   docker network inspect infra_default
   ```

### Cleanup Commands

```bash
# Remove all containers and networks
docker compose -f infra/docker-compose.yml down --volumes --remove-orphans

# Remove all images
docker system prune -a

# Remove specific service
docker compose -f infra/docker-compose.yml rm -f backend
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Container Security](https://docs.docker.com/engine/security/)
- [Production Deployment Guide](https://docs.docker.com/compose/production/)
