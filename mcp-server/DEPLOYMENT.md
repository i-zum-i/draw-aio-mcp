# MCP Draw.io Server - Deployment Guide

This guide covers deploying the MCP Draw.io Server using Docker Compose in both development and production environments.

## Quick Start

### Development Environment

1. Copy the development environment template:
   ```bash
   cp .env.dev .env
   ```

2. Set your Anthropic API key in `.env`:
   ```bash
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

3. Deploy the development environment:
   ```bash
   # Linux/macOS
   ./deploy.sh --environment dev --build

   # Windows PowerShell
   .\deploy.ps1 -Environment dev -Build
   ```

### Production Environment

1. Copy the production environment template:
   ```bash
   cp .env.prod .env
   ```

2. Configure your production settings in `.env`

3. Deploy the production environment:
   ```bash
   # Linux/macOS
   ./deploy.sh --environment prod --build

   # Windows PowerShell
   .\deploy.ps1 -Environment prod -Build
   ```

## Environment Configurations

### Development Environment

The development environment (`docker-compose.dev.yml`) is optimized for:

- **Hot reloading**: Source code is mounted as a volume
- **Debug logging**: Verbose logging enabled
- **Faster iteration**: Shorter cache TTL and file expiry
- **No resource limits**: Easier debugging
- **Frequent health checks**: Faster feedback

**Key Features:**
- Source code mounted for live updates
- Debug port exposed (8080)
- Shorter cache and file expiry times
- Verbose logging
- Development-specific data directories

### Production Environment

The production environment (`docker-compose.prod.yml`) is optimized for:

- **Security**: Read-only filesystem, non-root user
- **Performance**: Resource limits and optimized settings
- **Monitoring**: Optional monitoring services
- **Logging**: Structured logging with rotation
- **Scalability**: Support for multiple replicas

**Key Features:**
- Resource limits (512MB memory, 1 CPU)
- Read-only root filesystem
- Security hardening
- Log aggregation support
- Health monitoring
- Backup-friendly volume configuration

## Configuration Files

### Environment Variables

| File | Purpose | Usage |
|------|---------|-------|
| `.env.dev` | Development settings | Copy to `.env` for development |
| `.env.prod` | Production settings | Copy to `.env` for production |
| `.env.example` | Basic template | Legacy compatibility |
| `.env.docker` | Docker-specific settings | Advanced configuration |

### Docker Compose Files

| File | Purpose | Usage |
|------|---------|-------|
| `docker-compose.dev.yml` | Development environment | `docker-compose -f docker-compose.dev.yml up` |
| `docker-compose.prod.yml` | Production environment | `docker-compose -f docker-compose.prod.yml up` |
| `docker-compose.yml` | Legacy/general purpose | Default compose file |

## Deployment Scripts

### Linux/macOS: `deploy.sh`

```bash
# Basic usage
./deploy.sh --environment prod --build

# Advanced usage
./deploy.sh --environment prod --scale 3 --profiles monitoring

# View logs
./deploy.sh --action logs

# Check status
./deploy.sh --action status
```

### Windows: `deploy.ps1`

```powershell
# Basic usage
.\deploy.ps1 -Environment prod -Build

# Advanced usage
.\deploy.ps1 -Environment prod -Scale 3 -Profiles monitoring

# View logs
.\deploy.ps1 -Action logs

# Check status
.\deploy.ps1 -Action status
```

## Environment-Specific Settings

### Development Settings

```bash
# Cache settings (faster iteration)
CACHE_TTL=300                    # 5 minutes
MAX_CACHE_SIZE=50               # Smaller cache
FILE_EXPIRY_HOURS=1             # 1 hour
CLEANUP_INTERVAL_MINUTES=5      # Every 5 minutes

# Logging
LOG_LEVEL=DEBUG                 # Verbose logging

# Development flags
DEVELOPMENT_MODE=true
DEBUG=true
```

### Production Settings

```bash
# Cache settings (optimized for performance)
CACHE_TTL=7200                  # 2 hours
MAX_CACHE_SIZE=200              # Larger cache
FILE_EXPIRY_HOURS=48            # 2 days
CLEANUP_INTERVAL_MINUTES=30     # Every 30 minutes

# Logging
LOG_LEVEL=WARNING               # Minimal logging

