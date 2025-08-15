#!/usr/bin/env python3.10
"""
基本的なMCP統合テスト

MCPサーバーの基本機能をテストし、実際のMCPクライアントとの
互換性を確認します。
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# MCP imports
try:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.types import (
        CallToolRequest,
        ListToolsRequest,
        InitializeRequest,
        Tool,
        TextContent
    )
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MCP library not available: {e}")
    MCP_AVAILABLE = False


class BasicMCPIntegrationTest:
    """基本的なMCP統合テスト"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        
    def record_test_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """テスト結果を記録"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {'成功' if success else '失敗'}")
        
        if details and not success:
            print(f"   詳細: {details}")
    
    async def test_mcp_server_startup(self) -> bool:
        """MCPサーバーの起動テスト"""
        test_name = "MCPサーバー起動テスト"
        
        try:
            # 一時ディレクトリの作成
            temp_dir = tempfile.mkdtemp(prefix="mcp_basic_test_")
            
            # 環境変数の設定
            env = os.environ.copy()
            env.update({
                'ANTHROPIC_API_KEY': 'test-key-for-basic-integration-test',
                'TEMP_DIR': temp_dir,
                'LOG_LEVEL': 'INFO',
                'DEVELOPMENT_MODE': 'true'
            })
            
            # サーバープロセスの開始
            server_path = Path(__file__).parent / "src" / "server.py"
            process = subprocess.Popen(
                [sys.executable, str(server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=0
            )
            
            # サーバーの起動を少し待つ
            await asyncio.sleep(3)
            
            # プロセスが生きているかチェック
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.record_test_result(test_name, False, {
                    "error": "サーバープロセスが終了しました",
                    "exit_code": process.returncode,
                    "stdout": stdout[:500] if stdout else "",
                    "stderr": stderr[:500] if stderr else ""
                })
                return False
            
            # プロセスを終了
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            # 一時ディレクトリのクリーンアップ
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            
            self.record_test_result(test_name, True, {
                "process_id": process.pid,
                "startup_time": "< 3 seconds"
            })
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_mcp_client_connection(self) -> bool:
        """MCPクライアント接続テスト"""
        test_name = "MCPクライアント接続テスト"
        
        if not MCP_AVAILABLE:
            self.record_test_result(test_name, False, {"error": "MCP library not available"})
            return False
        
        try:
            # 一時ディレクトリの作成
            temp_dir = tempfile.mkdtemp(prefix="mcp_client_test_")
            
            # サーバーパラメータの設定
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.server"],
                cwd=str(Path(__file__).parent),
                env={
                    'ANTHROPIC_API_KEY': 'test-key-for-client-connection-test',
                    'TEMP_DIR': temp_dir,
                    'LOG_LEVEL': 'INFO',
                    'DEVELOPMENT_MODE': 'true'
                }
            )
            
            # MCPクライアント接続
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初期化
                    await session.initialize()
                    
                    # ツールリストの取得
                    tools_result = await session.list_tools()
                    
                    # 期待されるツールの確認
                    expected_tools = {"generate-drawio-xml", "save-drawio-file", "convert-to-png"}
                    actual_tools = {tool.name for tool in tools_result.tools}
                    
                    success = expected_tools.issubset(actual_tools)
                    
                    self.record_test_result(test_name, success, {
                        "expected_tools": list(expected_tools),
                        "actual_tools": list(actual_tools),
                        "tools_count": len(tools_result.tools)
                    })
                    
                    # 一時ディレクトリのクリーンアップ
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
                    
                    return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_basic_tool_execution(self) -> bool:
        """基本的なツール実行テスト"""
        test_name = "基本ツール実行テスト"
        
        if not MCP_AVAILABLE:
            self.record_test_result(test_name, False, {"error": "MCP library not available"})
            return False
        
        try:
            # 一時ディレクトリの作成
            temp_dir = tempfile.mkdtemp(prefix="mcp_tool_test_")
            
            # サーバーパラメータの設定
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.server"],
                cwd=str(Path(__file__).parent),
                env={
                    'ANTHROPIC_API_KEY': 'test-key-for-tool-execution-test',
                    'TEMP_DIR': temp_dir,
                    'LOG_LEVEL': 'INFO',
                    'DEVELOPMENT_MODE': 'true'
                }
            )
            
            # MCPクライアント接続
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初期化
                    await session.initialize()
                    
                    # generate-drawio-xml ツールの実行
                    result = await session.call_tool(
                        "generate-drawio-xml",
                        {"prompt": "Create a simple test flowchart"}
                    )
                    
                    # 結果の検証
                    success = len(result.content) > 0
                    
                    if success and result.content:
                        content = result.content[0]
                        if hasattr(content, 'text'):
                            response_text = content.text
                            # XMLコンテンツが含まれているかチェック
                            xml_indicators = ["<mxfile", "<mxGraphModel", "<?xml"]
                            has_xml = any(indicator in response_text for indicator in xml_indicators)
                            success = has_xml
                            
                            details = {
                                "response_length": len(response_text),
                                "has_xml_content": has_xml,
                                "content_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
                            }
                        else:
                            success = False
                            details = {"error": "レスポンスにテキストコンテンツがありません"}
                    else:
                        details = {"error": "空のレスポンス"}
                    
                    self.record_test_result(test_name, success, details)
                    
                    # 一時ディレクトリのクリーンアップ
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
                    
                    return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_claude_code_config_generation(self) -> bool:
        """Claude Code設定生成テスト"""
        test_name = "Claude Code設定生成テスト"
        
        try:
            # 現在のスクリプトディレクトリを取得
            server_dir = Path(__file__).parent.absolute()
            
            # Claude Code用MCP設定の生成
            mcp_config = {
                "mcpServers": {
                    "drawio-server": {
                        "command": "python",
                        "args": ["-m", "src.server"],
                        "cwd": str(server_dir),
                        "env": {
                            "ANTHROPIC_API_KEY": "your-api-key-here"
                        },
                        "disabled": False,
                        "autoApprove": [
                            "generate-drawio-xml",
                            "save-drawio-file",
                            "convert-to-png"
                        ]
                    }
                }
            }
            
            # 設定の検証
            validation_errors = []
            
            # 基本構造の確認
            if "mcpServers" not in mcp_config:
                validation_errors.append("mcpServers セクションが不足")
            
            if "drawio-server" not in mcp_config.get("mcpServers", {}):
                validation_errors.append("drawio-server 設定が不足")
            
            server_config = mcp_config.get("mcpServers", {}).get("drawio-server", {})
            
            # 必須フィールドの確認
            required_fields = ["command", "args", "cwd"]
            for field in required_fields:
                if field not in server_config:
                    validation_errors.append(f"必須フィールド '{field}' が不足")
            
            # パスの確認
            if "cwd" in server_config:
                cwd_path = Path(server_config["cwd"])
                if not cwd_path.exists():
                    validation_errors.append(f"作業ディレクトリが存在しません: {cwd_path}")
                
                server_py_path = cwd_path / "src" / "server.py"
                if not server_py_path.exists():
                    validation_errors.append(f"サーバーファイルが存在しません: {server_py_path}")
            
            success = len(validation_errors) == 0
            details = {
                "config": mcp_config,
                "validation_errors": validation_errors,
                "server_dir": str(server_dir)
            }
            
            self.record_test_result(test_name, success, details)
            
            # 設定ファイルの例を出力
            if success:
                print(f"   📋 Claude Code設定例:")
                print(f"   {json.dumps(mcp_config, indent=2, ensure_ascii=False)}")
            
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """すべてのテストを実行"""
        print("🚀 基本MCP統合テスト開始")
        
        # テスト実行
        test_methods = [
            self.test_mcp_server_startup,
            self.test_claude_code_config_generation
        ]
        
        # MCP library が利用可能な場合のみ実行するテスト
        if MCP_AVAILABLE:
            test_methods.extend([
                self.test_mcp_client_connection,
                self.test_basic_tool_execution
            ])
        else:
            print("⚠️ MCP library が利用できないため、一部のテストをスキップします")
        
        results = []
        for test_method in test_methods:
            try:
                result = await test_method()
                results.append(result)
            except Exception as e:
                print(f"❌ テスト実行エラー: {test_method.__name__}: {str(e)}")
                results.append(False)
        
        # 結果の集計
        tests_run = len(results)
        tests_passed = sum(results)
        success_rate = (tests_passed / tests_run) * 100 if tests_run > 0 else 0
        
        print(f"\n📊 基本MCP統合テスト結果:")
        print(f"   実行テスト数: {tests_run}")
        print(f"   成功テスト数: {tests_passed}")
        print(f"   成功率: {success_rate:.1f}%")
        
        return {
            "success": tests_passed == tests_run,
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results,
            "mcp_available": MCP_AVAILABLE
        }


async def main():
    """メイン実行関数"""
    print("🚀 基本MCP統合テスト開始")
    print("=" * 60)
    
    tester = BasicMCPIntegrationTest()
    results = await tester.run_all_tests()
    
    # 総合結果
    print("\n" + "=" * 60)
    print("📊 基本MCP統合テスト総合結果")
    print("=" * 60)
    
    overall_success = results.get("success", False)
    
    print(f"🎯 総合評価: {'✅ 成功' if overall_success else '❌ 要改善'}")
    print(f"📈 MCP library 利用可能: {'✅ はい' if results.get('mcp_available', False) else '❌ いいえ'}")
    
    if results.get("tests_run", 0) > 0:
        print(f"📊 テスト統計:")
        print(f"   実行: {results['tests_run']}")
        print(f"   成功: {results['tests_passed']}")
        print(f"   成功率: {results.get('success_rate', 0):.1f}%")
    
    # 推奨事項
    print(f"\n💡 推奨事項:")
    if overall_success:
        print("   • 基本的なMCP統合テストが成功しました")
        if results.get('mcp_available', False):
            print("   • 実際のClaude Code環境でテストしてください")
            print("   • 本番用APIキーを設定してテストしてください")
        else:
            print("   • MCP client library をインストールしてください: pip install mcp[cli]")
    else:
        print("   • 失敗したテストの詳細を確認してください")
        print("   • サーバーの起動ログを確認してください")
        print("   • 依存関係を確認してください")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)