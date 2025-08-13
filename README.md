# AI Diagram Generator MCP Server

A Model Context Protocol (MCP) server that generates Draw.io diagrams from natural language descriptions using Claude AI. This server migrates the core functionality of an Express.js web application into a lightweight, containerized MCP server compatible with Claude Code and other MCP clients.

## Overview

This MCP server provides three main tools for diagram generation:
- **Generate Draw.io XML** from natural language prompts
- **Save diagrams** to temporary files with automatic cleanup
- **Convert Draw.io files to PNG images** using Draw.io CLI

The server is designed for seamless integration with Claude Code, providing instant diagram generation capabilities through natural language interaction.

## Features

### Core Functionality
- 🎨 **Natural Language to Diagram**: Convert descriptions into valid Draw.io XML
- 💾 **File Management**: Temporary file storage with automatic cleanup
- 🖼️ **Image Generation**: PNG export using Draw.io CLI
- 🔄 **Caching**: Intelligent response caching for improved performance
- 🛡️ **Error Handling**: Comprehensive error categorization and graceful degradation

### Architecture
- 🐍 **Python 3.10+**: Modern Python with async/await support
- 📦 **Containerized**: Docker-ready for easy deployment
- 🔧 **MCP Protocol**: Full compliance with Model Context Protocol specifications
- ⚡ **Performance**: Optimized for low latency and resource efficiency
- 🧪 **Tested**: Comprehensive test coverage (unit, integration, end-to-end)

## Quick Start

### Docker (Recommended)

1. **Build and run with Docker Compose:**
```bash
cd mcp-server
docker-compose up --build
```

2. **Set your API key:**
```bash
export ANTHROPIC_API_KEY=your-claude-api-key-here
```

### Manual Installation

1. **Prerequisites:**
```bash
# Python 3.10+
python --version

# Draw.io CLI (for PNG conversion)
npm install -g @drawio/drawio-desktop-cli
```

2. **Setup:**
```bash
cd mcp-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

4. **Run the server:**
```bash
python -m src.server
```

## MCP Tools

### 1. generate-drawio-xml
Generate Draw.io XML diagrams from natural language descriptions.

**Parameters:**
- `prompt` (string): Natural language description of the diagram

**Response:**
```json
{
  "success": true,
  "xml_content": "<mxfile>...</mxfile>",
  "error": null
}
```

### 2. save-drawio-file
Save XML content to temporary files with unique identifiers.

**Parameters:**
- `xml_content` (string): Valid Draw.io XML content
- `filename` (string, optional): Custom filename (UUID generated if not provided)

**Response:**
```json
{
  "success": true,
  "file_id": "uuid-string",
  "file_path": "/app/temp/uuid.drawio",
  "expires_at": "2024-01-01T12:00:00Z",
  "error": null
}
```

### 3. convert-to-png
Convert Draw.io files to PNG images using Draw.io CLI.

**Parameters:**
- `file_id` (string): File ID from save-drawio-file
- `file_path` (string, alternative): Direct file path

**Response:**
```json
{
  "success": true,
  "png_file_id": "uuid-string",
  "png_file_path": "/app/temp/uuid.png",
  "base64_content": "base64-encoded-image-data",
  "error": null
}
```

## Integration with Claude Code

### Setup in Claude Code

1. **Add MCP server configuration:**
```json
{
  "mcpServers": {
    "draw-aio-mcp": {
      "command": "docker",
      "args": ["run", "-it", "--rm", "-e", "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}", "draw-aio-mcp:latest"]
    }
  }
}
```

2. **Use in conversations:**
```
Create a flowchart showing the user authentication process with login, validation, and error handling steps.
```

Claude Code will automatically use the MCP server to generate and display the diagram.

## Development

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/container/     # Container tests
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

### Docker Development

```bash
# Build optimized image
docker build -f Dockerfile.optimized -t draw-aio-mcp:latest .

# Run with development settings
docker-compose -f docker-compose.dev.yml up

# Run tests in container
make test-container
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | - | Yes |
| `TEMP_DIR` | Temporary files directory | `./temp` | No |
| `DRAWIO_CLI_PATH` | Draw.io CLI executable path | `drawio` | No |
| `CACHE_TTL` | LLM response cache TTL (seconds) | `3600` | No |
| `MAX_CACHE_SIZE` | Maximum cache entries | `100` | No |
| `FILE_EXPIRY_HOURS` | Temporary file expiry | `24` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Container Resources

