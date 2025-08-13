# Standard MCP Server Initialization Pattern Implementation Guide

## Overview

This document describes the standard MCP server initialization patterns and lifecycle management implemented in the Draw.io MCP Server. The implementation follows best practices from the official MCP Python SDK.

---

# 標準MCPサーバー初期化パターン実装ガイド

## 概要

このドキュメントは、Draw.io MCP サーバーに実装された標準的なMCPサーバー初期化パターンとライフサイクル管理について説明します。公式MCP Python SDKのベストプラクティスに準拠した実装となっています。

## Implemented Standard Patterns

### 1. Server Metadata and Constants

## 実装された標準パターン

### 1. サーバーメタデータとコンスタント

```python
# MCPサーバー設定とメタデータ - 標準パターン
SERVER_NAME = "drawio-mcp-server"
SERVER_VERSION = "1.0.0"
SERVER_DESCRIPTION = "Draw.io diagram generation MCP server with official MCP SDK"

# サーバー機能定義 - 標準MCPサーバーパターン
SERVER_CAPABILITIES = ServerCapabilities(
    tools={}  # ツール機能を有効化
)

# サーバー実装情報 - MCP標準
SERVER_IMPLEMENTATION = Implementation(
    name=SERVER_NAME,
    version=SERVER_VERSION
)
```

**特徴:**
- 明確なサーバー識別情報
- MCP標準のServerCapabilitiesとImplementation使用
- バージョン管理とメタデータの標準化

### 2. 標準MCPサーバーインスタンス

```python
# 公式MCPサーバーインスタンス - 標準初期化パターン
server = Server(SERVER_NAME)
```

**特徴:**
- 公式MCP SDKのServerクラス使用
- 一意のサーバー名による識別
- グローバルサーバーインスタンス管理

### 3. ライフサイクル管理コンテキストマネージャー

```python
@asynccontextmanager
async def server_lifecycle():
    """
    標準MCPサーバーライフサイクル管理コンテキストマネージャー
    
    MCPサーバーの初期化、実行、クリーンアップを標準パターンで管理します。
    """
    try:
        # 初期化フェーズ
        await initialize_services()
        yield
    finally:
        # クリーンアップフェーズ
        await shutdown_services()
```

**特徴:**
- 標準的なリソース管理パターン
- 自動クリーンアップ保証
- 例外安全性の確保

### 4. 標準初期化パターン

```python
async def initialize_services():
    """
    標準MCPサーバー初期化パターン
    
    すべてのサーバーサービスとコンポーネントを標準的な順序で初期化します。
    """
    # 1. 設定とログの初期化
    # 2. コアサービスの初期化
    # 3. ヘルスチェッカーとモニタリング
    # 4. バックグラウンドタスクの開始
    # 5. 初期ヘルスチェック
    # 6. 初期化完了
```

**特徴:**
- 段階的な初期化プロセス
- 詳細なログ出力
- エラーハンドリングと検証
- パフォーマンス測定

### 5. 標準ツール定義パターン

```python
# 標準MCPツール定義 - ツールレジストリパターン
TOOL_DEFINITIONS = [
    Tool(
        name="generate-drawio-xml",
        description="自然言語プロンプトからDraw.io XML図表を生成",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "生成する図表の自然言語記述",
                    "minLength": 5,
                    "maxLength": 10000
                }
            },
            "required": ["prompt"],
            "additionalProperties": False
        }
    ),
    # ... 他のツール定義
]
```

**特徴:**
- 集中化されたツール定義
- JSON Schema による厳密な入力検証
- 標準的なツールメタデータ
- additionalProperties: false による厳密性

### 6. 標準ツールハンドラー

```python
@server.list_tools()
async def list_tools() -> List[Tool]:
    """
    標準MCPツールリストハンドラー
    
    利用可能なMCPツールのリストを標準形式で返します。
    """
    logger.debug(f"📋 ツールリスト要求 - {len(TOOL_DEFINITIONS)}個のツールを返却")
    return TOOL_DEFINITIONS
```

**特徴:**
- 公式MCP SDKデコレーター使用
- 統一されたツールレジストリ参照
- デバッグログ出力

### 7. 標準ツール実行パターン

```python
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    標準MCPツール呼び出しハンドラー
    
    公式MCP SDKの標準パターンに従ってツールを実行します。
    """
    try:
        # 標準ツール実行パターン
        result = await execute_tool_safely(name, arguments)
        return format_tool_response(name, result)
    except Exception as e:
        # 標準エラーレスポンス
        return [TextContent(type="text", text=error_message)]
```

