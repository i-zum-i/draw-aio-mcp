# MCP クライアント統合テストガイド

## 概要

このドキュメントでは、MCP Draw.io サーバーと公式MCPクライアントとの統合テストについて説明します。カスタムテストスクリプトではなく、実際のMCPクライアントライブラリを使用して実環境での動作を保証します。

## 目次

- [テストの目的](#テストの目的)
- [テストスイート構成](#テストスイート構成)
- [実行方法](#実行方法)
- [テスト内容詳細](#テスト内容詳細)
- [結果の解釈](#結果の解釈)
- [トラブルシューティング](#トラブルシューティング)
- [継続的インテグレーション](#継続的インテグレーション)

## テストの目的

### 主要目標

1. **実環境動作保証**: 実際のMCPクライアントでの動作確認
2. **プロトコル準拠確認**: MCP標準プロトコルへの完全準拠
3. **Claude Code互換性**: Claude Code環境での正常動作
4. **エラーハンドリング検証**: 異常系での適切な動作
5. **パフォーマンス確認**: 実用的な応答時間の確保

### 対象クライアント

- **公式MCPクライアントライブラリ** (`mcp` Python SDK)
- **Claude Code** (Anthropic公式IDE統合)
- **その他のMCP互換クライアント** (標準プロトコル準拠)

## テストスイート構成

### 1. 公式MCPクライアント統合テスト

**ファイル**: `test_official_mcp_client_integration.py`

**テスト内容**:
- MCPサーバープロセス管理
- 公式MCPクライアントセッション確立
- ツールリスト取得と検証
- 各MCPツールの実行テスト
- エラーハンドリング確認
- プロトコル準拠検証

**重要な機能**:
```python
class MCPClientIntegrationTester:
    async def test_tool_listing(self) -> bool
    async def test_generate_drawio_xml_tool(self) -> bool
    async def test_save_drawio_file_tool(self) -> bool
    async def test_convert_to_png_tool(self) -> bool
    async def test_error_handling(self) -> bool
    async def test_protocol_compliance(self) -> bool
```

### 2. Claude Code統合テスト

**ファイル**: `test_claude_code_integration.py`

**テスト内容**:
- Claude Codeワークスペース環境シミュレーション
- MCP設定ファイル生成と検証
- サーバー起動シミュレーション
- 使用シナリオテスト
- 自動承認設定テスト

**重要な機能**:
```python
class ClaudeCodeSimulator:
    async def test_mcp_config_validation(self) -> bool
    async def test_server_startup_simulation(self) -> bool
    async def test_workspace_integration(self) -> bool
    async def test_usage_scenarios(self) -> bool
    async def test_auto_approval_configuration(self) -> bool
```

### 3. 統合テスト実行管理

**ファイル**: `run_mcp_client_integration_tests.py`

**機能**:
- 前提条件チェック
- 全テストスイートの実行
- 結果集計とレポート生成
- 詳細ログ出力

## 実行方法

### 基本実行

```bash
# 全統合テストの実行
python run_mcp_client_integration_tests.py

# 個別テストの実行
python test_official_mcp_client_integration.py
python test_claude_code_integration.py
```

### 前提条件

1. **Python 3.10+**
2. **必要なライブラリ**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
3. **環境変数** (オプション):
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

### Docker環境での実行

```bash
# Dockerコンテナ内でテスト実行
docker run --rm -it \
  -v $(pwd):/app \
  -w /app \
  -e ANTHROPIC_API_KEY="your-api-key" \
  python:3.10 \
  python run_mcp_client_integration_tests.py
```

## テスト内容詳細

### 公式MCPクライアント統合テスト

#### 1. ツールリスト取得テスト

```python
async def test_tool_listing(self) -> bool:
    """期待されるMCPツールが正しく公開されているかテスト"""
    tools_result = await self.client_session.list_tools(ListToolsRequest())
    expected_tools = {"generate-drawio-xml", "save-drawio-file", "convert-to-png"}
    actual_tools = {tool.name for tool in tools_result.tools}
    return expected_tools.issubset(actual_tools)
```

**検証項目**:
- 3つの必須ツールの存在確認
- ツールスキーマの妥当性
- ツール説明の適切性

#### 2. generate-drawio-xml ツールテスト

```python
async def test_generate_drawio_xml_tool(self) -> bool:
    """XML生成ツールの動作テスト"""
    result = await self.client_session.call_tool(
        CallToolRequest(
            name="generate-drawio-xml",
            arguments={"prompt": "Create a simple flowchart with Start -> Process -> End"}
        )
    )
    # XMLコンテンツの検証
    return self.validate_xml_response(result)
```

**検証項目**:
- 有効なDraw.io XMLの生成
- プロンプト処理の正確性
- レスポンス形式の準拠

#### 3. save-drawio-file ツールテスト

```python
async def test_save_drawio_file_tool(self) -> bool:
    """ファイル保存ツールの動作テスト"""
    result = await self.client_session.call_tool(
        CallToolRequest(
            name="save-drawio-file",
            arguments={
                "xml_content": test_xml,
                "filename": "integration-test-diagram"
            }
        )
    )
    return self.validate_file_save_response(result)
```

**検証項目**:
- ファイル保存の成功
- ファイルIDの生成
- メタデータの正確性

#### 4. convert-to-png ツールテスト

```python
async def test_convert_to_png_tool(self) -> bool:
    """PNG変換ツールの動作テスト"""
    # まずファイルを保存
    file_id = await self.save_test_file()
    
    # PNG変換を実行
    result = await self.client_session.call_tool(
        CallToolRequest(
            name="convert-to-png",
            arguments={"file_id": file_id}
        )
    )
    return self.validate_png_conversion_response(result)
```

**検証項目**:
- PNG変換の実行
- Draw.io CLI利用可能性の確認
- フォールバック機能の動作

### Claude Code統合テスト

#### 1. MCP設定ファイル検証

```python
async def test_mcp_config_validation(self) -> bool:
    """Claude Code用MCP設定の妥当性テスト"""
    config = self.load_mcp_config()
    
    # 必須フィールドの確認
    required_fields = ["command", "args", "cwd"]
    for field in required_fields:
        if field not in config["mcpServers"]["drawio-server"]:
            return False
    
    # パスの存在確認
    return self.validate_paths(config)
```

**検証項目**:
- 設定ファイル構造の正確性
- 必須フィールドの存在
- ファイルパスの有効性
- 自動承認設定の適切性

#### 2. 使用シナリオテスト

```python
async def test_usage_scenarios(self) -> bool:
    """典型的なClaude Code使用パターンのテスト"""
    scenarios = [
        {
            "name": "簡単なフローチャート作成",
            "prompt": "Create a simple flowchart for user registration process",
            "expected_tools": ["generate-drawio-xml"]
        },
        {
            "name": "図表保存とPNG変換",
            "prompt": "Save the diagram and convert to PNG for documentation",
            "expected_tools": ["save-drawio-file", "convert-to-png"]
        }
    ]
    
    return self.validate_scenarios(scenarios)
```

**検証項目**:
- 実用的な使用パターンの妥当性
- ツール選択の適切性
- ワークフロー連携の確認

## 結果の解釈

### 成功基準

#### 全体成功の条件
- すべてのクリティカルテストが成功
- 成功率が95%以上
- プロトコル準拠テストが完全成功

#### 個別テスト成功基準

**公式MCPクライアント統合**:
- ツールリスト取得: 3つのツールすべてが正しく公開
- XML生成: 有効なDraw.io XMLが生成される
- ファイル保存: ファイルIDが正常に返される
- PNG変換: 変換処理が実行される（CLI利用可否に関わらず）

**Claude Code統合**:
- MCP設定: 構文エラーなし、必須フィールド完備
- サーバー起動: プロセスが正常に開始
- ワークスペース統合: 設定ファイルが正しい場所に配置

### 結果レポート

#### コンソール出力例

```
📊 MCP クライアント統合テスト結果サマリー
================================================================================
🎯 総合評価: ✅ 成功

📈 テスト統計:
   総テスト数: 11
   成功: 11
   失敗: 0
   成功率: 100.0%

🔥 クリティカルテスト:
   クリティカルテスト数: 6
   成功: 6
   失敗: 0
   成功率: 100.0%

⏱️ 実行時間:
   テスト実行時間: 45.32秒
   全体実行時間: 48.15秒

📋 個別テスト結果:
   ✅ 公式MCPクライアント - ツールリスト取得 🔥 (2.15秒)
   ✅ 公式MCPクライアント - generate-drawio-xml ツール 🔥 (8.42秒)
   ✅ 公式MCPクライアント - save-drawio-file ツール 🔥 (1.23秒)
   ✅ 公式MCPクライアント - convert-to-png ツール 🔥 (12.34秒)
   ✅ 公式MCPクライアント - エラーハンドリング (1.45秒)
   ✅ 公式MCPクライアント - プロトコル準拠 🔥 (0.89秒)
   ✅ Claude Code - MCP設定ファイル検証 🔥 (0.12秒)
   ✅ Claude Code - サーバー起動シミュレーション (3.45秒)
   ✅ Claude Code - ワークスペース統合 (0.34秒)
   ✅ Claude Code - 使用シナリオ (0.23秒)
   ✅ Claude Code - 自動承認設定 (0.15秒)
```

#### JSON詳細レポート

```json
{
  "test_run_info": {
    "timestamp": "2024-01-15 14:30:25",
    "python_version": "3.10.12",
    "working_directory": "/path/to/mcp-server",
    "environment": {
      "ANTHROPIC_API_KEY": "設定済み"
    }
  },
  "summary": {
    "overall_success": true,
    "total_tests": 11,
    "successful_tests": 11,
    "failed_tests": 0,
    "success_rate": 100.0,
    "critical_tests": 6,
    "critical_passed": 6,
    "critical_failed": 0,
    "critical_success_rate": 100.0,
    "total_execution_time": 45.32,
    "overall_execution_time": 48.15,
    "test_results": [...]
  }
}
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. MCPライブラリが見つからない

**症状**:
```
❌ Failed to import MCP library: No module named 'mcp'
```

**解決方法**:
```bash
pip install mcp[cli]>=1.2.0
```

#### 2. サーバー起動失敗

**症状**:
```
❌ サーバープロセスが終了しました: ModuleNotFoundError: No module named 'src'
```

**解決方法**:
```bash
# PYTHONPATHの設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# または相対インポートの修正
cd mcp-server
python -m src.server
```

#### 3. APIキー関連エラー

**症状**:
```
❌ APIキー検証に失敗: Invalid API key format
```

**解決方法**:
```bash
# 有効なAPIキーの設定
export ANTHROPIC_API_KEY="sk-ant-your-actual-api-key"

# または開発モードでテスト
export DEVELOPMENT_MODE="true"
```

#### 4. Draw.io CLI エラー

**症状**:
```
⚠️ Draw.io CLI が利用できません
```

**解決方法**:
```bash
# Node.js環境でのCLIインストール
npm install -g @drawio/drawio-desktop-cli

# またはDockerコンテナの使用
docker run --rm -v $(pwd):/app mcp-drawio-server:latest
```

#### 5. 権限エラー

**症状**:
```
❌ Permission denied: '/tmp/mcp_test_xxx'
```

**解決方法**:
```bash
# 一時ディレクトリの権限修正
chmod 755 /tmp
mkdir -p ./temp
export TEMP_DIR="./temp"
```

### デバッグ手順

#### 1. 詳細ログの有効化

```bash
export LOG_LEVEL="DEBUG"
python run_mcp_client_integration_tests.py
```

#### 2. 個別テストの実行

```bash
# 特定のテストのみ実行
python test_official_mcp_client_integration.py

# または特定の機能のテスト
python -c "
import asyncio
from test_official_mcp_client_integration import MCPClientIntegrationTester
async def main():
    tester = MCPClientIntegrationTester()
    await tester.setup()
    result = await tester.test_tool_listing()
    print(f'Result: {result}')
    await tester.teardown()
asyncio.run(main())
"
```

#### 3. サーバーの手動テスト

```bash
# サーバーを手動で起動
python -m src.server

# 別のターミナルでMCPクライアントテスト
python -c "
import asyncio
from mcp.client.stdio import stdio_client
from mcp.client import ClientSession
# ... テストコード
"
```

## 継続的インテグレーション

### GitHub Actions設定例

```yaml
name: MCP Client Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Install Draw.io CLI
      run: |
        npm install -g @drawio/drawio-desktop-cli
    
    - name: Run MCP Client Integration Tests
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        cd mcp-server
        python run_mcp_client_integration_tests.py
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: integration-test-results-${{ matrix.python-version }}
        path: mcp-server/mcp_integration_test_report.json
```

### ローカル開発での継続テスト

```bash
# ファイル変更監視でテスト自動実行
pip install watchdog
python -c "
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class TestHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print('Running integration tests...')
            subprocess.run(['python', 'run_mcp_client_integration_tests.py'])

observer = Observer()
observer.schedule(TestHandler(), path='src', recursive=True)
observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
"
```

## ベストプラクティス

### テスト実行のベストプラクティス

1. **定期実行**: 毎日または各コミット時に実行
2. **環境分離**: 本番環境とは分離されたテスト環境を使用
3. **結果保存**: テスト結果を履歴として保存
4. **失敗時対応**: 失敗時の自動通知とロールバック手順

### テスト保守のベストプラクティス

1. **テスト更新**: MCPプロトコル更新時のテスト同期
2. **カバレッジ監視**: 新機能追加時のテストカバレッジ確保
3. **パフォーマンス監視**: 実行時間の継続的な監視
4. **ドキュメント更新**: テスト手順の最新化

## まとめ

MCP クライアント統合テストは、実環境での動作保証を提供する重要なテストスイートです。定期的な実行により、MCPサーバーの品質と信頼性を維持できます。

### 重要なポイント

- **実際のクライアント使用**: カスタムテストではなく公式クライアントを使用
- **包括的テスト**: プロトコル準拠からエラーハンドリングまで網羅
- **継続的実行**: 開発サイクルに組み込んだ定期実行
- **詳細レポート**: 問題特定のための詳細な結果記録

これらのテストにより、MCPサーバーが実際のClaude Code環境や他のMCP互換クライアントで確実に動作することを保証できます。