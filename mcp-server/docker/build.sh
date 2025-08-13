#!/bin/bash
# Build script for MCP Draw.io Server Docker image
# Supports multi-platform builds and optimization

set -e

# Configuration
IMAGE_NAME="mcp-drawio-server"
IMAGE_TAG="${1:-latest}"
DOCKERFILE_PATH="../Dockerfile"
BUILD_CONTEXT=".."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "$DOCKERFILE_PATH" ]; then
    log_error "Dockerfile not found at $DOCKERFILE_PATH"
    log_error "Please run this script from the docker/ directory"
    exit 1
fi

# Build information
log_info "Building MCP Draw.io Server Docker image"
log_info "Image name: $IMAGE_NAME:$IMAGE_TAG"
log_info "Dockerfile: $DOCKERFILE_PATH"
log_info "Build context: $BUILD_CONTEXT"

# Build the image
log_info "Starting Docker build..."
docker build \
    -f "$DOCKERFILE_PATH" \
    -t "$IMAGE_NAME:$IMAGE_TAG" \
    --build-arg BUILDTIME="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --build-arg VERSION="$IMAGE_TAG" \
    "$BUILD_CONTEXT"

# Check build success
if [ $? -eq 0 ]; then
    log_success "Docker image built successfully!"
    
    # Show image information
    log_info "Image details:"
    docker images "$IMAGE_NAME:$IMAGE_TAG" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Show image layers (optional)
    if command -v dive &> /dev/null; then
        log_info "To analyze image layers, run: dive $IMAGE_NAME:$IMAGE_TAG"
    else
        log_info "Install 'dive' to analyze image layers: https://github.com/wagoodman/dive"
    fi
    
    log_info "To run the container:"
    echo "  docker run --rm -e ANTHROPIC_API_KEY=your_key_here $IMAGE_NAME:$IMAGE_TAG"
    
else
    log_error "Docker build failed!"
    exit 1
fi