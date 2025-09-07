.PHONY: up down logs fmt setup dev help

# Default target
help:
	@echo "Available targets:"
	@echo "  setup  - Set up virtual environment and install dependencies"
	@echo "  dev    - Start backend in development mode (requires venv)"
	@echo "  up     - Start all services with Docker"
	@echo "  down   - Stop all services"
	@echo "  logs   - Show service logs"
	@echo "  fmt    - Format code"
	@echo "  help   - Show this help message"

# Start all services
up:
	@echo "Starting services..."
	docker compose -f infra/docker-compose.yml up --build -d

# Stop all services
down:
	@echo "Stopping services..."
	docker compose -f infra/docker-compose.yml down

# Show service logs
logs:
	@echo "Showing service logs..."
	docker compose -f infra/docker-compose.yml logs -f

# Set up virtual environment and install dependencies
setup:
	@echo "Setting up Auralis project..."
	@./setup.sh

# Start backend in development mode
dev:
	@echo "Starting backend in development mode..."
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@source venv/bin/activate && cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Format code
fmt:
	@echo "Formatting code..."
	# TODO: Add code formatting commands