**Minimum Requirements:**
- Memory: 256MB
- CPU: 0.5 cores
- Storage: 1GB (for temporary files)

**Recommended:**
- Memory: 512MB
- CPU: 1 core
- Storage: 2GB

## Project Structure

```
mcp-server/
├── src/                           # Source code
│   ├── __init__.py
│   ├── server.py                  # Main MCP server implementation
│   ├── config.py                  # Configuration management
│   ├── tools.py                   # MCP tool implementations
│   ├── llm_service.py            # Claude AI integration
│   ├── file_service.py           # File management service
│   ├── image_service.py          # PNG generation service
│   ├── exceptions.py             # Custom exception classes
│   └── health.py                 # Health check endpoints
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── container/                # Container tests
│   └── fixtures/                 # Test data and utilities
├── docker/                       # Docker configuration
│   ├── Dockerfile                # Standard Dockerfile
│   ├── Dockerfile.optimized      # Production-optimized image
│   └── docker-compose.*.yml      # Various deployment configs
├── docs/                         # Documentation
│   ├── API_DOCUMENTATION.md      # Detailed API reference
│   ├── DEVELOPER_GUIDE.md        # Development guidelines
│   └── INSTALLATION_GUIDE.md     # Setup instructions
├── deploy/                       # Deployment scripts
├── monitoring/                   # Monitoring configuration
├── pyproject.toml               # Project configuration
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── Makefile                     # Build automation
└── README.md                    # This file
```

## Deployment

### Production Deployment

```bash
# Build production image
make build-production

# Deploy with resource limits
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl http://localhost:8000/health
```

### Scaling

The server is stateless and supports horizontal scaling:

```yaml
# docker-compose.prod.yml
services:
  mcp-server:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
```

## Troubleshooting

### Common Issues

1. **Draw.io CLI not found:**
   ```bash
   npm install -g @drawio/drawio-desktop-cli
   ```

2. **API key issues:**
   ```bash
   # Verify key format
   echo $ANTHROPIC_API_KEY | grep "^sk-ant-"
   ```

3. **Container memory issues:**
   ```bash
   # Increase container memory
   docker run -m 1g draw-aio-mcp:latest
   ```

### Health Checks

The server provides comprehensive health monitoring:

- **GET /health** - Basic health status
- **GET /health/ready** - Readiness check (all services initialized)
- **GET /health/live** - Liveness check (server responsive)

### Logs