**特徴:**
- 公式MCP SDKデコレーター使用
- 統一されたエラーハンドリング
- パフォーマンス測定とログ
- 標準レスポンス形式

### 8. 標準ユーティリティ関数

```python
def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> None:
    """標準MCPツール引数検証ユーティリティ"""

async def execute_tool_safely(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """標準MCPツール実行ヘルパー"""

def format_tool_response(tool_name: str, result: Dict[str, Any]) -> List[TextContent]:
    """標準MCPレスポンスフォーマッター"""
```

**特徴:**
- 再利用可能なユーティリティ関数
- 一貫した引数検証
- 標準化されたレスポンス形式
- エラーハンドリングの統一

### 9. 標準初期化オプション

```python
def create_initialization_options() -> InitializationOptions:
    """
    標準MCPサーバー初期化オプションを作成
    
    Returns:
        InitializationOptions: MCP標準の初期化オプション
    """
    return InitializationOptions(
        server_name=SERVER_NAME,
        server_version=SERVER_VERSION,
        capabilities=SERVER_CAPABILITIES
    )
```

**特徴:**
- MCP標準のInitializationOptions使用
- サーバーメタデータの統合
- 機能定義の明示

### 10. 標準シグナルハンドリング

```python
def setup_signal_handlers():
    """
    標準的なシグナルハンドラーを設定
    
    SIGINT (Ctrl+C) と SIGTERM の適切な処理を行います。
    """
    def signal_handler(signum, frame):
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logger.info(f"📡 {signal_name} シグナル受信 - 正常シャットダウン開始")
        shutdown_requested = True
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
```

**特徴:**
- 標準的なUnixシグナル処理
- 正常シャットダウンの保証
- 詳細なログ出力

### 11. 標準メイン実行パターン

```python
async def main():
    """
    標準MCPサーバーメイン関数
    
    公式MCP SDKの標準パターンに従ってサーバーを初期化・実行します。
    """
    try:
        # 標準ライフサイクル管理でサーバー実行
        async with server_lifecycle():
            await run_mcp_server()
    except KeyboardInterrupt:
        logger.info("⌨️ キーボード割り込み受信")
    except Exception as e:
        logger.error(f"❌ メイン実行エラー: {str(e)}", exc_info=True)
        raise
```

**特徴:**
- 標準的なasyncio実行パターン
- ライフサイクル管理の統合
- 包括的な例外処理
- 適切なログ出力

## MCPベストプラクティス準拠

### 1. 公式SDK使用
- `mcp.server.Server` クラスの使用
- `mcp.server.stdio.stdio_server` による標準I/O通信
- `mcp.types` の標準型定義使用

### 2. 標準プロトコル準拠
- MCP 2024-11-05 仕様準拠
- 標準的なツール定義形式
- 適切なエラーレスポンス形式

### 3. ライフサイクル管理
- 適切な初期化順序
- リソースの自動クリーンアップ
- 正常シャットダウン処理

### 4. エラーハンドリング
- 統一されたエラー分類
- 詳細なエラー情報提供
- グレースフル・デグラデーション

### 5. ログとモニタリング
- 構造化ログ出力
- パフォーマンス測定
- ヘルスチェック機能

## 検証方法

標準パターンの実装は以下のテストで検証できます：

```bash
# 標準パターンテストの実行
python mcp-server/test_standard_mcp_patterns.py
```

このテストは以下を検証します：
- MCP SDK インポート
- サーバー定数定義
- サーバー機能定義
- ツール定義
- 初期化オプション
- 引数検証

## まとめ

この実装により、Draw.io MCP サーバーは以下の標準パターンを採用しています：

1. ✅ **公式MCP SDK使用**: 完全なMCP準拠
2. ✅ **標準初期化パターン**: 段階的で安全な初期化
3. ✅ **ライフサイクル管理**: 自動リソース管理
4. ✅ **ツールレジストリ**: 集中化されたツール定義
5. ✅ **統一エラーハンドリング**: 一貫したエラー処理
6. ✅ **標準ユーティリティ**: 再利用可能なヘルパー関数
7. ✅ **シグナルハンドリング**: 正常シャットダウン
8. ✅ **包括的ログ**: 詳細な実行ログ

これらのパターンにより、MCPサーバーは保守性、拡張性、信頼性を確保し、公式MCP仕様に完全準拠しています。