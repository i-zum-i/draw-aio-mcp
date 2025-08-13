# MCP Draw.io サーバー ドキュメント

## 概要

MCP Draw.io サーバーのドキュメントへようこそ。このサーバーは、Model Context Protocol（MCP）を通じてDraw.ioを使用した自然言語による図表生成を可能にし、Claude Codeから直接プロフェッショナルな図表を簡単に作成できます。

## クイックリンク

### はじめに
- 🚀 [インストールガイド](INSTALLATION_GUIDE.md) - 完全なセットアップ手順
- 📖 [使用ガイド](MCP_SERVER_USAGE_GUIDE.md) - サーバーの使用方法
- 🔧 [Claude Code統合](CLAUDE_CODE_INTEGRATION.md) - Claude Codeとの統合

### 技術ドキュメント
- 📋 [APIドキュメント](API_DOCUMENTATION.md) - サーバーAPIとツールリファレンス
- 🏗️ [アーキテクチャ概要](../DEPLOYMENT.md) - システムアーキテクチャと設計
- 🐳 [Dockerガイド](../docker/README.md) - コンテナデプロイメント

### テストと開発
- 🧪 [テストガイド](../tests/README.md) - テスト実行と検証
- 🔍 [トラブルシューティング](TROUBLESHOOTING.md) - 一般的な問題と解決策
- 🛠️ [開発者ガイド](DEVELOPER_GUIDE.md) - 貢献と開発

## MCP Draw.io サーバーとは？

MCP Draw.io サーバーは、3つの主要機能を提供するコンテナ化されたサービスです：

1. **自然言語から図表へ**: テキスト記述をDraw.io XML図表に変換
2. **ファイル管理**: 自動クリーンアップ機能付きの図表ファイル保存・管理
3. **画像変換**: Draw.io CLIを使用してDraw.ioファイルをPNG画像に変換

### 主要機能

- ✅ **自然言語処理**: 図表を平易な日本語で記述
- ✅ **複数の図表タイプ**: フローチャート、AWSアーキテクチャ、データベーススキーマなど
- ✅ **プロフェッショナル出力**: 高品質なDraw.io互換図表
- ✅ **画像エクスポート**: Draw.io CLIによるPNG変換
- ✅ **コンテナ化**: Dockerによる簡単デプロイメント
- ✅ **MCP互換**: Claude Codeとのシームレス連携
- ✅ **セキュア**: 非root実行、一時ファイル自動クリーンアップ
- ✅ **スケーラブル**: リソース制限と水平スケーリング対応

## クイックスタート

### 1. 前提条件
- DockerとDocker Compose
- Anthropic APIキー
- MCP対応のClaude Code

### 2. インストール
```bash
# リポジトリをクローン
git clone <repository-url>
cd mcp-server

# 環境設定
cp .env.example .env
# .envを編集してANTHROPIC_API_KEYを追加

# サーバー起動
docker-compose up --build
```

### 3. Claude Code設定
MCP設定に以下を追加：
```json
{
  "mcpServers": {
    "drawio-server": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "--env-file", "/path/to/.env", "mcp-drawio-server"]
    }
  }
}
```

### 4. 図表作成開始
```
ユーザー: ユーザー登録プロセスを示すフローチャートを作成してください

Claude: ユーザー登録プロセスのフローチャートを作成します。
[MCPツールを使用して生成、保存、オプションでPNGに変換]
```

## 利用可能なツール

### generate-drawio-xml
自然言語記述をDraw.io XML図表に変換します。

**使用例:**
- "ALB、EC2、RDSを含むAWSアーキテクチャを作成"
- "ECサイト用のデータベーススキーマを設計"
- "CI/CDパイプラインのフローチャートを作成"

### save-drawio-file
生成されたXMLコンテンツを一意のIDを持つ一時ファイルに保存します。

**機能:**
- UUIDによる自動ファイル命名
- 設定可能な有効期限
- メタデータ追跡

### convert-to-png
Draw.io CLIを使用してDraw.ioファイルをPNG画像に変換します。

**機能:**
- 高品質画像出力
- Base64エンコーディングオプション
- フォールバックエラーハンドリング

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claude Code   │───▶│  MCP Draw.io    │───▶│   Claude API    │
│                 │    │     Server      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Draw.io CLI   │
                       │  (PNG Export)   │
                       └─────────────────┘
```

## Documentation Structure

### User Guides
- **[Installation Guide](INSTALLATION_GUIDE.md)**: Step-by-step setup for all environments
- **[Usage Guide](MCP_SERVER_USAGE_GUIDE.md)**: Comprehensive usage instructions and examples
- **[Claude Code Integration](CLAUDE_CODE_INTEGRATION.md)**: Detailed integration guide

### Technical References
- **[API Documentation](../README.md)**: Complete API reference and tool specifications
- **[Docker Documentation](../docker/README.md)**: Container deployment and optimization
- **[Testing Documentation](../tests/README.md)**: Test suites and validation procedures

### Troubleshooting and Support
- **[Troubleshooting Guide](TROUBLESHOOTING.md)**: Common issues and solutions
- **[FAQ](FAQ.md)**: Frequently asked questions
- **[Development Guide](DEVELOPMENT.md)**: Contributing and development setup

## サポートされる図表タイプ

### ビジネス図表
- フローチャートとプロセスフロー
- 組織図
- ビジネスプロセスモデル
- 決定木

### 技術図表
- システムアーキテクチャ図
- ネットワーク図
- データベーススキーマ（ER図）
- APIフロー図

### クラウドアーキテクチャ
- AWSアーキテクチャ図
- Azureアーキテクチャ図
- Google Cloud図
- マルチクラウドアーキテクチャ

### ソフトウェア開発
- UML図
- シーケンス図
- クラス図
- コンポーネント図

## Environment Support

### Development
- Hot reloading with volume mounts
- Debug logging
- Shorter cache times
- Development-specific configurations

### Production
- Optimized resource usage
- Security hardening
- Monitoring and logging
- Health checks and auto-restart

### Testing
- Automated test suites
- Container validation
- Integration testing
- Performance benchmarks

## Security Features

- **Non-root execution**: Container runs as unprivileged user
- **Read-only filesystem**: Minimal write access
- **Automatic cleanup**: Temporary files are automatically removed
- **Resource limits**: CPU and memory constraints
- **Network isolation**: Minimal network access requirements

## Performance Optimization

- **Caching**: Intelligent caching of LLM responses
- **Resource management**: Configurable limits and cleanup
- **Multi-stage builds**: Optimized container images
- **Horizontal scaling**: Support for multiple instances

## Getting Help

### Documentation
1. Start with the [Installation Guide](INSTALLATION_GUIDE.md)
2. Follow the [Usage Guide](MCP_SERVER_USAGE_GUIDE.md)
3. Check [Troubleshooting](TROUBLESHOOTING.md) for common issues

### Support Channels
- GitHub Issues for bug reports
- Discussions for questions and ideas
- Documentation improvements via pull requests

### Community
- Share your diagram examples
- Contribute to documentation
- Report issues and suggest improvements

## Contributing

We welcome contributions! Please see:
- [Development Guide](DEVELOPMENT.md) for setup instructions
- [Contributing Guidelines](../CONTRIBUTING.md) for code standards
- [Testing Guide](../tests/README.md) for test requirements

## License

This project is licensed under the MIT License. See [LICENSE](../LICENSE) for details.

---

**Ready to get started?** Begin with the [Installation Guide](INSTALLATION_GUIDE.md) and start creating amazing diagrams with natural language!