```bash
# View server logs
docker logs mcp-server

# Follow logs in real-time
docker logs -f mcp-server

# Filter error logs
docker logs mcp-server 2>&1 | grep ERROR
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add comprehensive tests for new features
- Update documentation for API changes
- Use type hints for all functions
- Ensure Docker builds pass

## Migration from Express.js

This MCP server migrates core functionality from the original Express.js web application:

### Migrated Components
- ✅ **LLMService**: Claude AI integration with caching
- ✅ **FileService**: Temporary file management with cleanup
- ✅ **ImageService**: Draw.io CLI integration for PNG generation
- ✅ **Error Handling**: Comprehensive error categorization
- ✅ **Performance**: Response caching and resource management

### New Features
- 🆕 **MCP Protocol**: Full compliance with Model Context Protocol
- 🆕 **Container Ready**: Optimized Docker deployment
- 🆕 **Claude Code Integration**: Seamless integration with Claude Code
- 🆕 **Enhanced Monitoring**: Health checks and observability

## License

This project is dual-licensed:

### Personal and Non-Commercial Use
For personal, educational, research, and non-commercial use, this software is licensed under the **MIT License**. See [LICENSE-MIT](LICENSE-MIT) for details.

### Commercial Use  
Commercial use requires a separate **Commercial License**. Commercial use includes:
- Use by for-profit organizations with annual revenue over $10,000 USD
- Integration into commercial products or services
- Commercial cloud service deployment
- Revenue-generating consulting services

**Commercial License Benefits:**
- ✅ Commercial usage rights
- ✅ Priority technical support  
- ✅ Software updates and patches
- ✅ Customization options
- ✅ Legal compliance assurance

**To obtain a commercial license:**
- 📧 Contact: [your-email@domain.com]
- 📄 See: [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL) for detailed terms
- 🤝 Custom licensing agreements available

**License Overview:** [LICENSE](LICENSE) | **MIT Terms:** [LICENSE-MIT](LICENSE-MIT) | **Commercial Terms:** [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL)

## Documentation Files

This repository contains comprehensive documentation in Markdown format:

### Root Documentation
- [README.md](README.md) - Main project documentation (English)
- [README_ja.md](README_ja.md) - Main project documentation (Japanese)
- [CLAUDE.md](CLAUDE.md) - Claude Code integration guidance

### MCP Server Documentation
- [mcp-server/DEPLOYMENT.md](mcp-server/DEPLOYMENT.md) - Deployment guide (English/Japanese)
- [mcp-server/MCP_MIGRATION_SUMMARY.md](mcp-server/MCP_MIGRATION_SUMMARY.md) - Migration summary (English/Japanese)

#### Core Documentation (`mcp-server/docs/`)
- [API_DOCUMENTATION.md](mcp-server/docs/API_DOCUMENTATION.md) - Complete API reference (English/Japanese)
- [DEVELOPER_GUIDE.md](mcp-server/docs/DEVELOPER_GUIDE.md) - Development guidelines (English/Japanese)
- [INSTALLATION_GUIDE.md](mcp-server/docs/INSTALLATION_GUIDE.md) - Installation instructions (English/Japanese)
- [MCP_SERVER_USAGE_GUIDE.md](mcp-server/docs/MCP_SERVER_USAGE_GUIDE.md) - Usage guide (English/Japanese)
- [README.md](mcp-server/docs/README.md) - Documentation overview (English/Japanese)

#### Integration & Testing (`mcp-server/docs/`)
- [CLAUDE_CODE_INTEGRATION.md](mcp-server/docs/CLAUDE_CODE_INTEGRATION.md) - Claude Code integration (English/Japanese)
- [MCP_CLIENT_INTEGRATION_TESTING.md](mcp-server/docs/MCP_CLIENT_INTEGRATION_TESTING.md) - Integration testing (English/Japanese)

#### Technical Documentation (`mcp-server/docs/`)
- [API_KEY_VALIDATION.md](mcp-server/docs/API_KEY_VALIDATION.md) - API key validation (English/Japanese)
- [DEPENDENCY_CHECKING.md](mcp-server/docs/DEPENDENCY_CHECKING.md) - Dependency checking (English/Japanese)
- [PROTOCOL_VERSION_VALIDATION.md](mcp-server/docs/PROTOCOL_VERSION_VALIDATION.md) - Protocol validation (English/Japanese)
- [STANDARD_MCP_PATTERNS.md](mcp-server/docs/STANDARD_MCP_PATTERNS.md) - MCP patterns (English/Japanese)

### Test Documentation
- [mcp-server/tests/INTEGRATION_TEST_SUMMARY.md](mcp-server/tests/INTEGRATION_TEST_SUMMARY.md) - Integration test summary (English/Japanese)
- [mcp-server/tests/UNIT_TEST_SUMMARY.md](mcp-server/tests/UNIT_TEST_SUMMARY.md) - Unit test summary (English/Japanese)
- [mcp-server/tests/container/TASK_17_COMPLETION_SUMMARY.md](mcp-server/tests/container/TASK_17_COMPLETION_SUMMARY.md) - Container test completion

### Source Documentation
- [mcp-server/src/README_TOOL.md](mcp-server/src/README_TOOL.md) - Tool implementation guide (English/Japanese)

### Infrastructure & Examples
- [mcp-server/infrastructure/examples/sample-project/README.md](mcp-server/infrastructure/examples/sample-project/README.md) - Sample project
- [mcp-server/.pytest_cache/README.md](mcp-server/.pytest_cache/README.md) - Pytest cache information

### Performance & Reports
- [mcp-server/reports/benchmarks/performance-results.md](mcp-server/reports/benchmarks/performance-results.md) - Performance benchmarks

### Project Specifications
- [.kiro/specs/mcp-server-migration/design.md](.kiro/specs/mcp-server-migration/design.md) - Migration design
- [.kiro/specs/mcp-server-migration/requirements.md](.kiro/specs/mcp-server-migration/requirements.md) - Requirements specification
- [.kiro/specs/mcp-server-migration/tasks.md](.kiro/specs/mcp-server-migration/tasks.md) - Task breakdown

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/draw-aio-mcp/issues)
- **Documentation**: [docs/](docs/)
- **API Reference**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)