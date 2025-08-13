# Security vulnerability scanning script for MCP Draw.io Server (PowerShell)
# Task 27: Docker Image Optimization - Security vulnerability scanning

param(
    [string]$ImageName = "mcp-drawio-server:latest",
    [string]$OutputDir = "./security-reports"
)

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$SCAN_OUTPUT_DIR = $OutputDir

Write-Host "=== MCP Draw.io Server Security Vulnerability Scan ===" -ForegroundColor Blue
Write-Host "Image: $ImageName" -ForegroundColor Blue
Write-Host "Timestamp: $TIMESTAMP" -ForegroundColor Blue
Write-Host ""

# Create output directory
if (!(Test-Path $SCAN_OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $SCAN_OUTPUT_DIR -Force | Out-Null
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to run Docker Scout scan
function Invoke-DockerScoutScan {
    Write-Host "Running Docker Scout vulnerability scan..." -ForegroundColor Yellow
    try {
        if (Test-Command "docker") {
            docker scout version 2>$null | Out-Null
            docker scout cves $ImageName --format json > "$SCAN_OUTPUT_DIR/docker-scout-$TIMESTAMP.json" 2>$null
            docker scout cves $ImageName --format table > "$SCAN_OUTPUT_DIR/docker-scout-$TIMESTAMP.txt" 2>$null
            Write-Host "✓ Docker Scout scan completed" -ForegroundColor Green
        } else {
            Write-Host "⚠ Docker Scout not available" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ Docker Scout scan failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Function to run Trivy scan
function Invoke-TrivyScan {
    Write-Host "Running Trivy vulnerability scan..." -ForegroundColor Yellow
    try {
        if (Test-Command "trivy") {
            trivy image --format json --output "$SCAN_OUTPUT_DIR/trivy-$TIMESTAMP.json" $ImageName 2>$null
            trivy image --format table --output "$SCAN_OUTPUT_DIR/trivy-$TIMESTAMP.txt" $ImageName 2>$null
            Write-Host "✓ Trivy scan completed" -ForegroundColor Green
        } else {
            Write-Host "⚠ Trivy not installed" -ForegroundColor Yellow
            Write-Host "  Install with: winget install Aqua.Trivy" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ Trivy scan failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Function to run Snyk scan
function Invoke-SnykScan {
    Write-Host "Running Snyk vulnerability scan..." -ForegroundColor Yellow
    try {
        if (Test-Command "snyk") {
            snyk container test $ImageName --json > "$SCAN_OUTPUT_DIR/snyk-$TIMESTAMP.json" 2>$null
            snyk container test $ImageName > "$SCAN_OUTPUT_DIR/snyk-$TIMESTAMP.txt" 2>$null
            Write-Host "✓ Snyk scan completed" -ForegroundColor Green
        } else {
            Write-Host "⚠ Snyk not available (requires authentication)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ Snyk scan failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Function to analyze image layers
function Invoke-ImageAnalysis {
    Write-Host "Analyzing image layers and size..." -ForegroundColor Yellow
    try {
        docker history $ImageName > "$SCAN_OUTPUT_DIR/image-history-$TIMESTAMP.txt" 2>$null
        docker inspect $ImageName > "$SCAN_OUTPUT_DIR/image-inspect-$TIMESTAMP.json" 2>$null
        
        # Get image size
        $imageSize = (docker images $ImageName --format "{{.Size}}" | Select-Object -First 1)
        "Image Size: $imageSize" | Out-File -FilePath "$SCAN_OUTPUT_DIR/image-size-$TIMESTAMP.txt"
        Write-Host "✓ Image analysis completed" -ForegroundColor Green
        return $imageSize
    } catch {
        Write-Host "⚠ Image analysis failed: $($_.Exception.Message)" -ForegroundColor Yellow
        return "unknown"
    }
}

# Function to check security best practices
function Test-SecurityBestPractices {
    param([string]$ImageSize)
    
    Write-Host "Checking security best practices..." -ForegroundColor Yellow
    try {
        # Check if running as root
        $userCheck = docker run --rm $ImageName whoami 2>$null
        if (!$userCheck) { $userCheck = "unknown" }
        
        # Check exposed ports
        $portsCheck = docker inspect $ImageName | ConvertFrom-Json | ForEach-Object { $_.Config.ExposedPorts } | Get-Member -MemberType NoteProperty | ForEach-Object { $_.Name }
        if (!$portsCheck) { $portsCheck = "none" }
        
        # Create security checklist
        $securityChecklist = @"
Security Best Practices Check - $TIMESTAMP
============================================

Image: $ImageName
User: $userCheck
Exposed Ports: $($portsCheck -join ', ')

Checklist:
- [ ] Non-root user: $(if ($userCheck -ne "root") { "✓ PASS" } else { "✗ FAIL" })
- [ ] Minimal base image: $(if ($ImageName -match "alpine") { "✓ PASS" } else { "? UNKNOWN" })
- [ ] No unnecessary ports: $(if ($portsCheck -eq "none" -or $portsCheck -eq "8000/tcp") { "✓ PASS" } else { "? REVIEW" })
- [ ] Image size reasonable: $(if ($ImageSize -match "\d+MB") { "✓ PASS" } else { "? REVIEW" })

"@
        $securityChecklist | Out-File -FilePath "$SCAN_OUTPUT_DIR/security-checklist-$TIMESTAMP.txt"
        Write-Host "✓ Security best practices check completed" -ForegroundColor Green
        return @{ User = $userCheck; Ports = $portsCheck }
    } catch {
        Write-Host "⚠ Security check failed: $($_.Exception.Message)" -ForegroundColor Yellow
        return @{ User = "unknown"; Ports = "unknown" }
    }
}

# Function to generate summary report
function New-SummaryReport {
    param(
        [string]$ImageSize,
        [hashtable]$SecurityInfo
    )
    
    Write-Host "Generating summary report..." -ForegroundColor Yellow
    
    $summaryReport = @"
# Security Scan Summary Report

**Image:** $ImageName  
**Scan Date:** $(Get-Date)  
**Report ID:** $TIMESTAMP

## Scan Results

### Tools Used
- Docker Scout: $(if (Test-Command "docker") { "✓ Available" } else { "✗ Not available" })
- Trivy: $(if (Test-Command "trivy") { "✓ Available" } else { "✗ Not available" })
- Snyk: $(if (Test-Command "snyk") { "✓ Available" } else { "✗ Not available" })

### Image Information
- **Size:** $ImageSize
- **User:** $($SecurityInfo.User)
- **Exposed Ports:** $($SecurityInfo.Ports -join ', ')

### Files Generated
- Docker Scout: docker-scout-$TIMESTAMP.json, docker-scout-$TIMESTAMP.txt
- Trivy: trivy-$TIMESTAMP.json, trivy-$TIMESTAMP.txt
- Snyk: snyk-$TIMESTAMP.json, snyk-$TIMESTAMP.txt
- Image Analysis: image-history-$TIMESTAMP.txt, image-inspect-$TIMESTAMP.json
- Security Checklist: security-checklist-$TIMESTAMP.txt

### Recommendations
1. Review vulnerability reports for critical and high severity issues
2. Update base images and dependencies regularly
3. Implement automated security scanning in CI/CD pipeline
4. Monitor for new vulnerabilities in dependencies

### Next Steps
1. Address any critical vulnerabilities found
2. Update Dockerfile if security issues are identified
3. Re-scan after applying fixes
4. Document security exceptions if any

"@
    $summaryReport | Out-File -FilePath "$SCAN_OUTPUT_DIR/security-summary-$TIMESTAMP.md"
    Write-Host "✓ Summary report generated" -ForegroundColor Green
}

# Main execution
Write-Host "Starting comprehensive security scan..." -ForegroundColor Blue

# Check if image exists
try {
    docker image inspect $ImageName | Out-Null
} catch {
    Write-Host "Error: Image $ImageName not found" -ForegroundColor Red
    Write-Host "Please build the image first or specify an existing image" -ForegroundColor Yellow
    exit 1
}

# Run all scans
Invoke-DockerScoutScan
Invoke-TrivyScan
Invoke-SnykScan
$imageSize = Invoke-ImageAnalysis
$securityInfo = Test-SecurityBestPractices -ImageSize $imageSize
New-SummaryReport -ImageSize $imageSize -SecurityInfo $securityInfo

Write-Host ""
Write-Host "=== Security scan completed ===" -ForegroundColor Green
Write-Host "Reports saved to: $SCAN_OUTPUT_DIR" -ForegroundColor Green
Write-Host "Summary report: $SCAN_OUTPUT_DIR/security-summary-$TIMESTAMP.md" -ForegroundColor Blue

# Display quick summary
Write-Host ""
Write-Host "=== Quick Summary ===" -ForegroundColor Blue
Write-Host "Image Size: $imageSize" -ForegroundColor Blue
Write-Host "Running User: $($securityInfo.User)" -ForegroundColor Blue
Write-Host "Exposed Ports: $($securityInfo.Ports -join ', ')" -ForegroundColor Blue

# Try to get vulnerability counts from Trivy if available
$trivyFile = "$SCAN_OUTPUT_DIR/trivy-$TIMESTAMP.json"
if (Test-Path $trivyFile) {
    try {
        $trivyData = Get-Content $trivyFile | ConvertFrom-Json
        $criticalCount = ($trivyData.Results | ForEach-Object { $_.Vulnerabilities } | Where-Object { $_.Severity -eq "CRITICAL" }).Count
        $highCount = ($trivyData.Results | ForEach-Object { $_.Vulnerabilities } | Where-Object { $_.Severity -eq "HIGH" }).Count
        Write-Host "Critical Vulnerabilities: $criticalCount" -ForegroundColor Blue
        Write-Host "High Vulnerabilities: $highCount" -ForegroundColor Blue
    } catch {
        Write-Host "Could not parse Trivy results" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Security scan process completed successfully" -ForegroundColor Green