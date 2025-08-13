# AI図表生成MCPサーバー

Claude AIを使用して自然言語の説明からDraw.io図表を生成するModel Context Protocol（MCP）サーバーです。このサーバーは、Express.jsウェブアプリケーションのコア機能を軽量でコンテナ化されたMCPサーバーに移行し、Claude Codeやその他のMCPクライアントと互換性があります。

## 概要

このMCPサーバーは、図表生成のための3つの主要ツールを提供します：
- 自然言語プロンプトから**Draw.io XMLを生成**
- 自動クリーンアップ機能付きの一時ファイルに**図表を保存**
- Draw.io CLIを使用して**Draw.ioファイルをPNG画像に変換**

このサーバーは、Claude Codeとのシームレスな統合を目的として設計されており、自然言語による対話を通じて即座に図表生成機能を提供します。

## 機能

### コア機能
- 🎨 **自然言語から図表へ**: 説明を有効なDraw.io XMLに変換
- 💾 **ファイル管理**: 自動クリーンアップ機能付きの一時ファイルストレージ
- 🖼️ **画像生成**: Draw.io CLIを使用したPNGエクスポート
- 🔄 **キャッシュ**: パフォーマンス向上のためのインテリジェントなレスポンスキャッシュ
- 🛡️ **エラーハンドリング**: 包括的なエラー分類とグレースフルデグラデーション

### アーキテクチャ
- 🐍 **Python 3.10+**: async/awaitサポートを備えたモダンPython
- 📦 **コンテナ化**: 簡単デプロイのためのDocker対応
- 🔧 **MCPプロトコル**: Model Context Protocol仕様への完全準拠
- ⚡ **パフォーマンス**: 低レイテンシとリソース効率の最適化
- 🧪 **テスト済み**: 包括的なテストカバレッジ（単体、統合、エンドツーエンド）

## クイックスタート

### Docker（推奨）

1. **Docker Composeでビルドと実行:**
```bash
cd mcp-server
docker-compose up --build
```

2. **APIキーを設定:**
```bash
export ANTHROPIC_API_KEY=your-claude-api-key-here
```

### 手動インストール

1. **前提条件:**
```bash
# Python 3.10+
python --version

# Draw.io CLI（PNG変換用）
npm install -g @drawio/drawio-desktop-cli
```

2. **セットアップ:**
```bash
cd mcp-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **環境設定:**
```bash
cp .env.example .env
# .envを編集してANTHROPIC_API_KEYを追加
```

4. **サーバーを実行:**
```bash
python -m src.server
```

## MCPツール

### 1. generate-drawio-xml
自然言語の説明からDraw.io XML図表を生成します。

**パラメータ:**
- `prompt` (string): 図表の自然言語記述

**レスポンス:**
```json
{
  "success": true,
  "xml_content": "<mxfile>...</mxfile>",
  "error": null
}
```

### 2. save-drawio-file
一意な識別子を持つ一時ファイルにXMLコンテンツを保存します。

**パラメータ:**
- `xml_content` (string): 有効なDraw.io XMLコンテンツ
- `filename` (string, オプション): カスタムファイル名（提供されない場合はUUIDが生成されます）

**レスポンス:**
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
Draw.io CLIを使用してDraw.ioファイルをPNG画像に変換します。

**パラメータ:**
- `file_id` (string): save-drawio-fileからのファイルID
- `file_path` (string, 代替): 直接ファイルパス

**レスポンス:**
```json
{
  "success": true,
  "png_file_id": "uuid-string",
  "png_file_path": "/app/temp/uuid.png",
  "base64_content": "base64-encoded-image-data",
  "error": null
}
```

## Claude Codeとの統合

### Claude Codeでの設定

1. **MCPサーバー設定を追加:**
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

2. **会話での使用:**
```
ログイン、検証、エラーハンドリングのステップを含むユーザー認証プロセスのフローチャートを作成してください。
```

Claude Codeが自動的にMCPサーバーを使用して図表を生成し表示します。

## 開発

### テスト

```bash
# 全テストを実行
pytest

