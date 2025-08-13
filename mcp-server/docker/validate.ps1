# Dockerfile validation script for MCP Draw.io Server
# Checks syntax and best practices without requiring Docker daemon

param(
    [string]$DockerfilePath = "../Dockerfile"
)

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if Dockerfile exists
if (-not (Test-Path $DockerfilePath)) {
    Write-Error "Dockerfile not found at $DockerfilePath"
    exit 1
}

Write-Info "Validating Dockerfile at $DockerfilePath"

# Read Dockerfile content
$dockerfileContent = Get-Content $DockerfilePath -Raw
$lines = Get-Content $DockerfilePath

# Basic syntax validation
$errors = @()
$warnings = @()
$info = @()

# Check for required instructions
$requiredInstructions = @("FROM", "WORKDIR", "COPY", "RUN")
foreach ($instruction in $requiredInstructions) {
    if ($dockerfileContent -notmatch "(?m)^$instruction\s") {
        $errors += "Missing required instruction: $instruction"
    }
}

# Check for multi-stage build
$fromCount = ($lines | Where-Object { $_ -match "^FROM\s" }).Count
if ($fromCount -gt 1) {
    $info += "Multi-stage build detected ($fromCount stages)"
} else {
    $warnings += "Single-stage build - consider multi-stage for optimization"
}

# Check for security best practices
if ($dockerfileContent -match "USER\s+\w+") {
    $info += "Non-root user specified (security best practice)"
} else {
    $warnings += "No USER instruction found - container will run as root"
}

# Check for health check
if ($dockerfileContent -match "HEALTHCHECK") {
    $info += "Health check configured"
} else {
    $warnings += "No health check configured"
}

# Check for .dockerignore reference
$dockerignorePath = Split-Path $DockerfilePath -Parent | Join-Path -ChildPath ".dockerignore"
if (Test-Path $dockerignorePath) {
    $info += ".dockerignore file found"
} else {
    $warnings += ".dockerignore file not found - build context may be larger than necessary"
}

# Check for Alpine base images (size optimization)
$alpineImages = $lines | Where-Object { $_ -match "FROM.*alpine" }
if ($alpineImages.Count -gt 0) {
    $info += "Alpine base images used for size optimization"
}

# Check for package manager cache cleanup
$cleanupPatterns = @("rm -rf /var/cache/apk/\*", "npm cache clean", "pip.*--no-cache")
$hasCleanup = $false
foreach ($pattern in $cleanupPatterns) {
    if ($dockerfileContent -match $pattern) {
        $hasCleanup = $true
        break
    }
}

if ($hasCleanup) {
    $info += "Package manager cache cleanup detected"
} else {
    $warnings += "No package manager cache cleanup found - image may be larger than necessary"
}

# Check for COPY vs ADD usage
$addInstructions = $lines | Where-Object { $_ -match "^ADD\s" }
if ($addInstructions.Count -gt 0) {
    $warnings += "ADD instruction used - consider COPY for better security"
}

# Check for exposed ports
if ($dockerfileContent -match "EXPOSE\s+\d+") {
    $info += "Port exposure configured"
}

# Check for labels
if ($dockerfileContent -match "LABEL") {
    $info += "Metadata labels configured"
} else {
    $warnings += "No metadata labels found - consider adding for better container management"
}

# Check for entrypoint
if ($dockerfileContent -match "ENTRYPOINT") {
    $info += "ENTRYPOINT configured"
} else {
    $warnings += "No ENTRYPOINT found - consider using for better signal handling"
}

# Report results
Write-Info "Validation Results:"
Write-Host ""

if ($errors.Count -eq 0) {
    Write-Success "✅ No critical errors found"
} else {
    Write-Error "❌ Critical errors found:"
    foreach ($error in $errors) {
        Write-Host "  • $error" -ForegroundColor Red
    }
}

if ($warnings.Count -eq 0) {
    Write-Success "✅ No warnings"
} else {
    Write-Warning "⚠️ Warnings found:"
    foreach ($warning in $warnings) {
        Write-Host "  • $warning" -ForegroundColor Yellow
    }
}

if ($info.Count -gt 0) {
    Write-Info "ℹ️ Best practices detected:"
    foreach ($infoItem in $info) {
        Write-Host "  • $infoItem" -ForegroundColor Cyan
    }
}

Write-Host ""

# Summary
$totalIssues = $errors.Count + $warnings.Count
if ($totalIssues -eq 0) {
    Write-Success "🎉 Dockerfile validation passed with no issues!"
} elseif ($errors.Count -eq 0) {
    Write-Warning "⚠️ Dockerfile validation passed with $($warnings.Count) warnings"
} else {
    Write-Error "❌ Dockerfile validation failed with $($errors.Count) errors and $($warnings.Count) warnings"
    exit 1
}

# Additional checks
Write-Info "Additional Information:"
Write-Host "  • Dockerfile size: $((Get-Item $DockerfilePath).Length) bytes"
Write-Host "  • Number of instructions: $(($lines | Where-Object { $_ -match '^[A-Z]+\s' }).Count)"
Write-Host "  • Number of RUN instructions: $(($lines | Where-Object { $_ -match '^RUN\s' }).Count)"
Write-Host "  • Multi-stage stages: $fromCount"