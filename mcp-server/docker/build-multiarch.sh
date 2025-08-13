#!/bin/bash
# Multi-architecture Docker build script for MCP Draw.io Server
# Task 27: Docker Image Optimization - Multi-architecture support

set -e

# Configuration
IMAGE_NAME="mcp-drawio-server"
VERSION="${VERSION:-1.0.0}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF="${VCS_REF:-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')}"

# Supported architectures
PLATFORMS="linux/amd64,linux/arm64,linux/arm/v7"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== MCP Draw.io Server Multi-Architecture Build ===${NC}"
echo -e "${BLUE}Version: ${VERSION}${NC}"
echo -e "${BLUE}Build Date: ${BUILD_DATE}${NC}"
echo -e "${BLUE}VCS Ref: ${VCS_REF}${NC}"
echo -e "${BLUE}Platforms: ${PLATFORMS}${NC}"
echo ""

# Check if Docker Buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker Buildx is required for multi-architecture builds${NC}"
    echo -e "${YELLOW}Please install Docker Buildx or use Docker Desktop${NC}"
    exit 1
fi

# Create and use a new builder instance
echo -e "${YELLOW}Setting up Docker Buildx builder...${NC}"
docker buildx create --name mcp-builder --use --bootstrap 2>/dev/null || docker buildx use mcp-builder

# Verify builder supports required platforms
echo -e "${YELLOW}Verifying platform support...${NC}"
docker buildx inspect --bootstrap

# Build and push multi-architecture image
echo -e "${YELLOW}Building multi-architecture image...${NC}"
docker buildx build \
    --platform "${PLATFORMS}" \
    --file Dockerfile.optimized \
    --tag "${IMAGE_NAME}:${VERSION}" \
    --tag "${IMAGE_NAME}:latest" \
    --build-arg VERSION="${VERSION}" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${VCS_REF}" \
    --push \
    .

echo -e "${GREEN}✓ Multi-architecture build completed successfully${NC}"
echo -e "${GREEN}✓ Images pushed to registry${NC}"

# Display image information
echo -e "${BLUE}=== Build Summary ===${NC}"
docker buildx imagetools inspect "${IMAGE_NAME}:${VERSION}"

# Cleanup builder (optional)
read -p "Remove builder instance? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker buildx rm mcp-builder
    echo -e "${GREEN}✓ Builder instance removed${NC}"
fi

echo -e "${GREEN}=== Multi-architecture build process completed ===${NC}"