# カバレッジ付きで実行
pytest --cov=src --cov-report=html

# 特定のテストカテゴリを実行
pytest tests/unit/          # 単体テスト
pytest tests/integration/   # 統合テスト
pytest tests/container/     # コンテナテスト
```

### コード品質

```bash
# コードフォーマット
black src/ tests/
isort src/ tests/

# 型チェック
mypy src/

# リンティング
flake8 src/ tests/
```

### Docker開発

```bash
# 最適化されたイメージをビルド
docker build -f Dockerfile.optimized -t draw-aio-mcp:latest .

# 開発設定で実行
docker-compose -f docker-compose.dev.yml up

# コンテナでテストを実行
make test-container
```

## 設定

### 環境変数

| 変数 | 説明 | デフォルト | 必須 |
|------|------|-----------|------|
| `ANTHROPIC_API_KEY` | Claude APIキー | - | はい |
| `TEMP_DIR` | 一時ファイルディレクトリ | `./temp` | いいえ |
| `DRAWIO_CLI_PATH` | Draw.io CLI実行可能ファイルパス | `drawio` | いいえ |
| `CACHE_TTL` | LLMレスポンスキャッシュTTL（秒） | `3600` | いいえ |
| `MAX_CACHE_SIZE` | 最大キャッシュエントリ数 | `100` | いいえ |
| `FILE_EXPIRY_HOURS` | 一時ファイル有効期限 | `24` | いいえ |
| `LOG_LEVEL` | ログレベル | `INFO` | いいえ |

### コンテナリソース

**最小要件:**
- メモリ: 256MB
- CPU: 0.5コア
- ストレージ: 1GB（一時ファイル用）

**推奨:**
- メモリ: 512MB
- CPU: 1コア
- ストレージ: 2GB

## プロジェクト構造

```
mcp-server/
├── src/                           # ソースコード
│   ├── __init__.py
│   ├── server.py                  # メインMCPサーバー実装
│   ├── config.py                  # 設定管理
│   ├── tools.py                   # MCPツール実装
│   ├── llm_service.py            # Claude AI統合
│   ├── file_service.py           # ファイル管理サービス
│   ├── image_service.py          # PNG生成サービス
│   ├── exceptions.py             # カスタム例外クラス
│   └── health.py                 # ヘルスチェックエンドポイント
├── tests/                        # テストスイート
│   ├── unit/                     # 単体テスト
│   ├── integration/              # 統合テスト
│   ├── container/                # コンテナテスト
│   └── fixtures/                 # テストデータとユーティリティ
├── docker/                       # Docker設定
│   ├── Dockerfile                # 標準Dockerfile
│   ├── Dockerfile.optimized      # 本番最適化イメージ
│   └── docker-compose.*.yml      # 各種デプロイ設定
├── docs/                         # ドキュメント
│   ├── API_DOCUMENTATION.md      # 詳細APIリファレンス
│   ├── DEVELOPER_GUIDE.md        # 開発ガイドライン
│   └── INSTALLATION_GUIDE.md     # セットアップ手順
├── deploy/                       # デプロイスクリプト
├── monitoring/                   # 監視設定
├── pyproject.toml               # プロジェクト設定
├── requirements.txt             # 本番依存関係
├── requirements-dev.txt         # 開発依存関係
├── Makefile                     # ビルド自動化
└── README.md                    # このファイル
```

## デプロイ

### 本番デプロイ

```bash
# 本番イメージをビルド
make build-production

# リソース制限付きでデプロイ
docker-compose -f docker-compose.prod.yml up -d

