# MCP Server - Docker Hub Repository

## Quick Start

```bash
# Pull the latest image
docker pull mcpserver/diagram-generator:latest

# Run with your API key
docker run -d \
  --name mcp-server \
  -e ANTHROPIC_API_KEY=your_api_key_here \
  -p 8000:8000 \
  mcpserver/diagram-generator:latest
```

## Available Tags

| Tag | Description | Size |
|-----|-------------|------|
| `latest` | Latest stable release | ~380MB |
| `v1.0.0` | Version 1.0.0 | ~380MB |
| `develop` | Development branch | ~385MB |
| `alpine` | Alpine-based minimal image | ~320MB |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Your Anthropic API key |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `TEMP_DIR` | No | `/app/temp` | Temporary files directory |
| `CACHE_TTL` | No | `3600` | Cache TTL in seconds |
| `MAX_CACHE_SIZE` | No | `100` | Maximum cache entries |

## Docker Compose Example

```yaml
version: '3.8'
services:
  mcp-server:
    image: mcpserver/diagram-generator:latest
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./temp:/app/temp
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    restart: unless-stopped
```

## Health Check

The container includes built-in health checks:

```bash
# Check container health
docker exec mcp-server python -c "import requests; print(requests.get('http://localhost:8000/health').status_code)"
```

## Volumes

- `/app/temp` - Temporary diagram files (auto-cleanup enabled)
- `/app/logs` - Application logs (optional)

## Supported Architectures

- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/AArch64)

## Usage with Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "diagram-generator": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ANTHROPIC_API_KEY=your_key_here",
        "mcpserver/diagram-generator:latest",
        "python", "-m", "src.server"
      ]
    }
  }
}
```

## Security

- Runs as non-root user
- Minimal attack surface
- No persistent sensitive data
- Automatic cleanup of temporary files

## Support

- **Documentation**: [GitHub Repository](https://github.com/your-org/mcp-server)
- **Issues**: [GitHub Issues](https://github.com/your-org/mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/mcp-server/discussions)

## License

MIT License - see [LICENSE](https://github.com/your-org/mcp-server/blob/main/LICENSE) file.