# Production flags
DEVELOPMENT_MODE=false
DEBUG=false
```

## Resource Management

### Development Resources

- **No resource limits**: Allows for easier debugging
- **Larger log files**: 50MB max size, 5 files
- **Frequent health checks**: Every 15 seconds

### Production Resources

- **Memory**: 512MB limit, 256MB reservation
- **CPU**: 1.0 limit, 0.5 reservation
- **Disk**: Optimized log rotation (10MB, 3 files)
- **Health checks**: Every 30 seconds

## Security Considerations

### Development Security

- Source code mounted read-only
- No special security restrictions
- Debug port exposed locally

### Production Security

- **Read-only filesystem**: Container runs with read-only root
- **Non-root user**: Runs as UID/GID 1000
- **No new privileges**: Security option enabled
- **Minimal attack surface**: Only necessary ports exposed
- **Secure tmpfs**: Temporary filesystem with security options

## Monitoring and Logging

### Log Aggregation

Production environment includes optional log aggregation with Fluent Bit:

```bash
# Deploy with monitoring
COMPOSE_PROFILES=monitoring docker-compose -f docker-compose.prod.yml up -d
```

### Health Monitoring

Both environments include comprehensive health checks:

- **Liveness**: Basic server responsiveness
- **Readiness**: Service initialization status
- **Dependencies**: External service availability

### Monitoring Services

Production environment supports optional monitoring:

```bash
# Enable monitoring profile
export COMPOSE_PROFILES=monitoring
docker-compose -f docker-compose.prod.yml up -d
```

## Data Persistence

### Development Data

- `./temp_dev/`: Development temporary files
- `./logs_dev/`: Development logs

### Production Data

- `./temp_prod/`: Production temporary files (or `/var/lib/mcp-server/temp`)
- `./logs_prod/`: Production logs (or `/var/log/mcp-server`)

## Backup and Recovery

### Backup Commands

```bash
# Backup temporary data
docker run --rm -v mcp-server_temp_data_prod:/data -v $(pwd):/backup alpine tar czf /backup/temp_backup.tar.gz -C /data .

# Backup logs
docker run --rm -v mcp-server_logs_data_prod:/data -v $(pwd):/backup alpine tar czf /backup/logs_backup.tar.gz -C /data .
```

### Recovery Commands

```bash
# Restore temporary data
docker run --rm -v mcp-server_temp_data_prod:/data -v $(pwd):/backup alpine tar xzf /backup/temp_backup.tar.gz -C /data

# Restore logs
docker run --rm -v mcp-server_logs_data_prod:/data -v $(pwd):/backup alpine tar xzf /backup/logs_backup.tar.gz -C /data
```

## Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```
   Error: Please set your Anthropic API key
   ```
   Solution: Set `ANTHROPIC_API_KEY` in your `.env` file

2. **Permission Denied**
   ```
   Error: Permission denied accessing /app/temp
   ```
   Solution: Check directory permissions and UID/GID settings

3. **Draw.io CLI Not Found**
   ```
   Error: Draw.io CLI not available
   ```
   Solution: Rebuild the container with `--build` flag

4. **Container Won't Start**
   ```
   Error: Container exits immediately
   ```
   Solution: Check logs with `docker-compose logs`

### Debug Commands

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f mcp-server

# Execute health check manually
docker-compose -f docker-compose.prod.yml exec mcp-server python -c "
import sys; sys.path.append('/app/src'); 
from health import HealthChecker; 
import asyncio; 
print(asyncio.run(HealthChecker().get_health()))
"

# Access container shell
docker-compose -f docker-compose.prod.yml exec mcp-server sh
```

## Performance Tuning

### Memory Optimization

- Adjust `MEMORY_LIMIT` and `MEMORY_RESERVATION` in `.env`
- Monitor memory usage with `docker stats`
- Tune cache settings (`MAX_CACHE_SIZE`, `CACHE_TTL`)

### CPU Optimization

- Adjust `CPU_LIMIT` and `CPU_RESERVATION` in `.env`
- Scale horizontally with `--scale` option
- Monitor CPU usage with `docker stats`

### Disk Optimization

- Configure log rotation settings
- Monitor disk usage in temp directories
- Adjust file expiry settings