# ヘルスチェック
curl http://localhost:8000/health
```

### スケーリング

サーバーはステートレスで水平スケーリングをサポートします：

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

## トラブルシューティング

### よくある問題

1. **Draw.io CLIが見つからない:**
   ```bash
   npm install -g @drawio/drawio-desktop-cli
   ```

2. **APIキーの問題:**
   ```bash
   # キー形式を確認
   echo $ANTHROPIC_API_KEY | grep "^sk-ant-"
   ```

3. **コンテナメモリの問題:**
   ```bash
   # コンテナメモリを増加
   docker run -m 1g draw-aio-mcp:latest
   ```

### ヘルスチェック

サーバーは包括的な健康監視を提供します：

- **GET /health** - 基本的な健康状態
- **GET /health/ready** - 準備状況チェック（全サービス初期化済み）
- **GET /health/live** - 生存チェック（サーバー応答性）

### ログ

```bash
# サーバーログを表示
docker logs mcp-server

# リアルタイムでログを追跡
docker logs -f mcp-server

# エラーログをフィルタ
docker logs mcp-server 2>&1 | grep ERROR
```

## 貢献

1. リポジトリをフォーク
2. 機能ブランチを作成: `git checkout -b feature/amazing-feature`
3. 変更をコミット: `git commit -m 'Add amazing feature'`
4. ブランチにプッシュ: `git push origin feature/amazing-feature`
5. プルリクエストを開く

### 開発ガイドライン

- PEP 8スタイルガイドラインに従う
- 新機能には包括的なテストを追加
- API変更時はドキュメントを更新
- 全関数に型ヒントを使用
- Dockerビルドが通ることを確認

## Express.jsからの移行

このMCPサーバーは、元のExpress.jsウェブアプリケーションからコア機能を移行しています：

### 移行済みコンポーネント
- ✅ **LLMService**: キャッシュ機能付きClaude AI統合
- ✅ **FileService**: クリーンアップ機能付き一時ファイル管理
- ✅ **ImageService**: PNG生成のためのDraw.io CLI統合
- ✅ **エラーハンドリング**: 包括的なエラー分類
- ✅ **パフォーマンス**: レスポンスキャッシュとリソース管理

### 新機能
- 🆕 **MCPプロトコル**: Model Context Protocolへの完全準拠
- 🆕 **コンテナ対応**: 最適化されたDockerデプロイ
- 🆕 **Claude Code統合**: Claude Codeとのシームレスな統合
- 🆕 **強化された監視**: ヘルスチェックと可観測性

## ライセンス

本プロジェクトはデュアルライセンスです：

### 個人・非商用利用
個人、教育、研究、非商用利用については、**MITライセンス**でライセンスされています。詳細は[LICENSE-MIT](LICENSE-MIT)を参照してください。

### 商用利用
商用利用には別途**商用ライセンス**が必要です。商用利用には以下が含まれます：
- 年間売上1万ドル超の営利組織での利用
- 商用製品・サービスへの組み込み
- 商用クラウドサービスでの展開
- 収益を生成するコンサルティングサービス

**商用ライセンスの特典:**
- ✅ 商用利用権
- ✅ 優先技術サポート
- ✅ ソフトウェア更新・パッチ
- ✅ カスタマイズオプション
- ✅ 法的コンプライアンス保証

**商用ライセンスの取得:**
- 📧 連絡先: [your-email@domain.com]
- 📄 詳細: [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL)で詳細条件を確認
- 🤝 カスタムライセンス契約も対応可能

**ライセンス概要:** [LICENSE](LICENSE) | **MIT条項:** [LICENSE-MIT](LICENSE-MIT) | **商用条項:** [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL)

## ドキュメントファイル

このリポジトリには、Markdown形式の包括的なドキュメントが含まれています：

### ルートドキュメント
- [README.md](README.md) - メインプロジェクトドキュメント（英語）
- [README_ja.md](README_ja.md) - メインプロジェクトドキュメント（日本語）
- [CLAUDE.md](CLAUDE.md) - Claude Code統合ガイダンス

### MCPサーバードキュメント
- [mcp-server/DEPLOYMENT.md](mcp-server/DEPLOYMENT.md) - デプロイメントガイド（英語/日本語）
- [mcp-server/MCP_MIGRATION_SUMMARY.md](mcp-server/MCP_MIGRATION_SUMMARY.md) - 移行概要（英語/日本語）

#### コアドキュメント (`mcp-server/docs/`)
- [API_DOCUMENTATION.md](mcp-server/docs/API_DOCUMENTATION.md) - 完全なAPIリファレンス（英語/日本語）
- [DEVELOPER_GUIDE.md](mcp-server/docs/DEVELOPER_GUIDE.md) - 開発ガイドライン（英語/日本語）
- [INSTALLATION_GUIDE.md](mcp-server/docs/INSTALLATION_GUIDE.md) - インストール手順（英語/日本語）
- [MCP_SERVER_USAGE_GUIDE.md](mcp-server/docs/MCP_SERVER_USAGE_GUIDE.md) - 使用ガイド（英語/日本語）
- [README.md](mcp-server/docs/README.md) - ドキュメント概要（英語/日本語）

#### 統合・テスト (`mcp-server/docs/`)
- [CLAUDE_CODE_INTEGRATION.md](mcp-server/docs/CLAUDE_CODE_INTEGRATION.md) - Claude Code統合（英語/日本語）
- [MCP_CLIENT_INTEGRATION_TESTING.md](mcp-server/docs/MCP_CLIENT_INTEGRATION_TESTING.md) - 統合テスト（英語/日本語）

#### 技術ドキュメント (`mcp-server/docs/`)
- [API_KEY_VALIDATION.md](mcp-server/docs/API_KEY_VALIDATION.md) - APIキー検証（英語/日本語）
- [DEPENDENCY_CHECKING.md](mcp-server/docs/DEPENDENCY_CHECKING.md) - 依存関係チェック（英語/日本語）
- [PROTOCOL_VERSION_VALIDATION.md](mcp-server/docs/PROTOCOL_VERSION_VALIDATION.md) - プロトコル検証（英語/日本語）
- [STANDARD_MCP_PATTERNS.md](mcp-server/docs/STANDARD_MCP_PATTERNS.md) - MCPパターン（英語/日本語）

### テストドキュメント
- [mcp-server/tests/INTEGRATION_TEST_SUMMARY.md](mcp-server/tests/INTEGRATION_TEST_SUMMARY.md) - 統合テスト概要（英語/日本語）
- [mcp-server/tests/UNIT_TEST_SUMMARY.md](mcp-server/tests/UNIT_TEST_SUMMARY.md) - ユニットテスト概要（英語/日本語）
- [mcp-server/tests/container/TASK_17_COMPLETION_SUMMARY.md](mcp-server/tests/container/TASK_17_COMPLETION_SUMMARY.md) - コンテナテスト完了

### ソースドキュメント
- [mcp-server/src/README_TOOL.md](mcp-server/src/README_TOOL.md) - ツール実装ガイド（英語/日本語）

### インフラストラクチャ・例
- [mcp-server/infrastructure/examples/sample-project/README.md](mcp-server/infrastructure/examples/sample-project/README.md) - サンプルプロジェクト
- [mcp-server/.pytest_cache/README.md](mcp-server/.pytest_cache/README.md) - Pytestキャッシュ情報

### パフォーマンス・レポート
- [mcp-server/reports/benchmarks/performance-results.md](mcp-server/reports/benchmarks/performance-results.md) - パフォーマンスベンチマーク

### プロジェクト仕様
- [.kiro/specs/mcp-server-migration/design.md](.kiro/specs/mcp-server-migration/design.md) - 移行設計
- [.kiro/specs/mcp-server-migration/requirements.md](.kiro/specs/mcp-server-migration/requirements.md) - 要件仕様
- [.kiro/specs/mcp-server-migration/tasks.md](.kiro/specs/mcp-server-migration/tasks.md) - タスク分解

## サポート

- **課題**: [GitHub Issues](https://github.com/your-org/draw-aio-mcp/issues)
- **ドキュメント**: [docs/](docs/)
- **APIリファレンス**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)