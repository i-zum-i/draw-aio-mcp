# MCP Draw.io Server API Documentation

## Overview

The MCP Draw.io Server provides three Model Context Protocol (MCP) tools for generating, saving, and converting Draw.io diagrams. This document provides comprehensive API specifications for each tool, including detailed parameters, return values, and error codes.

## Table of Contents

- [Tool Overview](#tool-overview)
- [generate-drawio-xml](#generate-drawio-xml)
- [save-drawio-file](#save-drawio-file)
- [convert-to-png](#convert-to-png)
- [Error Code Reference](#error-code-reference)
- [Common Response Patterns](#common-response-patterns)
- [Usage Examples](#usage-examples)

## Tool Overview

| Tool Name | Purpose | Input | Output |
|-----------|---------|-------|--------|
| `generate-drawio-xml` | Generate Draw.io XML from natural language | Text prompt | Draw.io XML content |
| `save-drawio-file` | Save XML content to temporary files | XML content + optional filename | File ID and metadata |
| `convert-to-png` | Convert Draw.io files to PNG images | File ID or path | PNG file information |

## generate-drawio-xml

Generates Draw.io XML diagram content from natural language descriptions using Claude AI.

### Tool Schema

```json
{
  "name": "generate-drawio-xml",
  "description": "Generate Draw.io XML diagrams from natural language descriptions",
  "inputSchema": {
    "type": "object",
    "properties": {
      "prompt": {
        "type": "string",
        "description": "Natural language description of the diagram to generate"
      }
    },
    "required": ["prompt"]
  }
}
```

### Parameters

- **prompt** (string, required): Natural language description of the diagram
  - Must be a non-empty string
  - Supports complex diagram descriptions including flowcharts, AWS architectures, network diagrams, etc.
  - Examples: "Create a flowchart for user authentication", "AWS 3-tier architecture with load balancer"

### Response Format

```json
{
  "success": true,
  "xml_content": "<mxfile>...</mxfile>",
  "error": null
}
```

### Response Fields

- **success** (boolean): Indicates if the operation was successful
- **xml_content** (string): Generated Draw.io XML content (only present when success=true)
- **error** (string|null): Error message if operation failed

## save-drawio-file

Saves XML content to temporary files with unique identifiers and automatic cleanup.

### Tool Schema

```json
{
  "name": "save-drawio-file", 
  "description": "Save Draw.io XML content to temporary files",
  "inputSchema": {
    "type": "object",
    "properties": {
      "xml_content": {
        "type": "string",
        "description": "Valid Draw.io XML content"
      },
      "filename": {
        "type": "string",
        "description": "Optional custom filename (UUID generated if not provided)"
      }
    },
    "required": ["xml_content"]
  }
}
```

### Parameters

- **xml_content** (string, required): Valid Draw.io XML content
  - Must contain valid XML structure with mxfile root element
  - Will be validated before saving
- **filename** (string, optional): Custom filename
  - If not provided, UUID will be generated
  - Should not include file extension (.drawio will be added automatically)

### Response Format

```json
{
  "success": true,
  "file_id": "uuid-string",
  "file_path": "/app/temp/uuid.drawio",
  "expires_at": "2024-01-01T12:00:00Z",
  "error": null
}
```

### Response Fields

- **success** (boolean): Indicates if the operation was successful
- **file_id** (string): Unique file identifier
- **file_path** (string): Full path to the saved file
- **expires_at** (string): ISO timestamp when file will be automatically deleted
- **error** (string|null): Error message if operation failed

## convert-to-png

Converts Draw.io files to PNG images using Draw.io CLI.

### Tool Schema

```json
{
  "name": "convert-to-png",
  "description": "Convert Draw.io files to PNG images",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_id": {
        "type": "string",
        "description": "File ID from save-drawio-file (recommended)"
      },
      "file_path": {
        "type": "string", 
        "description": "Direct file path (alternative to file_id)"
      }
    },
    "anyOf": [
      {"required": ["file_id"]},
      {"required": ["file_path"]}
    ]
  }
}
```

### Parameters

- **file_id** (string, optional): File ID returned from save-drawio-file
  - Recommended approach for security and validation
- **file_path** (string, optional): Direct file path
  - Alternative to file_id for external files
  - Must be accessible by the server

### Response Format

```json
{
  "success": true,
  "png_file_id": "uuid-string",
  "png_file_path": "/app/temp/uuid.png",
  "base64_content": "base64-encoded-image-data",
  "error": null
}
```

### Response Fields

- **success** (boolean): Indicates if the operation was successful
- **png_file_id** (string): Unique identifier for the generated PNG
- **png_file_path** (string): Full path to the generated PNG file
- **base64_content** (string): Base64 encoded PNG image data
- **error** (string|null): Error message if operation failed

## Error Code Reference

### LLM Service Errors

| Error Code | Description | Typical Cause | Resolution |
|------------|-------------|---------------|------------|
| `API_KEY_MISSING` | Claude API key not provided | Missing ANTHROPIC_API_KEY | Set environment variable |
| `CONNECTION_ERROR` | Network connection failed | Network/DNS issues | Check connectivity |
| `RATE_LIMIT_ERROR` | API rate limit exceeded | Too many requests | Wait and retry |
| `QUOTA_EXCEEDED` | API quota exhausted | Monthly/daily limits reached | Upgrade plan or wait |
| `INVALID_RESPONSE` | Unexpected API response | API changes or malformed request | Check request format |
| `INVALID_XML` | Generated XML is invalid | AI generation error | Retry with clearer prompt |
| `TIMEOUT_ERROR` | Request timed out | Slow network or complex request | Retry or simplify prompt |
| `UNKNOWN_ERROR` | Unexpected error occurred | Various internal issues | Check logs and retry |

### File Service Errors

| Error Code | Description | Typical Cause | Resolution |
|------------|-------------|---------------|------------|
| `FILE_NOT_FOUND` | Requested file not found | Invalid file_id or expired file | Check file_id or regenerate |
| `PERMISSION_DENIED` | File access denied | File system permissions | Check directory permissions |
| `DISK_FULL` | Insufficient disk space | Storage quota exceeded | Free up space |
| `INVALID_PATH` | Invalid file path provided | Malformed path or security violation | Use valid file paths |

### Image Service Errors

| Error Code | Description | Typical Cause | Resolution |
|------------|-------------|---------------|------------|
| `CLI_NOT_FOUND` | Draw.io CLI not available | Missing installation | Install @drawio/drawio-desktop-cli |
| `CLI_ERROR` | CLI execution failed | Invalid input or CLI bug | Check input file validity |
| `CONVERSION_FAILED` | PNG conversion failed | Corrupted input or CLI error | Verify input file |

## Common Response Patterns

### Success Response

All successful operations return:
```json
{
  "success": true,
  // ... tool-specific data
  "error": null
}
```

### Error Response

All failed operations return:
```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE_CONSTANT",
  "details": {
    "original_error": "Technical details",
    "timestamp": "2024-01-01T00:00:00Z",
    // ... additional context
  }
}
```

## Usage Examples

### Basic Workflow

1. **Generate XML from prompt:**
```json
{
  "tool": "generate-drawio-xml",
  "arguments": {
    "prompt": "Create a simple flowchart with start, process, decision, and end nodes"
  }
}
```

2. **Save generated XML:**
```json
{
  "tool": "save-drawio-file",
  "arguments": {
    "xml_content": "<mxfile>...</mxfile>",
    "filename": "user-process-flow"
  }
}
```

3. **Convert to PNG:**
```json
{
  "tool": "convert-to-png", 
  "arguments": {
    "file_id": "uuid-from-save-operation"
  }
}
```

### AWS Architecture Example

```json
{
  "tool": "generate-drawio-xml",
  "arguments": {
    "prompt": "AWS 3-tier architecture with Application Load Balancer, Auto Scaling Group with EC2 instances, and RDS database. Include VPC with public and private subnets across two availability zones."
  }
}
```

### Error Handling Example

```json
{
  "success": false,
  "error": "Draw.io CLI not found. Please install @drawio/drawio-desktop-cli",
  "error_code": "CLI_NOT_FOUND",
  "details": {
    "original_error": "Command 'drawio' not found",
    "timestamp": "2024-01-01T12:00:00Z",
    "resolution": "Run: npm install -g @drawio/drawio-desktop-cli"
  }
}
```

---

# MCP Draw.io サーバー API ドキュメント

## 概要

MCP Draw.io サーバーは、Draw.io 図表の生成、保存、変換を行う3つのModel Context Protocol（MCP）ツールを提供します。このドキュメントでは、各ツールの包括的なAPI仕様、パラメータの詳細、戻り値、エラーコードを説明します。

## 目次

- [ツール概要](#ツール概要)
- [generate-drawio-xml](#generate-drawio-xml-1)
- [save-drawio-file](#save-drawio-file-1)
- [convert-to-png](#convert-to-png-1)
- [エラーコードリファレンス](#エラーコードリファレンス)
- [共通レスポンスパターン](#共通レスポンスパターン)
- [使用例](#使用例-1)

## ツール概要

| ツール名 | 目的 | 入力 | 出力 |
|-----------|---------|-------|--------|
| `generate-drawio-xml` | 自然言語からDraw.io XMLを生成 | テキストプロンプト | Draw.io XMLコンテンツ |
| `save-drawio-file` | XMLコンテンツを一時ファイルに保存 | XMLコンテンツ + オプションのファイル名 | ファイルIDとメタデータ |
| `convert-to-png` | Draw.ioファイルをPNG画像に変換 | ファイルIDまたはパス | PNGファイル情報 |

## generate-drawio-xml

Claude AIを使用して自然言語の説明からDraw.io XMLダイアグラムコンテンツを生成します。

### ツールスキーマ

```json
{
  "name": "generate-drawio-xml",
  "description": "自然言語の説明からDraw.io XMLダイアグラムを生成",
  "inputSchema": {
    "type": "object",
    "properties": {
      "prompt": {
        "type": "string",
        "description": "生成する図表の自然言語記述"
      }
    },
    "required": ["prompt"]
  }
}
```

### パラメータ

- **prompt** (string, 必須): 図表の自然言語記述
  - 空でない文字列である必要があります
  - フローチャート、AWSアーキテクチャ、ネットワーク図など、複雑な図表記述をサポート
  - 例: "ユーザー認証のフローチャートを作成", "ロードバランサー付きAWS 3層アーキテクチャ"

### レスポンス形式

```json
{
  "success": true,
  "xml_content": "<mxfile>...</mxfile>",
  "error": null
}
```

### レスポンスフィールド

- **success** (boolean): 操作が成功したかを示します
- **xml_content** (string): 生成されたDraw.io XMLコンテンツ（success=trueの場合のみ存在）
- **error** (string|null): 操作が失敗した場合のエラーメッセージ

## save-drawio-file

一意の識別子と自動クリーンアップ機能付きで、XMLコンテンツを一時ファイルに保存します。

### ツールスキーマ

```json
{
  "name": "save-drawio-file", 
  "description": "Draw.io XMLコンテンツを一時ファイルに保存",
  "inputSchema": {
    "type": "object",
    "properties": {
      "xml_content": {
        "type": "string",
        "description": "有効なDraw.io XMLコンテンツ"
      },
      "filename": {
        "type": "string",
        "description": "オプションのカスタムファイル名（提供されない場合はUUID生成）"
      }
    },
    "required": ["xml_content"]
  }
}
```

### パラメータ

- **xml_content** (string, 必須): 有効なDraw.io XMLコンテンツ
  - mxfileルート要素を含む有効なXML構造である必要があります
  - 保存前に検証されます
- **filename** (string, オプション): カスタムファイル名
  - 提供されない場合、UUIDが生成されます
  - ファイル拡張子は含めないでください（.drawioが自動追加されます）

### レスポンス形式

```json
{
  "success": true,
  "file_id": "uuid-string",
  "file_path": "/app/temp/uuid.drawio",
  "expires_at": "2024-01-01T12:00:00Z",
  "error": null
}
```

### レスポンスフィールド

- **success** (boolean): 操作が成功したかを示します
- **file_id** (string): 一意のファイル識別子
- **file_path** (string): 保存されたファイルのフルパス
- **expires_at** (string): ファイルが自動削除されるISOタイムスタンプ
- **error** (string|null): 操作が失敗した場合のエラーメッセージ

## convert-to-png

Draw.io CLIを使用してDraw.ioファイルをPNG画像に変換します。

### ツールスキーマ

```json
{
  "name": "convert-to-png",
  "description": "Draw.ioファイルをPNG画像に変換",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_id": {
        "type": "string",
        "description": "save-drawio-fileからのファイルID（推奨）"
      },
      "file_path": {
        "type": "string", 
        "description": "直接ファイルパス（file_idの代替）"
      }
    },
    "anyOf": [
      {"required": ["file_id"]},
      {"required": ["file_path"]}
    ]
  }
}
```

### パラメータ

- **file_id** (string, オプション): save-drawio-fileから返されたファイルID
  - セキュリティと検証のため推奨されるアプローチ
- **file_path** (string, オプション): 直接ファイルパス
  - 外部ファイル用のfile_idの代替
  - サーバーからアクセス可能である必要があります

### レスポンス形式

```json
{
  "success": true,
  "png_file_id": "uuid-string",
  "png_file_path": "/app/temp/uuid.png",
  "base64_content": "base64-encoded-image-data",
  "error": null
}
```

### レスポンスフィールド

- **success** (boolean): 操作が成功したかを示します
- **png_file_id** (string): 生成されたPNGの一意識別子
- **png_file_path** (string): 生成されたPNGファイルのフルパス
- **base64_content** (string): Base64エンコードされたPNG画像データ
- **error** (string|null): 操作が失敗した場合のエラーメッセージ

## エラーコードリファレンス

### LLMサービスエラー

| エラーコード | 説明 | 典型的な原因 | 解決方法 |
|------------|-------------|---------------|------------|
| `API_KEY_MISSING` | Claude APIキーが提供されていません | ANTHROPIC_API_KEYの欠落 | 環境変数を設定 |
| `CONNECTION_ERROR` | ネットワーク接続が失敗しました | ネットワーク/DNS問題 | 接続性を確認 |
| `RATE_LIMIT_ERROR` | APIレート制限を超過しました | リクエスト過多 | 待機して再試行 |
| `QUOTA_EXCEEDED` | APIクォータが枯渇しました | 月次/日次制限に到達 | プランをアップグレードまたは待機 |
| `INVALID_RESPONSE` | 予期しないAPIレスポンス | API変更または不正なリクエスト | リクエスト形式を確認 |
| `INVALID_XML` | 生成されたXMLが無効です | AI生成エラー | より明確なプロンプトで再試行 |
| `TIMEOUT_ERROR` | リクエストがタイムアウトしました | 低速ネットワークまたは複雑なリクエスト | 再試行またはプロンプトを簡素化 |
| `UNKNOWN_ERROR` | 予期しないエラーが発生しました | 様々な内部問題 | ログを確認して再試行 |

### ファイルサービスエラー

| エラーコード | 説明 | 典型的な原因 | 解決方法 |
|------------|-------------|---------------|------------|
| `FILE_NOT_FOUND` | 要求されたファイルが見つかりません | 無効なfile_idまたは期限切れファイル | file_idを確認または再生成 |
| `PERMISSION_DENIED` | ファイルアクセスが拒否されました | ファイルシステム権限 | ディレクトリ権限を確認 |
| `DISK_FULL` | ディスク容量不足 | ストレージクォータ超過 | 容量を解放 |
| `INVALID_PATH` | 無効なファイルパスが提供されました | 不正な形式のパスまたはセキュリティ違反 | 有効なファイルパスを使用 |

### 画像サービスエラー

| エラーコード | 説明 | 典型的な原因 | 解決方法 |
|------------|-------------|---------------|------------|
| `CLI_NOT_FOUND` | Draw.io CLIが利用できません | インストールの欠落 | @drawio/drawio-desktop-cliをインストール |
| `CLI_ERROR` | CLI実行が失敗しました | 無効な入力またはCLIバグ | 入力ファイルの有効性を確認 |
| `CONVERSION_FAILED` | PNG変換が失敗しました | 破損した入力またはCLIエラー | 入力ファイルを検証 |

## 共通レスポンスパターン

### 成功レスポンス

すべての成功した操作は以下を返します：
```json
{
  "success": true,
  // ... ツール固有のデータ
  "error": null
}
```

### エラーレスポンス

すべての失敗した操作は以下を返します：
```json
{
  "success": false,
  "error": "人間が読める形式のエラーメッセージ",
  "error_code": "ERROR_CODE_CONSTANT",
  "details": {
    "original_error": "技術的詳細",
    "timestamp": "2024-01-01T00:00:00Z",
    // ... 追加のコンテキスト
  }
}
```

## 使用例

### 基本ワークフロー

1. **プロンプトからXMLを生成:**
```json
{
  "tool": "generate-drawio-xml",
  "arguments": {
    "prompt": "開始、処理、判定、終了ノードを含むシンプルなフローチャートを作成"
  }
}
```

2. **生成されたXMLを保存:**
```json
{
  "tool": "save-drawio-file",
  "arguments": {
    "xml_content": "<mxfile>...</mxfile>",
    "filename": "user-process-flow"
  }
}
```

3. **PNGに変換:**
```json
{
  "tool": "convert-to-png", 
  "arguments": {
    "file_id": "uuid-from-save-operation"
  }
}
```

### AWSアーキテクチャの例

```json
{
  "tool": "generate-drawio-xml",
  "arguments": {
    "prompt": "Application Load Balancer、EC2インスタンスのAuto Scaling Group、RDSデータベースを含むAWS 3層アーキテクチャ。2つのアベイラビリティゾーンにまたがるパブリックおよびプライベートサブネットを持つVPCを含める。"
  }
}
```

### エラーハンドリングの例

```json
{
  "success": false,
  "error": "Draw.io CLIが見つかりません。@drawio/drawio-desktop-cliをインストールしてください",
  "error_code": "CLI_NOT_FOUND",
  "details": {
    "original_error": "Command 'drawio' not found",
    "timestamp": "2024-01-01T12:00:00Z",
    "resolution": "実行: npm install -g @drawio/drawio-desktop-cli"
  }
}
```

### Tool Schema

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

### Parameters

#### `prompt` (required)
- **Type**: `string`
- **Description**: Natural language description of the diagram to generate
- **Constraints**: 
  - Minimum length: 5 characters
  - Maximum length: 10,000 characters
  - Must be non-empty after trimming whitespace
- **Examples**:
  - `"Create a flowchart showing user login process"`
  - `"Generate an AWS architecture diagram with EC2, RDS, and S3"`
  - `"Draw a simple organizational chart with CEO, managers, and employees"`

### Response Format

```json
{
  "success": boolean,
  "xml_content": string | null,
  "error": string | null,
  "error_code": string | null,
  "timestamp": string
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the generation was successful |
| `xml_content` | `string \| null` | Valid Draw.io XML content (if successful) |
| `error` | `string \| null` | Human-readable error message (if failed) |
| `error_code` | `string \| null` | Machine-readable error code (if failed) |
| `timestamp` | `string` | ISO 8601 timestamp of the operation |

### Success Response Example

```json
{
  "success": true,
  "xml_content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<mxfile host=\"app.diagrams.net\" modified=\"2024-01-01T00:00:00.000Z\" agent=\"Claude\" version=\"22.1.11\">\n  <diagram name=\"Page-1\" id=\"abc123\">\n    <mxGraphModel dx=\"1422\" dy=\"794\" grid=\"1\" gridSize=\"10\" guides=\"1\" tooltips=\"1\" connect=\"1\" arrows=\"1\" fold=\"1\" page=\"1\" pageScale=\"1\" pageWidth=\"827\" pageHeight=\"1169\" math=\"0\" shadow=\"0\">\n      <root>\n        <mxCell id=\"0\" />\n        <mxCell id=\"1\" parent=\"0\" />\n        <!-- Diagram content -->\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>",
  "error": null,
  "error_code": null,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Error Response Example

```json
{
  "success": false,
  "xml_content": null,
  "error": "Invalid input: Prompt is too short (minimum 5 characters)",
  "error_code": "INVALID_INPUT",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Possible Error Codes

- `INVALID_INPUT` - Input validation failed
- `API_KEY_MISSING` - Anthropic API key not configured
- `CONNECTION_ERROR` - Network connection failed
- `RATE_LIMIT_ERROR` - API rate limit exceeded
- `QUOTA_EXCEEDED` - API quota exceeded
- `INVALID_RESPONSE` - Invalid response from Claude API
- `INVALID_XML` - Generated XML failed validation
- `TIMEOUT_ERROR` - Request timed out
- `UNKNOWN_ERROR` - Unexpected error occurred

## save-drawio-file

Saves Draw.io XML content to a temporary file and returns a file ID for future reference.

### Tool Schema

```json
{
  "name": "save-drawio-file",
  "description": "Save Draw.io XML content to a temporary file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "xml_content": {
        "type": "string",
        "description": "Valid Draw.io XML content to save",
        "minLength": 10
      },
      "filename": {
        "type": "string",
        "description": "Optional custom filename (without extension)",
        "maxLength": 100
      }
    },
    "required": ["xml_content"]
  }
}
```

### Parameters

#### `xml_content` (required)
- **Type**: `string`
- **Description**: Valid Draw.io XML content to save
- **Constraints**:
  - Minimum length: 10 characters
  - Must contain required Draw.io elements: `mxfile`, `mxGraphModel`, `root`
  - Must be valid XML structure
- **Validation**: Automatically validated for Draw.io XML structure

#### `filename` (optional)
- **Type**: `string`
- **Description**: Custom filename without extension (.drawio will be added automatically)
- **Constraints**:
  - Maximum length: 100 characters
  - Will be sanitized to remove invalid characters
  - If not provided, UUID-based filename will be generated
- **Examples**: `"my-diagram"`, `"user-flow-v2"`, `"aws-architecture"`

### Response Format

```json
{
  "success": boolean,
  "file_id": string | null,
  "file_path": string | null,
  "filename": string | null,
  "expires_at": string | null,
  "error": string | null,
  "error_code": string | null,
  "timestamp": string
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the save operation was successful |
| `file_id` | `string \| null` | Unique identifier for the saved file |
| `file_path` | `string \| null` | Absolute path to the saved file |
| `filename` | `string \| null` | Final filename used (including .drawio extension) |
| `expires_at` | `string \| null` | ISO 8601 timestamp when file will expire |
| `error` | `string \| null` | Human-readable error message (if failed) |
| `error_code` | `string \| null` | Machine-readable error code (if failed) |
| `timestamp` | `string` | ISO 8601 timestamp of the operation |

### Success Response Example

```json
{
  "success": true,
  "file_id": "abc123-def456-ghi789",
  "file_path": "/app/temp/my-diagram_abc123.drawio",
  "filename": "my-diagram_abc123.drawio",
  "expires_at": "2024-01-02T12:00:00.000Z",
  "error": null,
  "error_code": null,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Error Response Example

```json
{
  "success": false,
  "file_id": null,
  "file_path": null,
  "filename": null,
  "expires_at": null,
  "error": "Invalid XML content: missing required element 'mxfile'",
  "error_code": "INVALID_XML",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Possible Error Codes

- `INVALID_XML` - XML content validation failed
- `INVALID_FILENAME` - Filename validation failed
- `SERVICE_ERROR` - File service initialization failed
- `FILE_SERVICE_ERROR` - File operation failed
- `PERMISSION_DENIED` - Insufficient permissions
- `DISK_FULL` - Insufficient disk space
- `UNKNOWN_ERROR` - Unexpected error occurred

## convert-to-png

Converts a Draw.io file to PNG format using the Draw.io CLI. Supports both file ID (from save-drawio-file) and direct file path input.

### Tool Schema

```json
{
  "name": "convert-to-png",
  "description": "Convert Draw.io file to PNG image using Draw.io CLI",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_id": {
        "type": "string",
        "description": "File ID returned from save-drawio-file tool (recommended)"
      },
      "file_path": {
        "type": "string",
        "description": "Direct path to .drawio file (alternative to file_id)"
      }
    },
    "oneOf": [
      {"required": ["file_id"]},
      {"required": ["file_path"]}
    ]
  }
}
```

### Parameters

You must provide exactly one of the following parameters:

#### `file_id` (conditional)
- **Type**: `string`
- **Description**: File ID returned from the save-drawio-file tool
- **Recommended**: This is the preferred method as it ensures file validity
- **Example**: `"abc123-def456-ghi789"`

#### `file_path` (conditional)
- **Type**: `string`
- **Description**: Direct path to a .drawio file
- **Constraints**: Must be a valid path to an existing .drawio file
- **Example**: `"/path/to/diagram.drawio"`

### Response Format

```json
{
  "success": boolean,
  "png_file_id": string | null,
  "png_file_path": string | null,
  "base64_content": string | null,
  "error": string | null,
  "error_code": string | null,
  "cli_available": boolean,
  "fallback_message": string | null,
  "alternatives": object | null,
  "timestamp": string,
  "troubleshooting": object | null,
  "metadata": object | null
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the conversion was successful |
| `png_file_id` | `string \| null` | Unique identifier for the PNG file |
| `png_file_path` | `string \| null` | Absolute path to the PNG file |
| `base64_content` | `string \| null` | Base64 encoded PNG content (optional) |
| `error` | `string \| null` | Human-readable error message (if failed) |
| `error_code` | `string \| null` | Machine-readable error code (if failed) |
| `cli_available` | `boolean` | Whether Draw.io CLI is available |
| `fallback_message` | `string \| null` | Detailed fallback instructions (if CLI unavailable) |
| `alternatives` | `object \| null` | Alternative options when CLI is unavailable |
| `timestamp` | `string` | ISO 8601 timestamp of the operation |
| `troubleshooting` | `object \| null` | Troubleshooting information (if failed) |
| `metadata` | `object \| null` | Additional metadata about the operation |

### Success Response Example

```json
{
  "success": true,
  "png_file_id": "xyz789-abc123-def456",
  "png_file_path": "/app/temp/my-diagram_abc123.png",
  "base64_content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "error": null,
  "error_code": null,
  "cli_available": true,
  "fallback_message": null,
  "alternatives": null,
  "timestamp": "2024-01-01T12:00:00.000Z",
  "troubleshooting": null,
  "metadata": {
    "original_file_id": "abc123-def456-ghi789",
    "original_file_path": "/app/temp/my-diagram_abc123.drawio",
    "conversion_message": "Successfully converted using Draw.io CLI",
    "file_size_bytes": 1024,
    "expires_at": "2024-01-02T12:00:00.000Z"
  }
}
```

### Error Response Example (CLI Not Available)

```json
{
  "success": false,
  "png_file_id": null,
  "png_file_path": null,
  "base64_content": null,
  "error": "Draw.io CLI is not available for PNG conversion",
  "error_code": "CLI_NOT_AVAILABLE",
  "cli_available": false,
  "fallback_message": "Draw.io CLI is required for PNG conversion. Install it with: npm install -g @drawio/drawio-desktop-cli",
  "alternatives": {
    "manual_export": "Open the .drawio file in Draw.io Desktop and export as PNG manually",
    "web_version": "Use Draw.io web version at https://app.diagrams.net/ to open and export the file",
    "docker_solution": "Use the Docker container which includes Draw.io CLI pre-installed"
  },
  "timestamp": "2024-01-01T12:00:00.000Z",
  "troubleshooting": {
    "check_installation": "Run 'drawio --version' to check if CLI is installed",
    "install_command": "npm install -g @drawio/drawio-desktop-cli",
    "docker_alternative": "Use the provided Docker container for guaranteed CLI availability"
  },
  "metadata": {
    "original_file_id": "abc123-def456-ghi789",
    "original_file_path": "/app/temp/my-diagram_abc123.drawio"
  }
}
```

### Possible Error Codes

- `MISSING_PARAMETER` - Neither file_id nor file_path provided
- `CONFLICTING_PARAMETERS` - Both file_id and file_path provided
- `INVALID_FILE_ID` - File ID format is invalid
- `INVALID_FILE_PATH` - File path format is invalid
- `FILE_NOT_FOUND` - File does not exist or has expired
- `INVALID_FILE_TYPE` - File is not a .drawio file
- `CLI_NOT_AVAILABLE` - Draw.io CLI is not installed
- `CONVERSION_FAILED` - PNG conversion failed
- `IMAGE_SERVICE_ERROR` - Image service error
- `SERVICE_INITIALIZATION_ERROR` - Service initialization failed
- `UNKNOWN_ERROR` - Unexpected error occurred

## Error Codes Reference

### LLM Service Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| `API_KEY_MISSING` | Anthropic API key not configured | Missing ANTHROPIC_API_KEY environment variable | Set the API key in environment variables |
| `CONNECTION_ERROR` | Network connection failed | Network issues, firewall, DNS problems | Check network connectivity |
| `RATE_LIMIT_ERROR` | API rate limit exceeded | Too many requests in short time | Wait and retry, implement backoff |
| `QUOTA_EXCEEDED` | API quota exceeded | Monthly/daily quota reached | Check Anthropic account limits |
| `INVALID_RESPONSE` | Invalid response from Claude API | API returned unexpected format | Retry request, check API status |
| `INVALID_XML` | Generated XML failed validation | Claude generated invalid Draw.io XML | Retry with different prompt |
| `TIMEOUT_ERROR` | Request timed out | Long-running request exceeded timeout | Retry with shorter prompt |
| `UNKNOWN_ERROR` | Unexpected LLM service error | Various internal errors | Check logs, retry request |

### File Service Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| `FILE_NOT_FOUND` | File does not exist | Invalid file ID, file expired | Check file ID, regenerate if expired |
| `FILE_EXPIRED` | File has expired | File older than retention period | Regenerate and save new file |
| `INVALID_FILE_ID` | File ID format is invalid | Malformed file ID string | Use valid file ID from save operation |
| `PERMISSION_DENIED` | Insufficient file permissions | File system permission issues | Check container/process permissions |
| `DISK_FULL` | Insufficient disk space | Storage volume full | Free up disk space |
| `INVALID_FILENAME` | Filename validation failed | Invalid characters in filename | Use alphanumeric characters only |
| `FILE_TOO_LARGE` | File exceeds size limits | XML content too large | Reduce diagram complexity |
| `CLEANUP_ERROR` | File cleanup operation failed | Permission or lock issues | Check file system status |
| `UNKNOWN_ERROR` | Unexpected file service error | Various internal errors | Check logs, retry operation |

### Image Service Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| `CLI_NOT_AVAILABLE` | Draw.io CLI not installed | Missing Draw.io CLI installation | Install CLI or use Docker container |
| `CLI_EXECUTION_ERROR` | CLI execution failed | CLI crashed or returned error | Check CLI installation, file validity |
| `INVALID_INPUT_FILE` | Input file is invalid | Corrupted or invalid .drawio file | Regenerate the Draw.io file |
| `OUTPUT_FILE_ERROR` | Output file creation failed | Permission or disk space issues | Check permissions and disk space |
| `CONVERSION_TIMEOUT` | Conversion process timed out | Complex diagram or system load | Simplify diagram or retry |
| `UNSUPPORTED_FORMAT` | File format not supported | Non-.drawio file provided | Ensure file has .drawio extension |
| `UNKNOWN_ERROR` | Unexpected image service error | Various internal errors | Check logs, retry operation |

### General MCP Server Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| `INVALID_REQUEST` | Request format is invalid | Malformed MCP request | Check request format |
| `METHOD_NOT_FOUND` | MCP method not found | Invalid tool name | Use valid tool names |
| `INVALID_PARAMETERS` | Parameter validation failed | Missing or invalid parameters | Check parameter requirements |
| `TOOL_NOT_FOUND` | Requested tool not found | Invalid tool name in request | Use valid tool names |
| `TOOL_EXECUTION_ERROR` | Tool execution failed | Various tool-specific errors | Check tool-specific error details |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | System overload or maintenance | Retry after delay |
| `CONFIGURATION_ERROR` | Server configuration error | Invalid environment variables | Check server configuration |
| `INITIALIZATION_ERROR` | Server initialization failed | Startup configuration issues | Check server logs and config |
| `UNKNOWN_ERROR` | Unexpected server error | Various internal errors | Check server logs |

## Common Response Patterns

### Success Response Pattern

All successful tool responses follow this pattern:

```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00.000Z",
  // Tool-specific success fields
  "error": null,
  "error_code": null
}
```

### Error Response Pattern

All error responses follow this pattern:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2024-01-01T12:00:00.000Z",
  // Tool-specific null fields
}
```

### Timestamp Format

All timestamps use ISO 8601 format with UTC timezone:
- Format: `YYYY-MM-DDTHH:mm:ss.sssZ`
- Example: `2024-01-01T12:00:00.000Z`

## Usage Examples

### Complete Workflow Example

```javascript
// 1. Generate Draw.io XML
const generateResult = await mcpClient.callTool("generate-drawio-xml", {
  prompt: "Create a simple user login flowchart with start, login form, validation, success, and error states"
});

if (generateResult.success) {
  console.log("Generated XML successfully");
  
  // 2. Save the XML to a file
  const saveResult = await mcpClient.callTool("save-drawio-file", {
    xml_content: generateResult.xml_content,
    filename: "user-login-flow"
  });
  
  if (saveResult.success) {
    console.log(`File saved with ID: ${saveResult.file_id}`);
    
    // 3. Convert to PNG
    const convertResult = await mcpClient.callTool("convert-to-png", {
      file_id: saveResult.file_id
    });
    
    if (convertResult.success) {
      console.log(`PNG created: ${convertResult.png_file_path}`);
      console.log(`Base64 content available: ${convertResult.base64_content ? 'Yes' : 'No'}`);
    } else {
      console.error(`PNG conversion failed: ${convertResult.error}`);
      if (!convertResult.cli_available) {
        console.log(`Fallback: ${convertResult.fallback_message}`);
      }
    }
  } else {
    console.error(`File save failed: ${saveResult.error}`);
  }
} else {
  console.error(`XML generation failed: ${generateResult.error}`);
}
```

### Error Handling Example

```javascript
async function handleToolCall(toolName, params) {
  try {
    const result = await mcpClient.callTool(toolName, params);
    
    if (result.success) {
      return result;
    } else {
      // Handle specific error codes
      switch (result.error_code) {
        case 'API_KEY_MISSING':
          throw new Error('Please configure your Anthropic API key');
        case 'RATE_LIMIT_ERROR':
          console.log('Rate limited, waiting 60 seconds...');
          await new Promise(resolve => setTimeout(resolve, 60000));
          return handleToolCall(toolName, params); // Retry
        case 'CLI_NOT_AVAILABLE':
          console.log('Draw.io CLI not available, alternatives:');
          console.log(result.alternatives);
          throw new Error(result.fallback_message);
        default:
          throw new Error(`Tool failed: ${result.error} (${result.error_code})`);
      }
    }
  } catch (error) {
    console.error(`Tool call failed: ${error.message}`);
    throw error;
  }
}
```

### Batch Processing Example

```javascript
async function processDiagramBatch(prompts) {
  const results = [];
  
  for (const [index, prompt] of prompts.entries()) {
    try {
      console.log(`Processing diagram ${index + 1}/${prompts.length}`);
      
      // Generate XML
      const xmlResult = await mcpClient.callTool("generate-drawio-xml", { prompt });
      if (!xmlResult.success) {
        results.push({ index, error: xmlResult.error, step: 'generate' });
        continue;
      }
      
      // Save file
      const saveResult = await mcpClient.callTool("save-drawio-file", {
        xml_content: xmlResult.xml_content,
        filename: `diagram-${index + 1}`
      });
      if (!saveResult.success) {
        results.push({ index, error: saveResult.error, step: 'save' });
        continue;
      }
      
      // Convert to PNG
      const pngResult = await mcpClient.callTool("convert-to-png", {
        file_id: saveResult.file_id
      });
      
      results.push({
        index,
        success: pngResult.success,
        file_id: saveResult.file_id,
        png_file_id: pngResult.png_file_id,
        error: pngResult.success ? null : pngResult.error
      });
      
    } catch (error) {
      results.push({ index, error: error.message, step: 'exception' });
    }
  }
  
  return results;
}
```

## Performance Considerations

### Caching

The `generate-drawio-xml` tool includes intelligent caching:
- Identical prompts return cached results
- Cache TTL: 1 hour (configurable)
- Cache size limit: 100 entries (configurable)
- Automatic cleanup of expired entries

### File Expiration

Temporary files have automatic expiration:
- Default expiration: 24 hours
- Automatic cleanup runs every hour
- Files are cleaned up when expired or on server restart

### Rate Limiting

Be aware of Anthropic API rate limits:
- Implement exponential backoff for rate limit errors
- Monitor your API usage and quotas
- Consider caching for repeated requests

### Resource Usage

- Memory: ~256MB minimum, 512MB recommended
- Disk: Temporary files require storage space
- CPU: PNG conversion is CPU-intensive
- Network: Outbound HTTPS for Claude API

## Security Considerations

### Input Validation

All tools perform comprehensive input validation:
- Prompt sanitization removes control characters
- XML validation ensures proper structure
- Filename sanitization prevents path traversal
- File type validation ensures .drawio files only

### File Security

- Files are stored in isolated temporary directories
- Automatic cleanup prevents disk space exhaustion
- Non-root container execution
- No persistent storage of sensitive data

### API Security

- API keys are never logged or exposed
- All external API calls use HTTPS
- Error messages don't expose internal details
- Request/response logging excludes sensitive data

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure `ANTHROPIC_API_KEY` environment variable is set
   - Verify API key is valid and has sufficient quota

2. **Draw.io CLI Issues**
   - Install CLI: `npm install -g @drawio/drawio-desktop-cli`
   - Verify installation: `drawio --version`
   - Use Docker container for guaranteed CLI availability

3. **File Not Found Errors**
   - Check if file has expired (24-hour default)
   - Verify file ID is correct and complete
   - Regenerate file if necessary

4. **Permission Errors**
   - Ensure container has write permissions to temp directory
   - Check disk space availability
   - Verify non-root user has appropriate permissions

### Debug Information

Enable debug logging by setting environment variables:
```bash
LOG_LEVEL=DEBUG
ANTHROPIC_LOG_LEVEL=DEBUG
```

### Support Resources

- Check server logs for detailed error information
- Use the validation tools provided in the test suite
- Refer to the troubleshooting sections in individual tool responses
- Review the installation and configuration guides

---

*This API documentation is automatically generated from the source code and is kept up-to-date with each release.*