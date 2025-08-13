# MCP Draw.io Server Makefile
# Provides convenient commands for development and deployment

.PHONY: help dev prod build clean logs status health test

# Default target
help:
	@echo "MCP Draw.io Server - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make dev-build    - Start development environment with rebuild"
	@echo "  make dev-logs     - Show development logs"
	@echo "  make dev-down     - Stop development environment"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Start production environment with rebuild"
	@echo "  make prod-logs    - Show production logs"
	@echo "  make prod-down    - Stop production environment"
	@echo ""
	@echo "Utilities:"
	@echo "  make status       - Show container status"
	@echo "  make health       - Run health check"
	@echo "  make clean        - Clean up containers and volumes"
	@echo "  make test         - Run tests"
	@echo "  make setup-dev    - Setup development environment"
	@echo "  make setup-prod   - Setup production environment"

# Development commands
dev:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.dev.yml up -d

dev-build:
	@echo "Starting development environment with rebuild..."
	docker-compose -f docker-compose.dev.yml up -d --build

dev-logs:
	@echo "Showing development logs..."
	docker-compose -f docker-compose.dev.yml logs -f

dev-down:
	@echo "Stopping development environment..."
	docker-compose -f docker-compose.dev.yml down

# Production commands
prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d

prod-build:
	@echo "Starting production environment with rebuild..."
	docker-compose -f docker-compose.prod.yml up -d --build

prod-logs:
	@echo "Showing production logs..."
	docker-compose -f docker-compose.prod.yml logs -f

prod-down:
	@echo "Stopping production environment..."
	docker-compose -f docker-compose.prod.yml down

# Utility commands
status:
	@echo "Container status:"
	@docker ps --filter "name=mcp-drawio-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

health:
	@echo "Running health check..."
	@if docker ps --format "{{.Names}}" | grep -q "mcp-drawio-server"; then \
		docker exec $$(docker ps --format "{{.Names}}" | grep "mcp-drawio-server" | head -1) python -c "\
import sys; sys.path.append('/app/src'); \
from health import HealthChecker; \
import asyncio; \
import json; \
result = asyncio.run(HealthChecker().get_health()); \
print(json.dumps(result, indent=2))"; \
	else \
		echo "No MCP server containers are running"; \
	fi

clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans
	docker system prune -f

test:
	@echo "Running tests..."
	python -m pytest tests/ -v

# Setup commands
setup-dev:
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		echo "Copying development environment template..."; \
		cp .env.dev .env; \
		echo "Please edit .env and set your ANTHROPIC_API_KEY"; \
	else \
		echo ".env file already exists"; \
	fi
	@mkdir -p temp_dev logs_dev
	@echo "Development environment setup complete"
	@echo "Next steps:"
	@echo "1. Edit .env and set your ANTHROPIC_API_KEY"
	@echo "2. Run 'make dev-build' to start the development environment"

setup-prod:
	@echo "Setting up production environment..."
	@if [ ! -f .env ]; then \
		echo "Copying production environment template..."; \
		cp .env.prod .env; \
		echo "Please edit .env and configure production settings"; \
	else \
		echo ".env file already exists"; \
	fi
	@mkdir -p temp_prod logs_prod
	@echo "Production environment setup complete"
	@echo "Next steps:"
	@echo "1. Edit .env and configure production settings"
	@echo "2. Run 'make prod-build' to start the production environment"

# Advanced commands
scale-prod:
	@echo "Scaling production environment..."
	@read -p "Number of replicas: " replicas; \
	docker-compose -f docker-compose.prod.yml up -d --scale mcp-server=$$replicas

monitoring:
	@echo "Starting production with monitoring..."
	COMPOSE_PROFILES=monitoring docker-compose -f docker-compose.prod.yml up -d

backup:
	@echo "Creating backup..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	mkdir -p backups; \
	docker run --rm -v mcp-server_temp_data_prod:/data -v $$(pwd)/backups:/backup alpine tar czf /backup/temp_data_$$timestamp.tar.gz -C /data .; \
	docker run --rm -v mcp-server_logs_data_prod:/data -v $$(pwd)/backups:/backup alpine tar czf /backup/logs_data_$$timestamp.tar.gz -C /data .; \
	echo "Backup created in backups/ directory"

# Docker image management
build-image:
	@echo "Building Docker image..."
	docker build -t mcp-drawio-server:latest .

push-image:
	@echo "Pushing Docker image..."
	@read -p "Registry URL: " registry; \
	docker tag mcp-drawio-server:latest $$registry/mcp-drawio-server:latest; \
	docker push $$registry/mcp-drawio-server:latest