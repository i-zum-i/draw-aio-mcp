# MCP Draw.io サーバー インストールガイド

## 概要

このガイドでは、様々な環境でMCP Draw.io サーバーをインストール・設定するための段階的な手順を提供します。

## 目次

- [クイックスタート](#クイックスタート)
- [Dockerインストール](#dockerインストール)
- [手動インストール](#手動インストール)
- [Claude Code設定](#claude-code設定)
- [検証](#検証)
- [環境固有セットアップ](#環境固有セットアップ)

## クイックスタート

### 前提条件チェック

開始前に以下を確認してください：

1. **Docker**（推奨）または **Python 3.10+**
2. **Anthropic APIキー** - [Anthropic Console](https://console.anthropic.com/)から取得
3. **Claude Code** - MCP統合用

### 5分セットアップ

1. **サーバーをダウンロード**
   ```bash
   git clone <repository-url>
   cd mcp-server
   ```

2. **環境設定**
   ```bash
   cp .env.example .env
   # .envを編集してANTHROPIC_API_KEYを追加
   ```

3. **Dockerで起動**
   ```bash
   docker-compose up --build
   ```

4. **Claude Code設定** ([Claude Code設定](#claude-code設定)を参照)

## Dockerインストール

### オプション1: Docker Compose（推奨）

#### Development Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd mcp-server

# 2. Create environment file
cp .env.example .env.dev

# 3. Edit environment file
nano .env.dev
# Add: ANTHROPIC_API_KEY=your-api-key-here

# 4. Start development server
docker-compose -f docker-compose.dev.yml up --build

# 5. Verify server is running
docker logs mcp-drawio-server-dev
```

#### Production Setup

```bash
# 1. Create production environment
cp .env.example .env.prod

# 2. Configure production settings
nano .env.prod
# Add production-optimized settings

# 3. Start production server
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Verify deployment
docker-compose -f docker-compose.prod.yml ps
```

### Option 2: Docker Run

#### Basic Docker Run

```bash
# Build image
docker build -t mcp-drawio-server .

# Run container
docker run -d \
  --name mcp-drawio-server \
  --env-file .env \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/logs:/app/logs \
  mcp-drawio-server
```

#### Advanced Docker Run

```bash
# Run with custom configuration
docker run -d \
  --name mcp-drawio-server \
  --restart unless-stopped \
  --memory 512m \
  --cpus 1.0 \
  -e ANTHROPIC_API_KEY="your-api-key" \
  -e LOG_LEVEL="INFO" \
  -e CACHE_TTL="3600" \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/logs:/app/logs \
  --health-cmd="python /app/src/healthcheck.py" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  mcp-drawio-server
```

## Manual Installation

### System Requirements

- **Python**: 3.10 or higher
- **Node.js**: 16 or higher (for Draw.io CLI)
- **Memory**: Minimum 256MB, recommended 512MB
- **Disk**: 1GB for dependencies and temporary files

### Step-by-Step Installation

#### 1. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Install Draw.io CLI

```bash
# Install Node.js (if not already installed)
# Ubuntu/Debian:
sudo apt update && sudo apt install nodejs npm

# macOS:
brew install node

# Windows:
# Download from https://nodejs.org/

# Install Draw.io CLI globally
npm install -g @drawio/drawio-desktop-cli

# Verify installation
drawio --version
```

#### 3. Configure Environment

```bash
# Create environment file
cp .env.example .env

# Edit configuration
nano .env
```

Add your configuration:
```bash
ANTHROPIC_API_KEY=your-api-key-here
TEMP_DIR=./temp
DRAWIO_CLI_PATH=drawio
LOG_LEVEL=INFO
```

#### 4. Create Required Directories

```bash
mkdir -p temp logs
chmod 755 temp logs
```

#### 5. Run the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python -m src.server
```

### Alternative: System-Wide Installation

```bash
# Install system-wide (not recommended for production)
sudo pip install -r requirements.txt

# Install Draw.io CLI globally
sudo npm install -g @drawio/drawio-desktop-cli

# Run server
python -m src.server
```

## Claude Code Configuration

### Method 1: MCP Settings UI

1. **Open Claude Code**
2. **Go to Settings** → **MCP Servers**
3. **Add New Server** with these settings:
   - **Name**: `drawio-server`
   - **Command**: `docker`
   - **Args**: `["run", "--rm", "-i", "--env-file", "/path/to/.env", "mcp-drawio-server"]`

### Method 2: Configuration File

#### For Docker Installation

Create or edit your MCP configuration file:

**Location**: `~/.claude/mcp.json` (or workspace-specific `.kiro/settings/mcp.json`)

```json
{
  "mcpServers": {
    "drawio-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/absolute/path/to/mcp-server/.env",
        "-v", "/absolute/path/to/mcp-server/temp:/app/temp",
        "mcp-drawio-server:latest"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### For Manual Installation

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

#### For Development

```json
{
  "mcpServers": {
    "drawio-server-dev": {
      "command": "docker-compose",
      "args": [
        "-f", "/absolute/path/to/mcp-server/docker-compose.dev.yml",
        "run", "--rm", "mcp-server-dev"
      ],
      "cwd": "/absolute/path/to/mcp-server",
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Verification

### 1. Check Server Status

#### Docker Installation
```bash
# Check container status
docker ps | grep mcp-drawio-server

# Check logs
docker logs mcp-drawio-server

# Run health check
docker exec mcp-drawio-server python /app/src/healthcheck.py
```

#### Manual Installation
```bash
# Check if server is running
ps aux | grep "src.server"

# Run health check
python src/healthcheck.py

# Check logs
tail -f logs/server.log
```

### 2. Test MCP Tools

Open Claude Code and try these commands:

1. **Test diagram generation**:
   ```
   Create a simple flowchart with start, process, and end nodes
   ```

2. **Test file saving**:
   ```
   Save the diagram as "test-diagram.drawio"
   ```

3. **Test PNG conversion**:
   ```
   Convert the saved diagram to PNG
   ```

### 3. Verify Tool Availability

In Claude Code, you should see these tools available:
- ✅ `generate-drawio-xml`
- ✅ `save-drawio-file`
- ✅ `convert-to-png`

## Environment-Specific Setup

### Development Environment

```bash
# Use development configuration
cp .env.example .env.dev

# Configure for development
cat >> .env.dev << EOF
LOG_LEVEL=DEBUG
CACHE_TTL=300
FILE_EXPIRY_HOURS=1
CLEANUP_INTERVAL_MINUTES=5
EOF

# Start development server
docker-compose -f docker-compose.dev.yml up --build
```

### Production Environment

```bash
# Use production configuration
cp .env.example .env.prod

# Configure for production
cat >> .env.prod << EOF
LOG_LEVEL=WARNING
CACHE_TTL=7200
FILE_EXPIRY_HOURS=48
CLEANUP_INTERVAL_MINUTES=30
EOF

# Start production server
docker-compose -f docker-compose.prod.yml up -d --build
```

### Testing Environment

```bash
# Create test environment
cp .env.example .env.test

# Configure for testing
cat >> .env.test << EOF
LOG_LEVEL=DEBUG
CACHE_TTL=60
FILE_EXPIRY_HOURS=1
ANTHROPIC_API_KEY=test-key-for-testing
EOF

# Run tests
python -m pytest tests/
```

## Troubleshooting Installation

### Common Issues

#### 1. Docker Build Fails

**Error**: `failed to solve with frontend dockerfile.v0`

**Solution**:
```bash
# Update Docker
sudo apt update && sudo apt upgrade docker.io

# Clear Docker cache
docker system prune -a

# Rebuild with no cache
docker build --no-cache -t mcp-drawio-server .
```

#### 2. Permission Denied

**Error**: `Permission denied: '/app/temp'`

**Solution**:
```bash
# Fix directory permissions
sudo chown -R $USER:$USER temp logs
chmod 755 temp logs

# Or for Docker
docker run --user $(id -u):$(id -g) ...
```

#### 3. Draw.io CLI Not Found

**Error**: `drawio: command not found`

**Solution**:
```bash
# Reinstall Draw.io CLI
npm uninstall -g @drawio/drawio-desktop-cli
npm install -g @drawio/drawio-desktop-cli

# Verify installation
which drawio
drawio --version
```

#### 4. Python Import Errors

**Error**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**:
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 5. API Key Issues

**Error**: `Invalid API key`

**Solution**:
```bash
# Verify API key format
echo $ANTHROPIC_API_KEY | grep "sk-ant-"

# Test API key
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/v1/messages
```

### Getting Help

If you encounter issues:

1. **Check logs** for detailed error messages
2. **Verify prerequisites** are properly installed
3. **Test components individually** (Docker, Python, Draw.io CLI)
4. **Review configuration** files for typos
5. **Check network connectivity** for API access

### Diagnostic Commands

```bash
# System information
docker --version
python3 --version
node --version
npm --version

# Server status
docker ps -a | grep mcp
docker logs mcp-drawio-server --tail 50

# Network connectivity
curl -I https://api.anthropic.com/
ping google.com

# File permissions
ls -la temp/ logs/
whoami
id
```

## Next Steps

After successful installation:

1. **Read the [Usage Guide](MCP_SERVER_USAGE_GUIDE.md)** for detailed usage instructions
2. **Try the examples** in the usage guide
3. **Configure monitoring** for production deployments
4. **Set up backups** for important diagrams
5. **Review security settings** for your environment

## Support

For additional support:
- Check the [Troubleshooting Guide](MCP_SERVER_USAGE_GUIDE.md#troubleshooting)
- Review the [FAQ](FAQ.md)
- Submit issues on GitHub
- Join the community discussions