## Scaling

### Horizontal Scaling

```bash
# Scale to 3 replicas
./deploy.sh --environment prod --scale 3

# Or with Docker Compose directly
docker-compose -f docker-compose.prod.yml up -d --scale mcp-server=3
```

### Load Balancing

For multiple replicas, consider adding a load balancer:

```yaml
# Add to docker-compose.prod.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - mcp-server
```

## Migration from Legacy Setup

If migrating from the existing setup:

1. **Backup existing data**:
   ```bash
   cp -r temp temp_backup
   cp -r logs logs_backup
   ```

2. **Update environment variables**:
   ```bash
   # Convert old .env to new format
   cp .env .env.legacy
   cp .env.prod .env
   # Manually transfer your API key and custom settings
   ```

3. **Test new setup**:
   ```bash
   ./deploy.sh --environment dev --build
   ```

4. **Deploy production**:
   ```bash
   ./deploy.sh --environment prod --build
   ```

## Support

For issues and questions:

1. Check the logs: `./deploy.sh --action logs`
2. Verify health: `./deploy.sh --action status`
3. Review configuration files
4. Check Docker and Docker Compose versions
5. Ensure all required files are present

## Next Steps

After successful deployment:

1. **Configure monitoring**: Enable monitoring profile for production
2. **Set up backups**: Implement regular backup schedule
3. **Configure alerts**: Set up monitoring and alerting
4. **Performance testing**: Test with expected load
5. **Security review**: Review security settings for your environment

---

# MCP Draw.io サーバー - デプロイメントガイド

このガイドでは、開発環境と本番環境の両方でDocker Composeを使用してMCP Draw.ioサーバーをデプロイする方法について説明します。

## クイックスタート

### 開発環境

1. 開発環境テンプレートをコピー:
   ```bash
   cp .env.dev .env
   ```

2. `.env`でAnthropic APIキーを設定:
   ```bash
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

3. 開発環境をデプロイ:
   ```bash
   # Linux/macOS
   ./deploy.sh --environment dev --build

   # Windows PowerShell
   .\deploy.ps1 -Environment dev -Build
   ```

### 本番環境

1. 本番環境テンプレートをコピー:
   ```bash
   cp .env.prod .env
   ```

2. `.env`で本番設定を構成

3. 本番環境をデプロイ:
   ```bash
   # Linux/macOS
   ./deploy.sh --environment prod --build

   # Windows PowerShell
   .\deploy.ps1 -Environment prod -Build
   ```

## 環境設定

### 開発環境

開発環境（`docker-compose.dev.yml`）は以下のために最適化されています:

- **ホットリロード**: ソースコードがボリュームとしてマウント
- **デバッグログ**: 詳細ログが有効
- **高速反復**: 短いキャッシュTTLとファイル有効期限
- **リソース制限なし**: デバッグが容易
- **頻繁なヘルスチェック**: 高速フィードバック

**主な機能:**
- ライブ更新のためのソースコードマウント
- デバッグポート公開（8080）
- 短いキャッシュとファイル有効期限
- 詳細ログ
- 開発専用データディレクトリ

### 本番環境

本番環境（`docker-compose.prod.yml`）は以下のために最適化されています:

- **セキュリティ**: 読み取り専用ファイルシステム、非rootユーザー
- **パフォーマンス**: リソース制限と最適化設定
- **監視**: オプションの監視サービス
- **ログ**: ローテーション付き構造化ログ
- **スケーラビリティ**: 複数レプリカのサポート

**主な機能:**
- リソース制限（512MBメモリ、1 CPU）
- 読み取り専用ルートファイルシステム
- セキュリティ強化
- ログ集約サポート
- ヘルス監視
- バックアップ対応ボリューム設定

## 設定ファイル

### 環境変数

| ファイル | 目的 | 使用方法 |
|------|---------|-------|
| `.env.dev` | 開発設定 | 開発時は`.env`にコピー |
| `.env.prod` | 本番設定 | 本番時は`.env`にコピー |
| `.env.example` | 基本テンプレート | レガシー互換性 |
| `.env.docker` | Docker固有設定 | 高度な設定 |

### Docker Composeファイル

| ファイル | 目的 | 使用方法 |
|------|---------|-------|
| `docker-compose.dev.yml` | 開発環境 | `docker-compose -f docker-compose.dev.yml up` |
| `docker-compose.prod.yml` | 本番環境 | `docker-compose -f docker-compose.prod.yml up` |
| `docker-compose.yml` | レガシー/汎用 | デフォルトのcomposeファイル |

## デプロイメントスクリプト

### Linux/macOS: `deploy.sh`

```bash
# 基本使用方法
./deploy.sh --environment prod --build

