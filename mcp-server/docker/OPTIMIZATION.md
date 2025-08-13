# Container Optimization and Security Guide

This document describes the optimization and security features implemented in the MCP Draw.io Server Docker container.

## 🎯 Optimization Features

### Image Size Reduction

The container implements several strategies to minimize image size:

#### Multi-stage Build
- **Build stage**: Contains all build dependencies (gcc, musl-dev, etc.)
- **Runtime stage**: Contains only runtime dependencies
- Build dependencies are completely removed from the final image

#### Package Management Optimization
```dockerfile
# Install only essential build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc musl-dev libffi-dev openssl-dev python3-dev build-base

# Remove build dependencies after use
RUN apk del .build-deps
```

#### Cache Cleanup
- Python pip cache is purged after installation
- npm cache is cleaned after Draw.io CLI installation
- APK cache is removed with `--no-cache` flag
- Temporary files are cleaned up

#### Python Optimization
```dockerfile
# Remove Python bytecode and cache files
RUN find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "__pycache__" -type d -exec rm -rf {} + || true
```

#### Layer Optimization
- Commands are combined to reduce layer count
- Dependencies are copied before source code for better caching
- `.dockerignore` file excludes unnecessary files from build context

### Expected Image Size
- **Target**: < 500MB (as per requirement 4.1)
- **Typical size**: 200-350MB depending on dependencies

## 🔒 Security Features

### Non-root User Execution

The container runs as a non-privileged user for security:

```dockerfile
# Create non-root user with minimal privileges
RUN addgroup -g 1001 -S mcpuser && \
    adduser -S mcpuser -u 1001 -G mcpuser -s /bin/sh -h /home/mcpuser

# Switch to non-root user
USER mcpuser
```

### File System Permissions

Proper file permissions are set throughout the container:

```dockerfile
# Set proper permissions for application directories
RUN mkdir -p /app/temp /app/logs /home/mcpuser/.cache && \
    chown -R mcpuser:mcpuser /app /home/mcpuser && \
    chmod 755 /app && \
    chmod 750 /app/temp /app/logs && \
    chmod 700 /home/mcpuser/.cache
```

### Security Environment Variables

```dockerfile
ENV PYTHONSAFEPATH=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

### Process Management

- **dumb-init**: Proper signal handling and zombie process reaping
- **Non-privileged port**: Uses port 8000 (non-privileged)
- **Read-only filesystem**: Can be enabled for additional security

## 🏥 Health Check Implementation

### Comprehensive Health Monitoring

The container includes a sophisticated health check system:

#### Health Check Script
- **Location**: `/app/src/healthcheck.py`
- **Timeout**: 15 seconds
- **Interval**: 30 seconds
- **Start period**: 10 seconds
- **Retries**: 3

#### Health Check Categories

1. **Basic Functionality**
   - Python module imports
   - JSON processing
   - File system access

2. **Configuration Validation**
   - API key presence and format
   - Directory configuration
   - Cache settings validation

3. **File System Health**
   - Temp directory accessibility
   - Write/read permissions
   - Disk space availability

4. **Python Environment**
   - Python version check (>= 3.10)
   - Required module availability
   - Virtual environment validation

5. **Draw.io CLI Status**
   - CLI executable availability
   - Version information
   - Responsiveness test

6. **Server Process Health**
   - Module import capability
   - Service initialization
   - Basic component functionality

#### Health Status Levels

- **Healthy**: All checks pass
- **Degraded**: Non-critical issues (e.g., Draw.io CLI unavailable)
- **Unhealthy**: Critical failures that prevent operation
- **Unknown**: Unable to determine status

### Health Check Usage

```bash
# Manual health check
docker exec <container> python /app/src/healthcheck.py

# Verbose output
docker exec -e HEALTHCHECK_VERBOSE=true <container> python /app/src/healthcheck.py

# Check Docker health status
docker inspect --format='{{.State.Health.Status}}' <container>
```

## 🧪 Validation and Testing

### Optimization Validation Script

Use the provided validation script to verify optimization and security:

```bash
# Linux/macOS
./docker/validate-optimization.sh

# Windows PowerShell
.\docker\validate-optimization.ps1

