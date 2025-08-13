# Dependency Checking Feature

The MCP Draw.io Server includes comprehensive dependency checking functionality to help with setup and troubleshooting.

---

# 依存関係チェック機能

MCP Draw.io サーバーには、セットアップとトラブルシューティングを支援する包括的な依存関係チェック機能が含まれています。

## Features

### 1. Startup Dependency Validation
- Automatically checks critical dependencies during server startup
- Prevents server startup if critical dependencies are missing
- Provides clear error messages and setup guidance

### 2. Command-Line Dependency Tools
- `--check-dependencies`: Check only critical dependencies
- `--check-all`: Check all dependencies (critical and optional)
- `--setup-guide`: Generate comprehensive setup guidance

### 3. Enhanced Error Messages
- Clear identification of missing dependencies
- Specific installation commands for each dependency
- Troubleshooting guidance for common issues

### 4. Automatic Setup Guidance
- Step-by-step installation instructions
- Alternative options when dependencies are unavailable
- Links to official documentation and download pages

## 機能

### 1. 起動時依存関係検証
- サーバー起動時に重要な依存関係を自動チェック
- 重要な依存関係が不足している場合はサーバー起動を防止
- 明確なエラーメッセージとセットアップガイダンスを提供

### 2. コマンドライン依存関係ツール
- `--check-dependencies`: 重要な依存関係のみをチェック
- `--check-all`: すべての依存関係（重要およびオプション）をチェック
- `--setup-guide`: 包括的なセットアップガイダンスを生成

### 3. 強化されたエラーメッセージ
- 不足している依存関係の明確な識別
- 各依存関係の具体的なインストールコマンド
- 一般的な問題のトラブルシューティングガイダンス

### 4. 自動セットアップガイダンス
- ステップバイステップのインストール手順
- 依存関係が利用できない場合の代替オプション
- 公式ドキュメントとダウンロードページへのリンク

## Usage

### Check Critical Dependencies
```bash
python -m src.server --check-dependencies
```

This checks only the dependencies required for server startup:
- Python libraries: `anthropic`, `mcp`
- Environment variables: `ANTHROPIC_API_KEY`

### Check All Dependencies
```bash
python -m src.server --check-all
```

This checks all dependencies including optional ones:
- Optional Python libraries: `httpx`
- Optional system commands: `drawio`, `node`, `npm`

### Generate Setup Guide
```bash
python -m src.server --setup-guide
```

This generates a comprehensive setup guide with:
- Installation instructions for missing dependencies
- Troubleshooting tips
- Alternative options
- Step-by-step setup process

## Dependency Categories

### Critical Dependencies (Required)
These dependencies are required for the server to start:

1. **anthropic** (Python library)
   - Purpose: Claude API client
   - Install: `pip install anthropic`
   - Minimum version: 0.3.0

2. **mcp** (Python library)
   - Purpose: Model Context Protocol SDK
   - Install: `pip install mcp`
   - Minimum version: 1.0.0

3. **ANTHROPIC_API_KEY** (Environment variable)
   - Purpose: Authentication with Claude API
   - Setup: `export ANTHROPIC_API_KEY=sk-ant-your-key-here`
   - Format: Must start with `sk-ant-`

### Optional Dependencies (Enhanced functionality)
These dependencies provide additional features but are not required:

1. **httpx** (Python library)
   - Purpose: HTTP client for async requests
   - Install: `pip install httpx`
   - Impact: Better HTTP performance

2. **drawio** (System command)
   - Purpose: PNG conversion from Draw.io files
   - Install: `npm install -g @drawio/drawio-desktop-cli`
   - Impact: Without this, PNG conversion will show fallback message

3. **node** (System command)
   - Purpose: Node.js runtime (required for Draw.io CLI)
   - Install: Download from https://nodejs.org/
   - Minimum version: 14.0.0

4. **npm** (System command)
   - Purpose: Node Package Manager (required for Draw.io CLI)
   - Install: Included with Node.js
   - Impact: Required to install Draw.io CLI

## Integration with Server

### Startup Process
1. Server loads configuration
2. **Dependency checker validates critical dependencies**
3. If critical dependencies are missing, server stops with error
4. If optional dependencies are missing, server shows warnings
5. Server continues with available functionality

### Health Checks
The dependency checker is integrated with the health check system:
- Health endpoint includes dependency status
- Periodic checks for dependency availability
- Cached results to avoid repeated checks

### Error Handling
When dependencies are missing:
- Clear error messages explain what's missing
- Installation commands are provided
- Alternative options are suggested
- Troubleshooting guidance is included

## Example Output

### All Dependencies Available
```
✅ すべての重要な依存関係が利用可能です
```

### Missing Critical Dependencies
```
❌ 重要な依存関係が不足しています:
  ❌ anthropic: Python library 'anthropic' not found
   💡 Install with: pip install anthropic
  ❌ ANTHROPIC_API_KEY: Environment variable 'ANTHROPIC_API_KEY' is not set
   💡 Set your Anthropic API key: export ANTHROPIC_API_KEY=sk-ant-...
```

### Setup Guidance
```
📋 MCP Draw.io Server - Dependency Setup Guide
==================================================

🚨 CRITICAL DEPENDENCIES (Required for server startup)
--------------------------------------------------

❌ anthropic - Anthropic Claude API client library
   Status: missing
   Issue: Python library 'anthropic' not found
   Install: pip install anthropic

🔧 GENERAL SETUP STEPS
--------------------------------------------------

1. Install Python dependencies:
   pip install -r requirements.txt

2. Set up environment variables:
   export ANTHROPIC_API_KEY=sk-ant-your-key-here

3. (Optional) Install Draw.io CLI for PNG conversion:
   npm install -g @drawio/drawio-desktop-cli

4. Verify installation:
   python -m src.server --check-dependencies

5. Start the server:
   python -m src.server
```

## Benefits

1. **Faster Troubleshooting**: Users can quickly identify and fix dependency issues
2. **Better User Experience**: Clear guidance instead of cryptic error messages
3. **Reduced Support Burden**: Self-service dependency checking and setup
4. **Operational Reliability**: Prevents server startup with incomplete setup
5. **Enhanced Monitoring**: Health checks include dependency status

## Implementation Details

The dependency checking is implemented in `src/dependency_checker.py` and includes:
- Modular dependency definitions
- Async checking for better performance
- Caching to avoid repeated checks
- Comprehensive error handling
- Integration with logging system
- Support for different dependency types (Python libraries, system commands, environment variables)

The feature is integrated into:
- Server startup process (`src/server.py`)
- Health checking system (`src/health.py`)
- Image service fallback messages (`src/image_service.py`)
- Command-line interface (argument parsing)