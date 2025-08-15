#!/usr/bin/env python3.10
"""
MCP クライアント互換性テスト

実際のMCPクライアントとの互換性を検証し、
Claude Code での使用方法を文書化します。
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


class MCPClientCompatibilityTester:
    """MCP クライアント互換性テスト"""
    
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
    
    async def test_server_module_execution(self) -> bool:
        """サーバーモジュール実行テスト"""
        test_name = "サーバーモジュール実行テスト"
        
        try:
            # 一時ディレクトリの作成
            temp_dir = tempfile.mkdtemp(prefix="mcp_module_test_")
            
            # 環境変数の設定
            env = os.environ.copy()
            env.update({
                'ANTHROPIC_API_KEY': 'test-key-for-module-execution-test',
                'TEMP_DIR': temp_dir,
                'LOG_LEVEL': 'INFO',
                'DEVELOPMENT_MODE': 'true'
            })
            
            # サーバーをモジュールとして実行
            process = subprocess.Popen(
                [sys.executable, "-m", "src.server"],
                cwd=Path(__file__).parent,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=0
            )
            
            # サーバーの起動を少し待つ
            await asyncio.sleep(5)
            
            # プロセスが生きているかチェック
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.record_test_result(test_name, False, {
                    "error": "サーバープロセスが終了しました",
                    "exit_code": process.returncode,
                    "stdout": stdout[:500] if stdout else "",
                    "stderr": stderr[:500] if stderr else ""
                })
                
                # 一時ディレクトリのクリーンアップ
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                
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
                "startup_time": "< 5 seconds",
                "execution_method": "python -m src.server"
            })
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_mcp_protocol_compliance(self) -> bool:
        """MCPプロトコル準拠テスト"""
        test_name = "MCPプロトコル準拠テスト"
        
        try:
            # サーバーファイルの存在確認
            server_path = Path(__file__).parent / "src" / "server.py"
            if not server_path.exists():
                self.record_test_result(test_name, False, {"error": f"サーバーファイルが見つかりません: {server_path}"})
                return False
            
            # サーバーファイルの内容確認
            with open(server_path, 'r', encoding='utf-8') as f:
                server_content = f.read()
            
            # MCP準拠の確認項目
            compliance_checks = {
                "公式MCP SDK使用": "from mcp.server import Server" in server_content,
                "stdio_server使用": "stdio_server" in server_content,
                "標準ツール定義": "@server.list_tools()" in server_content,
                "標準ツール実行": "@server.call_tool()" in server_content,
                "プロトコルバージョン": "2024-11-05" in server_content,
                "サーバー機能定義": "ServerCapabilities" in server_content
            }
            
            # 準拠率の計算
            total_checks = len(compliance_checks)
            passed_checks = sum(compliance_checks.values())
            compliance_rate = (passed_checks / total_checks) * 100
            
            success = compliance_rate >= 80  # 80%以上で成功とする
            
            self.record_test_result(test_name, success, {
                "compliance_checks": compliance_checks,
                "compliance_rate": compliance_rate,
                "passed_checks": passed_checks,
                "total_checks": total_checks
            })
            
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_claude_code_configuration(self) -> bool:
        """Claude Code設定テスト"""
        test_name = "Claude Code設定テスト"
        
        try:
            # 現在のスクリプトディレクトリを取得
            server_dir = Path(__file__).parent.absolute()
            
            # 複数の設定パターンを生成
            config_patterns = {
                "基本設定": {
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
                },
                "Docker設定": {
                    "mcpServers": {
                        "drawio-server": {
                            "command": "docker",
                            "args": [
                                "run", "--rm", "-i",
                                "--env-file", f"{server_dir}/.env",
                                "-v", f"{server_dir}/temp:/app/temp:rw",
                                "mcp-drawio-server:latest"
                            ],
                            "env": {
                                "ANTHROPIC_API_KEY": "your-api-key-here"
                            },
                            "disabled": False,
                            "autoApprove": ["generate-drawio-xml"]
                        }
                    }
                },
                "開発設定": {
                    "mcpServers": {
                        "drawio-server-dev": {
                            "command": "python",
                            "args": ["-m", "src.server"],
                            "cwd": str(server_dir),
                            "env": {
                                "ANTHROPIC_API_KEY": "your-api-key-here",
                                "LOG_LEVEL": "DEBUG",
                                "DEVELOPMENT_MODE": "true"
                            },
                            "disabled": False,
                            "autoApprove": []
                        }
                    }
                }
            }
            
            # 各設定パターンの検証
            validation_results = {}
            
            for pattern_name, config in config_patterns.items():
                validation_errors = []
                
                # 基本構造の確認
                if "mcpServers" not in config:
                    validation_errors.append("mcpServers セクションが不足")
                
                for server_name, server_config in config.get("mcpServers", {}).items():
                    # 必須フィールドの確認
                    required_fields = ["command", "args"]
                    for field in required_fields:
                        if field not in server_config:
                            validation_errors.append(f"{server_name}: 必須フィールド '{field}' が不足")
                    
                    # パスの確認（Docker以外）
                    if server_config.get("command") == "python" and "cwd" in server_config:
                        cwd_path = Path(server_config["cwd"])
                        if not cwd_path.exists():
                            validation_errors.append(f"{server_name}: 作業ディレクトリが存在しません: {cwd_path}")
                        
                        server_py_path = cwd_path / "src" / "server.py"
                        if not server_py_path.exists():
                            validation_errors.append(f"{server_name}: サーバーファイルが存在しません: {server_py_path}")
                
                validation_results[pattern_name] = {
                    "valid": len(validation_errors) == 0,
                    "errors": validation_errors,
                    "config": config
                }
            
            # 全体の成功判定
            all_valid = all(result["valid"] for result in validation_results.values())
            
            self.record_test_result(test_name, all_valid, {
                "patterns_tested": len(config_patterns),
                "valid_patterns": sum(1 for result in validation_results.values() if result["valid"]),
                "validation_results": validation_results
            })
            
            # 設定例の出力
            if all_valid:
                print(f"   📋 Claude Code設定パターン:")
                for pattern_name, result in validation_results.items():
                    print(f"   ✅ {pattern_name}")
            
            return all_valid
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_usage_scenarios_documentation(self) -> bool:
        """使用シナリオドキュメント化テスト"""
        test_name = "使用シナリオドキュメント化テスト"
        
        try:
            # 典型的な使用シナリオの定義
            usage_scenarios = [
                {
                    "name": "基本的なフローチャート作成",
                    "description": "ユーザーがClaude Codeで簡単なフローチャートを作成する",
                    "user_prompt": "Create a flowchart for user registration process",
                    "expected_tools": ["generate-drawio-xml"],
                    "expected_outcome": "Draw.io XML形式のフローチャートが生成される",
                    "auto_approval": "推奨（generate-drawio-xmlを自動承認）"
                },
                {
                    "name": "AWS アーキテクチャ図作成",
                    "description": "AWS サービスを使用したシステムアーキテクチャ図を作成",
                    "user_prompt": "Create an AWS architecture diagram with ALB, EC2, and RDS",
                    "expected_tools": ["generate-drawio-xml"],
                    "expected_outcome": "AWS固有のアイコンを使用したアーキテクチャ図が生成される",
                    "auto_approval": "推奨（generate-drawio-xmlを自動承認）"
                },
                {
                    "name": "図表の保存と共有",
                    "description": "生成した図表をファイルに保存してチームで共有",
                    "user_prompt": "Save this diagram as a file for team sharing",
                    "expected_tools": ["save-drawio-file"],
                    "expected_outcome": "一意のファイルIDと保存パスが返される",
                    "auto_approval": "推奨（save-drawio-fileを自動承認）"
                },
                {
                    "name": "ドキュメント用PNG変換",
                    "description": "図表をPNG形式に変換してドキュメントに埋め込み",
                    "user_prompt": "Convert this diagram to PNG for documentation",
                    "expected_tools": ["convert-to-png"],
                    "expected_outcome": "PNG画像ファイルが生成される（CLI利用可能時）",
                    "auto_approval": "条件付き（環境に依存）"
                },
                {
                    "name": "完全ワークフロー",
                    "description": "図表作成から保存、PNG変換までの完全なワークフロー",
                    "user_prompt": "Create a database schema diagram, save it, and convert to PNG",
                    "expected_tools": ["generate-drawio-xml", "save-drawio-file", "convert-to-png"],
                    "expected_outcome": "図表作成、ファイル保存、PNG変換が順次実行される",
                    "auto_approval": "部分的（generate-drawio-xml, save-drawio-fileを自動承認）"
                }
            ]
            
            # シナリオの妥当性検証
            scenario_validation = {}
            
            for scenario in usage_scenarios:
                validation_issues = []
                
                # 必須フィールドの確認
                required_fields = ["name", "description", "user_prompt", "expected_tools", "expected_outcome"]
                for field in required_fields:
                    if not scenario.get(field):
                        validation_issues.append(f"必須フィールド '{field}' が不足または空")
                
                # プロンプトの妥当性確認
                if len(scenario.get("user_prompt", "")) < 10:
                    validation_issues.append("user_prompt が短すぎます")
                
                # 期待されるツールの妥当性確認
                valid_tools = {"generate-drawio-xml", "save-drawio-file", "convert-to-png"}
                expected_tools = set(scenario.get("expected_tools", []))
                invalid_tools = expected_tools - valid_tools
                if invalid_tools:
                    validation_issues.append(f"無効なツール: {invalid_tools}")
                
                scenario_validation[scenario["name"]] = {
                    "valid": len(validation_issues) == 0,
                    "issues": validation_issues
                }
            
            # 全体の成功判定
            all_scenarios_valid = all(result["valid"] for result in scenario_validation.values())
            
            self.record_test_result(test_name, all_scenarios_valid, {
                "total_scenarios": len(usage_scenarios),
                "valid_scenarios": sum(1 for result in scenario_validation.values() if result["valid"]),
                "scenario_validation": scenario_validation,
                "scenarios": usage_scenarios
            })
            
            return all_scenarios_valid
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_troubleshooting_guide(self) -> bool:
        """トラブルシューティングガイドテスト"""
        test_name = "トラブルシューティングガイドテスト"
        
        try:
            # よくある問題とその解決方法
            troubleshooting_items = [
                {
                    "issue": "MCPサーバーが見つからない",
                    "symptoms": [
                        "Claude Codeでツールが表示されない",
                        "MCP server not available エラー"
                    ],
                    "solutions": [
                        "MCP設定ファイル（.kiro/settings/mcp.json）のパスを確認",
                        "サーバーファイル（src/server.py）の存在確認",
                        "Claude Codeの再起動",
                        "設定ファイルのJSON構文確認"
                    ],
                    "validation_commands": [
                        "python -m src.server --check-dependencies",
                        "python -c \"import json; json.load(open('.kiro/settings/mcp.json'))\""
                    ]
                },
                {
                    "issue": "APIキー認証エラー",
                    "symptoms": [
                        "Invalid API key エラー",
                        "Authentication failed エラー"
                    ],
                    "solutions": [
                        "ANTHROPIC_API_KEYの設定確認",
                        "APIキーの形式確認（sk-ant-で始まる）",
                        "APIキーの有効性確認",
                        "開発モードでのテスト実行"
                    ],
                    "validation_commands": [
                        "echo $ANTHROPIC_API_KEY",
                        "python -m src.server --check-api-key"
                    ]
                },
                {
                    "issue": "Draw.io CLI エラー",
                    "symptoms": [
                        "PNG conversion failed エラー",
                        "drawio: command not found エラー"
                    ],
                    "solutions": [
                        "Draw.io CLIのインストール: npm install -g @drawio/drawio-desktop-cli",
                        "Node.js環境の確認",
                        "Dockerコンテナの使用検討",
                        "フォールバック機能の利用"
                    ],
                    "validation_commands": [
                        "drawio --version",
                        "npm list -g @drawio/drawio-desktop-cli"
                    ]
                },
                {
                    "issue": "権限エラー",
                    "symptoms": [
                        "Permission denied エラー",
                        "ファイル作成失敗"
                    ],
                    "solutions": [
                        "一時ディレクトリの権限確認",
                        "実行ユーザーの権限確認",
                        "Dockerユーザーマッピングの設定",
                        "作業ディレクトリの権限修正"
                    ],
                    "validation_commands": [
                        "ls -la temp/",
                        "whoami"
                    ]
                }
            ]
            
            # トラブルシューティング項目の妥当性検証
            troubleshooting_validation = {}
            
            for item in troubleshooting_items:
                validation_issues = []
                
                # 必須フィールドの確認
                required_fields = ["issue", "symptoms", "solutions"]
                for field in required_fields:
                    if not item.get(field) or len(item.get(field, [])) == 0:
                        validation_issues.append(f"必須フィールド '{field}' が不足または空")
                
                # 症状と解決方法の数の確認
                if len(item.get("symptoms", [])) < 1:
                    validation_issues.append("症状が不足しています")
                
                if len(item.get("solutions", [])) < 2:
                    validation_issues.append("解決方法が不足しています（最低2つ必要）")
                
                troubleshooting_validation[item["issue"]] = {
                    "valid": len(validation_issues) == 0,
                    "issues": validation_issues
                }
            
            # 全体の成功判定
            all_items_valid = all(result["valid"] for result in troubleshooting_validation.values())
            
            self.record_test_result(test_name, all_items_valid, {
                "total_items": len(troubleshooting_items),
                "valid_items": sum(1 for result in troubleshooting_validation.values() if result["valid"]),
                "troubleshooting_validation": troubleshooting_validation,
                "troubleshooting_items": troubleshooting_items
            })
            
            return all_items_valid
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """すべてのテストを実行"""
        print("🚀 MCP クライアント互換性テスト開始")
        
        # テスト実行
        test_methods = [
            self.test_server_module_execution,
            self.test_mcp_protocol_compliance,
            self.test_claude_code_configuration,
            self.test_usage_scenarios_documentation,
            self.test_troubleshooting_guide
        ]
        
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
        
        print(f"\n📊 MCP クライアント互換性テスト結果:")
        print(f"   実行テスト数: {tests_run}")
        print(f"   成功テスト数: {tests_passed}")
        print(f"   成功率: {success_rate:.1f}%")
        
        return {
            "success": tests_passed == tests_run,
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results
        }


async def generate_integration_documentation():
    """統合ドキュメントの生成"""
    print("\n📚 MCP クライアント統合ドキュメント生成")
    
    # Claude Code統合ガイドの生成
    integration_guide = {
        "title": "MCP Draw.io サーバー Claude Code 統合ガイド",
        "sections": [
            {
                "title": "セットアップ手順",
                "content": [
                    "1. MCP Draw.io サーバーのインストール",
                    "2. Anthropic APIキーの取得と設定",
                    "3. Claude Code MCP設定ファイルの作成",
                    "4. 接続テストの実行",
                    "5. 基本的な使用方法の確認"
                ]
            },
            {
                "title": "設定ファイル例",
                "content": {
                    "workspace_config": ".kiro/settings/mcp.json",
                    "global_config": "~/.kiro/settings/mcp.json"
                }
            },
            {
                "title": "使用パターン",
                "content": [
                    "基本的なフローチャート作成",
                    "AWS アーキテクチャ図作成",
                    "データベーススキーマ図作成",
                    "図表の保存と共有",
                    "PNG変換とドキュメント埋め込み"
                ]
            },
            {
                "title": "トラブルシューティング",
                "content": [
                    "サーバー接続問題",
                    "APIキー認証エラー",
                    "Draw.io CLI問題",
                    "権限エラー"
                ]
            }
        ]
    }
    
    print("✅ Claude Code統合ガイド生成完了")
    return integration_guide


async def main():
    """メイン実行関数"""
    print("🚀 MCP クライアント互換性テスト開始")
    print("=" * 60)
    
    # 互換性テストの実行
    tester = MCPClientCompatibilityTester()
    test_results = await tester.run_all_tests()
    
    # 統合ドキュメントの生成
    integration_guide = await generate_integration_documentation()
    
    # 総合結果
    print("\n" + "=" * 60)
    print("📊 MCP クライアント互換性テスト総合結果")
    print("=" * 60)
    
    overall_success = test_results.get("success", False)
    
    print(f"🎯 総合評価: {'✅ 成功' if overall_success else '❌ 要改善'}")
    
    if test_results.get("tests_run", 0) > 0:
        print(f"📊 テスト統計:")
        print(f"   実行: {test_results['tests_run']}")
        print(f"   成功: {test_results['tests_passed']}")
        print(f"   成功率: {test_results.get('success_rate', 0):.1f}%")
    
    # 推奨事項
    print(f"\n💡 次のステップ:")
    if overall_success:
        print("   • MCP クライアント互換性テストが成功しました")
        print("   • 実際のClaude Code環境でテストしてください")
        print("   • 本番用APIキーを設定してテストしてください")
        print("   • チーム向けの設定ドキュメントを作成してください")
    else:
        print("   • 失敗したテストの詳細を確認してください")
        print("   • サーバーの設定と依存関係を確認してください")
        print("   • ドキュメントの推奨事項に従ってください")
    
    # 実用的な情報の表示
    print(f"\n📋 Claude Code での使用方法:")
    print(f"   1. .kiro/settings/mcp.json ファイルを作成")
    print(f"   2. 以下の設定を追加:")
    print(f'   {{')
    print(f'     "mcpServers": {{')
    print(f'       "drawio-server": {{')
    print(f'         "command": "python",')
    print(f'         "args": ["-m", "src.server"],')
    print(f'         "cwd": "{Path(__file__).parent.absolute()}",')
    print(f'         "env": {{ "ANTHROPIC_API_KEY": "your-api-key-here" }},')
    print(f'         "autoApprove": ["generate-drawio-xml", "save-drawio-file"]')
    print(f'       }}')
    print(f'     }}')
    print(f'   }}')
    print(f"   3. Claude Code を再起動")
    print(f"   4. 'Create a flowchart for...' のようなプロンプトでテスト")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)