# With custom image name
./docker/validate-optimization.sh my-custom-image
```

### Validation Checks

The validation script performs the following checks:

1. **Image Size Validation**
   - Verifies image size < 500MB
   - Reports actual size in MB

2. **Layer Optimization**
   - Counts image layers
   - Checks for optimization indicators
   - Validates multi-stage build usage

3. **Security Settings**
   - Non-root user configuration
   - Proper entrypoint setup
   - Security environment variables
   - Working directory validation

4. **Health Check Functionality**
   - Starts test container
   - Waits for health check initialization
   - Validates health status
   - Captures health check logs

5. **Runtime Behavior**
   - Container startup success
   - Resource usage monitoring
   - Error log analysis

## 📊 Performance Characteristics

### Resource Requirements

- **Memory**: 
  - Minimum: 256MB
  - Recommended: 512MB
  - Typical usage: 100-200MB

- **CPU**: 
  - Minimum: 0.5 cores
  - Recommended: 1 core
  - Typical usage: 5-15% during idle

- **Storage**: 
  - Container size: 200-350MB
  - Temp files: Up to 1GB (configurable)
  - Logs: Minimal (stdout/stderr only)

### Startup Performance

- **Cold start**: 5-10 seconds
- **Health check ready**: 10-15 seconds
- **Full initialization**: 15-20 seconds

## 🔧 Configuration Options

### Environment Variables

```bash
# Security and optimization related
PYTHONSAFEPATH=1                    # Enable Python safe path
PYTHONHASHSEED=random              # Randomize hash seed
HEALTHCHECK_VERBOSE=false          # Verbose health check output

# Resource limits (Docker run options)
--memory=512m                      # Memory limit
--cpus=1.0                        # CPU limit
--read-only                       # Read-only filesystem
--tmpfs /app/temp:rw,size=1g      # Writable temp directory
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  mcp-server:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - PYTHONSAFEPATH=1
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /app/temp:rw,size=1g
      - /tmp:rw,size=100m
    healthcheck:
      test: ["CMD", "python", "/app/src/healthcheck.py"]
      interval: 30s
      timeout: 15s
      retries: 3
      start_period: 10s
```

## 🚀 Best Practices

### Deployment Recommendations

1. **Resource Limits**: Always set memory and CPU limits
2. **Health Checks**: Enable health checks in production
3. **Read-only Filesystem**: Use read-only filesystem when possible
4. **Security Context**: Run with security options enabled
5. **Monitoring**: Monitor health check status and resource usage

### Security Hardening

1. **Network Policies**: Restrict network access to required endpoints only
2. **Secrets Management**: Use Docker secrets or external secret management
3. **Image Scanning**: Regularly scan images for vulnerabilities
4. **Updates**: Keep base images and dependencies updated

### Performance Optimization

1. **Resource Allocation**: Right-size memory and CPU based on usage
2. **Caching**: Utilize Docker layer caching for faster builds
3. **Multi-stage Builds**: Keep using multi-stage builds for size optimization
4. **Health Check Tuning**: Adjust health check intervals based on requirements

## 🐛 Troubleshooting

### Common Issues

1. **Health Check Failures**
   ```bash
   # Check health check logs
   docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' <container>
   
   # Run health check manually
   docker exec <container> python /app/src/healthcheck.py
   ```

2. **Permission Issues**
   ```bash
   # Check file permissions
   docker exec <container> ls -la /app/temp
   
   # Check user context
   docker exec <container> whoami
   ```

3. **Size Issues**
   ```bash
   # Analyze image layers
   docker history <image>
   
   # Check for large files
   docker run --rm <image> du -sh /*
   ```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
docker run -e DEBUG=true -e HEALTHCHECK_VERBOSE=true <image>
```

## 📈 Monitoring and Metrics

### Health Metrics

The health check system provides detailed metrics:

- Response times for each check
- Success/failure rates
- Resource usage information
- Dependency status

### Logging

- Structured logging available (JSON format)
- Health check events logged
- Security events logged
- Performance metrics logged

### Integration

The health check system integrates with:

- Docker health checks
- Kubernetes liveness/readiness probes
- Monitoring systems (Prometheus, etc.)
- Alerting systems

## 🔄 Maintenance

### Regular Tasks

1. **Image Updates**: Rebuild images monthly or when dependencies update
2. **Security Scans**: Run security scans on images before deployment
3. **Performance Review**: Monitor resource usage and optimize as needed
4. **Health Check Tuning**: Adjust health check parameters based on performance

### Upgrade Path

When upgrading the container:

1. Test new image with validation script
2. Verify health checks pass
3. Check resource usage hasn't increased significantly
4. Validate security settings remain intact
5. Deploy with rolling update strategy