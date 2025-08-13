# Container optimization and security validation script for Windows
param(
    [string]$ImageName = "mcp-drawio-server"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting container optimization and security validation..." -ForegroundColor Green

# Change to the mcp-server directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$mcpServerDir = Split-Path -Parent $scriptDir
Set-Location $mcpServerDir

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        $pythonVersion = python3 --version 2>&1
        $pythonCmd = "python3"
    } else {
        $pythonCmd = "python"
    }
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Validation Configuration:" -ForegroundColor Cyan
Write-Host "   Image name: $ImageName"
Write-Host "   Working directory: $(Get-Location)"
Write-Host "   Docker version: $dockerVersion"
Write-Host "   Python version: $pythonVersion"
Write-Host ""

# Run the validation
try {
    & $pythonCmd docker/validate-optimization.py --image $ImageName
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "❌ Failed to run validation script: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "🎉 Container optimization and security validation completed successfully!" -ForegroundColor Green
    Write-Host "✅ All critical requirements met" -ForegroundColor Green
} else {
    Write-Host "💥 Container optimization and security validation failed!" -ForegroundColor Red
    Write-Host "❌ Some critical requirements not met" -ForegroundColor Red
}

exit $exitCode