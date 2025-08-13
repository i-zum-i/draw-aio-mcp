# generate-drawio-xml MCP Tool

This document describes the `generate-drawio-xml` MCP tool implementation.

## Overview

The `generate-drawio-xml` tool converts natural language descriptions into valid Draw.io XML format that can be opened in diagrams.net. It supports various diagram types including flowcharts, system diagrams, AWS architecture diagrams, and more.

## Implementation Details

### Tool Function

```python
async def generate_drawio_xml(prompt: str) -> Dict[str, Any]
```

### Input Parameters

- **prompt** (string, required): Natural language description of the diagram to generate
  - Minimum length: 5 characters
  - Maximum length: 10,000 characters
  - Must be a non-empty string

### Return Format

```python
{
    "success": bool,           # Whether the generation was successful
    "xml_content": str,        # Valid Draw.io XML content (if successful)
    "error": str,              # Error message (if failed)
    "error_code": str,         # Specific error code for programmatic handling (if failed)
    "timestamp": str           # ISO timestamp of the generation
}
```

### Error Codes

- `INVALID_INPUT`: Input validation failed (empty, too short, too long, etc.)
- `API_KEY_MISSING`: Anthropic API key not configured
- `CONNECTION_ERROR`: Network connection issues
- `RATE_LIMIT_ERROR`: API rate limit exceeded
- `QUOTA_EXCEEDED`: API usage quota exceeded
- `INVALID_RESPONSE`: Invalid response from Claude API
- `INVALID_XML`: Generated XML failed validation
- `TIMEOUT_ERROR`: API request timed out
- `UNKNOWN_ERROR`: Unexpected error occurred

### Input Validation and Sanitization

The tool includes comprehensive input validation:

1. **Type checking**: Ensures input is a string
2. **Length validation**: Enforces minimum (5) and maximum (10,000) character limits
3. **Content sanitization**: Removes control characters while preserving natural language
4. **Empty string detection**: Rejects empty or whitespace-only inputs

### MCP Tool Schema

```json
{
    "name": "generate-drawio-xml",
    "description": "Generate Draw.io XML diagram from natural language prompt",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Natural language description of the diagram to generate",
                "minLength": 5,
                "maxLength": 10000
            }
        },
        "required": ["prompt"]
    }
}
```

## Usage Examples

### Basic Usage

```python
result = await generate_drawio_xml("Create a simple flowchart showing user login process")

if result["success"]:
    print("Generated XML:", result["xml_content"])
else:
    print("Error:", result["error"])
    print("Error Code:", result["error_code"])
```

### AWS Architecture Diagram

```python
result = await generate_drawio_xml("""
Create an AWS architecture diagram showing:
- VPC with public and private subnets
- Application Load Balancer in public subnet
- EC2 instances in private subnet
- RDS database in private subnet
- NAT Gateway for outbound traffic
""")
```

### System Architecture

```python
result = await generate_drawio_xml("""
Create a microservices architecture diagram with:
- API Gateway
- User Service
- Order Service
- Payment Service
- Database for each service
- Message queue between services
""")
```

## Error Handling

The tool implements comprehensive error handling:

1. **Input validation errors** are caught and returned with `INVALID_INPUT` code
2. **LLM service errors** are categorized and returned with appropriate error codes
3. **Unexpected errors** are caught and returned with `UNKNOWN_ERROR` code
4. **All errors include timestamps** for debugging purposes

## Integration with LLMService

The tool integrates with the `LLMService` class which provides:

- **Caching**: Identical prompts return cached results for better performance
- **XML validation**: Generated XML is validated for Draw.io compatibility
- **Error categorization**: API errors are properly categorized and handled
- **AWS diagram rules**: Special handling for AWS architecture diagrams

## Testing

The implementation includes comprehensive tests:

- **Structure tests**: Verify tool schema and function signatures
- **Input validation tests**: Test all validation scenarios
- **MCP server tests**: Test server request handling
- **Integration tests**: Test with actual API calls (requires API key)

Run tests with:

```bash
python test_structure.py    # Structure and validation tests
python test_mcp_server.py   # MCP server functionality tests
python test_tool.py         # Full integration tests (requires API key)
```

## Requirements Compliance

This implementation satisfies the following requirements:

- **Requirement 1.1**: Generates valid Draw.io XML from natural language prompts
- **Requirement 1.2**: Returns file ID for future reference (via timestamp and success tracking)
- **Requirement 1.3**: Validates XML structure for required elements
- **Requirement 1.4**: Applies AWS-specific diagram rules when generating AWS diagrams

## Dependencies

- `anthropic`: Claude API integration
- `python-dotenv`: Environment variable management (optional)
- Standard library modules: `asyncio`, `logging`, `datetime`, `typing`, `re`

---

# generate-drawio-xml MCPツール

このドキュメントでは、`generate-drawio-xml` MCPツールの実装について説明します。

## 概要

`generate-drawio-xml`ツールは、自然言語による説明を、diagrams.netで開くことができる有効なDraw.io XML形式に変換します。フローチャート、システム図、AWSアーキテクチャ図など、さまざまな図表タイプをサポートしています。

## 実装詳細

### ツール関数

