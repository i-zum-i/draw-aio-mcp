# MCP Draw.io Server Deployment Script (PowerShell)
# This script helps deploy the MCP server in different environments on Windows

param(
    [Parameter(HelpMessage="Environment to deploy (dev|prod)")]
    [ValidateSet("dev", "prod", "development", "production")]
    [string]$Environment = "prod",
    
    [Parameter(HelpMessage="Action to perform (up|down|restart|logs|status)")]
    [ValidateSet("up", "down", "restart", "logs", "status")]
    [string]$Action = "up",
    
    [Parameter(HelpMessage="Force rebuild of images")]
    [switch]$Build,
    
    [Parameter(HelpMessage="Run in foreground (don't detach)")]
    [switch]$Foreground,
    
    [Parameter(HelpMessage="Number of replicas to run")]
    [int]$Scale = 1,
    
    [Parameter(HelpMessage="Comma-separated list of profiles to enable")]
    [string]$Profiles = "",
    
    [Parameter(HelpMessage="Show help message")]
    [switch]$Help
)

# Function to show usage
function Show-Usage {
    Write-Host @"
MCP Draw.io Server Deployment Script (PowerShell)

Usage: .\deploy.ps1 [OPTIONS]

OPTIONS:
    -Environment ENV     Environment to deploy (dev|prod) [default: prod]
    -Action ACTION       Action to perform (up|down|restart|logs|status) [default: up]
    -Build              Force rebuild of images
    -Foreground         Run in foreground (don't detach)
    -Scale NUM          Number of replicas to run [default: 1]
    -Profiles LIST      Comma-separated list of profiles to enable
    -Help               Show this help message

EXAMPLES:
    # Deploy production environment
    .\deploy.ps1 -Environment prod -Build

    # Deploy development environment in foreground
    .\deploy.ps1 -Environment dev -Foreground

    # Scale production to 3 replicas
    .\deploy.ps1 -Environment prod -Scale 3

    # Deploy with monitoring enabled
    .\deploy.ps1 -Environment prod -Profiles monitoring

    # View logs
    .\deploy.ps1 -Action logs

    # Stop all services
    .\deploy.ps1 -Action down

    # Restart services
    .\deploy.ps1 -Action restart

"@ -ForegroundColor Cyan
}

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Header {
    param([string]$Message)
    Write-Host "[DEPLOY] $Message" -ForegroundColor Blue
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Normalize environment
switch ($Environment.ToLower()) {
    { $_ -in @("dev", "development") } {
        $Environment = "dev"
        $ComposeFile = "docker-compose.dev.yml"
        $EnvFile = ".env.dev"
    }
    { $_ -in @("prod", "production") } {
        $Environment = "prod"
        $ComposeFile = "docker-compose.prod.yml"
        $EnvFile = ".env.prod"
    }
    default {
        Write-Error "Invalid environment: $Environment. Use 'dev' or 'prod'"
        exit 1
    }
}

# Check if required files exist
if (-not (Test-Path $ComposeFile)) {
    Write-Error "Docker Compose file not found: $ComposeFile"
    exit 1
}

if (-not (Test-Path $EnvFile)) {
    Write-Warning "Environment file not found: $EnvFile"
    Write-Warning "Using default .env file or environment variables"
    $EnvFile = ""
}

# Build Docker Compose command
$DockerComposeCmd = "docker-compose -f $ComposeFile"

if ($EnvFile -and (Test-Path $EnvFile)) {
    $DockerComposeCmd += " --env-file $EnvFile"
}

if ($Profiles) {
    $env:COMPOSE_PROFILES = $Profiles
}

# Function to check if API key is set
function Test-ApiKey {
    $apiKey = $env:ANTHROPIC_API_KEY
    
    if (-not $apiKey -and $EnvFile -and (Test-Path $EnvFile)) {
        $envContent = Get-Content $EnvFile
        $apiKeyLine = $envContent | Where-Object { $_ -match "^ANTHROPIC_API_KEY=" }
        if ($apiKeyLine) {
            $apiKey = ($apiKeyLine -split "=", 2)[1]
        }
    }
    
    if (-not $apiKey -or $apiKey -eq "your_anthropic_api_key_here") {
        Write-Error "Please set your Anthropic API key in $EnvFile or as an environment variable"
        exit 1
    }
}

# Function to create necessary directories
function New-Directories {
    if ($Environment -eq "dev") {
        $tempDir = ".\temp_dev"
        $logsDir = ".\logs_dev"
    } else {
        $tempDir = ".\temp_prod"
        $logsDir = ".\logs_prod"
    }
    
    Write-Status "Creating directories..."
    
    if (-not (Test-Path $tempDir)) {
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    }
    
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }
}

# Function to perform health check
function Test-Health {
    Write-Status "Performing health check..."
    
    $containerName = if ($Environment -eq "dev") { "mcp-drawio-server-dev" } else { "mcp-drawio-server-prod" }
    
    try {
        $containers = docker ps --format "table {{.Names}}" | Select-String $containerName
        if ($containers) {
            $healthScript = @"
import sys
sys.path.append('/app/src')
from health import HealthChecker
import asyncio
import json

async def check():
    checker = HealthChecker()
    health = await checker.get_health()
    print(json.dumps(health, indent=2))

asyncio.run(check())
"@
            docker exec $containerName python -c $healthScript
        } else {
            Write-Warning "Container $containerName is not running"
        }
    } catch {
        Write-Warning "Health check failed: $($_.Exception.Message)"
    }
}

# Main deployment logic
switch ($Action) {
    "up" {
        Write-Header "Deploying MCP Draw.io Server ($Environment environment)"
        
        Test-ApiKey
        New-Directories
        
        # Build command options
        $cmdOptions = @()
        
        if ($Build) {
            $cmdOptions += "--build"
        }
        
        if (-not $Foreground) {
            $cmdOptions += "-d"
        }
        
        if ($Scale -gt 1 -and $Environment -eq "prod") {
            $cmdOptions += "--scale", "mcp-server=$Scale"
        }
        
        $fullCmd = "$DockerComposeCmd up $($cmdOptions -join ' ')"
        Write-Status "Running: $fullCmd"
        
        Invoke-Expression $fullCmd
        
        if (-not $Foreground) {
            Start-Sleep -Seconds 5
            Test-Health
            Write-Status "Deployment completed successfully!"
            Write-Status "Use '.\deploy.ps1 -Action logs' to view logs"
            Write-Status "Use '.\deploy.ps1 -Action status' to check status"
        }
    }
    
    "down" {
        Write-Header "Stopping MCP Draw.io Server ($Environment environment)"
        Invoke-Expression "$DockerComposeCmd down"
        Write-Status "Services stopped successfully!"
    }
    
    "restart" {
        Write-Header "Restarting MCP Draw.io Server ($Environment environment)"
        Invoke-Expression "$DockerComposeCmd restart"
        Start-Sleep -Seconds 5
        Test-Health
        Write-Status "Services restarted successfully!"
    }
    
    "logs" {
        Write-Header "Showing logs for MCP Draw.io Server ($Environment environment)"
        Invoke-Expression "$DockerComposeCmd logs -f"
    }
    
    "status" {
        Write-Header "Status of MCP Draw.io Server ($Environment environment)"
        Invoke-Expression "$DockerComposeCmd ps"
        Write-Host ""
        Test-Health
    }
    
    default {
        Write-Error "Invalid action: $Action"
        Write-Error "Valid actions: up, down, restart, logs, status"
        exit 1
    }
}