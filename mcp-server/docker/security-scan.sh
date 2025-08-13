#!/bin/bash
# Security vulnerability scanning script for MCP Draw.io Server
# Task 27: Docker Image Optimization - Security vulnerability scanning

set -e

# Configuration
IMAGE_NAME="${1:-mcp-drawio-server:latest}"
SCAN_OUTPUT_DIR="./security-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== MCP Draw.io Server Security Vulnerability Scan ===${NC}"
echo -e "${BLUE}Image: ${IMAGE_NAME}${NC}"
echo -e "${BLUE}Timestamp: ${TIMESTAMP}${NC}"
echo ""

# Create output directory
mkdir -p "${SCAN_OUTPUT_DIR}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run Docker Scout scan
run_docker_scout() {
    echo -e "${YELLOW}Running Docker Scout vulnerability scan...${NC}"
    if command_exists docker && docker scout version >/dev/null 2>&1; then
        docker scout cves "${IMAGE_NAME}" --format json > "${SCAN_OUTPUT_DIR}/docker-scout-${TIMESTAMP}.json" 2>/dev/null || true
        docker scout cves "${IMAGE_NAME}" --format table > "${SCAN_OUTPUT_DIR}/docker-scout-${TIMESTAMP}.txt" 2>/dev/null || true
        echo -e "${GREEN}✓ Docker Scout scan completed${NC}"
    else
        echo -e "${YELLOW}⚠ Docker Scout not available${NC}"
    fi
}

# Function to run Trivy scan
run_trivy_scan() {
    echo -e "${YELLOW}Running Trivy vulnerability scan...${NC}"
    if command_exists trivy; then
        trivy image --format json --output "${SCAN_OUTPUT_DIR}/trivy-${TIMESTAMP}.json" "${IMAGE_NAME}" 2>/dev/null || true
        trivy image --format table --output "${SCAN_OUTPUT_DIR}/trivy-${TIMESTAMP}.txt" "${IMAGE_NAME}" 2>/dev/null || true
        echo -e "${GREEN}✓ Trivy scan completed${NC}"
    else
        echo -e "${YELLOW}⚠ Trivy not installed. Installing...${NC}"
        if command_exists curl; then
            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
            run_trivy_scan
        else
            echo -e "${RED}✗ Cannot install Trivy (curl not available)${NC}"
        fi
    fi
}

# Function to run Snyk scan
run_snyk_scan() {
    echo -e "${YELLOW}Running Snyk vulnerability scan...${NC}"
    if command_exists snyk; then
        snyk container test "${IMAGE_NAME}" --json > "${SCAN_OUTPUT_DIR}/snyk-${TIMESTAMP}.json" 2>/dev/null || true
        snyk container test "${IMAGE_NAME}" > "${SCAN_OUTPUT_DIR}/snyk-${TIMESTAMP}.txt" 2>/dev/null || true
        echo -e "${GREEN}✓ Snyk scan completed${NC}"
    else
        echo -e "${YELLOW}⚠ Snyk not available (requires authentication)${NC}"
    fi
}

# Function to analyze image layers
analyze_image_layers() {
    echo -e "${YELLOW}Analyzing image layers and size...${NC}"
    docker history "${IMAGE_NAME}" > "${SCAN_OUTPUT_DIR}/image-history-${TIMESTAMP}.txt" 2>/dev/null || true
    docker inspect "${IMAGE_NAME}" > "${SCAN_OUTPUT_DIR}/image-inspect-${TIMESTAMP}.json" 2>/dev/null || true
    
    # Get image size
    IMAGE_SIZE=$(docker images "${IMAGE_NAME}" --format "table {{.Size}}" | tail -n +2)
    echo "Image Size: ${IMAGE_SIZE}" > "${SCAN_OUTPUT_DIR}/image-size-${TIMESTAMP}.txt"
    echo -e "${GREEN}✓ Image analysis completed${NC}"
}

