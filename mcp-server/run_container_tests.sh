#!/bin/bash

# Container Test Runner Script for MCP Draw.io Server
# This script runs comprehensive container tests including build and runtime tests

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_IMAGE_NAME="mcp-drawio-server:test"
TEST_CONTAINER_NAME="mcp-test-container"

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

cleanup() {
    log_info "Cleaning up test resources..."
    
    # Stop and remove test containers
    docker stop "$TEST_CONTAINER_NAME" 2>/dev/null || true
    docker rm "$TEST_CONTAINER_NAME" 2>/dev/null || true
    
    # Remove test images
    docker rmi "$TEST_IMAGE_NAME" 2>/dev/null || true
    
    # Clean up test directories
    rm -rf "$PROJECT_ROOT/temp_test" "$PROJECT_ROOT/logs_test" 2>/dev/null || true
    
    log_success "Cleanup completed"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        return 1
    fi
    
    # Check required files
    local required_files=("Dockerfile" "requirements.txt" "src/server.py" "src/tools.py")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            log_error "Required file missing: $file"
            return 1
        fi
    done
    
    log_success "All prerequisites met"
    return 0
}

setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Create test directories
    mkdir -p "$PROJECT_ROOT/temp_test" "$PROJECT_ROOT/logs_test"
    mkdir -p "$PROJECT_ROOT/tests/container"
    
    # Set permissions
    chmod 755 "$PROJECT_ROOT/temp_test" "$PROJECT_ROOT/logs_test"
    
    # Create test environment file
    cat > "$PROJECT_ROOT/.env.test" << EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-test-key-for-testing}
LOG_LEVEL=DEBUG
CACHE_TTL=300
FILE_EXPIRY_HOURS=1
TEMP_DIR=/app/temp
DRAWIO_CLI_PATH=drawio
EOF
    
    log_success "Test environment ready"
}

build_test_image() {
    log_info "Building test Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Build the image
    if docker build -t "$TEST_IMAGE_NAME" .; then
        log_success "Docker image built successfully"
        
        # Get image info
        local image_size=$(docker images "$TEST_IMAGE_NAME" --format "table {{.Size}}" | tail -n 1)
        log_info "Image size: $image_size"
        
        return 0
    else
        log_error "Docker image build failed"
        return 1
    fi
}

test_image_properties() {
    log_info "Testing image properties..."
    
    # Test image size (should be under 500MB)
    local size_bytes=$(docker inspect "$TEST_IMAGE_NAME" --format='{{.Size}}')
    local size_mb=$((size_bytes / 1024 / 1024))
    
    if [[ $size_mb -lt 500 ]]; then
        log_success "Image size acceptable: ${size_mb}MB (limit: 500MB)"
    else
        log_warning "Image size large: ${size_mb}MB (limit: 500MB)"
    fi
    
    # Test image layers
    local layers=$(docker inspect "$TEST_IMAGE_NAME" --format='{{len .RootFS.Layers}}')
    log_info "Image layers: $layers"
    
    # Test image labels
    local labels=$(docker inspect "$TEST_IMAGE_NAME" --format='{{json .Config.Labels}}')
    if [[ "$labels" != "null" ]]; then
        log_success "Image has metadata labels"
    else
        log_warning "Image missing metadata labels"
    fi
}

test_container_startup() {
    log_info "Testing container startup..."
    
    # Start container
    if docker run -d \
        --name "$TEST_CONTAINER_NAME" \
        --env-file "$PROJECT_ROOT/.env.test" \
        -v "$PROJECT_ROOT/temp_test:/app/temp" \
        -v "$PROJECT_ROOT/logs_test:/app/logs" \
        "$TEST_IMAGE_NAME"; then
        log_success "Container started successfully"
    else
        log_error "Container failed to start"
        return 1
    fi
    
    # Wait for container to be ready
    log_info "Waiting for container to be ready..."
    local max_wait=30
    local wait_time=0
    
    while [[ $wait_time -lt $max_wait ]]; do
        if docker exec "$TEST_CONTAINER_NAME" python /app/src/healthcheck.py &>/dev/null; then
            log_success "Container is healthy"
            return 0
        fi
        
        sleep 2
        wait_time=$((wait_time + 2))
        log_info "Waiting... (${wait_time}s/${max_wait}s)"
    done
    
    log_error "Container not ready after ${max_wait} seconds"
    docker logs "$TEST_CONTAINER_NAME"
    return 1
}