# 高度な使用方法
./deploy.sh --environment prod --scale 3 --profiles monitoring

# ログ表示
./deploy.sh --action logs

# ステータス確認
./deploy.sh --action status
```

### Windows: `deploy.ps1`

```powershell
# 基本使用方法
.\deploy.ps1 -Environment prod -Build

# 高度な使用方法
.\deploy.ps1 -Environment prod -Scale 3 -Profiles monitoring

# ログ表示
.\deploy.ps1 -Action logs

# ステータス確認
.\deploy.ps1 -Action status
```

## 環境固有設定

### 開発設定

```bash
# キャッシュ設定（高速反復）
CACHE_TTL=300                    # 5分
MAX_CACHE_SIZE=50               # 小さなキャッシュ
FILE_EXPIRY_HOURS=1             # 1時間
CLEANUP_INTERVAL_MINUTES=5      # 5分毎

# ログ
LOG_LEVEL=DEBUG                 # 詳細ログ

# 開発フラグ
DEVELOPMENT_MODE=true
DEBUG=true
```

### 本番設定

```bash
# キャッシュ設定（パフォーマンス最適化）
CACHE_TTL=7200                  # 2時間
MAX_CACHE_SIZE=200              # 大きなキャッシュ
FILE_EXPIRY_HOURS=48            # 2日
CLEANUP_INTERVAL_MINUTES=30     # 30分毎

# ログ
LOG_LEVEL=WARNING               # 最小ログ

# 本番フラグ
DEVELOPMENT_MODE=false
DEBUG=false
```

## リソース管理

### 開発リソース

- **リソース制限なし**: デバッグが容易
- **大きなログファイル**: 最大50MB、5ファイル
- **頻繁なヘルスチェック**: 15秒毎

### 本番リソース

- **メモリ**: 512MB制限、256MB予約
- **CPU**: 1.0制限、0.5予約
- **ディスク**: 最適化されたログローテーション（10MB、3ファイル）
- **ヘルスチェック**: 30秒毎

## セキュリティ考慮事項

### 開発セキュリティ

- ソースコードが読み取り専用でマウント
- 特別なセキュリティ制限なし
- デバッグポートがローカルで公開

### 本番セキュリティ

- **読み取り専用ファイルシステム**: 読み取り専用ルートでコンテナ実行
- **非rootユーザー**: UID/GID 1000で実行
- **新しい権限なし**: セキュリティオプションが有効
- **最小攻撃面**: 必要なポートのみ公開
- **セキュアtmpfs**: セキュリティオプション付き一時ファイルシステム

## 監視とログ

### ログ集約

本番環境にはFluent Bitを使用したオプションのログ集約が含まれています:

```bash
# 監視付きデプロイ
COMPOSE_PROFILES=monitoring docker-compose -f docker-compose.prod.yml up -d
```

### ヘルス監視

両環境とも包括的なヘルスチェックを含みます:

- **生存確認**: 基本的なサーバー応答性
- **準備確認**: サービス初期化状態
- **依存関係**: 外部サービス可用性

### 監視サービス

本番環境はオプションの監視をサポート:

```bash
# 監視プロファイル有効化
export COMPOSE_PROFILES=monitoring
docker-compose -f docker-compose.prod.yml up -d
```

## データ永続化

### 開発データ

- `./temp_dev/`: 開発一時ファイル
- `./logs_dev/`: 開発ログ

### 本番データ

- `./temp_prod/`: 本番一時ファイル（または `/var/lib/mcp-server/temp`）
- `./logs_prod/`: 本番ログ（または `/var/log/mcp-server`）

## バックアップと復旧

### バックアップコマンド

```bash
# 一時データのバックアップ
docker run --rm -v mcp-server_temp_data_prod:/data -v $(pwd):/backup alpine tar czf /backup/temp_backup.tar.gz -C /data .

