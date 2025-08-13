#!/bin/bash

# MCP Draw.io Server Deployment Script
# This script helps deploy the MCP server in different environments

set -e

# Default values
ENVIRONMENT="production"
COMPOSE_FILE=""
ENV_FILE=""
ACTION="up"
BUILD=false
DETACH=true
SCALE=1
PROFILES=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[DEPLOY]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
MCP Draw.io Server Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Environment to deploy (dev|prod) [default: prod]
    -a, --action ACTION      Action to perform (up|down|restart|logs|status) [default: up]
    -b, --build             Force rebuild of images
    -f, --foreground        Run in foreground (don't detach)
    -s, --scale NUM         Number of replicas to run [default: 1]
    -p, --profiles LIST     Comma-separated list of profiles to enable
    -h, --help              Show this help message

EXAMPLES:
    # Deploy production environment
    $0 --environment prod --build

    # Deploy development environment in foreground
    $0 --environment dev --foreground

    # Scale production to 3 replicas
    $0 --environment prod --scale 3

    # Deploy with monitoring enabled
    $0 --environment prod --profiles monitoring

    # View logs
    $0 --action logs

    # Stop all services
    $0 --action down

    # Restart services
    $0 --action restart

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -f|--foreground)
            DETACH=false
            shift
            ;;
        -s|--scale)
            SCALE="$2"
            shift 2
            ;;
        -p|--profiles)
            PROFILES="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
case $ENVIRONMENT in
    dev|development)
        ENVIRONMENT="dev"
        COMPOSE_FILE="docker-compose.dev.yml"
        ENV_FILE=".env.dev"
        ;;
    prod|production)
        ENVIRONMENT="prod"
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.prod"
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT. Use 'dev' or 'prod'"
        exit 1
        ;;
esac

# Check if required files exist
if [[ ! -f "$COMPOSE_FILE" ]]; then
    print_error "Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    print_warning "Environment file not found: $ENV_FILE"
    print_warning "Using default .env file or environment variables"
    ENV_FILE=""
fi

# Build Docker Compose command
DOCKER_COMPOSE_CMD="docker-compose -f $COMPOSE_FILE"

if [[ -n "$ENV_FILE" ]]; then
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD --env-file $ENV_FILE"
fi

if [[ -n "$PROFILES" ]]; then
    export COMPOSE_PROFILES="$PROFILES"
fi

# Function to check if API key is set
check_api_key() {
    if [[ -z "$ANTHROPIC_API_KEY" ]]; then
        if [[ -f "$ENV_FILE" ]] && grep -q "ANTHROPIC_API_KEY=" "$ENV_FILE"; then
            local api_key=$(grep "ANTHROPIC_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
            if [[ "$api_key" == "your_anthropic_api_key_here" ]] || [[ -z "$api_key" ]]; then
                print_error "Please set your Anthropic API key in $ENV_FILE"
                exit 1
            fi
        else
            print_error "ANTHROPIC_API_KEY environment variable is not set"
            print_error "Please set it in your environment or in $ENV_FILE"
            exit 1
        fi
    fi
}

# Function to create necessary directories
create_directories() {
    local temp_dir logs_dir
    
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        temp_dir="./temp_dev"
        logs_dir="./logs_dev"
    else
        temp_dir="./temp_prod"
        logs_dir="./logs_prod"
    fi
    
    print_status "Creating directories..."
    mkdir -p "$temp_dir" "$logs_dir"
    
    # Set appropriate permissions
    chmod 755 "$temp_dir" "$logs_dir"
}

# Function to perform health check
health_check() {
    print_status "Performing health check..."
    
    local container_name
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        container_name="mcp-drawio-server-dev"
    else
        container_name="mcp-drawio-server-prod"
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        docker exec "$container_name" python -c "
import sys
sys.path.append('/app/src')
from health import HealthChecker
import asyncio
import json

async def check():
    checker = HealthChecker()
    health = await checker.get_health()
    print(json.dumps(health, indent=2))

asyncio.run(check())
" || print_warning "Health check failed"
    else
        print_warning "Container $container_name is not running"
    fi
}

# Main deployment logic
case $ACTION in
    up)
        print_header "Deploying MCP Draw.io Server ($ENVIRONMENT environment)"
        
        check_api_key
        create_directories
        
        # Build command options
        CMD_OPTIONS=""
        if [[ "$BUILD" == true ]]; then
            CMD_OPTIONS="$CMD_OPTIONS --build"
        fi
        
        if [[ "$DETACH" == true ]]; then
            CMD_OPTIONS="$CMD_OPTIONS -d"
        fi
        
        if [[ "$SCALE" -gt 1 ]] && [[ "$ENVIRONMENT" == "prod" ]]; then
            CMD_OPTIONS="$CMD_OPTIONS --scale mcp-server=$SCALE"
        fi
        
        print_status "Running: $DOCKER_COMPOSE_CMD up $CMD_OPTIONS"
        eval "$DOCKER_COMPOSE_CMD up $CMD_OPTIONS"
        
        if [[ "$DETACH" == true ]]; then
            sleep 5
            health_check
            print_status "Deployment completed successfully!"
            print_status "Use '$0 --action logs' to view logs"
            print_status "Use '$0 --action status' to check status"
        fi
        ;;
        
    down)
        print_header "Stopping MCP Draw.io Server ($ENVIRONMENT environment)"
        eval "$DOCKER_COMPOSE_CMD down"
        print_status "Services stopped successfully!"
        ;;
        
    restart)
        print_header "Restarting MCP Draw.io Server ($ENVIRONMENT environment)"
        eval "$DOCKER_COMPOSE_CMD restart"
        sleep 5
        health_check
        print_status "Services restarted successfully!"
        ;;
        
    logs)
        print_header "Showing logs for MCP Draw.io Server ($ENVIRONMENT environment)"
        eval "$DOCKER_COMPOSE_CMD logs -f"
        ;;
        
    status)
        print_header "Status of MCP Draw.io Server ($ENVIRONMENT environment)"
        eval "$DOCKER_COMPOSE_CMD ps"
        echo
        health_check
        ;;
        
    *)
        print_error "Invalid action: $ACTION"
        print_error "Valid actions: up, down, restart, logs, status"
        exit 1
        ;;
esac