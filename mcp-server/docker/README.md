# Docker Configuration for MCP Draw.io Server

This directory contains Docker configuration files for building and running the MCP Draw.io Server in containerized environments.

## Quick Start

### Prerequisites

- Docker 20.10+ with BuildKit support
- Docker Compose 2.0+ (optional, for orchestration)
- Anthropic API key

### Build and Run

1. **Build the Docker image:**
   ```bash
   # Using PowerShell script (Windows)
   .\build.ps1
   
   # Using bash script (Linux/macOS)
   ./build.sh
   
   # Manual build
   docker build -f ../Dockerfile -t mcp-drawio-server:latest ..
   ```

2. **Run the container:**
   ```bash
   docker run --rm -e ANTHROPIC_API_KEY=your_key_here mcp-drawio-server:latest
   ```

3. **Using Docker Compose:**
   ```bash
   # Copy environment template
   cp .env.docker .env
   # Edit .env with your API key
   
   # Run with Docker Compose
   docker-compose up
   ```

## Image Details

### Multi-Stage Build

The Dockerfile uses a multi-stage build approach for optimization:

1. **Builder Stage** (`python:3.10-alpine`):
   - Installs build dependencies
   - Creates Python virtual environment
   - Installs Python packages

2. **Runtime Stage** (`node:18-alpine`):
   - Minimal runtime environment
   - Installs Draw.io CLI via npm
   - Copies Python virtual environment
   - Runs as non-root user

### Image Specifications

- **Base Images**: `python:3.10-alpine` (builder), `node:18-alpine` (runtime)
- **Target Size**: < 500MB
- **User**: Non-root (`mcpuser`, UID 1001)
- **Working Directory**: `/app`
- **Exposed Port**: 8000 (for health checks)
- **Entry Point**: `tini` for proper signal handling

### Installed Components

- **Python 3.10**: Runtime environment
- **Draw.io CLI**: `@drawio/drawio-desktop-cli` via npm
- **Python Packages**: As specified in `requirements.txt`
- **System Tools**: `tini`, `ca-certificates`, `tzdata`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *required* | Anthropic API key for Claude access |
| `TEMP_DIR` | `/app/temp` | Temporary files directory |
| `DRAWIO_CLI_PATH` | `drawio` | Path to Draw.io CLI executable |
| `CACHE_TTL` | `3600` | Cache time-to-live in seconds |
| `MAX_CACHE_SIZE` | `100` | Maximum cache entries |
| `FILE_EXPIRY_HOURS` | `24` | File expiration time in hours |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REQUEST_TIMEOUT` | `300` | Request timeout in seconds |

### Volume Mounts

- `/app/temp`: Temporary file storage
- `/app/logs`: Application logs (optional)

### Health Checks

The container includes comprehensive health checks:

- **Liveness**: Basic server responsiveness
- **Readiness**: All services initialized
- **Dependencies**: Claude API and Draw.io CLI availability

## Usage Examples

### Basic Usage

```bash
# Run with minimal configuration
docker run --rm \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  mcp-drawio-server:latest
```

### Development Mode

```bash
# Run with debug logging and volume mounts
docker run --rm \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e LOG_LEVEL=DEBUG \
  -v "$(pwd)/temp:/app/temp" \
  -v "$(pwd)/logs:/app/logs" \
  mcp-drawio-server:latest
```

### Production Deployment

```bash
# Run with resource limits and restart policy
docker run -d \
  --name mcp-drawio-server \
  --restart unless-stopped \
  --memory 512m \
  --cpus 1.0 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e LOG_LEVEL=WARNING \
  -v mcp_temp:/app/temp \
  mcp-drawio-server:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  mcp-server:
    image: mcp-drawio-server:latest
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - temp_data:/app/temp
    restart: unless-stopped

volumes:
  temp_data:
```

## Build Scripts

### PowerShell Script (`build.ps1`)

Windows-compatible build script with features:
- Automatic Docker detection
- BuildKit optimization
- Image size reporting
- Usage instructions
- Error handling

```powershell
# Build with custom tag
.\build.ps1 -ImageTag "v1.0.0"

# Build with verbose output
.\build.ps1 -Verbose

# Build without BuildKit
.\build.ps1 -NoBuildKit
```

### Bash Script (`build.sh`)

Linux/macOS build script with features:
- Cross-platform support
- Colored output
- Image analysis suggestions
- Build optimization

```bash
# Build with custom tag
./build.sh v1.0.0

# Build latest
./build.sh
```

## Optimization Features

### Size Optimization

- Multi-stage build reduces final image size
- Alpine Linux base images
- Minimal runtime dependencies
- Layer caching optimization
- `.dockerignore` excludes unnecessary files

### Security Features

- Non-root user execution
- Read-only root filesystem (with exceptions)
- No new privileges
- Minimal attack surface
- Security labels

### Performance Features

- BuildKit support for faster builds
- Layer caching for dependencies
- Optimized layer ordering
- Parallel build stages

## Troubleshooting

### Common Issues

1. **Build Failures**:
   - Ensure Docker BuildKit is enabled
   - Check network connectivity for package downloads
   - Verify Dockerfile path and build context

2. **Runtime Issues**:
   - Verify ANTHROPIC_API_KEY is set
   - Check Draw.io CLI installation with health check
   - Monitor container logs for errors

3. **Permission Issues**:
   - Ensure volume mount permissions
   - Check non-root user access to mounted directories

### Debug Commands

```bash
# Check image layers
docker history mcp-drawio-server:latest

# Inspect image configuration
docker inspect mcp-drawio-server:latest

# Run interactive shell
docker run --rm -it --entrypoint /bin/sh mcp-drawio-server:latest

# Check health status
docker exec <container_id> python -c "import sys; sys.path.append('/app/src'); from health import HealthChecker; import asyncio; print(asyncio.run(HealthChecker().get_liveness()))"
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats mcp-drawio-server

# Check container logs
docker logs -f mcp-drawio-server

# Export container metrics
docker exec mcp-drawio-server python -c "import sys; sys.path.append('/app/src'); from health import HealthChecker; import asyncio; print(asyncio.run(HealthChecker().check_all()))"
```

## Production Considerations

### Resource Requirements

- **Memory**: 256MB minimum, 512MB recommended
- **CPU**: 0.5 cores minimum, 1.0 core recommended
- **Storage**: 1GB for temporary files and cache
- **Network**: Outbound HTTPS for Claude API

### Scaling

- Stateless design supports horizontal scaling
- Use load balancer for multiple instances
- Consider shared storage for temporary files
- Monitor API rate limits across instances

### Monitoring

- Health check endpoints for load balancer integration
- Structured logging for centralized log management
- Metrics export for monitoring systems
- Alert on health check failures

### Security

- Use Docker secrets for API keys in production
- Regular security updates for base images
- Network isolation with Docker networks
- Container scanning for vulnerabilities