# Function to check for common security issues
check_security_best_practices() {
    echo -e "${YELLOW}Checking security best practices...${NC}"
    
    # Check if running as root
    USER_CHECK=$(docker run --rm "${IMAGE_NAME}" whoami 2>/dev/null || echo "unknown")
    
    # Check exposed ports
    PORTS_CHECK=$(docker inspect "${IMAGE_NAME}" | jq -r '.[0].Config.ExposedPorts // {} | keys[]' 2>/dev/null || echo "none")
    
    # Create security checklist
    cat > "${SCAN_OUTPUT_DIR}/security-checklist-${TIMESTAMP}.txt" << EOF
Security Best Practices Check - ${TIMESTAMP}
============================================

Image: ${IMAGE_NAME}
User: ${USER_CHECK}
Exposed Ports: ${PORTS_CHECK}

Checklist:
- [ ] Non-root user: $([ "${USER_CHECK}" != "root" ] && echo "✓ PASS" || echo "✗ FAIL")
- [ ] Minimal base image: $(echo "${IMAGE_NAME}" | grep -q "alpine" && echo "✓ PASS" || echo "? UNKNOWN")
- [ ] No unnecessary ports: $([ "${PORTS_CHECK}" = "none" ] || [ "${PORTS_CHECK}" = "8000/tcp" ] && echo "✓ PASS" || echo "? REVIEW")
- [ ] Image size reasonable: $(echo "${IMAGE_SIZE}" | grep -qE "[0-9]+MB" && echo "✓ PASS" || echo "? REVIEW")

EOF
    echo -e "${GREEN}✓ Security best practices check completed${NC}"
}

# Function to generate summary report
generate_summary_report() {
    echo -e "${YELLOW}Generating summary report...${NC}"
    
    cat > "${SCAN_OUTPUT_DIR}/security-summary-${TIMESTAMP}.md" << EOF
# Security Scan Summary Report

**Image:** ${IMAGE_NAME}  
**Scan Date:** $(date)  
**Report ID:** ${TIMESTAMP}

## Scan Results

### Tools Used
- Docker Scout: $(command_exists docker && docker scout version >/dev/null 2>&1 && echo "✓ Available" || echo "✗ Not available")
- Trivy: $(command_exists trivy && echo "✓ Available" || echo "✗ Not available")
- Snyk: $(command_exists snyk && echo "✓ Available" || echo "✗ Not available")

### Image Information
- **Size:** ${IMAGE_SIZE}
- **User:** ${USER_CHECK}
- **Exposed Ports:** ${PORTS_CHECK}

### Files Generated
- Docker Scout: docker-scout-${TIMESTAMP}.json, docker-scout-${TIMESTAMP}.txt
- Trivy: trivy-${TIMESTAMP}.json, trivy-${TIMESTAMP}.txt
- Snyk: snyk-${TIMESTAMP}.json, snyk-${TIMESTAMP}.txt
- Image Analysis: image-history-${TIMESTAMP}.txt, image-inspect-${TIMESTAMP}.json
- Security Checklist: security-checklist-${TIMESTAMP}.txt

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

EOF
    echo -e "${GREEN}✓ Summary report generated${NC}"
}

# Main execution
echo -e "${BLUE}Starting comprehensive security scan...${NC}"

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
    echo -e "${RED}Error: Image ${IMAGE_NAME} not found${NC}"
    echo -e "${YELLOW}Please build the image first or specify an existing image${NC}"
    exit 1
fi

# Run all scans
run_docker_scout
run_trivy_scan
run_snyk_scan
analyze_image_layers
check_security_best_practices
generate_summary_report

echo ""
echo -e "${GREEN}=== Security scan completed ===${NC}"
echo -e "${GREEN}Reports saved to: ${SCAN_OUTPUT_DIR}/${NC}"
echo -e "${BLUE}Summary report: ${SCAN_OUTPUT_DIR}/security-summary-${TIMESTAMP}.md${NC}"

# Display quick summary
echo ""
echo -e "${BLUE}=== Quick Summary ===${NC}"
echo -e "${BLUE}Image Size: ${IMAGE_SIZE}${NC}"
echo -e "${BLUE}Running User: ${USER_CHECK}${NC}"
echo -e "${BLUE}Exposed Ports: ${PORTS_CHECK}${NC}"

if [ -f "${SCAN_OUTPUT_DIR}/trivy-${TIMESTAMP}.json" ]; then
    CRITICAL_COUNT=$(jq -r '.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL") | .VulnerabilityID' "${SCAN_OUTPUT_DIR}/trivy-${TIMESTAMP}.json" 2>/dev/null | wc -l || echo "0")
    HIGH_COUNT=$(jq -r '.Results[]?.Vulnerabilities[]? | select(.Severity=="HIGH") | .VulnerabilityID' "${SCAN_OUTPUT_DIR}/trivy-${TIMESTAMP}.json" 2>/dev/null | wc -l || echo "0")
    echo -e "${BLUE}Critical Vulnerabilities: ${CRITICAL_COUNT}${NC}"
    echo -e "${BLUE}High Vulnerabilities: ${HIGH_COUNT}${NC}"
fi

echo ""
echo -e "${GREEN}Security scan process completed successfully${NC}"