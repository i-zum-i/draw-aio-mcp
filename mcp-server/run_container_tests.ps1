# Container Test Runner Script for MCP Draw.io Server (PowerShell)
# This script runs comprehensive container tests including build and runtime tests

param(
    [switch]$SkipBuild,
    [switch]$Verbose
)

# Configuration
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TestImageName = "mcp-drawio-server:test"
$TestContainerName = "mcp-test-container"

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

# Functions
function Write-LogInfo {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-LogSuccess {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-LogWarning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-LogError {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Cleanup {
    Write-LogInfo "Cleaning up test resources..."
    
    try {
        # Stop and remove test containers
        docker stop $TestContainerName 2>$null
        docker rm $TestContainerName 2>$null
        
        # Remove test images
        docker rmi $TestImageName 2>$null
        
        # Clean up test directories
        Remove-Item -Path "$ProjectRoot\temp_test" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path "$ProjectRoot\logs_test" -Recurse -Force -ErrorAction SilentlyContinue
        
        Write-LogSuccess "Cleanup completed"
    }
    catch {
        Write-LogWarning "Some cleanup operations failed: $_"
    }
}

function Test-Prerequisites {
    Write-LogInfo "Checking prerequisites..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-LogSuccess "Docker available: $dockerVersion"
    }
    catch {
        Write-LogError "Docker is not installed or not in PATH"
        return $false
    }
    
    # Check Docker daemon
    try {
        docker info | Out-Null
        Write-LogSuccess "Docker daemon running"
    }
    catch {
        Write-LogError "Docker daemon is not running"
        return $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-LogSuccess "Python available: $pythonVersion"
    }
    catch {
        Write-LogError "Python is not installed or not in PATH"
        return $false
    }
    
    # Check required files
    $requiredFiles = @("Dockerfile", "requirements.txt", "src\server.py", "src\tools.py")
    foreach ($file in $requiredFiles) {
        $filePath = Join-Path $ProjectRoot $file
        if (-not (Test-Path $filePath)) {
            Write-LogError "Required file missing: $file"
            return $false
        }
    }
    
    Write-LogSuccess "All prerequisites met"
    return $true
}

function Initialize-TestEnvironment {
    Write-LogInfo "Setting up test environment..."
    
    # Create test directories
    New-Item -Path "$ProjectRoot\temp_test" -ItemType Directory -Force | Out-Null
    New-Item -Path "$ProjectRoot\logs_test" -ItemType Directory -Force | Out-Null
    New-Item -Path "$ProjectRoot\tests\container" -ItemType Directory -Force | Out-Null
    
    # Create test environment file
    $apiKey = if ($env:ANTHROPIC_API_KEY) { $env:ANTHROPIC_API_KEY } else { "test-key-for-testing" }
    $envContent = @"
ANTHROPIC_API_KEY=$apiKey
LOG_LEVEL=DEBUG
CACHE_TTL=300
FILE_EXPIRY_HOURS=1
TEMP_DIR=/app/temp
DRAWIO_CLI_PATH=drawio
"@
    
    $envContent | Out-File -FilePath "$ProjectRoot\.env.test" -Encoding UTF8
    
    Write-LogSuccess "Test environment ready"
    return $true
}

function Build-TestImage {
    if ($SkipBuild) {
        Write-LogInfo "Skipping image build (--SkipBuild specified)"
        return $true
    }
    
    Write-LogInfo "Building test Docker image..."
    
    Push-Location $ProjectRoot
    try {
        $buildResult = docker build -t $TestImageName . 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Docker image built successfully"
            
            # Get image info
            $imageSize = docker images $TestImageName --format "{{.Size}}" | Select-Object -First 1
            Write-LogInfo "Image size: $imageSize"
            
            return $true
        }
        else {
            Write-LogError "Docker image build failed"
            Write-Host $buildResult
            return $false
        }
    }
    finally {
        Pop-Location
    }
}

function Test-ImageProperties {
    Write-LogInfo "Testing image properties..."
    
    try {
        # Test image size (should be under 500MB)
        $sizeBytes = docker inspect $TestImageName --format='{{.Size}}' | ConvertTo-Json | ConvertFrom-Json
        $sizeMB = [math]::Round($sizeBytes / 1024 / 1024, 2)
        
        if ($sizeMB -lt 500) {
            Write-LogSuccess "Image size acceptable: ${sizeMB}MB (limit: 500MB)"
        }
        else {
            Write-LogWarning "Image size large: ${sizeMB}MB (limit: 500MB)"
        }
        
        # Test image layers
        $layers = docker inspect $TestImageName --format='{{len .RootFS.Layers}}'
        Write-LogInfo "Image layers: $layers"
        
        # Test image labels
        $labels = docker inspect $TestImageName --format='{{json .Config.Labels}}'
        if ($labels -ne "null") {
            Write-LogSuccess "Image has metadata labels"
        }
        else {
            Write-LogWarning "Image missing metadata labels"
        }
        
        return $true
    }
    catch {
        Write-LogError "Image properties test failed: $_"
        return $false
    }
}

function Test-ContainerStartup {
    Write-LogInfo "Testing container startup..."
    
    try {
        # Start container
        $startResult = docker run -d `
            --name $TestContainerName `
            --env-file "$ProjectRoot\.env.test" `
            -v "${ProjectRoot}\temp_test:/app/temp" `
            -v "${ProjectRoot}\logs_test:/app/logs" `
            $TestImageName
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Container started successfully"
        }
        else {
            Write-LogError "Container failed to start"
            return $false
        }
        
        # Wait for container to be ready
        Write-LogInfo "Waiting for container to be ready..."
        $maxWait = 30
        $waitTime = 0
        
        while ($waitTime -lt $maxWait) {
            try {
                docker exec $TestContainerName python /app/src/healthcheck.py | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-LogSuccess "Container is healthy"
                    return $true
                }
            }
            catch {
                # Continue waiting
            }
            
            Start-Sleep 2
            $waitTime += 2
            Write-LogInfo "Waiting... (${waitTime}s/${maxWait}s)"
        }
        
        Write-LogError "Container not ready after $maxWait seconds"
        docker logs $TestContainerName
        return $false
    }
    catch {
        Write-LogError "Container startup test failed: $_"
        return $false
    }
}

function Test-Dependencies {
    Write-LogInfo "Testing dependencies..."
    
    try {
        # Test Python
        $pythonResult = docker exec $TestContainerName python3 --version
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Python 3 available: $pythonResult"
        }
        else {
            Write-LogError "Python 3 not available"
            return $false
        }
        
        # Test Draw.io CLI
        $drawioResult = docker exec $TestContainerName drawio --version
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Draw.io CLI available"
        }
        else {
            Write-LogError "Draw.io CLI not available"
            return $false
        }
        
        # Test Python packages
        $packages = @("mcp", "anthropic", "httpx")
        foreach ($package in $packages) {
            $testResult = docker exec $TestContainerName python3 -c "import $package; print('$package imported successfully')"
            if ($LASTEXITCODE -eq 0) {
                Write-LogSuccess "Python package available: $package"
            }
            else {
                Write-LogError "Python package missing: $package"
                return $false
            }
        }
        
        # Test application modules
        $appTest = docker exec $TestContainerName python3 -c "import sys; sys.path.append('/app/src'); from llm_service import LLMService; print('Application modules imported successfully')"
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Application modules importable"
        }
        else {
            Write-LogError "Application modules not importable"
            return $false
        }
        
        return $true
    }
    catch {
        Write-LogError "Dependencies test failed: $_"
        return $false
    }
}

function Test-FilePermissions {
    Write-LogInfo "Testing file permissions..."
    
    try {
        # Test temp directory
        $tempTest = docker exec $TestContainerName python3 -c "import os; os.makedirs('/app/temp/test', exist_ok=True); print('Temp directory writable')"
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Temp directory writable"
        }
        else {
            Write-LogError "Temp directory not writable"
            return $false
        }
        
        # Test logs directory
        $logsTest = docker exec $TestContainerName python3 -c "import os; os.makedirs('/app/logs/test', exist_ok=True); print('Logs directory writable')"
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Logs directory writable"
        }
        else {
            Write-LogError "Logs directory not writable"
            return $false
        }
        
        # Test user
        $user = docker exec $TestContainerName whoami
        if ($user -ne "root") {
            Write-LogSuccess "Container runs as non-root user: $user"
        }
        else {
            Write-LogWarning "Container runs as root user"
        }
        
        return $true
    }
    catch {
        Write-LogError "File permissions test failed: $_"
        return $false
    }
}

function Invoke-PythonTests {
    Write-LogInfo "Running Python container tests..."
    
    $pythonTestFile = Join-Path $ProjectRoot "tests\container\run_container_tests.py"
    if (Test-Path $pythonTestFile) {
        Push-Location $ProjectRoot
        try {
            python tests\container\run_container_tests.py
            if ($LASTEXITCODE -eq 0) {
                Write-LogSuccess "Python container tests passed"
                return $true
            }
            else {
                Write-LogError "Python container tests failed"
                return $false
            }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-LogWarning "Python container tests not found, skipping"
        return $true
    }
}

function New-TestReport {
    param(
        [datetime]$StartTime,
        [datetime]$EndTime,
        [string]$TestResults
    )
    
    Write-LogInfo "Generating test report..."
    
    $reportFile = Join-Path $ProjectRoot "tests\container\test_report.txt"
    $duration = ($EndTime - $StartTime).TotalSeconds
    
    $reportContent = @"
================================================================================
MCP DRAW.IO SERVER - CONTAINER TEST REPORT
================================================================================
Test execution time: $(Get-Date)
Duration: $duration seconds

Test Results:
$TestResults

Image Information:
- Name: $TestImageName
- Size: $(docker images $TestImageName --format "{{.Size}}" | Select-Object -First 1)
- Layers: $(docker inspect $TestImageName --format='{{len .RootFS.Layers}}')

Container Information:
- Name: $TestContainerName
- Status: $(try { docker inspect $TestContainerName --format='{{.State.Status}}' } catch { "Not running" })
- User: $(try { docker exec $TestContainerName whoami } catch { "Unknown" })

System Information:
- Docker version: $(docker --version)
- Python version: $(python --version)
- OS: $($env:OS) $($env:PROCESSOR_ARCHITECTURE)

================================================================================
"@
    
    $reportContent | Out-File -FilePath $reportFile -Encoding UTF8
    
    Write-LogSuccess "Test report saved to: $reportFile"
    Write-Host $reportContent
}

function Main {
    $startTime = Get-Date
    $testResults = @()
    $overallSuccess = $true
    
    Write-LogInfo "Starting MCP Draw.io Server Container Tests"
    Write-Host "========================================================"
    
    # Define tests
    $tests = @(
        @{ Name = "Prerequisites"; Function = { Test-Prerequisites } },
        @{ Name = "Test Environment"; Function = { Initialize-TestEnvironment } },
        @{ Name = "Build Image"; Function = { Build-TestImage } },
        @{ Name = "Image Properties"; Function = { Test-ImageProperties } },
        @{ Name = "Container Startup"; Function = { Test-ContainerStartup } },
        @{ Name = "Dependencies"; Function = { Test-Dependencies } },
        @{ Name = "File Permissions"; Function = { Test-FilePermissions } },
        @{ Name = "Python Tests"; Function = { Invoke-PythonTests } }
    )
    
    # Run tests
    foreach ($test in $tests) {
        Write-LogInfo "Running test: $($test.Name)"
        try {
            $result = & $test.Function
            if ($result) {
                $testResults += "✓ $($test.Name): PASSED"
                Write-LogSuccess "Test passed: $($test.Name)"
            }
            else {
                $testResults += "✗ $($test.Name): FAILED"
                Write-LogError "Test failed: $($test.Name)"
                $overallSuccess = $false
            }
        }
        catch {
            $testResults += "✗ $($test.Name): ERROR - $_"
            Write-LogError "Test error: $($test.Name) - $_"
            $overallSuccess = $false
        }
        Write-Host "----------------------------------------"
    }
    
    $endTime = Get-Date
    
    # Generate report
    New-TestReport -StartTime $startTime -EndTime $endTime -TestResults ($testResults -join "`n")
    
    # Final result
    Write-Host "========================================================"
    if ($overallSuccess) {
        Write-LogSuccess "All container tests passed!"
        Write-LogInfo "The MCP Draw.io Server container is ready for deployment."
        return 0
    }
    else {
        Write-LogError "Some container tests failed!"
        Write-LogInfo "Please review the test output and fix issues before deployment."
        return 1
    }
}

# Cleanup on exit
try {
    $exitCode = Main
    exit $exitCode
}
finally {
    Cleanup
}