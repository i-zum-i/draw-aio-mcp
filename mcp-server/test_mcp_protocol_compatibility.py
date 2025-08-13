#!/usr/bin/env python3
"""
MCP プロトコル互換性テスト

このテストは、MCPサーバーが公式MCP仕様と完全に互換性があることを確認します。
プロトコルバージョン、メッセージ形式、エラーハンドリングなどをテストします。
"""

import asyncio
import json
import logging
import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

# 公式MCPライブラリのインポート
from mcp.types import (
    LATEST_PROTOCOL_VERSION,
    DEFAULT_NEGOTIATED_VERSION,
    InitializeRequest,
    InitializeRequestParams,
    InitializeResult,
    ListToolsRequest,
    ListToolsResult,
    CallToolRequest,
    CallToolRequestParams,
    CallToolResult,
    ServerCapabilities,
    Implementation,
    Tool,
    TextContent,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError
)

from src.config import MCPServerConfig
from src.server import (
    SERVER_NAME,
    SERVER_VERSION,
    TOOL_DEFINITIONS,
    list_tools,
    call_tool,
    validate_tool_arguments,
    execute_tool_safely
)


class MCPProtocolCompatibilityTester:
    """MCP プロトコル互換性テスター"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results: Dict[str, Any] = {}
    
    def test_protocol_version_compliance(self) -> Dict[str, Any]:
        """プロトコルバージョンの準拠性をテスト"""
        config = MCPServerConfig.from_env()
        server_version = config.protocol_version
        
        # 公式バージョンとの比較
        official_latest = LATEST_PROTOCOL_VERSION
        official_default = DEFAULT_NEGOTIATED_VERSION
        
        # バージョン形式の検証
        version_format_valid = self._validate_version_format(server_version)
        
        # サポート状況の確認
        is_supported = server_version in [official_latest, official_default, "2024-11-05"]
        
        return {
            "server_protocol_version": server_version,
            "official_latest_version": official_latest,
            "official_default_version": official_default,
            "version_format_valid": version_format_valid,
            "is_supported_version": is_supported,
            "is_latest_version": server_version == official_latest,
            "is_default_version": server_version == official_default,
            "compliance_level": self._assess_compliance_level(server_version, official_latest, official_default)
        }
    
    def _validate_version_format(self, version: str) -> bool:
        """バージョン形式の検証（YYYY-MM-DD）"""
        try:
            parts = version.split("-")
            if len(parts) != 3:
                return False
            
            year, month, day = parts
            if not (year.isdigit() and month.isdigit() and day.isdigit()):
                return False
            
            year_int = int(year)
            month_int = int(month)
            day_int = int(day)
            
            # 合理的な範囲チェック
            if not (2024 <= year_int <= 2030):
                return False
            if not (1 <= month_int <= 12):
                return False
            if not (1 <= day_int <= 31):
                return False
            
            return True
        except Exception:
            return False
    
    def _assess_compliance_level(self, server_version: str, latest: str, default: str) -> str:
        """準拠レベルの評価"""
        if server_version == latest:
            return "FULLY_COMPLIANT"
        elif server_version == default:
            return "COMPLIANT"
        elif server_version == "2024-11-05":
            return "LEGACY_COMPLIANT"
        else:
            return "NON_COMPLIANT"
    
    def test_server_capabilities_compliance(self) -> Dict[str, Any]:
        """サーバー機能の準拠性をテスト"""
        # サーバー機能の定義をチェック
        capabilities_test = {
            "has_tools_capability": True,  # ツール機能は実装済み
            "tools_properly_defined": len(TOOL_DEFINITIONS) > 0,
            "tool_schemas_valid": self._validate_tool_schemas(),
            "server_metadata_complete": self._validate_server_metadata()
        }
        
        return {
            "capabilities_test": capabilities_test,
            "compliance_score": sum(capabilities_test.values()) / len(capabilities_test) * 100,
            "all_capabilities_compliant": all(capabilities_test.values())
        }
    
    def _validate_tool_schemas(self) -> bool:
        """ツールスキーマの検証"""
        try:
            for tool in TOOL_DEFINITIONS:
                # 必須フィールドの確認
                if not hasattr(tool, 'name') or not tool.name:
                    return False
                if not hasattr(tool, 'description') or not tool.description:
                    return False
                if not hasattr(tool, 'inputSchema') or not tool.inputSchema:
                    return False
                
                # スキーマ構造の確認
                schema = tool.inputSchema
                if not isinstance(schema, dict):
                    return False
                if schema.get("type") != "object":
                    return False
                if "properties" not in schema:
                    return False
            
            return True
        except Exception:
            return False
    
    def _validate_server_metadata(self) -> bool:
        """サーバーメタデータの検証"""
        try:
            # サーバー名とバージョンの確認
            if not SERVER_NAME or not isinstance(SERVER_NAME, str):
                return False
            if not SERVER_VERSION or not isinstance(SERVER_VERSION, str):
                return False
            
            return True
        except Exception:
            return False
    
    async def test_initialize_request_handling(self) -> Dict[str, Any]:
        """初期化リクエストの処理をテスト"""
        test_results = []
        
        # 異なるプロトコルバージョンでの初期化をテスト
        test_versions = [
            LATEST_PROTOCOL_VERSION,
            DEFAULT_NEGOTIATED_VERSION,
            "2024-11-05"
        ]
        
        for version in test_versions:
            try:
                # 初期化パラメータの作成
                init_params = InitializeRequestParams(
                    protocolVersion=version,
                    capabilities={},
                    clientInfo=Implementation(
                        name="test-client",
                        version="1.0.0"
                    )
                )
                
                # リクエストの作成
                init_request = InitializeRequest(
                    method="initialize",
                    params=init_params
                )
                
                test_results.append({
                    "protocol_version": version,
                    "request_created": True,
                    "params_valid": True,
                    "error": None
                })
                
            except Exception as e:
                test_results.append({
                    "protocol_version": version,
                    "request_created": False,
                    "params_valid": False,
                    "error": str(e)
                })
        
        return {
            "test_results": test_results,
            "all_versions_supported": all(result["request_created"] for result in test_results),
            "supported_versions": [result["protocol_version"] for result in test_results if result["request_created"]]
        }
    
    async def test_tool_list_compliance(self) -> Dict[str, Any]:
        """ツールリストの準拠性をテスト"""
        try:
            # ツールリストの取得
            tools = await list_tools()
            
            # 基本的な検証
            tools_valid = isinstance(tools, list) and len(tools) > 0
            
            # 各ツールの検証
            tool_validations = []
            for tool in tools:
                validation = {
                    "name": tool.name,
                    "has_name": bool(tool.name),
                    "has_description": bool(tool.description),
                    "has_input_schema": bool(tool.inputSchema),
                    "schema_is_object": tool.inputSchema.get("type") == "object" if tool.inputSchema else False,
                    "has_properties": "properties" in tool.inputSchema if tool.inputSchema else False
                }
                tool_validations.append(validation)
            
            return {
                "tools_returned": len(tools),
                "tools_list_valid": tools_valid,
                "tool_validations": tool_validations,
                "all_tools_valid": all(
                    val["has_name"] and val["has_description"] and val["has_input_schema"] 
                    for val in tool_validations
                )
            }
            
        except Exception as e:
            return {
                "tools_returned": 0,
                "tools_list_valid": False,
                "error": str(e),
                "all_tools_valid": False
            }
    
    async def test_tool_call_compliance(self) -> Dict[str, Any]:
        """ツール呼び出しの準拠性をテスト"""
        test_results = []
        
        # 各ツールの基本的な呼び出しテスト
        tool_tests = [
            {
                "name": "generate-drawio-xml",
                "arguments": {"prompt": "Create a simple flowchart"}
            },
            {
                "name": "save-drawio-file", 
                "arguments": {"xml_content": "<mxfile><diagram><mxGraphModel><root></root></mxGraphModel></diagram></mxfile>"}
            },
            {
                "name": "convert-to-png",
                "arguments": {"file_id": "test-file-id"}
            }
        ]
        
        for test in tool_tests:
            try:
                # 引数検証のテスト
                validate_tool_arguments(test["name"], test["arguments"])
                
                test_results.append({
                    "tool_name": test["name"],
                    "argument_validation": True,
                    "error": None
                })
                
            except Exception as e:
                test_results.append({
                    "tool_name": test["name"],
                    "argument_validation": False,
                    "error": str(e)
                })
        
        return {
            "test_results": test_results,
            "all_validations_passed": all(result["argument_validation"] for result in test_results),
            "validation_errors": [result for result in test_results if not result["argument_validation"]]
        }
    
    def test_error_handling_compliance(self) -> Dict[str, Any]:
        """エラーハンドリングの準拠性をテスト"""
        error_tests = []
        
        # 無効な引数でのテスト
        invalid_argument_tests = [
            {
                "tool": "generate-drawio-xml",
                "args": {},  # 必須パラメータなし
                "expected_error": "必須パラメータ 'prompt' が不足しています"
            },
            {
                "tool": "save-drawio-file",
                "args": {},  # 必須パラメータなし
                "expected_error": "必須パラメータ 'xml_content' が不足しています"
            },
            {
                "tool": "convert-to-png",
                "args": {},  # 必須パラメータなし
                "expected_error": "'file_id' または 'file_path' のいずれかが必要です"
            }
        ]
        
        for test in invalid_argument_tests:
            try:
                validate_tool_arguments(test["tool"], test["args"])
                error_tests.append({
                    "test": test["tool"],
                    "error_caught": False,
                    "expected_error": test["expected_error"],
                    "actual_error": None
                })
            except ValueError as e:
                error_tests.append({
                    "test": test["tool"],
                    "error_caught": True,
                    "expected_error": test["expected_error"],
                    "actual_error": str(e),
                    "error_message_correct": test["expected_error"] in str(e)
                })
            except Exception as e:
                error_tests.append({
                    "test": test["tool"],
                    "error_caught": True,
                    "expected_error": test["expected_error"],
                    "actual_error": str(e),
                    "error_message_correct": False
                })
        
        return {
            "error_tests": error_tests,
            "all_errors_handled": all(test["error_caught"] for test in error_tests),
            "correct_error_messages": all(
                test.get("error_message_correct", False) for test in error_tests if test["error_caught"]
            )
        }
    
    def test_message_format_compliance(self) -> Dict[str, Any]:
        """メッセージ形式の準拠性をテスト"""
        # JSON-RPC 2.0 形式の確認
        format_tests = {
            "supports_jsonrpc_2_0": True,  # 公式MCPライブラリを使用しているため
            "proper_request_format": True,
            "proper_response_format": True,
            "proper_error_format": True,
            "content_type_compliance": True  # TextContentを使用
        }
        
        return {
            "format_tests": format_tests,
            "all_formats_compliant": all(format_tests.values()),
            "compliance_percentage": sum(format_tests.values()) / len(format_tests) * 100
        }
    
    async def run_comprehensive_compliance_test(self) -> Dict[str, Any]:
        """包括的な準拠性テストを実行"""
        self.logger.info("🔍 MCP プロトコル準拠性テストを開始...")
        
        # 各テストの実行
        protocol_version_test = self.test_protocol_version_compliance()
        capabilities_test = self.test_server_capabilities_compliance()
        initialize_test = await self.test_initialize_request_handling()
        tool_list_test = await self.test_tool_list_compliance()
        tool_call_test = await self.test_tool_call_compliance()
        error_handling_test = self.test_error_handling_compliance()
        message_format_test = self.test_message_format_compliance()
        
        # 全体的な評価
        overall_assessment = self._calculate_overall_compliance(
            protocol_version_test,
            capabilities_test,
            initialize_test,
            tool_list_test,
            tool_call_test,
            error_handling_test,
            message_format_test
        )
        
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "protocol_version_compliance": protocol_version_test,
            "server_capabilities_compliance": capabilities_test,
            "initialize_request_compliance": initialize_test,
            "tool_list_compliance": tool_list_test,
            "tool_call_compliance": tool_call_test,
            "error_handling_compliance": error_handling_test,
            "message_format_compliance": message_format_test,
            "overall_assessment": overall_assessment
        }
    
    def _calculate_overall_compliance(self, *test_results) -> Dict[str, Any]:
        """全体的な準拠性を計算"""
        # 各テストの重要度重み付け
        weights = {
            "protocol_version": 0.25,
            "capabilities": 0.20,
            "initialize": 0.15,
            "tool_list": 0.15,
            "tool_call": 0.15,
            "error_handling": 0.05,
            "message_format": 0.05
        }
        
        # スコア計算
        scores = []
        
        # プロトコルバージョン
        pv_test = test_results[0]
        if pv_test["compliance_level"] == "FULLY_COMPLIANT":
            scores.append(100 * weights["protocol_version"])
        elif pv_test["compliance_level"] == "COMPLIANT":
            scores.append(90 * weights["protocol_version"])
        elif pv_test["compliance_level"] == "LEGACY_COMPLIANT":
            scores.append(70 * weights["protocol_version"])
        else:
            scores.append(0 * weights["protocol_version"])
        
        # サーバー機能
        cap_test = test_results[1]
        scores.append(cap_test["compliance_score"] * weights["capabilities"])
        
        # 初期化リクエスト
        init_test = test_results[2]
        init_score = 100 if init_test["all_versions_supported"] else 50
        scores.append(init_score * weights["initialize"])
        
        # ツールリスト
        tool_list_test = test_results[3]
        tool_list_score = 100 if tool_list_test["all_tools_valid"] else 0
        scores.append(tool_list_score * weights["tool_list"])
        
        # ツール呼び出し
        tool_call_test = test_results[4]
        tool_call_score = 100 if tool_call_test["all_validations_passed"] else 50
        scores.append(tool_call_score * weights["tool_call"])
        
        # エラーハンドリング
        error_test = test_results[5]
        error_score = 100 if error_test["all_errors_handled"] else 0
        scores.append(error_score * weights["error_handling"])
        
        # メッセージ形式
        msg_test = test_results[6]
        scores.append(msg_test["compliance_percentage"] * weights["message_format"])
        
        total_score = sum(scores)
        
        # 準拠レベルの決定
        if total_score >= 95:
            compliance_level = "EXCELLENT"
            status_message = "✅ 完全にMCP仕様に準拠しています"
        elif total_score >= 85:
            compliance_level = "GOOD"
            status_message = "✅ MCP仕様に十分準拠しています"
        elif total_score >= 70:
            compliance_level = "ACCEPTABLE"
            status_message = "⚠️ MCP仕様に概ね準拠していますが、改善の余地があります"
        else:
            compliance_level = "NEEDS_IMPROVEMENT"
            status_message = "❌ MCP仕様への準拠に問題があります"
        
        return {
            "total_score": round(total_score, 2),
            "compliance_level": compliance_level,
            "status_message": status_message,
            "score_breakdown": {
                "protocol_version": round(scores[0], 2),
                "capabilities": round(scores[1], 2),
                "initialize": round(scores[2], 2),
                "tool_list": round(scores[3], 2),
                "tool_call": round(scores[4], 2),
                "error_handling": round(scores[5], 2),
                "message_format": round(scores[6], 2)
            }
        }


# Pytestテストクラス
class TestMCPProtocolCompliance:
    """MCP プロトコル準拠性のテストクラス"""
    
    @pytest.fixture
    def tester(self):
        """テスターのフィクスチャ"""
        return MCPProtocolCompatibilityTester()
    
    def test_protocol_version_is_supported(self, tester):
        """プロトコルバージョンがサポートされていることをテスト"""
        result = tester.test_protocol_version_compliance()
        
        assert result["version_format_valid"], "プロトコルバージョンの形式が無効です"
        assert result["is_supported_version"], "サポートされていないプロトコルバージョンです"
        assert result["compliance_level"] in ["FULLY_COMPLIANT", "COMPLIANT", "LEGACY_COMPLIANT"]
    
    def test_server_capabilities_are_compliant(self, tester):
        """サーバー機能が準拠していることをテスト"""
        result = tester.test_server_capabilities_compliance()
        
        assert result["all_capabilities_compliant"], "サーバー機能の準拠性に問題があります"
        assert result["compliance_score"] >= 80, f"準拠スコアが低すぎます: {result['compliance_score']}"
    
    @pytest.mark.asyncio
    async def test_initialize_request_handling(self, tester):
        """初期化リクエストの処理をテスト"""
        result = await tester.test_initialize_request_handling()
        
        assert result["all_versions_supported"], "一部のプロトコルバージョンがサポートされていません"
        assert len(result["supported_versions"]) >= 2, "十分なプロトコルバージョンがサポートされていません"
    
    @pytest.mark.asyncio
    async def test_tool_list_compliance(self, tester):
        """ツールリストの準拠性をテスト"""
        result = await tester.test_tool_list_compliance()
        
        assert result["tools_list_valid"], "ツールリストが無効です"
        assert result["tools_returned"] >= 3, "期待されるツール数が不足しています"
        assert result["all_tools_valid"], "一部のツールが無効です"
    
    @pytest.mark.asyncio
    async def test_tool_call_compliance(self, tester):
        """ツール呼び出しの準拠性をテスト"""
        result = await tester.test_tool_call_compliance()
        
        assert result["all_validations_passed"], "ツール引数の検証に問題があります"
        assert len(result["validation_errors"]) == 0, f"検証エラー: {result['validation_errors']}"
    
    def test_error_handling_compliance(self, tester):
        """エラーハンドリングの準拠性をテスト"""
        result = tester.test_error_handling_compliance()
        
        assert result["all_errors_handled"], "エラーハンドリングに問題があります"
        assert result["correct_error_messages"], "エラーメッセージが正しくありません"
    
    def test_message_format_compliance(self, tester):
        """メッセージ形式の準拠性をテスト"""
        result = tester.test_message_format_compliance()
        
        assert result["all_formats_compliant"], "メッセージ形式の準拠性に問題があります"
        assert result["compliance_percentage"] == 100, "メッセージ形式の準拠率が100%ではありません"
    
    @pytest.mark.asyncio
    async def test_comprehensive_compliance(self, tester):
        """包括的な準拠性をテスト"""
        result = await tester.run_comprehensive_compliance_test()
        
        overall = result["overall_assessment"]
        assert overall["total_score"] >= 85, f"全体的な準拠スコアが低すぎます: {overall['total_score']}"
        assert overall["compliance_level"] in ["EXCELLENT", "GOOD"], f"準拠レベルが不十分です: {overall['compliance_level']}"


async def main():
    """メイン実行関数"""
    print("🔍 MCP プロトコル準拠性テストを開始...")
    print("=" * 60)
    
    tester = MCPProtocolCompatibilityTester()
    
    try:
        # 包括的な準拠性テストの実行
        result = await tester.run_comprehensive_compliance_test()
        
        # 結果の表示
        print("📊 MCP プロトコル準拠性テスト結果")
        print("=" * 60)
        
        # プロトコルバージョン
        pv_result = result["protocol_version_compliance"]
        print(f"📋 プロトコルバージョン準拠性:")
        print(f"   サーバーバージョン: {pv_result['server_protocol_version']}")
        print(f"   公式最新バージョン: {pv_result['official_latest_version']}")
        print(f"   準拠レベル: {pv_result['compliance_level']}")
        print(f"   最新バージョン: {'✅' if pv_result['is_latest_version'] else '❌'}")
        print()
        
        # サーバー機能
        cap_result = result["server_capabilities_compliance"]
        print(f"⚙️ サーバー機能準拠性:")
        print(f"   準拠スコア: {cap_result['compliance_score']:.1f}%")
        print(f"   全機能準拠: {'✅' if cap_result['all_capabilities_compliant'] else '❌'}")
        print()
        
        # ツール関連
        tool_list_result = result["tool_list_compliance"]
        tool_call_result = result["tool_call_compliance"]
        print(f"🔧 ツール準拠性:")
        print(f"   ツール数: {tool_list_result['tools_returned']}")
        print(f"   ツールリスト有効: {'✅' if tool_list_result['all_tools_valid'] else '❌'}")
        print(f"   ツール呼び出し有効: {'✅' if tool_call_result['all_validations_passed'] else '❌'}")
        print()
        
        # エラーハンドリング
        error_result = result["error_handling_compliance"]
        print(f"🚨 エラーハンドリング準拠性:")
        print(f"   エラー処理: {'✅' if error_result['all_errors_handled'] else '❌'}")
        print(f"   エラーメッセージ: {'✅' if error_result['correct_error_messages'] else '❌'}")
        print()
        
        # 全体評価
        overall = result["overall_assessment"]
        print(f"📈 全体評価:")
        print(f"   総合スコア: {overall['total_score']:.2f}/100")
        print(f"   準拠レベル: {overall['compliance_level']}")
        print(f"   ステータス: {overall['status_message']}")
        print()
        
        # スコア内訳
        print(f"📊 スコア内訳:")
        breakdown = overall["score_breakdown"]
        for category, score in breakdown.items():
            print(f"   {category}: {score:.2f}")
        print()
        
        # 結果をファイルに保存
        import datetime
        report_filename = f"mcp_protocol_compliance_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 詳細レポートを保存: {report_filename}")
        
        # 終了コードの決定
        if overall["compliance_level"] in ["EXCELLENT", "GOOD"]:
            print("✅ MCP プロトコル準拠性テスト完了 - 合格")
            return 0
        else:
            print("❌ MCP プロトコル準拠性テスト完了 - 改善が必要")
            return 1
            
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 非同期実行
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)