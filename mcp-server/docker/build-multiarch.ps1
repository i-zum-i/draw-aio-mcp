# Multi-architecture Docker build script for MCP Draw.io Server (PowerShell)
# Task 27: Docker Image Optimization - Multi-architecture support

param(
    [string]$Version = "1.0.0",
    [string]$ImageName = "mcp-drawio-server",
    [switch]$Push = $false,
    [switch]$CleanupBuilder = $false
)

# Configuration
$BUILD_DATE = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$VCS_REF = try { (git rev-parse --short HEAD 2>$null) } catch { "unknown" }
$PLATFORMS = "linux/amd64,linux/arm64,linux/arm/v7"

Write-Host "=== MCP Draw.io Server Multi-Architecture Build ===" -ForegroundColor Blue
Write-Host "Version: $Version" -ForegroundColor Blue
Write-Host "Build Date: $BUILD_DATE" -ForegroundColor Blue
Write-Host "VCS Ref: $VCS_REF" -ForegroundColor Blue
Write-Host "Platforms: $PLATFORMS" -ForegroundColor Blue
Write-Host ""

# Check if Docker Buildx is available
try {
    docker buildx version | Out-Null
} catch {
    Write-Host "Error: Docker Buildx is required for multi-architecture builds" -ForegroundColor Red
    Write-Host "Please install Docker Buildx or use Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# Create and use a new builder instance
Write-Host "Setting up Docker Buildx builder..." -ForegroundColor Yellow
try {
    docker buildx create --name mcp-builder --use --bootstrap 2>$null
} catch {
    docker buildx use mcp-builder
}

# Verify builder supports required platforms
Write-Host "Verifying platform support..." -ForegroundColor Yellow
docker buildx inspect --bootstrap

# Build arguments
$buildArgs = @(
    "--platform", $PLATFORMS,
    "--file", "Dockerfile.optimized",
    "--tag", "${ImageName}:${Version}",
    "--tag", "${ImageName}:latest",
    "--build-arg", "VERSION=${Version}",
    "--build-arg", "BUILD_DATE=${BUILD_DATE}",
    "--build-arg", "VCS_REF=${VCS_REF}"
)

if ($Push) {
    $buildArgs += "--push"
} else {
    $buildArgs += "--load"
    Write-Host "Note: Multi-arch images cannot be loaded locally. Use -Push to push to registry." -ForegroundColor Yellow
}

# Build multi-architecture image
Write-Host "Building multi-architecture image..." -ForegroundColor Yellow
docker buildx build @buildArgs .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Multi-architecture build completed successfully" -ForegroundColor Green
    if ($Push) {
        Write-Host "✓ Images pushed to registry" -ForegroundColor Green
    }
} else {
    Write-Host "✗ Build failed" -ForegroundColor Red
    exit 1
}

# Display image information
Write-Host "=== Build Summary ===" -ForegroundColor Blue
if ($Push) {
    docker buildx imagetools inspect "${ImageName}:${Version}"
} else {
    docker images "${ImageName}:${Version}"
}

# Cleanup builder (optional)
if ($CleanupBuilder) {
    docker buildx rm mcp-builder
    Write-Host "✓ Builder instance removed" -ForegroundColor Green
}

Write-Host "=== Multi-architecture build process completed ===" -ForegroundColor Green