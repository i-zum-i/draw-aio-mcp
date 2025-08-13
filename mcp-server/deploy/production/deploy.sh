#!/bin/bash
set -e

# Production deployment script for MCP Server
# Usage: ./deploy.sh [version]

VERSION=${1:-latest}
CONTAINER_NAME="mcp-server-prod"
IMAGE_NAME="mcpserver/diagram-generator:${VERSION}"
BACKUP_DIR="/opt/mcp-server/backups"
LOG_DIR="/opt/mcp-server/logs"
TEMP_DIR="/opt/mcp-server/temp"

echo "🚀 Starting MCP Server production deployment..."
echo "Version: ${VERSION}"
echo "Container: ${CONTAINER_NAME}"
echo "Image: ${IMAGE_NAME}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root for security reasons"
   exit 1
fi

# Check required environment variables
if [[ -z "${ANTHROPIC_API_KEY}" ]]; then
    echo "❌ ANTHROPIC_API_KEY environment variable is required"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
sudo mkdir -p ${BACKUP_DIR} ${LOG_DIR} ${TEMP_DIR}
sudo chown -R $(whoami):$(whoami) ${BACKUP_DIR} ${LOG_DIR} ${TEMP_DIR}

# Pull the latest image
echo "📥 Pulling Docker image..."
docker pull ${IMAGE_NAME}

# Stop existing container if running
if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
    echo "🛑 Stopping existing container..."
    docker stop ${CONTAINER_NAME}
fi

# Backup existing container if it exists
if docker ps -a -q -f name=${CONTAINER_NAME} | grep -q .; then
    echo "💾 Creating backup..."
    BACKUP_NAME="${CONTAINER_NAME}-backup-$(date +%Y%m%d-%H%M%S)"
    docker rename ${CONTAINER_NAME} ${BACKUP_NAME}
    echo "Backup created: ${BACKUP_NAME}"
fi

# Run new container
echo "🏃 Starting new container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    --restart unless-stopped \
    -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
    -e LOG_LEVEL=INFO \
    -e ENVIRONMENT=production \
    -e LOG_FILE=/app/logs/mcp-server.log \
    -v ${LOG_DIR}:/app/logs \
    -v ${TEMP_DIR}:/app/temp \
    -p 8000:8000 \
    --memory=1g \
    --cpus=1.0 \
    --health-cmd="python -c 'import requests; requests.get(\"http://localhost:8000/health\")'" \
    --health-interval=30s \
    --health-timeout=10s \
    --health-retries=3 \
    --health-start-period=40s \
    ${IMAGE_NAME}

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
timeout=120
counter=0
while [ $counter -lt $timeout ]; do
    if docker inspect --format='{{.State.Health.Status}}' ${CONTAINER_NAME} | grep -q "healthy"; then
        echo "✅ Container is healthy!"
        break
    fi
    
    if [ $counter -eq $timeout ]; then
        echo "❌ Container failed to become healthy within ${timeout} seconds"
        echo "Container logs:"
        docker logs ${CONTAINER_NAME}
        exit 1
    fi
    
    sleep 2
    counter=$((counter + 2))
    echo "Waiting... (${counter}/${timeout}s)"
done

# Test the deployment
echo "🧪 Testing deployment..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    docker logs ${CONTAINER_NAME}
    exit 1
fi

# Clean up old backups (keep last 5)
echo "🧹 Cleaning up old backups..."
docker ps -a --format "table {{.Names}}" | grep "${CONTAINER_NAME}-backup-" | tail -n +6 | xargs -r docker rm

echo "🎉 Deployment completed successfully!"
echo ""
echo "Container Status:"
docker ps --filter name=${CONTAINER_NAME} --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Logs: docker logs ${CONTAINER_NAME}"
echo "Stop: docker stop ${CONTAINER_NAME}"
echo "Restart: docker restart ${CONTAINER_NAME}"