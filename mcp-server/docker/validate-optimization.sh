#!/bin/bash
# Container optimization and security validation script

set -e

echo "🚀 Starting container optimization and security validation..."

# Change to the mcp-server directory
cd "$(dirname "$0")/.."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Set image name
IMAGE_NAME="${1:-mcp-drawio-server}"

echo "📋 Validation Configuration:"
echo "   Image name: $IMAGE_NAME"
echo "   Working directory: $(pwd)"
echo "   Docker version: $(docker --version)"
echo "   Python version: $(python3 --version)"
echo ""

# Run the validation
python3 docker/validate-optimization.py --image "$IMAGE_NAME"

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 Container optimization and security validation completed successfully!"
    echo "✅ All critical requirements met"
else
    echo ""
    echo "💥 Container optimization and security validation failed!"
    echo "❌ Some critical requirements not met"
fi

exit $EXIT_CODE