#!/usr/bin/env python3.10
"""
MCP クライアント統合テスト実行スクリプト

公式MCPクライアントとの統合テストを包括的に実行し、
実環境での動作保証を提供します。
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class MCPClientIntegrationTestRunner:
    """MCP クライアント統合テスト実行管理クラス"""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.start_time = time.time()
        self.test_scripts = [
            {
                "name": "公式MCPクライアント統合テスト",
                "script": "test_official_mcp_client_integration.py",
                "description": "公式MCPクライアントライブラリを使用した統合テスト",
                "critical": True
            },
            {
                "name": "Claude Code統合テスト",
                "script": "test_claude_code_integration.py", 
                "description": "Claude Code環境での動作確認テスト",
                "critical": True
            }
        ]
    
    def print_header(self):
        """テストヘッダーの表示"""
        print("=" * 80)
        print("🚀 MCP クライアント統合テスト実行")
        print("=" * 80)
        print(f"📅 実行日時: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python バージョン: {sys.version}")
        print(f"📁 作業ディレクトリ: {Path.cwd()}")
        print(f"📋 実行予定テスト数: {len(self.test_scripts)}")
        print("=" * 80)
    
    async def check_prerequisites(self) -> bool:
        """前提条件のチェック"""
        print("\n🔍 前提条件チェック中...")
        
        prerequisites_ok = True
        issues = []
        
        # Python バージョンチェック
        if sys.version_info < (3, 10):
            prerequisites_ok = False
            issues.append(f"Python 3.10+ が必要です (現在: {sys.version_info.major}.{sys.version_info.minor})")
        else:
            print(f"✅ Python バージョン: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        
        # 必要なファイルの存在確認
        required_files = [
            "src/server.py",
            "src/config.py",
            "src/llm_service.py",
            "src/file_service.py",
            "src/image_service.py",
            "requirements.txt"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                prerequisites_ok = False
                issues.append(f"必要なファイルが見つかりません: {file_path}")
            else:
                print(f"✅ ファイル確認: {file_path}")
        
        # テストスクリプトの存在確認
        for test_info in self.test_scripts:
            script_path = Path(test_info["script"])
            if not script_path.exists():
                prerequisites_ok = False
                issues.append(f"テストスクリプトが見つかりません: {script_path}")
            else:
                print(f"✅ テストスクリプト: {test_info['script']}")
        
        # MCP ライブラリの確認
        try:
            import mcp
            print(f"✅ MCP ライブラリ: {mcp.__version__ if hasattr(mcp, '__version__') else '利用可能'}")
        except ImportError:
            print("⚠️ MCP ライブラリが見つかりません（一部のテストがスキップされる可能性があります）")
        
        # 環境変数の確認
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            if api_key.startswith('sk-ant-'):
                print("✅ ANTHROPIC_API_KEY: 設定済み（本番キー）")
            else:
                print("⚠️ ANTHROPIC_API_KEY: テスト用キー")
        else:
            print("⚠️ ANTHROPIC_API_KEY: 未設定（テスト用キーが使用されます）")
        
        if not prerequisites_ok:
            print("\n❌ 前提条件チェック失敗:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        
        print("✅ 前提条件チェック完了")
        return True
    
    async def run_test_script(self, test_info: Dict[str, Any]) -> Dict[str, Any]:
        """個別テストスクリプトの実行"""
        script_name = test_info["name"]
        script_path = test_info["script"]
        
        print(f"\n🧪 {script_name} 実行中...")
        print(f"📄 スクリプト: {script_path}")
        print(f"📝 説明: {test_info['description']}")
        
        start_time = time.time()
        
        try:
            # テストスクリプトの実行
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path.cwd()
            )
            
            stdout, stderr = process.communicate(timeout=300)  # 5分タイムアウト
            execution_time = time.time() - start_time
            
            # 結果の解析
            success = process.returncode == 0
            
            result = {
                "name": script_name,
                "script": script_path,
                "success": success,
                "execution_time": execution_time,
                "return_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "critical": test_info.get("critical", False)
            }
            
            # 結果の表示
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"{status} {script_name} ({execution_time:.2f}秒)")
            
            if not success:
                print(f"   終了コード: {process.returncode}")
                if stderr:
                    print(f"   エラー出力: {stderr[:200]}...")
            
            return result
            
        except subprocess.TimeoutExpired:
            process.kill()
            execution_time = time.time() - start_time
            
            result = {
                "name": script_name,
                "script": script_path,
                "success": False,
                "execution_time": execution_time,
                "return_code": -1,
                "stdout": "",
                "stderr": "テストがタイムアウトしました（5分）",
                "critical": test_info.get("critical", False)
            }
            
            print(f"⏰ タイムアウト {script_name} ({execution_time:.2f}秒)")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = {
                "name": script_name,
                "script": script_path,
                "success": False,
                "execution_time": execution_time,
                "return_code": -1,
                "stdout": "",
                "stderr": f"実行エラー: {str(e)}",
                "critical": test_info.get("critical", False)
            }
            
            print(f"❌ 実行エラー {script_name}: {str(e)}")
            return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """すべての統合テストを実行"""
        print("\n🚀 統合テスト実行開始")
        
        test_results = []
        
        for test_info in self.test_scripts:
            result = await self.run_test_script(test_info)
            test_results.append(result)
            
            # クリティカルテストが失敗した場合の処理
            if not result["success"] and result["critical"]:
                print(f"\n⚠️ クリティカルテスト '{result['name']}' が失敗しました")
                print("   残りのテストを継続しますが、全体の成功は期待できません")
        
        return test_results
    
    def generate_summary_report(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """テスト結果のサマリーレポート生成"""
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        critical_tests = [result for result in test_results if result["critical"]]
        critical_passed = sum(1 for result in critical_tests if result["success"])
        critical_failed = len(critical_tests) - critical_passed
        
        total_execution_time = sum(result["execution_time"] for result in test_results)
        overall_execution_time = time.time() - self.start_time
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        critical_success_rate = (critical_passed / len(critical_tests) * 100) if critical_tests else 100
        
        overall_success = (
            successful_tests == total_tests and
            critical_failed == 0
        )
        
        summary = {
            "overall_success": overall_success,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "critical_tests": len(critical_tests),
            "critical_passed": critical_passed,
            "critical_failed": critical_failed,
            "critical_success_rate": critical_success_rate,
            "total_execution_time": total_execution_time,
            "overall_execution_time": overall_execution_time,
            "test_results": test_results
        }
        
        return summary
    
    def print_summary_report(self, summary: Dict[str, Any]):
        """サマリーレポートの表示"""
        print("\n" + "=" * 80)
        print("📊 MCP クライアント統合テスト結果サマリー")
        print("=" * 80)
        
        # 全体結果
        overall_status = "✅ 成功" if summary["overall_success"] else "❌ 失敗"
        print(f"🎯 総合評価: {overall_status}")
        
        # 統計情報
        print(f"\n📈 テスト統計:")
        print(f"   総テスト数: {summary['total_tests']}")
        print(f"   成功: {summary['successful_tests']}")
        print(f"   失敗: {summary['failed_tests']}")
        print(f"   成功率: {summary['success_rate']:.1f}%")
        
        # クリティカルテスト統計
        print(f"\n🔥 クリティカルテスト:")
        print(f"   クリティカルテスト数: {summary['critical_tests']}")
        print(f"   成功: {summary['critical_passed']}")
        print(f"   失敗: {summary['critical_failed']}")
        print(f"   成功率: {summary['critical_success_rate']:.1f}%")
        
        # 実行時間
        print(f"\n⏱️ 実行時間:")
        print(f"   テスト実行時間: {summary['total_execution_time']:.2f}秒")
        print(f"   全体実行時間: {summary['overall_execution_time']:.2f}秒")
        
        # 個別テスト結果
        print(f"\n📋 個別テスト結果:")
        for result in summary["test_results"]:
            status = "✅" if result["success"] else "❌"
            critical_mark = " 🔥" if result["critical"] else ""
            print(f"   {status} {result['name']}{critical_mark} ({result['execution_time']:.2f}秒)")
            
            if not result["success"]:
                print(f"      終了コード: {result['return_code']}")
                if result["stderr"]:
                    error_preview = result["stderr"][:100].replace('\n', ' ')
                    print(f"      エラー: {error_preview}...")
        
        # 推奨事項
        print(f"\n💡 推奨事項:")
        if summary["overall_success"]:
            print("   • すべてのテストが成功しました！")
            print("   • 実際のClaude Code環境でテストしてください")
            print("   • 本番環境での動作確認を行ってください")
        else:
            print("   • 失敗したテストの詳細を確認してください")
            if summary["critical_failed"] > 0:
                print("   • クリティカルテストの失敗を優先的に修正してください")
            print("   • ログファイルとエラーメッセージを確認してください")
            print("   • 必要に応じて依存関係を再インストールしてください")
        
        print("=" * 80)
    
    def save_detailed_report(self, summary: Dict[str, Any], output_file: str = "mcp_integration_test_report.json"):
        """詳細レポートをJSONファイルに保存"""
        try:
            report_data = {
                "test_run_info": {
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "working_directory": str(Path.cwd()),
                    "environment": {
                        "ANTHROPIC_API_KEY": "設定済み" if os.environ.get('ANTHROPIC_API_KEY') else "未設定"
                    }
                },
                "summary": summary
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📄 詳細レポート保存: {output_file}")
            
        except Exception as e:
            print(f"⚠️ レポート保存エラー: {str(e)}")
    
    async def run(self) -> bool:
        """統合テストの実行"""
        self.print_header()
        
        # 前提条件チェック
        if not await self.check_prerequisites():
            print("\n❌ 前提条件が満たされていないため、テストを中止します")
            return False
        
        # テスト実行
        test_results = await self.run_all_tests()
        
        # サマリー生成
        summary = self.generate_summary_report(test_results)
        
        # 結果表示
        self.print_summary_report(summary)
        
        # 詳細レポート保存
        self.save_detailed_report(summary)
        
        return summary["overall_success"]


async def main():
    """メイン実行関数"""
    runner = MCPClientIntegrationTestRunner()
    success = await runner.run()
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⌨️ テスト実行が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)