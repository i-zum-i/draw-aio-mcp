# MCP Draw.io Server Usage Guide

## Overview

The MCP Draw.io Server is a Model Context Protocol (MCP) server that enables natural language diagram generation using Draw.io. It provides three main tools for diagram creation, saving, and image conversion.

---

# MCP Draw.io サーバー 使用ガイド

## 概要

MCP Draw.io サーバーは、Draw.ioを使用した自然言語による図表生成を可能にするModel Context Protocol（MCP）サーバーです。図表の作成、保存、画像変換のための3つの主要ツールを提供します。

## 目次

- [インストール](#インストール)
- [設定](#設定)
- [Claude Code統合](#claude-code統合)
- [利用可能なツール](#利用可能なツール)
- [使用例](#使用例)
- [トラブルシューティング](#トラブルシューティング)
- [高度な設定](#高度な設定)

## インストール

### 前提条件

- DockerとDocker Compose
- Anthropic APIキー
- Claude Code（MCP統合用）

### Dockerでのクイックスタート

1. **MCPサーバーファイルをクローンまたはダウンロード**
   ```bash
   git clone <repository-url>
   cd mcp-server
   ```

2. **環境変数の設定**
   ```bash
   cp .env.example .env
   # .envを編集してAnthropic APIキーを追加
   ```

3. **サーバーのビルドと起動**
   ```bash
   # 開発用
   docker-compose -f docker-compose.dev.yml up --build
   
   # 本番用
   docker-compose -f docker-compose.prod.yml up --build
   ```

### Manual Installation

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Draw.io CLI**
   ```bash
   npm install -g @drawio/drawio-desktop-cli
   ```

3. **Set environment variables**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

4. **Run the server**
   ```bash
   python -m src.server
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | - | Yes |
| `TEMP_DIR` | Directory for temporary files | `/app/temp` | No |
| `DRAWIO_CLI_PATH` | Path to Draw.io CLI | `drawio` | No |
| `CACHE_TTL` | Cache time-to-live in seconds | `3600` | No |
| `MAX_CACHE_SIZE` | Maximum cache entries | `100` | No |
| `FILE_EXPIRY_HOURS` | Hours before temp files expire | `24` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Configuration Files

#### Development (.env.dev)
```bash
ANTHROPIC_API_KEY=your-api-key
LOG_LEVEL=DEBUG
CACHE_TTL=300
FILE_EXPIRY_HOURS=1
```

#### Production (.env.prod)
```bash
ANTHROPIC_API_KEY=your-api-key
LOG_LEVEL=WARNING
CACHE_TTL=7200
FILE_EXPIRY_HOURS=48
```

## Claude Code Integration

### Adding the MCP Server

1. **Open Claude Code settings**
   - Go to Settings → MCP Servers

2. **Add new server configuration**
   ```json
   {
     "mcpServers": {
       "drawio-server": {
         "command": "docker",
         "args": [
           "run", "--rm", "-i",
           "--env-file", "/path/to/your/.env",
           "mcp-drawio-server:latest"
         ],
         "env": {
           "ANTHROPIC_API_KEY": "your-api-key-here"
         }
       }
     }
   }
   ```

3. **Alternative: Local installation**
   ```json
   {
     "mcpServers": {
       "drawio-server": {
         "command": "python",
         "args": ["-m", "src.server"],
         "cwd": "/path/to/mcp-server",
         "env": {
           "ANTHROPIC_API_KEY": "your-api-key-here"
         }
       }
     }
   }
   ```

### Verification

After adding the server, you should see three new tools available in Claude Code:
- `generate-drawio-xml`
- `save-drawio-file`
- `convert-to-png`

## Available Tools

### 1. generate-drawio-xml

Generates Draw.io XML from natural language descriptions.

**Parameters:**
- `prompt` (string): Natural language description of the diagram

**Returns:**
```json
{
  "success": true,
  "xml_content": "<mxfile>...</mxfile>",
  "error": null
}
```

### 2. save-drawio-file

Saves Draw.io XML content to a temporary file.

**Parameters:**
- `xml_content` (string): Valid Draw.io XML content
- `filename` (string, optional): Custom filename

**Returns:**
```json
{
  "success": true,
  "file_id": "uuid-string",
  "file_path": "/app/temp/diagram.drawio",
  "expires_at": "2024-01-02T00:00:00Z",
  "error": null
}
```

### 3. convert-to-png

Converts a Draw.io file to PNG image.

**Parameters:**
- `file_id` (string): File ID from save-drawio-file
- `file_path` (string, alternative): Direct file path

**Returns:**
```json
{
  "success": true,
  "png_file_id": "uuid-string",
  "png_file_path": "/app/temp/diagram.png",
  "base64_content": "base64-encoded-image",
  "error": null
}
```

## Usage Examples

### Basic Workflow

1. **Generate a diagram**
   ```
   User: Create a flowchart showing the user registration process
   
   Claude: I'll create a flowchart for the user registration process.
   
   [Uses generate-drawio-xml tool]
   ```

2. **Save the diagram**
   ```
   Claude: I'll save this diagram for you.
   
   [Uses save-drawio-file tool with the generated XML]
   ```

3. **Convert to image**
   ```
   User: Can you convert this to a PNG image?
   
   Claude: I'll convert the diagram to a PNG image.
   
   [Uses convert-to-png tool with the file ID]
   ```

### Advanced Examples

#### AWS Architecture Diagram
```
User: Create an AWS architecture diagram showing:
- Application Load Balancer
- EC2 instances in multiple AZs
- RDS database with read replica
- S3 bucket for static assets
- CloudFront distribution

Claude: I'll create an AWS architecture diagram with those components.
[Generates diagram with AWS-specific styling and best practices]
```

#### Database Schema
```
User: Create a database schema diagram for an e-commerce system with:
- Users table
- Products table
- Orders table
- Order items table
- Show relationships between tables

Claude: I'll create a database schema diagram for your e-commerce system.
[Generates ER diagram with proper relationships]
```

#### Process Flow
```
User: Create a process flow diagram for our CI/CD pipeline:
1. Code commit
2. Build and test
3. Security scan
4. Deploy to staging
5. Run integration tests
6. Deploy to production

Claude: I'll create a CI/CD pipeline flow diagram.
[Generates process flow with decision points and parallel processes]
```

## Troubleshooting

### Common Issues

#### 1. "Draw.io CLI not available"
**Problem:** PNG conversion fails with CLI not available error.

**Solutions:**
- Ensure Draw.io CLI is installed: `npm install -g @drawio/drawio-desktop-cli`
- Check CLI path: `which drawio`
- Verify container includes Draw.io CLI (if using Docker)

#### 2. "Invalid API key"
**Problem:** XML generation fails with authentication error.

**Solutions:**
- Verify your Anthropic API key is correct
- Check environment variable is set: `echo $ANTHROPIC_API_KEY`
- Ensure API key has sufficient credits

#### 3. "File not found"
**Problem:** PNG conversion fails with file not found error.

**Solutions:**
- Ensure file was saved successfully first
- Check file hasn't expired (default: 24 hours)
- Verify temp directory permissions

#### 4. "Container startup fails"
**Problem:** Docker container doesn't start properly.

**Solutions:**
- Check Docker logs: `docker logs mcp-drawio-server`
- Verify environment variables are set
- Ensure ports aren't already in use

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Environment variable
export LOG_LEVEL=DEBUG

# Or in .env file
LOG_LEVEL=DEBUG
```

### Health Checks

Check server health:

```bash
# Docker container
docker exec mcp-drawio-server python /app/src/healthcheck.py

# Local installation
python src/healthcheck.py
```

## Advanced Configuration

### Custom System Prompts

The server uses specialized system prompts for different diagram types. You can customize these by modifying the `LLMService` class.

### Caching Configuration

Optimize performance with caching settings:

```bash
# Cache for 2 hours
CACHE_TTL=7200

# Store up to 200 entries
MAX_CACHE_SIZE=200
```

### File Management

Configure temporary file handling:

```bash
# Files expire after 48 hours
FILE_EXPIRY_HOURS=48

# Clean up every 30 minutes
CLEANUP_INTERVAL_MINUTES=30
```

### Resource Limits

For production deployments, configure resource limits in docker-compose.prod.yml:

```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '2.0'
    reservations:
      memory: 512M
      cpus: '1.0'
```

### Security Considerations

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables or secure secret management
   - Rotate API keys regularly

2. **Network Security**
   - Run containers with minimal network access
   - Use firewalls to restrict access
   - Consider VPN for remote access

3. **File System Security**
   - Temporary files are automatically cleaned up
   - Container runs as non-root user
   - Read-only root filesystem in production

### Monitoring and Logging

#### Log Aggregation
Configure log aggregation with Fluent Bit (included in production setup):

```yaml
# Enable monitoring profile
docker-compose -f docker-compose.prod.yml --profile monitoring up
```

#### Health Monitoring
The server includes comprehensive health checks:
- Liveness: Basic server responsiveness
- Readiness: All services initialized
- Dependencies: Claude API and Draw.io CLI availability

### Performance Optimization

1. **Caching Strategy**
   - Enable caching for repeated requests
   - Adjust cache size based on memory availability
   - Monitor cache hit rates

2. **Resource Management**
   - Set appropriate memory limits
   - Configure CPU limits for consistent performance
   - Monitor disk usage for temporary files

3. **Scaling**
   - Run multiple container instances
   - Use load balancer for distribution
   - Consider horizontal pod autoscaling in Kubernetes

## Support and Contributing

### Getting Help

1. Check the troubleshooting section above
2. Review container logs for error messages
3. Verify configuration and environment variables
4. Test with minimal examples

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Reporting Issues

When reporting issues, please include:
- Server version and configuration
- Error messages and logs
- Steps to reproduce
- Expected vs actual behavior

## License

This project is licensed under the MIT License. See LICENSE file for details.