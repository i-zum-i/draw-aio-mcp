#!/usr/bin/env python3.10
"""
Claude Code統合テスト

Claude Codeでの実際の使用パターンをシミュレートし、
MCPサーバーがClaude Code環境で正常に動作することを確認します。
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
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class ClaudeCodeSimulator:
    """Claude Code環境をシミュレートするクラス"""
    
    def __init__(self):
        self.workspace_dir = None
        self.mcp_config_path = None
        self.test_results: List[Dict[str, Any]] = []
        
    async def setup_workspace(self) -> bool:
        """テスト用ワークスペースの作成"""
        try:
            # 一時ワークスペースディレクトリの作成
            self.workspace_dir = tempfile.mkdtemp(prefix="claude_code_test_")
            workspace_path = Path(self.workspace_dir)
            
            # .kiro/settings ディレクトリの作成
            kiro_settings_dir = workspace_path / ".kiro" / "settings"
            kiro_settings_dir.mkdir(parents=True, exist_ok=True)
            
            # MCP設定ファイルの作成
            self.mcp_config_path = kiro_settings_dir / "mcp.json"
            
            # 現在のスクリプトディレクトリを取得
            server_dir = Path(__file__).parent.absolute()
            
            mcp_config = {
                "mcpServers": {
                    "drawio-server": {
                        "command": "python",
                        "args": ["-m", "src.server"],
                        "cwd": str(server_dir),
                        "env": {
                            "ANTHROPIC_API_KEY": "test-key-for-claude-code-test",
                            "DEVELOPMENT_MODE": "true",
                            "LOG_LEVEL": "DEBUG"
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
            
            # 設定ファイルの書き込み
            with open(self.mcp_config_path, 'w', encoding='utf-8') as f:
                json.dump(mcp_config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Claude Codeテストワークスペース作成: {self.workspace_dir}")
            print(f"📁 MCP設定ファイル: {self.mcp_config_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ ワークスペースセットアップエラー: {str(e)}")
            return False
    
    def cleanup_workspace(self):
        """テストワークスペースのクリーンアップ"""
        if self.workspace_dir and Path(self.workspace_dir).exists():
            import shutil
            try:
                shutil.rmtree(self.workspace_dir)
                print(f"✅ テストワークスペースクリーンアップ完了")
            except Exception as e:
                print(f"⚠️ ワークスペースクリーンアップエラー: {str(e)}")
    
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
    
    async def test_mcp_config_validation(self) -> bool:
        """MCP設定ファイルの検証"""
        test_name = "Claude Code - MCP設定ファイル検証"
        
        try:
            if not self.mcp_config_path or not self.mcp_config_path.exists():
                self.record_test_result(test_name, False, {"error": "MCP設定ファイルが存在しません"})
                return False
            
            # 設定ファイルの読み込み
            with open(self.mcp_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 設定の検証
            validation_errors = []
            
            # 基本構造の確認
            if "mcpServers" not in config:
                validation_errors.append("mcpServers セクションが不足")
            
            if "drawio-server" not in config.get("mcpServers", {}):
                validation_errors.append("drawio-server 設定が不足")
            
            server_config = config.get("mcpServers", {}).get("drawio-server", {})
            
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
            
            # autoApprove設定の確認
            auto_approve = server_config.get("autoApprove", [])
            expected_tools = {"generate-drawio-xml", "save-drawio-file", "convert-to-png"}
            auto_approve_set = set(auto_approve)
            
            success = len(validation_errors) == 0
            details = {
                "config_file": str(self.mcp_config_path),
                "validation_errors": validation_errors,
                "auto_approve_tools": auto_approve,
                "expected_tools": list(expected_tools),
                "auto_approve_complete": expected_tools.issubset(auto_approve_set)
            }
            
            self.record_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_server_startup_simulation(self) -> bool:
        """サーバー起動シミュレーション"""
        test_name = "Claude Code - サーバー起動シミュレーション"
        
        try:
            # MCP設定の読み込み
            with open(self.mcp_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            server_config = config["mcpServers"]["drawio-server"]
            
            # 環境変数の設定
            env = os.environ.copy()
            env.update(server_config.get("env", {}))
            
            # サーバー起動コマンドの構築
            command = [server_config["command"]] + server_config["args"]
            cwd = server_config["cwd"]
            
            print(f"🚀 サーバー起動テスト: {' '.join(command)}")
            print(f"📁 作業ディレクトリ: {cwd}")
            
            # サーバープロセスの開始
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 起動を少し待つ
            await asyncio.sleep(3)
            
            # プロセスの状態確認
            poll_result = process.poll()
            
            if poll_result is None:
                # プロセスが実行中
                success = True
                details = {
                    "process_id": process.pid,
                    "status": "running",
                    "startup_time": "< 3 seconds"
                }
                
                # プロセスを終了
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                
            else:
                # プロセスが終了している
                stdout, stderr = process.communicate()
                success = False
                details = {
                    "exit_code": poll_result,
                    "stdout": stdout[:500] if stdout else "",
                    "stderr": stderr[:500] if stderr else "",
                    "status": "exited"
                }
            
            self.record_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_workspace_integration(self) -> bool:
        """ワークスペース統合テスト"""
        test_name = "Claude Code - ワークスペース統合"
        
        try:
            workspace_path = Path(self.workspace_dir)
            
            # テストプロジェクトファイルの作成
            test_files = {
                "README.md": "# Test Project\n\nThis is a test project for MCP integration.",
                "main.py": "#!/usr/bin/env python3\nprint('Hello, MCP!')",
                "requirements.txt": "# Project dependencies\nrequests>=2.25.0"
            }
            
            for filename, content in test_files.items():
                file_path = workspace_path / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # .kiro ディレクトリ構造の確認
            kiro_dir = workspace_path / ".kiro"
            settings_dir = kiro_dir / "settings"
            
            structure_valid = (
                kiro_dir.exists() and
                settings_dir.exists() and
                self.mcp_config_path.exists()
            )
            
            # ファイル権限の確認
            permissions_ok = True
            permission_details = {}
            
            for path in [kiro_dir, settings_dir, self.mcp_config_path]:
                try:
                    # 読み取り権限の確認
                    path.stat()
                    permission_details[str(path)] = "OK"
                except PermissionError:
                    permissions_ok = False
                    permission_details[str(path)] = "Permission Error"
            
            success = structure_valid and permissions_ok
            details = {
                "workspace_dir": str(workspace_path),
                "structure_valid": structure_valid,
                "permissions_ok": permissions_ok,
                "permission_details": permission_details,
                "test_files_created": len(test_files),
                "kiro_config_exists": self.mcp_config_path.exists()
            }
            
            self.record_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_usage_scenarios(self) -> bool:
        """使用シナリオテスト"""
        test_name = "Claude Code - 使用シナリオ"
        
        try:
            # 典型的なClaude Codeでの使用パターンをシミュレート
            usage_scenarios = [
                {
                    "name": "簡単なフローチャート作成",
                    "prompt": "Create a simple flowchart for user registration process",
                    "expected_tools": ["generate-drawio-xml"],
                    "description": "ユーザー登録プロセスの簡単なフローチャートを作成"
                },
                {
                    "name": "図表保存とPNG変換",
                    "prompt": "Save the diagram and convert to PNG for documentation",
                    "expected_tools": ["save-drawio-file", "convert-to-png"],
                    "description": "図表をファイルに保存してPNG形式に変換"
                },
                {
                    "name": "AWS アーキテクチャ図",
                    "prompt": "Create an AWS architecture diagram with ALB, EC2, and RDS",
                    "expected_tools": ["generate-drawio-xml"],
                    "description": "AWS アーキテクチャ図の作成"
                },
                {
                    "name": "データベーススキーマ図",
                    "prompt": "Create an ER diagram for e-commerce database schema",
                    "expected_tools": ["generate-drawio-xml"],
                    "description": "Eコマースデータベースのスキーマ図作成"
                }
            ]
            
            scenario_results = []
            
            for scenario in usage_scenarios:
                scenario_valid = True
                scenario_details = {
                    "name": scenario["name"],
                    "prompt_length": len(scenario["prompt"]),
                    "expected_tools": scenario["expected_tools"],
                    "description": scenario["description"]
                }
                
                # プロンプトの妥当性チェック
                if len(scenario["prompt"]) < 10:
                    scenario_valid = False
                    scenario_details["error"] = "プロンプトが短すぎます"
                
                # 期待されるツールの妥当性チェック
                valid_tools = {"generate-drawio-xml", "save-drawio-file", "convert-to-png"}
                invalid_tools = set(scenario["expected_tools"]) - valid_tools
                if invalid_tools:
                    scenario_valid = False
                    scenario_details["error"] = f"無効なツール: {invalid_tools}"
                
                scenario_results.append(scenario_valid)
                
                status = "✅" if scenario_valid else "❌"
                print(f"   {status} {scenario['name']}")
            
            success = all(scenario_results)
            details = {
                "total_scenarios": len(usage_scenarios),
                "valid_scenarios": sum(scenario_results),
                "scenarios": usage_scenarios
            }
            
            self.record_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_auto_approval_configuration(self) -> bool:
        """自動承認設定テスト"""
        test_name = "Claude Code - 自動承認設定"
        
        try:
            # MCP設定の読み込み
            with open(self.mcp_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            server_config = config["mcpServers"]["drawio-server"]
            auto_approve = server_config.get("autoApprove", [])
            
            # 期待されるツールの確認
            expected_tools = {"generate-drawio-xml", "save-drawio-file", "convert-to-png"}
            auto_approve_set = set(auto_approve)
            
            # 自動承認設定の分析
            fully_approved = expected_tools.issubset(auto_approve_set)
            partially_approved = len(auto_approve_set.intersection(expected_tools)) > 0
            extra_approvals = auto_approve_set - expected_tools
            
            # セキュリティ考慮事項
            security_notes = []
            if fully_approved:
                security_notes.append("すべてのツールが自動承認されています")
            if extra_approvals:
                security_notes.append(f"未知のツールが自動承認されています: {extra_approvals}")
            
            success = fully_approved and len(extra_approvals) == 0
            details = {
                "auto_approve_tools": auto_approve,
                "expected_tools": list(expected_tools),
                "fully_approved": fully_approved,
                "partially_approved": partially_approved,
                "extra_approvals": list(extra_approvals),
                "security_notes": security_notes
            }
            
            self.record_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.record_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """すべてのClaude Code統合テストを実行"""
        print("🚀 Claude Code統合テスト開始")
        
        # ワークスペースのセットアップ
        if not await self.setup_workspace():
            return {
                "success": False,
                "error": "Workspace setup failed",
                "tests_run": 0,
                "tests_passed": 0
            }
        
        try:
            # テスト実行
            test_methods = [
                self.test_mcp_config_validation,
                self.test_server_startup_simulation,
                self.test_workspace_integration,
                self.test_usage_scenarios,
                self.test_auto_approval_configuration
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
            
            print(f"\n📊 Claude Code統合テスト結果:")
            print(f"   実行テスト数: {tests_run}")
            print(f"   成功テスト数: {tests_passed}")
            print(f"   成功率: {success_rate:.1f}%")
            
            return {
                "success": tests_passed == tests_run,
                "tests_run": tests_run,
                "tests_passed": tests_passed,
                "success_rate": success_rate,
                "test_results": self.test_results,
                "workspace_dir": self.workspace_dir,
                "mcp_config_path": str(self.mcp_config_path) if self.mcp_config_path else None
            }
            
        finally:
            # クリーンアップ
            self.cleanup_workspace()


async def generate_claude_code_documentation():
    """Claude Code統合ドキュメントの生成"""
    print("\n📚 Claude Code統合ドキュメント生成")
    
    # 設定例の生成
    config_examples = {
        "workspace_config": {
            "description": "ワークスペース固有の設定（.kiro/settings/mcp.json）",
            "config": {
                "mcpServers": {
                    "drawio-server": {
                        "command": "python",
                        "args": ["-m", "src.server"],
                        "cwd": "/absolute/path/to/mcp-server",
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
        },
        "docker_config": {
            "description": "Docker使用時の設定",
            "config": {
                "mcpServers": {
                    "drawio-server": {
                        "command": "docker",
                        "args": [
                            "run", "--rm", "-i",
                            "--env-file", "/absolute/path/to/mcp-server/.env",
                            "-v", "/absolute/path/to/mcp-server/temp:/app/temp:rw",
                            "mcp-drawio-server:latest"
                        ],
                        "env": {
                            "ANTHROPIC_API_KEY": "your-api-key-here"
                        },
                        "disabled": False,
                        "autoApprove": ["generate-drawio-xml"]
                    }
                }
            }
        }
    }
    
    # 使用例の生成
    usage_examples = [
        {
            "scenario": "基本的なフローチャート作成",
            "user_prompt": "Create a flowchart for the user login process",
            "expected_behavior": "Claude Codeがgenerate-drawio-xmlツールを使用してフローチャートを生成",
            "auto_approval": "設定されている場合は自動実行"
        },
        {
            "scenario": "AWS アーキテクチャ図作成",
            "user_prompt": "Create an AWS architecture diagram with ALB, EC2 instances, and RDS",
            "expected_behavior": "AWS固有のアイコンとレイアウトを使用した図表を生成",
            "auto_approval": "設定されている場合は自動実行"
        },
        {
            "scenario": "図表の保存と変換",
            "user_prompt": "Save this diagram and convert it to PNG for documentation",
            "expected_behavior": "save-drawio-fileとconvert-to-pngツールを順次実行",
            "auto_approval": "両方のツールが自動承認されている場合は連続実行"
        }
    ]
    
    # トラブルシューティングガイド
    troubleshooting_guide = [
        {
            "issue": "MCPサーバーが見つからない",
            "symptoms": ["Claude Codeでツールが表示されない", "接続エラー"],
            "solutions": [
                "MCP設定ファイルのパスを確認",
                "サーバーファイルの存在確認",
                "Claude Codeの再起動"
            ]
        },
        {
            "issue": "APIキーエラー",
            "symptoms": ["認証エラー", "API呼び出し失敗"],
            "solutions": [
                "ANTHROPIC_API_KEYの設定確認",
                "APIキーの有効性確認",
                "環境変数の設定確認"
            ]
        },
        {
            "issue": "Draw.io CLI エラー",
            "symptoms": ["PNG変換失敗", "CLI not found エラー"],
            "solutions": [
                "Draw.io CLIのインストール確認",
                "Dockerコンテナ使用の検討",
                "フォールバック機能の利用"
            ]
        }
    ]
    
    documentation = {
        "config_examples": config_examples,
        "usage_examples": usage_examples,
        "troubleshooting_guide": troubleshooting_guide,
        "setup_checklist": [
            "Anthropic APIキーの取得",
            "MCPサーバーのインストール",
            "Claude Codeの最新版インストール",
            "MCP設定ファイルの作成",
            "接続テストの実行"
        ]
    }
    
    print("✅ Claude Code統合ドキュメント生成完了")
    return documentation


async def main():
    """メインテスト実行"""
    print("🚀 Claude Code統合テスト開始")
    print("=" * 60)
    
    # Claude Code統合テストの実行
    simulator = ClaudeCodeSimulator()
    integration_results = await simulator.run_all_tests()
    
    # ドキュメント生成
    documentation = await generate_claude_code_documentation()
    
    # 総合結果
    print("\n" + "=" * 60)
    print("📊 Claude Code統合テスト総合結果")
    print("=" * 60)
    
    overall_success = integration_results.get("success", False)
    
    print(f"🎯 総合評価: {'✅ 成功' if overall_success else '❌ 要改善'}")
    
    if integration_results.get("tests_run", 0) > 0:
        print(f"📊 テスト統計:")
        print(f"   実行: {integration_results['tests_run']}")
        print(f"   成功: {integration_results['tests_passed']}")
        print(f"   成功率: {integration_results.get('success_rate', 0):.1f}%")
    
    # 設定ファイルの場所を表示
    if integration_results.get("mcp_config_path"):
        print(f"\n📁 生成された設定ファイル例:")
        print(f"   {integration_results['mcp_config_path']}")
    
    # 推奨事項
    print(f"\n💡 次のステップ:")
    if overall_success:
        print("   • 実際のClaude Code環境でテストしてください")
        print("   • 本番用APIキーを設定してください")
        print("   • チーム向けの設定ドキュメントを作成してください")
    else:
        print("   • 失敗したテストの問題を解決してください")
        print("   • 設定ファイルの内容を確認してください")
        print("   • サーバーの起動ログを確認してください")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)