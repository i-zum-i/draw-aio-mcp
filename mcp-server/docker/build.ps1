# Build script for MCP Draw.io Server Docker image
# PowerShell version for Windows support

param(
    [string]$ImageTag = "latest",
    [switch]$NoBuildKit = $false,
    [switch]$Verbose = $false
)

# Configuration
$ImageName = "mcp-drawio-server"
$DockerfilePath = "../Dockerfile"
$BuildContext = ".."

# Colors for output (Windows PowerShell compatible)
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $originalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Host $Message
    $Host.UI.RawUI.ForegroundColor = $originalColor
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Info "Docker found: $dockerVersion"
} catch {
    Write-Error "Docker is not installed or not in PATH"
    exit 1
}

# Check if we're in the correct directory
if (-not (Test-Path $DockerfilePath)) {
    Write-Error "Dockerfile not found at $DockerfilePath"
    Write-Error "Please run this script from the docker/ directory"
    exit 1
}

# Build information
Write-Info "Building MCP Draw.io Server Docker image"
Write-Info "Image name: ${ImageName}:${ImageTag}"
Write-Info "Dockerfile: $DockerfilePath"
Write-Info "Build context: $BuildContext"

# Prepare build arguments
$buildArgs = @(
    "build",
    "-f", $DockerfilePath,
    "-t", "${ImageName}:${ImageTag}",
    "--build-arg", "BUILDTIME=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')",
    "--build-arg", "VERSION=$ImageTag"
)

# Add BuildKit settings
if (-not $NoBuildKit) {
    $env:DOCKER_BUILDKIT = "1"
    Write-Info "Using Docker BuildKit for optimized builds"
}

# Add verbose output if requested
if ($Verbose) {
    $buildArgs += "--progress=plain"
}

# Add build context
$buildArgs += $BuildContext

# Build the image
Write-Info "Starting Docker build..."
try {
    & docker @buildArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker image built successfully!"
        
        # Show image information
        Write-Info "Image details:"
        docker images "${ImageName}:${ImageTag}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        
        # Show usage instructions
        Write-Info "To run the container:"
        Write-Host "  docker run --rm -e ANTHROPIC_API_KEY=your_key_here ${ImageName}:${ImageTag}" -ForegroundColor Gray
        
        Write-Info "To run with volume mount for temp files:"
        Write-Host "  docker run --rm -e ANTHROPIC_API_KEY=your_key_here -v `"temp_data:/app/temp`" ${ImageName}:${ImageTag}" -ForegroundColor Gray
        
        Write-Info "To run with custom configuration:"
        Write-Host "  docker run --rm --env-file .env ${ImageName}:${ImageTag}" -ForegroundColor Gray
        
    } else {
        Write-Error "Docker build failed with exit code $LASTEXITCODE"
        exit 1
    }
    
} catch {
    Write-Error "Docker build failed: $($_.Exception.Message)"
    exit 1
}

# Optional: Show build history
Write-Info "Build completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Check image size
try {
    $imageInfo = docker inspect "${ImageName}:${ImageTag}" | ConvertFrom-Json
    $sizeBytes = $imageInfo[0].Size
    $sizeMB = [math]::Round($sizeBytes / 1MB, 2)
    
    if ($sizeMB -lt 500) {
        Write-Success "Image size: ${sizeMB} MB (within 500MB target)"
    } else {
        Write-Warning "Image size: ${sizeMB} MB (exceeds 500MB target)"
    }
} catch {
    Write-Warning "Could not determine image size"
}