.PHONY: up down logs fmt help

# Default target
help:
	@echo "Available targets:"
	@echo "  up     - Start all services"
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

# Format code
fmt:
	@echo "Formatting code..."
	# TODO: Add code formatting commands