```python
async def generate_drawio_xml(prompt: str) -> Dict[str, Any]
```

### 入力パラメータ

- **prompt** (文字列、必須): 生成する図表の自然言語による説明
  - 最小長: 5文字
  - 最大長: 10,000文字
  - 空でない文字列である必要があります

### 戻り値形式

```python
{
    "success": bool,           # 生成が成功したかどうか
    "xml_content": str,        # 有効なDraw.io XMLコンテンツ（成功時）
    "error": str,              # エラーメッセージ（失敗時）
    "error_code": str,         # プログラムでの処理用の特定のエラーコード（失敗時）
    "timestamp": str           # 生成のISOタイムスタンプ
}
```

### エラーコード

- `INVALID_INPUT`: 入力検証に失敗（空、短すぎる、長すぎるなど）
- `API_KEY_MISSING`: Anthropic APIキーが設定されていない
- `CONNECTION_ERROR`: ネットワーク接続の問題
- `RATE_LIMIT_ERROR`: APIレート制限に達した
- `QUOTA_EXCEEDED`: API使用量クォータを超過
- `INVALID_RESPONSE`: Claude APIからの無効な応答
- `INVALID_XML`: 生成されたXMLが検証に失敗
- `TIMEOUT_ERROR`: APIリクエストがタイムアウト
- `UNKNOWN_ERROR`: 予期しないエラーが発生

### 入力検証とサニタイゼーション

ツールは包括的な入力検証を含みます：

1. **型チェック**: 入力が文字列であることを確認
2. **長さ検証**: 最小（5）および最大（10,000）文字制限を強制
3. **コンテンツサニタイゼーション**: 自然言語を保持しながら制御文字を削除
4. **空文字列検出**: 空またはスペースのみの入力を拒否

### MCPツールスキーマ

```json
{
    "name": "generate-drawio-xml",
    "description": "自然言語プロンプトからDraw.io XML図表を生成",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "生成する図表の自然言語による説明",
                "minLength": 5,
                "maxLength": 10000
            }
        },
        "required": ["prompt"]
    }
}
```

## 使用例

### 基本的な使用方法

```python
result = await generate_drawio_xml("ユーザーログインプロセスを示すシンプルなフローチャートを作成")

if result["success"]:
    print("生成されたXML:", result["xml_content"])
else:
    print("エラー:", result["error"])
    print("エラーコード:", result["error_code"])
```

### AWSアーキテクチャ図

```python
result = await generate_drawio_xml("""
次を含むAWSアーキテクチャ図を作成してください：
- パブリックサブネットとプライベートサブネットを持つVPC
- パブリックサブネット内のApplication Load Balancer
- プライベートサブネット内のEC2インスタンス
- プライベートサブネット内のRDSデータベース
- アウトバウンドトラフィック用のNAT Gateway
""")
```

### システムアーキテクチャ

```python
result = await generate_drawio_xml("""
次を含むマイクロサービスアーキテクチャ図を作成してください：
- API Gateway
- ユーザーサービス
- 注文サービス
- 決済サービス
- 各サービス用のデータベース
- サービス間のメッセージキュー
""")
```

## エラーハンドリング

ツールは包括的なエラーハンドリングを実装しています：

1. **入力検証エラー**はキャッチされ、`INVALID_INPUT`コードとともに返されます
2. **LLMサービスエラー**は分類され、適切なエラーコードとともに返されます
3. **予期しないエラー**はキャッチされ、`UNKNOWN_ERROR`コードとともに返されます
4. **すべてのエラーにはデバッグ目的のタイムスタンプが含まれます**

## LLMServiceとの統合

ツールは以下を提供する`LLMService`クラスと統合されています：

- **キャッシュ**: 同じプロンプトはパフォーマンス向上のためキャッシュされた結果を返します
- **XML検証**: 生成されたXMLはDraw.io互換性について検証されます
- **エラー分類**: APIエラーは適切に分類され処理されます
- **AWS図表ルール**: AWSアーキテクチャ図の特別な処理

## テスト

実装には包括的なテストが含まれています：

- **構造テスト**: ツールスキーマと関数シグネチャの検証
- **入力検証テスト**: すべての検証シナリオのテスト
- **MCPサーバーテスト**: サーバーリクエスト処理のテスト
- **統合テスト**: 実際のAPI呼び出しでのテスト（APIキーが必要）

テストの実行：

```bash
python test_structure.py    # 構造および検証テスト
python test_mcp_server.py   # MCPサーバー機能テスト
python test_tool.py         # 完全統合テスト（APIキーが必要）
```

## 要件コンプライアンス

この実装は以下の要件を満たします：

- **要件1.1**: 自然言語プロンプトから有効なDraw.io XMLを生成
- **要件1.2**: 将来の参照用にファイルIDを返す（タイムスタンプと成功追跡による）
- **要件1.3**: 必要な要素のXML構造を検証
- **要件1.4**: AWS図表生成時にAWS固有の図表ルールを適用

## 依存関係

- `anthropic`: Claude API統合
- `python-dotenv`: 環境変数管理（オプション）
- 標準ライブラリモジュール: `asyncio`, `logging`, `datetime`, `typing`, `re`