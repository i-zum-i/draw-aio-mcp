# Claude Code 統合ガイド

## 概要

このガイドでは、MCP Draw.io サーバーをClaude Codeと統合するための詳細な手順を提供します。設定、使用パターン、トラブルシューティングを含みます。

## 目次

- [前提条件](#前提条件)
- [設定方法](#設定方法)
- [使用パターン](#使用パターン)
- [高度な機能](#高度な機能)
- [トラブルシューティング](#トラブルシューティング)
- [ベストプラクティス](#ベストプラクティス)

## 前提条件

### 必要なソフトウェア

1. **Claude Code** - MCP対応の最新版
2. **MCP Draw.io サーバー** - インストール済みで実行中（[インストールガイド](INSTALLATION_GUIDE.md)参照）
3. **Anthropic APIキー** - 十分なクレジットを持つ有効なAPIキー

### 検証手順

Claude Codeを設定する前に、MCPサーバーが動作していることを確認：

```bash
# サーバーステータス確認
docker ps | grep mcp-drawio-server

# ヘルスチェックテスト
docker exec mcp-drawio-server python /app/src/healthcheck.py

# Draw.io CLI確認
docker exec mcp-drawio-server drawio --version
```

## 設定方法

### 方法1: MCP設定UI（推奨）

1. **Claude Codeを開く**
2. **MCP設定にアクセス**:
   - `設定` → `拡張機能` → `MCPサーバー`に移動
   - またはコマンドパレット: `Ctrl+Shift+P` → "MCP: Configure Servers"

3. **新しいサーバーを追加**:
   - "サーバーを追加"をクリック
   - 設定詳細を入力（以下の設定を参照）

4. **Test Connection**:
   - Click "Test Connection"
   - Verify all three tools are available

### Method 2: Configuration File

#### Workspace Configuration

Create `.kiro/settings/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "drawio-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/absolute/path/to/mcp-server/.env",
        "-v", "/absolute/path/to/mcp-server/temp:/app/temp:rw",
        "-v", "/absolute/path/to/mcp-server/logs:/app/logs:rw",
        "mcp-drawio-server:latest"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      },
      "disabled": false,
      "autoApprove": [
        "generate-drawio-xml",
        "save-drawio-file",
        "convert-to-png"
      ]
    }
  }
}
```

#### Global Configuration

Create `~/.kiro/settings/mcp.json` for global access:

```json
{
  "mcpServers": {
    "drawio-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/home/user/mcp-server/.env",
        "-v", "/home/user/mcp-server/temp:/app/temp:rw",
        "mcp-drawio-server:latest"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Configuration Examples

### Docker Compose Integration

```json
{
  "mcpServers": {
    "drawio-server": {
      "command": "docker-compose",
      "args": [
        "-f", "/absolute/path/to/mcp-server/docker-compose.yml",
        "exec", "-T", "mcp-server",
        "python", "-m", "src.server"
      ],
      "cwd": "/absolute/path/to/mcp-server",
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Development Configuration

```json
{
  "mcpServers": {
    "drawio-server-dev": {
      "command": "docker-compose",
      "args": [
        "-f", "/absolute/path/to/mcp-server/docker-compose.dev.yml",
        "exec", "-T", "mcp-server-dev",
        "python", "-m", "src.server"
      ],
      "cwd": "/absolute/path/to/mcp-server",
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Local Python Installation

```json
{
  "mcpServers": {
    "drawio-server": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/mcp-server",
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here",
        "PYTHONPATH": "/absolute/path/to/mcp-server/src"
      }
    }
  }
}
```

## Usage Patterns

### Basic Diagram Creation

#### Simple Flowchart

```
User: Create a flowchart for user login process

Claude: I'll create a flowchart for the user login process.

[Claude uses generate-drawio-xml tool]

The flowchart shows:
1. Start
2. Enter credentials
3. Validate credentials (decision)
4. If valid: Login success
5. If invalid: Show error, return to enter credentials
6. End

Would you like me to save this diagram or convert it to an image?
```

#### AWS Architecture Diagram

```
User: Create an AWS architecture diagram for a web application with:
- ALB (Application Load Balancer)
- EC2 instances in 2 AZs
- RDS MySQL database
- S3 bucket
- CloudFront

Claude: I'll create an AWS architecture diagram with those components.

[Claude uses generate-drawio-xml with AWS-specific styling]

The diagram shows a typical 3-tier architecture with proper AWS icons and connections. Would you like me to save this as a file?
```

### Advanced Workflows

#### Complete Diagram Workflow

```
User: Create a database schema for an e-commerce system, save it, and convert to PNG

Claude: I'll create a complete e-commerce database schema and provide you with both the diagram file and PNG image.

[Step 1: Generate XML]
[Step 2: Save to file]
[Step 3: Convert to PNG]

Here's your complete e-commerce database schema:
- Saved as: ecommerce-schema.drawio (File ID: abc123...)
- PNG image: ecommerce-schema.png (File ID: def456...)
- Base64 image data included for immediate viewing
```

#### Iterative Design

```
User: Create a simple process flow, then I'll ask for modifications

Claude: I'll create a basic process flow that we can refine together.

[Creates initial diagram]

User: Add a decision point after step 2 and a parallel process

Claude: I'll modify the diagram to add the decision point and parallel process.

[Generates updated diagram with modifications]
```

### Integration with Code Projects

#### API Documentation

```
User: Based on this OpenAPI spec, create a service architecture diagram

Claude: I'll analyze your OpenAPI specification and create a service architecture diagram showing the API structure and data flow.

[Analyzes the spec and creates appropriate diagram]
```

#### Database Design

```
User: Create an ER diagram for these database tables:
[User provides table definitions]

Claude: I'll create an Entity-Relationship diagram based on your table definitions.

[Creates ER diagram with proper relationships and cardinalities]
```

## Advanced Features

### Auto-Approval Configuration

Configure tools to run without confirmation:

```json
{
  "mcpServers": {
    "drawio-server": {
      "command": "docker",
      "args": ["..."],
      "autoApprove": [
        "generate-drawio-xml",
        "save-drawio-file"
      ]
    }
  }
}
```

### Environment-Specific Configurations

#### Development Environment

```json
{
  "mcpServers": {
    "drawio-dev": {
      "command": "docker-compose",
      "args": ["-f", "docker-compose.dev.yml", "exec", "-T", "mcp-server-dev", "python", "-m", "src.server"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "CACHE_TTL": "60"
      }
    }
  }
}
```

#### Production Environment

```json
{
  "mcpServers": {
    "drawio-prod": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "mcp-drawio-server:prod"],
      "env": {
        "LOG_LEVEL": "WARNING",
        "CACHE_TTL": "7200"
      }
    }
  }
}
```

### Custom Styling and Templates

The server supports custom diagram styling through prompts:

```
User: Create a flowchart using corporate colors (blue #003366, gray #666666)

Claude: I'll create a flowchart with your corporate color scheme.

[Generates diagram with custom styling]
```

## Troubleshooting

### Common Issues

#### 1. Server Not Found

**Symptoms**: Claude Code shows "MCP server not available"

**Solutions**:
```bash
# Check server status
docker ps | grep mcp-drawio-server

# Restart server
docker-compose restart mcp-server

# Check configuration path
ls -la /absolute/path/to/mcp-server/.env
```

#### 2. Tools Not Available

**Symptoms**: MCP tools don't appear in Claude Code

**Solutions**:
1. **Restart Claude Code** after configuration changes
2. **Check MCP server logs**:
   ```bash
   docker logs mcp-drawio-server
   ```
3. **Verify configuration syntax**:
   ```bash
   python -m json.tool ~/.kiro/settings/mcp.json
   ```

#### 3. Permission Errors

**Symptoms**: "Permission denied" errors in logs

**Solutions**:
```bash
# Fix directory permissions
sudo chown -R $USER:$USER /path/to/mcp-server/temp
chmod 755 /path/to/mcp-server/temp

# Or use Docker user mapping
docker run --user $(id -u):$(id -g) ...
```

#### 4. API Key Issues

**Symptoms**: "Invalid API key" or authentication errors

**Solutions**:
1. **Verify API key format**:
   ```bash
   echo $ANTHROPIC_API_KEY | grep "sk-ant-"
   ```
2. **Test API key**:
   ```bash
   curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
        https://api.anthropic.com/v1/messages
   ```
3. **Check API key in configuration**

#### 5. Draw.io CLI Issues

**Symptoms**: PNG conversion fails

**Solutions**:
```bash
# Test Draw.io CLI in container
docker exec mcp-drawio-server drawio --help

# Check CLI installation
docker exec mcp-drawio-server which drawio

# Reinstall if needed
docker exec mcp-drawio-server npm install -g @drawio/drawio-desktop-cli
```

### Debug Mode

Enable debug logging for troubleshooting:

```json
{
  "mcpServers": {
    "drawio-server": {
      "command": "docker",
      "args": ["..."],
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Log Analysis

Check logs for issues:

```bash
# Container logs
docker logs mcp-drawio-server --tail 100

# Application logs
docker exec mcp-drawio-server tail -f /app/logs/server.log

# Claude Code logs
# Check Claude Code's output panel for MCP-related messages
```

## Best Practices

### Configuration Management

1. **Use absolute paths** in configuration files
2. **Store API keys securely** using environment variables
3. **Version control** your MCP configuration (without secrets)
4. **Test configurations** in development before production

### Performance Optimization

1. **Enable caching** for better performance:
   ```json
   {
     "env": {
       "CACHE_TTL": "3600",
       "MAX_CACHE_SIZE": "100"
     }
   }
   ```

2. **Configure resource limits**:
   ```bash
   docker run --memory 512m --cpus 1.0 mcp-drawio-server
   ```

3. **Use auto-approval** for trusted tools:
   ```json
   {
     "autoApprove": ["generate-drawio-xml", "save-drawio-file"]
   }
   ```

### Security Considerations

1. **Limit network access** for the container
2. **Use non-root user** in container
3. **Regularly rotate API keys**
4. **Monitor resource usage**

### Workflow Optimization

1. **Create diagram templates** for common use cases
2. **Use descriptive filenames** when saving diagrams
3. **Organize diagrams** in project-specific directories
4. **Version control** important diagrams

### Team Collaboration

1. **Share MCP configurations** across team members
2. **Standardize diagram styles** and conventions
3. **Create diagram libraries** for common components
4. **Document diagram standards** and best practices

## Integration Examples

### Project Documentation

```
User: Create architecture diagrams for our microservices project

Claude: I'll create comprehensive architecture diagrams for your microservices project, including:
1. High-level system overview
2. Service interaction diagram
3. Data flow diagram
4. Deployment architecture

[Creates multiple related diagrams]
```

### Code Review Process

```
User: Create a flowchart showing our code review process

Claude: I'll create a flowchart that documents your code review workflow.

[Creates process diagram that can be saved to project documentation]
```

### API Design

```
User: Create a sequence diagram for this API endpoint workflow

Claude: I'll create a sequence diagram showing the API interaction flow.

[Generates sequence diagram with proper timing and interactions]
```

## Support and Resources

### Getting Help

1. **Check server health**: Use built-in health checks
2. **Review logs**: Both container and application logs
3. **Test components**: Verify each component individually
4. **Community support**: Join discussions and forums

### Additional Resources

- [MCP Server Usage Guide](MCP_SERVER_USAGE_GUIDE.md)
- [Installation Guide](INSTALLATION_GUIDE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### Contributing

Help improve the integration:
1. Report issues with detailed reproduction steps
2. Suggest configuration improvements
3. Share usage patterns and examples
4. Contribute to documentation