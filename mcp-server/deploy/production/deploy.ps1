# Production deployment script for MCP Server (PowerShell)
# Usage: .\deploy.ps1 [version]

param(
    [string]$Version = "latest"
)

$ContainerName = "mcp-server-prod"
$ImageName = "mcpserver/diagram-generator:$Version"
$BackupDir = "C:\opt\mcp-server\backups"
$LogDir = "C:\opt\mcp-server\logs"
$TempDir = "C:\opt\mcp-server\temp"

Write-Host "🚀 Starting MCP Server production deployment..." -ForegroundColor Green
Write-Host "Version: $Version" -ForegroundColor Cyan
Write-Host "Container: $ContainerName" -ForegroundColor Cyan
Write-Host "Image: $ImageName" -ForegroundColor Cyan

# Check required environment variables
if (-not $env:ANTHROPIC_API_KEY) {
    Write-Host "❌ ANTHROPIC_API_KEY environment variable is required" -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $BackupDir, $LogDir, $TempDir | Out-Null

# Pull the latest image
Write-Host "📥 Pulling Docker image..." -ForegroundColor Yellow
docker pull $ImageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to pull Docker image" -ForegroundColor Red
    exit 1
}

# Stop existing container if running
$RunningContainer = docker ps -q -f name=$ContainerName
if ($RunningContainer) {
    Write-Host "🛑 Stopping existing container..." -ForegroundColor Yellow
    docker stop $ContainerName
}

# Backup existing container if it exists
$ExistingContainer = docker ps -a -q -f name=$ContainerName
if ($ExistingContainer) {
    Write-Host "💾 Creating backup..." -ForegroundColor Yellow
    $BackupName = "$ContainerName-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    docker rename $ContainerName $BackupName
    Write-Host "Backup created: $BackupName" -ForegroundColor Green
}

# Run new container
Write-Host "🏃 Starting new container..." -ForegroundColor Yellow
$DockerArgs = @(
    "run", "-d",
    "--name", $ContainerName,
    "--restart", "unless-stopped",
    "-e", "ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY",
    "-e", "LOG_LEVEL=INFO",
    "-e", "ENVIRONMENT=production",
    "-e", "LOG_FILE=/app/logs/mcp-server.log",
    "-v", "${LogDir}:/app/logs",
    "-v", "${TempDir}:/app/temp",
    "-p", "8000:8000",
    "--memory=1g",
    "--cpus=1.0",
    "--health-cmd=python -c `"import requests; requests.get('http://localhost:8000/health')`"",
    "--health-interval=30s",
    "--health-timeout=10s",
    "--health-retries=3",
    "--health-start-period=40s",
    $ImageName
)

$ContainerId = docker @DockerArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
    exit 1
}

# Wait for container to be healthy
Write-Host "⏳ Waiting for container to be healthy..." -ForegroundColor Yellow
$Timeout = 120
$Counter = 0

while ($Counter -lt $Timeout) {
    $HealthStatus = docker inspect --format='{{.State.Health.Status}}' $ContainerName
    if ($HealthStatus -eq "healthy") {
        Write-Host "✅ Container is healthy!" -ForegroundColor Green
        break
    }
    
    if ($Counter -ge $Timeout) {
        Write-Host "❌ Container failed to become healthy within $Timeout seconds" -ForegroundColor Red
        Write-Host "Container logs:" -ForegroundColor Yellow
        docker logs $ContainerName
        exit 1
    }
    
    Start-Sleep -Seconds 2
    $Counter += 2
    Write-Host "Waiting... ($Counter/${Timeout}s)" -ForegroundColor Gray
}

# Test the deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    if ($Response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed!" -ForegroundColor Green
    } else {
        throw "Health check returned status code: $($Response.StatusCode)"
    }
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    docker logs $ContainerName
    exit 1
}

# Clean up old backups (keep last 5)
Write-Host "🧹 Cleaning up old backups..." -ForegroundColor Yellow
$BackupContainers = docker ps -a --format "{{.Names}}" | Where-Object { $_ -match "$ContainerName-backup-" } | Sort-Object | Select-Object -Skip 5
if ($BackupContainers) {
    $BackupContainers | ForEach-Object { docker rm $_ }
}

Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Container Status:" -ForegroundColor Cyan
docker ps --filter name=$ContainerName --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""
Write-Host "Logs: docker logs $ContainerName" -ForegroundColor Gray
Write-Host "Stop: docker stop $ContainerName" -ForegroundColor Gray
Write-Host "Restart: docker restart $ContainerName" -ForegroundColor Gray