test_dependencies() {
    log_info "Testing dependencies..."
    
    # Test Python
    if docker exec "$TEST_CONTAINER_NAME" python3 --version; then
        log_success "Python 3 available"
    else
        log_error "Python 3 not available"
        return 1
    fi
    
    # Test Draw.io CLI
    if docker exec "$TEST_CONTAINER_NAME" drawio --version; then
        log_success "Draw.io CLI available"
    else
        log_error "Draw.io CLI not available"
        return 1
    fi
    
    # Test Python packages
    local packages=("mcp" "anthropic" "httpx")
    for package in "${packages[@]}"; do
        if docker exec "$TEST_CONTAINER_NAME" python3 -c "import $package; print('$package imported successfully')"; then
            log_success "Python package available: $package"
        else
            log_error "Python package missing: $package"
            return 1
        fi
    done
    
    # Test application modules
    if docker exec "$TEST_CONTAINER_NAME" python3 -c "import sys; sys.path.append('/app/src'); from llm_service import LLMService; print('Application modules imported successfully')"; then
        log_success "Application modules importable"
    else
        log_error "Application modules not importable"
        return 1
    fi
}

test_file_permissions() {
    log_info "Testing file permissions..."
    
    # Test temp directory
    if docker exec "$TEST_CONTAINER_NAME" python3 -c "import os; os.makedirs('/app/temp/test', exist_ok=True); print('Temp directory writable')"; then
        log_success "Temp directory writable"
    else
        log_error "Temp directory not writable"
        return 1
    fi
    
    # Test logs directory
    if docker exec "$TEST_CONTAINER_NAME" python3 -c "import os; os.makedirs('/app/logs/test', exist_ok=True); print('Logs directory writable')"; then
        log_success "Logs directory writable"
    else
        log_error "Logs directory not writable"
        return 1
    fi
    
    # Test user
    local user=$(docker exec "$TEST_CONTAINER_NAME" whoami)
    if [[ "$user" != "root" ]]; then
        log_success "Container runs as non-root user: $user"
    else
        log_warning "Container runs as root user"
    fi
}

run_python_tests() {
    log_info "Running Python container tests..."
    
    # Check if Python test files exist
    if [[ -f "$PROJECT_ROOT/tests/container/run_container_tests.py" ]]; then
        cd "$PROJECT_ROOT"
        if python3 tests/container/run_container_tests.py; then
            log_success "Python container tests passed"
            return 0
        else
            log_error "Python container tests failed"
            return 1
        fi
    else
        log_warning "Python container tests not found, skipping"
        return 0
    fi
}

generate_test_report() {
    local start_time="$1"
    local end_time="$2"
    local test_results="$3"
    
    log_info "Generating test report..."
    
    local report_file="$PROJECT_ROOT/tests/container/test_report.txt"
    
    cat > "$report_file" << EOF
================================================================================
MCP DRAW.IO SERVER - CONTAINER TEST REPORT
================================================================================
Test execution time: $(date)
Duration: $((end_time - start_time)) seconds

Test Results:
$test_results

Image Information:
- Name: $TEST_IMAGE_NAME
- Size: $(docker images "$TEST_IMAGE_NAME" --format "{{.Size}}" | head -n 1)
- Layers: $(docker inspect "$TEST_IMAGE_NAME" --format='{{len .RootFS.Layers}}')

Container Information:
- Name: $TEST_CONTAINER_NAME
- Status: $(docker inspect "$TEST_CONTAINER_NAME" --format='{{.State.Status}}' 2>/dev/null || echo "Not running")
- User: $(docker exec "$TEST_CONTAINER_NAME" whoami 2>/dev/null || echo "Unknown")

System Information:
- Docker version: $(docker --version)
- Python version: $(python3 --version)
- OS: $(uname -a)

================================================================================
EOF
    
    log_success "Test report saved to: $report_file"
    cat "$report_file"
}

main() {
    local start_time=$(date +%s)
    local test_results=""
    local overall_success=true
    
    log_info "Starting MCP Draw.io Server Container Tests"
    echo "========================================================"
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Run tests
    local tests=(
        "check_prerequisites"
        "setup_test_environment"
        "build_test_image"
        "test_image_properties"
        "test_container_startup"
        "test_dependencies"
        "test_file_permissions"
        "run_python_tests"
    )
    
    for test in "${tests[@]}"; do
        log_info "Running test: $test"
        if $test; then
            test_results+="\n✓ $test: PASSED"
            log_success "Test passed: $test"
        else
            test_results+="\n✗ $test: FAILED"
            log_error "Test failed: $test"
            overall_success=false
        fi
        echo "----------------------------------------"
    done
    
    local end_time=$(date +%s)
    
    # Generate report
    generate_test_report "$start_time" "$end_time" "$test_results"
    
    # Final result
    echo "========================================================"
    if $overall_success; then
        log_success "All container tests passed! 🎉"
        log_info "The MCP Draw.io Server container is ready for deployment."
        return 0
    else
        log_error "Some container tests failed! ❌"
        log_info "Please review the test output and fix issues before deployment."
        return 1
    fi
}

# Run main function
main "$@"