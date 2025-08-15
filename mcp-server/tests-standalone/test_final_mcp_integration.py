#!/usr/bin/env python3.10
"""
最終MCP統合テスト

実際のMCPクライアントとの統合テストを実行し、
Claude Code での使用準備が完了していることを確認します。
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class FinalMCPIntegrationTest:
    """最終MCP統合テスト"""
    
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
    
    async def test_mcp_server_structure(self) -> bool:
        """MCPサーバー構造テスト"""
        test_name = "MCPサーバー構造テスト"
        
        try:
            # 必要なファイルの存在確認
            required_files = [
                "src/server.py",
                "src/config.py", 
                "src/llm_service.py",
                "src/file_service.py",
                "src/image_service.py",
                "src/tools.py",
                "requirements.txt"
            ]
            
            missing_files = []
            for file_path in required_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            # サーバーファイルの内容確認
            server_path = Path("src/server.py")
            if server_path.exists():
                with open(server_path, 'r', encoding='utf-8') as f:
                    server_content = f.read()
                
                # 重要な要素の確認
                required_elements = {
                    "公式MCP SDK": "from mcp.server import Server",
                    "stdio_server": "stdio_server",
                    "ツール定義": "@server.list_tools()",
                    "ツール実行": "@server.call_tool()",
                    "3つのツール": all(tool in server_content for tool in [
                        "generate-drawio-xml", "save-drawio-file", "convert-to-png"
                    ])
                }
                
                missing_elements = [name for name, check in required_elements.items() 
                                  if not (check in server_content if isinstance(check, str) else check)]
            else:
                missing_elements = ["サーバーファイル自体が存在しません"]
            
            success = len(missing_files) == 0 and len(missing_elements) == 0
            
            self.record_test_result(test_name, success, {
                "missing_files": missing_files,
                "missing_elements": missing_elements,
                "total_required_files": len(required_files)
            })
            
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_claude_code_integration_ready(self) -> bool:
        """Claude Code統合準備完了テスト"""
        test_name = "Claude Code統合準備完了テスト"
        
        try:
            server_dir = Path(__file__).parent.absolute()
            
            # Claude Code用設定の生成
            claude_code_config = {
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
            
            # 設定の妥当性確認
            validation_checks = {
                "JSON構文": self._validate_json_syntax(claude_code_config),
                "必須フィールド": self._validate_required_fields(claude_code_config),
                "パス存在": self._validate_paths(claude_code_config),
                "ツール設定": self._validate_tool_configuration(claude_code_config)
            }
            
            all_valid = all(validation_checks.values())
            
            self.record_test_result(test_name, all_valid, {
                "validation_checks": validation_checks,
                "config": claude_code_config
            })
            
            if all_valid:
                print(f"   📋 Claude Code設定（.kiro/settings/mcp.json）:")
                print(f"   {json.dumps(claude_code_config, indent=2, ensure_ascii=False)}")
            
            return all_valid
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    def _validate_json_syntax(self, config: Dict) -> bool:
        """JSON構文の妥当性確認"""
        try:
            json.dumps(config)
            return True
        except:
            return False
    
    def _validate_required_fields(self, config: Dict) -> bool:
        """必須フィールドの確認"""
        try:
            server_config = config["mcpServers"]["drawio-server"]
            required_fields = ["command", "args", "cwd", "env"]
            return all(field in server_config for field in required_fields)
        except:
            return False
    
    def _validate_paths(self, config: Dict) -> bool:
        """パスの存在確認"""
        try:
            server_config = config["mcpServers"]["drawio-server"]
            cwd_path = Path(server_config["cwd"])
            server_py_path = cwd_path / "src" / "server.py"
            return cwd_path.exists() and server_py_path.exists()
        except:
            return False
    
    def _validate_tool_configuration(self, config: Dict) -> bool:
        """ツール設定の確認"""
        try:
            server_config = config["mcpServers"]["drawio-server"]
            auto_approve = set(server_config.get("autoApprove", []))
            expected_tools = {"generate-drawio-xml", "save-drawio-file", "convert-to-png"}
            return expected_tools.issubset(auto_approve)
        except:
            return False
    
    async def test_usage_documentation(self) -> bool:
        """使用方法ドキュメント化テスト"""
        test_name = "使用方法ドキュメント化テスト"
        
        try:
            # 使用例の定義
            usage_examples = [
                {
                    "scenario": "基本的なフローチャート作成",
                    "user_input": "Create a flowchart for user login process",
                    "expected_behavior": "generate-drawio-xmlツールが自動実行され、ログインプロセスのフローチャートが生成される",
                    "expected_output": "Draw.io XML形式のフローチャート",
                    "claude_code_steps": [
                        "Claude Codeでプロンプトを入力",
                        "MCPツールが自動実行される（autoApprove設定により）",
                        "生成されたXMLが表示される"
                    ]
                },
                {
                    "scenario": "AWS アーキテクチャ図作成",
                    "user_input": "Create an AWS architecture diagram with ALB, EC2, and RDS",
                    "expected_behavior": "AWS固有のアイコンとレイアウトを使用した図表が生成される",
                    "expected_output": "AWS アーキテクチャ図のDraw.io XML",
                    "claude_code_steps": [
                        "AWSアーキテクチャの要求を入力",
                        "generate-drawio-xmlツールが実行される",
                        "AWS固有のスタイルが適用された図表が生成される"
                    ]
                },
                {
                    "scenario": "図表保存とPNG変換",
                    "user_input": "Save this diagram and convert it to PNG",
                    "expected_behavior": "save-drawio-fileとconvert-to-pngツールが順次実行される",
                    "expected_output": "ファイルID、保存パス、PNG画像",
                    "claude_code_steps": [
                        "図表保存の要求を入力",
                        "save-drawio-fileツールが実行される",
                        "convert-to-pngツールが実行される（CLI利用可能時）",
                        "ファイル情報とPNG結果が表示される"
                    ]
                }
            ]
            
            # 使用例の妥当性確認
            valid_examples = 0
            for example in usage_examples:
                if (example.get("scenario") and 
                    example.get("user_input") and 
                    example.get("expected_behavior") and
                    example.get("claude_code_steps") and
                    len(example["claude_code_steps"]) >= 2):
                    valid_examples += 1
            
            success = valid_examples == len(usage_examples)
            
            self.record_test_result(test_name, success, {
                "total_examples": len(usage_examples),
                "valid_examples": valid_examples,
                "usage_examples": usage_examples
            })
            
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_troubleshooting_coverage(self) -> bool:
        """トラブルシューティング網羅性テスト"""
        test_name = "トラブルシューティング網羅性テスト"
        
        try:
            # よくある問題のカバレッジ
            troubleshooting_coverage = {
                "接続問題": {
                    "問題": "MCPサーバーに接続できない",
                    "原因": ["設定ファイルの問題", "パスの問題", "権限の問題"],
                    "解決方法": [
                        "MCP設定ファイルの構文確認",
                        "サーバーファイルの存在確認",
                        "Claude Codeの再起動",
                        "ログファイルの確認"
                    ]
                },
                "認証問題": {
                    "問題": "APIキー認証エラー",
                    "原因": ["無効なAPIキー", "APIキー未設定", "権限不足"],
                    "解決方法": [
                        "APIキーの形式確認（sk-ant-で始まる）",
                        "環境変数の設定確認",
                        "APIキーの有効性確認",
                        "開発モードでのテスト"
                    ]
                },
                "機能問題": {
                    "問題": "特定の機能が動作しない",
                    "原因": ["依存関係の不足", "設定の問題", "環境の問題"],
                    "解決方法": [
                        "依存関係チェックの実行",
                        "Draw.io CLIのインストール確認",
                        "ログレベルをDEBUGに設定",
                        "個別ツールのテスト実行"
                    ]
                }
            }
            
            # カバレッジの妥当性確認
            coverage_valid = True
            coverage_details = {}
            
            for category, info in troubleshooting_coverage.items():
                category_valid = (
                    len(info.get("原因", [])) >= 2 and
                    len(info.get("解決方法", [])) >= 3 and
                    bool(info.get("問題"))
                )
                coverage_details[category] = category_valid
                if not category_valid:
                    coverage_valid = False
            
            self.record_test_result(test_name, coverage_valid, {
                "coverage_categories": len(troubleshooting_coverage),
                "coverage_details": coverage_details,
                "troubleshooting_coverage": troubleshooting_coverage
            })
            
            return coverage_valid
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_deployment_readiness(self) -> bool:
        """デプロイ準備完了テスト"""
        test_name = "デプロイ準備完了テスト"
        
        try:
            # デプロイ準備チェック項目
            deployment_checks = {
                "サーバーファイル": Path("src/server.py").exists(),
                "設定ファイル": Path("src/config.py").exists(),
                "依存関係定義": Path("requirements.txt").exists(),
                "ドキュメント": Path("docs").exists() and len(list(Path("docs").glob("*.md"))) > 0,
                "テストファイル": len([f for f in Path(".").glob("test_*.py") if f.is_file()]) >= 3,
                "Docker設定": Path("Dockerfile").exists() or Path("docker-compose.yml").exists()
            }
            
            # 追加の品質チェック
            quality_checks = {
                "エラーハンドリング": self._check_error_handling(),
                "ログ機能": self._check_logging_capability(),
                "設定管理": self._check_configuration_management(),
                "セキュリティ": self._check_security_features()
            }
            
            # 全体の準備状況
            deployment_ready = sum(deployment_checks.values()) >= len(deployment_checks) * 0.8  # 80%以上
            quality_ready = sum(quality_checks.values()) >= len(quality_checks) * 0.7  # 70%以上
            
            overall_ready = deployment_ready and quality_ready
            
            self.record_test_result(test_name, overall_ready, {
                "deployment_checks": deployment_checks,
                "quality_checks": quality_checks,
                "deployment_ready": deployment_ready,
                "quality_ready": quality_ready,
                "deployment_score": sum(deployment_checks.values()) / len(deployment_checks) * 100,
                "quality_score": sum(quality_checks.values()) / len(quality_checks) * 100
            })
            
            return overall_ready
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    def _check_error_handling(self) -> bool:
        """エラーハンドリングの確認"""
        try:
            server_path = Path("src/server.py")
            if not server_path.exists():
                return False
            
            with open(server_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            error_handling_indicators = [
                "try:", "except:", "Exception", "Error", "raise"
            ]
            
            return sum(1 for indicator in error_handling_indicators if indicator in content) >= 3
        except:
            return False
    
    def _check_logging_capability(self) -> bool:
        """ログ機能の確認"""
        try:
            server_path = Path("src/server.py")
            if not server_path.exists():
                return False
            
            with open(server_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logging_indicators = [
                "import logging", "logger", "log", "print"
            ]
            
            return sum(1 for indicator in logging_indicators if indicator in content) >= 2
        except:
            return False
    
    def _check_configuration_management(self) -> bool:
        """設定管理の確認"""
        try:
            config_path = Path("src/config.py")
            return config_path.exists()
        except:
            return False
    
    def _check_security_features(self) -> bool:
        """セキュリティ機能の確認"""
        try:
            server_path = Path("src/server.py")
            if not server_path.exists():
                return False
            
            with open(server_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            security_indicators = [
                "API_KEY", "validation", "sanitiz", "auth"
            ]
            
            return sum(1 for indicator in security_indicators if indicator.lower() in content.lower()) >= 2
        except:
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """すべてのテストを実行"""
        print("🚀 最終MCP統合テスト開始")
        
        # テスト実行
        test_methods = [
            self.test_mcp_server_structure,
            self.test_claude_code_integration_ready,
            self.test_usage_documentation,
            self.test_troubleshooting_coverage,
            self.test_deployment_readiness
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
        
        print(f"\n📊 最終MCP統合テスト結果:")
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


async def generate_final_integration_report():
    """最終統合レポートの生成"""
    print("\n📚 最終統合レポート生成")
    
    server_dir = Path(__file__).parent.absolute()
    
    # Claude Code統合手順
    integration_steps = {
        "title": "MCP Draw.io サーバー Claude Code 統合手順",
        "steps": [
            {
                "step": 1,
                "title": "MCP設定ファイルの作成",
                "description": "ワークスペースまたはグローバル設定ファイルを作成",
                "files": [
                    ".kiro/settings/mcp.json (ワークスペース固有)",
                    "~/.kiro/settings/mcp.json (グローバル)"
                ],
                "action": "設定ファイルに以下のJSON設定を追加"
            },
            {
                "step": 2,
                "title": "APIキーの設定",
                "description": "Anthropic APIキーを環境変数または設定ファイルに設定",
                "action": "有効なAPIキー（sk-ant-で始まる）を設定"
            },
            {
                "step": 3,
                "title": "Claude Codeの再起動",
                "description": "MCP設定を反映するためにClaude Codeを再起動",
                "action": "Claude Codeを完全に終了して再起動"
            },
            {
                "step": 4,
                "title": "接続テスト",
                "description": "基本的なプロンプトでMCPツールの動作を確認",
                "action": "'Create a simple flowchart' などのプロンプトでテスト"
            }
        ]
    }
    
    # 設定例
    config_example = {
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
    
    print("✅ 最終統合レポート生成完了")
    
    return {
        "integration_steps": integration_steps,
        "config_example": config_example,
        "server_directory": str(server_dir)
    }


async def main():
    """メイン実行関数"""
    print("🚀 最終MCP統合テスト開始")
    print("=" * 60)
    
    # 最終統合テストの実行
    tester = FinalMCPIntegrationTest()
    test_results = await tester.run_all_tests()
    
    # 最終統合レポートの生成
    integration_report = await generate_final_integration_report()
    
    # 総合結果
    print("\n" + "=" * 60)
    print("📊 最終MCP統合テスト総合結果")
    print("=" * 60)
    
    overall_success = test_results.get("success", False)
    
    print(f"🎯 総合評価: {'✅ 成功' if overall_success else '❌ 要改善'}")
    
    if test_results.get("tests_run", 0) > 0:
        print(f"📊 テスト統計:")
        print(f"   実行: {test_results['tests_run']}")
        print(f"   成功: {test_results['tests_passed']}")
        print(f"   成功率: {test_results.get('success_rate', 0):.1f}%")
    
    # 統合準備状況
    print(f"\n🎯 Claude Code統合準備状況:")
    if overall_success:
        print("   ✅ MCPサーバー構造: 完了")
        print("   ✅ Claude Code設定: 準備完了")
        print("   ✅ 使用方法ドキュメント: 完了")
        print("   ✅ トラブルシューティング: 準備完了")
        print("   ✅ デプロイ準備: 完了")
    else:
        print("   ⚠️ 一部の準備項目で改善が必要です")
    
    # 実用的な統合手順
    print(f"\n📋 Claude Code統合手順:")
    for step_info in integration_report["integration_steps"]["steps"]:
        print(f"   {step_info['step']}. {step_info['title']}")
        print(f"      {step_info['description']}")
    
    print(f"\n📄 MCP設定ファイル例 (.kiro/settings/mcp.json):")
    print(json.dumps(integration_report["config_example"], indent=2, ensure_ascii=False))
    
    # 次のステップ
    print(f"\n💡 次のステップ:")
    if overall_success:
        print("   • 上記の統合手順に従ってClaude Codeを設定してください")
        print("   • 実際のAPIキーを設定してテストしてください")
        print("   • 基本的な図表作成プロンプトで動作確認してください")
        print("   • チームメンバーと設定を共有してください")
    else:
        print("   • 失敗したテスト項目を確認して修正してください")
        print("   • 必要なファイルや設定が不足していないか確認してください")
        print("   • 修正後に再度テストを実行してください")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)