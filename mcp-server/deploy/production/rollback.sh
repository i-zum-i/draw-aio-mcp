#!/bin/bash
set -e

# Production rollback script for MCP Server
# Usage: ./rollback.sh [backup-name]

CONTAINER_NAME="mcp-server-prod"
BACKUP_NAME=${1}

echo "🔄 Starting MCP Server rollback..."

# List available backups if no backup name provided
if [[ -z "${BACKUP_NAME}" ]]; then
    echo "Available backups:"
    docker ps -a --format "table {{.Names}}\t{{.CreatedAt}}" | grep "${CONTAINER_NAME}-backup-" | head -5
    echo ""
    echo "Usage: $0 <backup-name>"
    echo "Example: $0 ${CONTAINER_NAME}-backup-20240101-120000"
    exit 1
fi

# Check if backup exists
if ! docker ps -a -q -f name=${BACKUP_NAME} | grep -q .; then
    echo "❌ Backup container '${BACKUP_NAME}' not found"
    exit 1
fi

# Stop current container
if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
    echo "🛑 Stopping current container..."
    docker stop ${CONTAINER_NAME}
fi

# Remove current container
if docker ps -a -q -f name=${CONTAINER_NAME} | grep -q .; then
    echo "🗑️ Removing current container..."
    docker rm ${CONTAINER_NAME}
fi

# Restore from backup
echo "📦 Restoring from backup: ${BACKUP_NAME}"
docker rename ${BACKUP_NAME} ${CONTAINER_NAME}

# Start the restored container
echo "🏃 Starting restored container..."
docker start ${CONTAINER_NAME}

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker inspect --format='{{.State.Health.Status}}' ${CONTAINER_NAME} | grep -q "healthy"; then
        echo "✅ Container is healthy!"
        break
    fi
    
    if [ $counter -eq $timeout ]; then
        echo "❌ Container failed to become healthy within ${timeout} seconds"
        docker logs ${CONTAINER_NAME}
        exit 1
    fi
    
    sleep 2
    counter=$((counter + 2))
    echo "Waiting... (${counter}/${timeout}s)"
done

# Test the rollback
echo "🧪 Testing rollback..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Rollback successful!"
else
    echo "❌ Rollback health check failed!"
    docker logs ${CONTAINER_NAME}
    exit 1
fi

echo "🎉 Rollback completed successfully!"
echo ""
echo "Container Status:"
docker ps --filter name=${CONTAINER_NAME} --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"