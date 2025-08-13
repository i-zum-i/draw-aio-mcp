# MCP Protocol Version Validation Guide

This document describes the MCP server protocol version validation process and ensuring compatibility with the official MCP specification.

---

# MCP プロトコルバージョン検証ガイド

このドキュメントは、MCPサーバーのプロトコルバージョン検証プロセスと、公式MCP仕様との互換性確保について説明します。

## Overview

Model Context Protocol (MCP) is a standardized communication protocol between AI assistants and tools. This project ensures compatibility with Claude Code and other MCP clients by fully complying with the official MCP specification.

## 概要

Model Context Protocol (MCP) は、AIアシスタントとツール間の標準化された通信プロトコルです。このプロジェクトでは、公式MCP仕様に完全準拠することで、Claude Codeやその他のMCPクライアントとの互換性を保証しています。

## プロトコルバージョン

### 現在の設定

- **サーバープロトコルバージョン**: `2025-06-18` (最新)
- **公式MCP最新バージョン**: `2025-06-18`
- **公式MCPデフォルトバージョン**: `2025-03-26`

### サポートされているバージョン

1. **2025-06-18** (最新) - ✅ 推奨
2. **2025-03-26** (デフォルト) - ✅ サポート
3. **2024-11-05** (レガシー) - ⚠️ 非推奨

## 検証ツール

### 1. プロトコルバージョン検証スクリプト

```bash
python validate_protocol_version.py
```

**機能:**
- 公式MCPライブラリとの比較
- プロトコルバージョンの形式検証
- 互換性レベルの評価
- プロトコルネゴシエーションテスト

**出力例:**
```
🔍 MCP プロトコルバージョン検証を開始...
============================================================
📋 公式MCPプロトコルバージョン:
   最新バージョン: 2025-06-18
   デフォルトバージョン: 2025-03-26

🖥️ サーバー設定:
   サーバー名: drawio-mcp-server
   サーバーバージョン: 1.0.0
   プロトコルバージョン: 2025-06-18

📊 評価結果:
   互換性レベル: EXCELLENT
   ステータス: ✅ 最新のプロトコルバージョンを使用中
   スコア: 100/100
```

### 2. MCP互換性チェックスクリプト

```bash
python check_mcp_compatibility.py
```

**機能:**
- プロトコルバージョン準拠性
- サーバー機能の検証
- ツール定義の妥当性チェック
- エラーハンドリングの検証

**出力例:**
```
📊 5. 全体評価
   総合スコア: 100.0/100
   評価レベル: EXCELLENT
   ステータス: ✅ 完全にMCP仕様に準拠しています
```

## 検証項目

### 1. プロトコルバージョン検証

- **バージョン形式**: YYYY-MM-DD形式の検証
- **公式バージョンとの比較**: 最新・デフォルトバージョンとの照合
- **サポート状況**: 既知のサポートされているバージョンかの確認
- **互換性レベル**: EXCELLENT/GOOD/DEPRECATED/UNKNOWNの評価

### 2. プロトコルネゴシエーション

- **初期化リクエスト**: 各プロトコルバージョンでの初期化パラメータ作成
- **成功率**: 複数バージョンでのネゴシエーション成功率
- **エラーハンドリング**: 不正なバージョンでの適切なエラー処理

### 3. サーバー機能準拠性

- **メタデータ**: サーバー名・バージョンの定義確認
- **ツール定義**: MCPツールの適切な定義
- **スキーマ検証**: JSON Schemaの妥当性確認

### 4. メッセージ形式準拠性

- **JSON-RPC 2.0**: 標準メッセージ形式への準拠
- **コンテンツタイプ**: TextContentの適切な使用
- **エラーレスポンス**: 標準エラー形式の実装

## 設定管理

### プロトコルバージョンの更新

プロトコルバージョンは `src/config.py` で管理されています：

```python
@dataclass
class MCPServerConfig:
    # Additional metadata
    server_name: str = "mcp-drawio-server"
    server_version: str = "1.0.0"
    protocol_version: str = "2025-06-18"  # Updated to latest MCP protocol version
```

### 環境変数での設定

将来的には環境変数での設定も可能です：

```bash
export MCP_PROTOCOL_VERSION="2025-06-18"
```

## 将来の互換性対応

### 1. バージョン監視

- 公式MCPライブラリの定期的な更新チェック
- 新しいプロトコルバージョンのリリース監視
- 非推奨バージョンの警告システム

### 2. 自動更新プロセス

```bash
# 最新バージョンの確認
python -c "from mcp.types import LATEST_PROTOCOL_VERSION; print(LATEST_PROTOCOL_VERSION)"

# 設定の自動更新（将来実装予定）
python update_protocol_version.py --to-latest
```

### 3. 後方互換性

- 複数プロトコルバージョンのサポート
- 適切なフォールバック機能
- クライアント要求に応じたバージョンネゴシエーション

## テスト自動化

### CI/CDパイプライン統合

```yaml
# .github/workflows/mcp-validation.yml
name: MCP Protocol Validation
on: [push, pull_request]
jobs:
  validate-protocol:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Validate Protocol Version
        run: python validate_protocol_version.py
      - name: Check MCP Compatibility
        run: python check_mcp_compatibility.py
```

### 定期実行

```bash
# crontabでの定期実行例
0 9 * * 1 cd /path/to/mcp-server && python validate_protocol_version.py
```

## トラブルシューティング

### よくある問題

#### 1. プロトコルバージョンが古い

**症状:**
```
⚠️ 古いプロトコルバージョンを使用中 - 更新を推奨
互換性レベル: DEPRECATED
```

**解決方法:**
1. `src/config.py`のprotocol_versionを最新バージョンに更新
2. サーバーを再起動
3. 検証スクリプトで確認

#### 2. MCPライブラリのバージョン不整合

**症状:**
```
❌ MCP ライブラリのインポートに失敗
```

**解決方法:**
```bash
pip install --upgrade mcp[cli]>=1.2.0
```

#### 3. プロトコルネゴシエーション失敗

**症状:**
```
成功率: 66.7% (2/3)
```

**解決方法:**
1. MCPライブラリの更新
2. プロトコルバージョンの確認
3. 初期化パラメータの検証

## 参考資料

### 公式ドキュメント

- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)

### 関連ファイル

- `src/config.py` - サーバー設定
- `src/server.py` - MCPサーバー実装
- `validate_protocol_version.py` - プロトコルバージョン検証
- `check_mcp_compatibility.py` - 互換性チェック
- `test_protocol_version_validation.py` - 詳細テストスイート
- `test_mcp_protocol_compatibility.py` - 互換性テストスイート

## 更新履歴

### 2024-01-13
- プロトコルバージョンを2025-06-18に更新
- 包括的な検証ツールを実装
- 互換性チェック機能を追加
- ドキュメントを作成

### 今後の予定
- 環境変数での設定サポート
- 自動更新機能の実装
- CI/CD統合の強化
- 監視・アラート機能の追加