# ログのバックアップ
docker run --rm -v mcp-server_logs_data_prod:/data -v $(pwd):/backup alpine tar czf /backup/logs_backup.tar.gz -C /data .
```

### 復旧コマンド

```bash
# 一時データの復元
docker run --rm -v mcp-server_temp_data_prod:/data -v $(pwd):/backup alpine tar xzf /backup/temp_backup.tar.gz -C /data

# ログの復元
docker run --rm -v mcp-server_logs_data_prod:/data -v $(pwd):/backup alpine tar xzf /backup/logs_backup.tar.gz -C /data
```

## トラブルシューティング

### 一般的な問題

1. **APIキーが設定されていない**
   ```
   Error: Please set your Anthropic API key
   ```
   解決策: `.env`ファイルで`ANTHROPIC_API_KEY`を設定

2. **権限拒否**
   ```
   Error: Permission denied accessing /app/temp
   ```
   解決策: ディレクトリ権限とUID/GID設定を確認

3. **Draw.io CLI が見つからない**
   ```
   Error: Draw.io CLI not available
   ```
   解決策: `--build`フラグでコンテナを再ビルド

4. **コンテナが起動しない**
   ```
   Error: Container exits immediately
   ```
   解決策: `docker-compose logs`でログを確認

### デバッグコマンド

```bash
# コンテナステータス確認
docker-compose -f docker-compose.prod.yml ps

# ログ表示
docker-compose -f docker-compose.prod.yml logs -f mcp-server

# ヘルスチェックを手動実行
docker-compose -f docker-compose.prod.yml exec mcp-server python -c "
import sys; sys.path.append('/app/src'); 
from health import HealthChecker; 
import asyncio; 
print(asyncio.run(HealthChecker().get_health()))
"

# コンテナシェルアクセス
docker-compose -f docker-compose.prod.yml exec mcp-server sh
```

## パフォーマンスチューニング

### メモリ最適化

- `.env`で`MEMORY_LIMIT`と`MEMORY_RESERVATION`を調整
- `docker stats`でメモリ使用量を監視
- キャッシュ設定を調整（`MAX_CACHE_SIZE`、`CACHE_TTL`）

### CPU最適化

- `.env`で`CPU_LIMIT`と`CPU_RESERVATION`を調整
- `--scale`オプションで水平スケール
- `docker stats`でCPU使用量を監視

### ディスク最適化

- ログローテーション設定を構成
- 一時ディレクトリのディスク使用量を監視
- ファイル有効期限設定を調整

## スケーリング

### 水平スケーリング

```bash
# 3レプリカにスケール
./deploy.sh --environment prod --scale 3

# またはDocker Composeで直接
docker-compose -f docker-compose.prod.yml up -d --scale mcp-server=3
```

### ロードバランシング

複数レプリカの場合、ロードバランサーの追加を検討:

```yaml
# docker-compose.prod.yml に追加
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - mcp-server
```

## レガシーセットアップからの移行

既存のセットアップから移行する場合:

1. **既存データのバックアップ**:
   ```bash
   cp -r temp temp_backup
   cp -r logs logs_backup
   ```

2. **環境変数の更新**:
   ```bash
   # 古い.envを新しい形式に変換
   cp .env .env.legacy
   cp .env.prod .env
   # APIキーとカスタム設定を手動で転送
   ```

3. **新しいセットアップのテスト**:
   ```bash
   ./deploy.sh --environment dev --build
   ```

4. **本番デプロイ**:
   ```bash
   ./deploy.sh --environment prod --build
   ```

## サポート

問題や質問については:

1. ログを確認: `./deploy.sh --action logs`
2. ヘルスを確認: `./deploy.sh --action status`
3. 設定ファイルを確認
4. DockerとDocker Composeのバージョンを確認
5. 必要なファイルがすべて存在することを確認

## 次のステップ

デプロイが成功した後:

1. **監視の設定**: 本番環境で監視プロファイルを有効化
2. **バックアップの設定**: 定期バックアップスケジュールの実装
3. **アラートの設定**: 監視とアラートの設定
4. **パフォーマンステスト**: 想定される負荷でのテスト
5. **セキュリティレビュー**: 環境のセキュリティ設定の確認