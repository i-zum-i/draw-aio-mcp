# MCP Draw.io Server Installation Guide

## Overview

This guide provides step-by-step instructions for installing and configuring the MCP Draw.io Server across various environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Installation](#docker-installation)
- [Manual Installation](#manual-installation)
- [Claude Code Configuration](#claude-code-configuration)
- [Verification](#verification)
- [Environment-Specific Setup](#environment-specific-setup)

## Quick Start

### Prerequisites Check

Before starting, ensure you have:

1. **Docker** (recommended) or **Python 3.10+**
2. **Anthropic API Key** - Get one from [Anthropic Console](https://console.anthropic.com/)
3. **Claude Code** - For MCP integration

### 5-Minute Setup

1. **Download the server**
   ```bash
   git clone <repository-url>
   cd mcp-server
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env to add your ANTHROPIC_API_KEY
   ```

3. **Start with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Configure Claude Code** (see [Claude Code Configuration](#claude-code-configuration))

## Docker Installation

### Option 1: Docker Compose (Recommended)

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

---

# MCP Draw.io サーバー インストールガイド

## 概要

このガイドでは、様々な環境でMCP Draw.io サーバーをインストール・設定するための段階的な手順を提供します。

## 目次

- [クイックスタート](#クイックスタート-1)
- [Dockerインストール](#dockerインストール-1)
- [手動インストール](#手動インストール-1)
- [Claude Code設定](#claude-code設定-1)
- [検証](#検証-1)
- [環境固有セットアップ](#環境固有セットアップ-1)

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

4. **Claude Code設定** ([Claude Code設定](#claude-code設定-1)を参照)

## Dockerインストール

### オプション1: Docker Compose（推奨）

#### 開発セットアップ

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd mcp-server

# 2. 環境ファイルを作成
cp .env.example .env.dev

# 3. 環境ファイルを編集
nano .env.dev
# 追加: ANTHROPIC_API_KEY=your-api-key-here

# 4. 開発サーバーを起動
docker-compose -f docker-compose.dev.yml up --build

# 5. サーバーが動作していることを確認
docker logs mcp-drawio-server-dev
```

#### 本番セットアップ

```bash
# 1. 本番環境ファイルを作成
cp .env.example .env.prod

# 2. 本番設定を構成
nano .env.prod
# 本番用最適化設定を追加

# 3. 本番サーバーを起動
docker-compose -f docker-compose.prod.yml up -d --build

# 4. デプロイを確認
docker-compose -f docker-compose.prod.yml ps
```

### オプション2: Docker Run

#### 基本Docker Run

```bash
# イメージをビルド
docker build -t mcp-drawio-server .

# コンテナを実行
docker run -d \
  --name mcp-drawio-server \
  --env-file .env \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/logs:/app/logs \
  mcp-drawio-server
```

#### 高度なDocker Run

```bash
# カスタム設定で実行
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

## 手動インストール

### システム要件

- **Python**: 3.10以上
- **Node.js**: 16以上 (Draw.io CLI用)
- **メモリ**: 最小256MB、推奨512MB
- **ディスク**: 依存関係と一時ファイル用に1GB

### 段階的インストール

#### 1. Python依存関係のインストール

```bash
# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt
```

#### 2. Draw.io CLIのインストール

```bash
# Node.jsをインストール（まだインストールしていない場合）
# Ubuntu/Debian:
sudo apt update && sudo apt install nodejs npm

# macOS:
brew install node

# Windows:
# https://nodejs.org/ からダウンロード

# Draw.io CLIをグローバルインストール
npm install -g @drawio/drawio-desktop-cli

# インストールを確認
drawio --version
```

#### 3. 環境設定

```bash
# 環境ファイルを作成
cp .env.example .env

# 設定を編集
nano .env
```

設定を追加:
```bash
ANTHROPIC_API_KEY=your-api-key-here
TEMP_DIR=./temp
DRAWIO_CLI_PATH=drawio
LOG_LEVEL=INFO
```

#### 4. 必要なディレクトリを作成

```bash
mkdir -p temp logs
chmod 755 temp logs
```

#### 5. サーバーを実行

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# サーバーを開始
python -m src.server
```

### 代替: システム全体インストール

```bash
# システム全体にインストール（本番環境では非推奨）
sudo pip install -r requirements.txt

# Draw.io CLIをグローバルインストール
sudo npm install -g @drawio/drawio-desktop-cli

# サーバーを実行
python -m src.server
```

## Claude Code設定

### 方法1: MCP設定UI

1. **Claude Codeを開く**
2. **設定に移動** → **MCPサーバー**
3. **新しいサーバーを追加** 以下の設定で:
   - **名前**: `drawio-server`
   - **コマンド**: `docker`
   - **引数**: `["run", "--rm", "-i", "--env-file", "/path/to/.env", "mcp-drawio-server"]`

### 方法2: 設定ファイル

#### Dockerインストール用

MCP設定ファイルを作成または編集:

**場所**: `~/.claude/mcp.json` (またはワークスペース固有の `.kiro/settings/mcp.json`)

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

#### 手動インストール用

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

#### 開発用

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

## 検証

### 1. サーバーステータスの確認

#### Dockerインストール
```bash
# コンテナステータスを確認
docker ps | grep mcp-drawio-server

# ログを確認
docker logs mcp-drawio-server

# ヘルスチェックを実行
docker exec mcp-drawio-server python /app/src/healthcheck.py
```

#### 手動インストール
```bash
# サーバーが動作しているかチェック
ps aux | grep "src.server"

# ヘルスチェックを実行
python src/healthcheck.py

# ログを確認
tail -f logs/server.log
```

### 2. MCPツールのテスト

Claude Codeを開いて以下のコマンドを試してください：

1. **図表生成のテスト**:
   ```
   Create a simple flowchart with start, process, and end nodes
   ```

2. **ファイル保存のテスト**:
   ```
   Save the diagram as "test-diagram.drawio"
   ```

3. **PNG変換のテスト**:
   ```
   Convert the saved diagram to PNG
   ```

### 3. ツール利用可能性の確認

Claude Codeで以下のツールが利用可能であることを確認してください：
- ✅ `generate-drawio-xml`
- ✅ `save-drawio-file`
- ✅ `convert-to-png`

## 環境固有セットアップ

### 開発環境

```bash
# 開発設定を使用
cp .env.example .env.dev

# 開発用に設定
cat >> .env.dev << EOF
LOG_LEVEL=DEBUG
CACHE_TTL=300
FILE_EXPIRY_HOURS=1
CLEANUP_INTERVAL_MINUTES=5
EOF

# 開発サーバーを起動
docker-compose -f docker-compose.dev.yml up --build
```

### 本番環境

```bash
# 本番設定を使用
cp .env.example .env.prod

# 本番用に設定
cat >> .env.prod << EOF
LOG_LEVEL=WARNING
CACHE_TTL=7200
FILE_EXPIRY_HOURS=48
CLEANUP_INTERVAL_MINUTES=30
EOF

# 本番サーバーを起動
docker-compose -f docker-compose.prod.yml up -d --build
```

### テスト環境

```bash
# テスト環境を作成
cp .env.example .env.test

# テスト用に設定
cat >> .env.test << EOF
LOG_LEVEL=DEBUG
CACHE_TTL=60
FILE_EXPIRY_HOURS=1
ANTHROPIC_API_KEY=test-key-for-testing
EOF

# テストを実行
python -m pytest tests/
```

## インストールのトラブルシューティング

### 一般的な問題

#### 1. Dockerビルド失敗

**エラー**: `failed to solve with frontend dockerfile.v0`

**解決策**:
```bash
# Dockerを更新
sudo apt update && sudo apt upgrade docker.io

# Dockerキャッシュをクリア
docker system prune -a

# キャッシュなしで再ビルド
docker build --no-cache -t mcp-drawio-server .
```

#### 2. 権限拒否

**エラー**: `Permission denied: '/app/temp'`

**解決策**:
```bash
# ディレクトリ権限を修正
sudo chown -R $USER:$USER temp logs
chmod 755 temp logs

# またはDockerの場合
docker run --user $(id -u):$(id -g) ...
```

#### 3. Draw.io CLIが見つからない

**エラー**: `drawio: command not found`

**解決策**:
```bash
# Draw.io CLIを再インストール
npm uninstall -g @drawio/drawio-desktop-cli
npm install -g @drawio/drawio-desktop-cli

# インストールを確認
which drawio
drawio --version
```

#### 4. Pythonインポートエラー

**エラー**: `ModuleNotFoundError: No module named 'mcp'`

**解決策**:
```bash
# 依存関係を再インストール
pip install --upgrade pip
pip install -r requirements.txt

# Pythonパスを確認
python -c "import sys; print(sys.path)"
```

#### 5. APIキーの問題

**エラー**: `Invalid API key`

**解決策**:
```bash
# APIキー形式を確認
echo $ANTHROPIC_API_KEY | grep "sk-ant-"

# APIキーをテスト
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/v1/messages
```

### ヘルプを得る

問題に遭遇した場合：

1. **詳細なエラーメッセージのためログを確認**
2. **前提条件が適切にインストールされていることを確認**
3. **コンポーネントを個別にテスト** (Docker, Python, Draw.io CLI)
4. **設定ファイルにタイポがないか確認**
5. **API アクセス用のネットワーク接続を確認**

### 診断コマンド

```bash
# システム情報
docker --version
python3 --version
node --version
npm --version

# サーバーステータス
docker ps -a | grep mcp
docker logs mcp-drawio-server --tail 50

# ネットワーク接続
curl -I https://api.anthropic.com/
ping google.com

# ファイル権限
ls -la temp/ logs/
whoami
id
```

## 次のステップ

インストール成功後：

1. **詳細な使用説明について[使用ガイド](MCP_SERVER_USAGE_GUIDE.md)を読む**
2. **使用ガイドの例を試す**
3. **本番デプロイメント用の監視を設定**
4. **重要な図表用のバックアップを設定**
5. **環境のセキュリティ設定を確認**

## サポート

追加サポートについて：
- [トラブルシューティングガイド](MCP_SERVER_USAGE_GUIDE.md#troubleshooting)を確認
- [FAQ](FAQ.md)を確認
- GitHubでイシューを提出
- コミュニティディスカッションに参加