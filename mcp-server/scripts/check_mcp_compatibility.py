#!/usr/bin/env python3
"""
MCP プロトコル互換性チェック（簡易版）

このスクリプトは、MCPサーバーが公式MCP仕様と互換性があることを確認します。
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List

# 公式MCPライブラリのインポート
try:
    from mcp.types import (
        LATEST_PROTOCOL_VERSION,
        DEFAULT_NEGOTIATED_VERSION,
        InitializeRequestParams,
        Implementation,
        Tool
    )
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"❌ MCP ライブラリのインポートに失敗: {e}")
    MCP_AVAILABLE = False

try:
    from src.config import MCPServerConfig
    from src.server import (
        SERVER_NAME,
        SERVER_VERSION,
        TOOL_DEFINITIONS,
        validate_tool_arguments
    )
    SERVER_AVAILABLE = True
except ImportError as e:
    print(f"❌ サーバーモジュールのインポートに失敗: {e}")
    SERVER_AVAILABLE = False


async def check_protocol_compatibility():
    """プロトコル互換性の包括的チェック"""
    print("🔍 MCP プロトコル互換性チェックを開始...")
    print("=" * 60)
    
    if not MCP_AVAILABLE or not SERVER_AVAILABLE:
        print("❌ 必要なモジュールが利用できません")
        return False
    
    try:
        results = {}
        
        # 1. プロトコルバージョンチェック
        print("📋 1. プロトコルバージョンチェック")
        version_result = check_protocol_version()
        results["protocol_version"] = version_result
        print_result_summary("プロトコルバージョン", version_result)
        print()
        
        # 2. サーバー機能チェック
        print("⚙️ 2. サーバー機能チェック")
        capabilities_result = check_server_capabilities()
        results["server_capabilities"] = capabilities_result
        print_result_summary("サーバー機能", capabilities_result)
        print()
        
        # 3. ツール定義チェック
        print("🔧 3. ツール定義チェック")
        tools_result = await check_tool_definitions()
        results["tool_definitions"] = tools_result
        print_result_summary("ツール定義", tools_result)
        print()
        
        # 4. エラーハンドリングチェック
        print("🚨 4. エラーハンドリングチェック")
        error_result = check_error_handling()
        results["error_handling"] = error_result
        print_result_summary("エラーハンドリング", error_result)
        print()
        
        # 5. 全体評価
        print("📊 5. 全体評価")
        overall_result = calculate_overall_score(results)
        print_overall_assessment(overall_result)
        
        # 結果をファイルに保存
        save_results(results, overall_result)
        
        return overall_result["success"]
        
    except Exception as e:
        print(f"❌ チェック中にエラーが発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_protocol_version() -> Dict[str, Any]:
    """プロトコルバージョンのチェック"""
    config = MCPServerConfig.from_env()
    server_version = config.protocol_version
    
    official_latest = LATEST_PROTOCOL_VERSION
    official_default = DEFAULT_NEGOTIATED_VERSION
    
    is_latest = server_version == official_latest
    is_supported = server_version in [official_latest, official_default, "2024-11-05"]
    
    # バージョン形式の検証
    version_format_valid = validate_version_format(server_version)
    
    return {
        "server_version": server_version,
        "official_latest": official_latest,
        "official_default": official_default,
        "is_latest": is_latest,
        "is_supported": is_supported,
        "format_valid": version_format_valid,
        "score": 100 if is_latest else (90 if is_supported else 50),
        "success": is_supported and version_format_valid
    }


def validate_version_format(version: str) -> bool:
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
        
        return (2024 <= year_int <= 2030 and 
                1 <= month_int <= 12 and 
                1 <= day_int <= 31)
    except Exception:
        return False


def check_server_capabilities() -> Dict[str, Any]:
    """サーバー機能のチェック"""
    checks = {
        "server_name_defined": bool(SERVER_NAME),
        "server_version_defined": bool(SERVER_VERSION),
        "tools_defined": len(TOOL_DEFINITIONS) > 0,
        "tool_schemas_valid": validate_tool_schemas()
    }
    
    score = sum(checks.values()) / len(checks) * 100
    success = all(checks.values())
    
    return {
        "checks": checks,
        "score": score,
        "success": success
    }


def validate_tool_schemas() -> bool:
    """ツールスキーマの検証"""
    try:
        for tool in TOOL_DEFINITIONS:
            if not hasattr(tool, 'name') or not tool.name:
                return False
            if not hasattr(tool, 'description') or not tool.description:
                return False
            if not hasattr(tool, 'inputSchema') or not tool.inputSchema:
                return False
            
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


async def check_tool_definitions() -> Dict[str, Any]:
    """ツール定義のチェック"""
    try:
        # TOOL_DEFINITIONSを直接使用（list_tools()はloggerが必要なため）
        tools = TOOL_DEFINITIONS
        
        checks = {
            "tools_returned": len(tools) > 0,
            "expected_tool_count": len(tools) >= 3,
            "all_tools_valid": all(
                hasattr(tool, 'name') and hasattr(tool, 'description') and hasattr(tool, 'inputSchema')
                for tool in tools
            )
        }
        
        # 各ツールの詳細チェック
        tool_details = []
        for tool in tools:
            detail = {
                "name": tool.name,
                "has_description": bool(tool.description),
                "has_schema": bool(tool.inputSchema),
                "schema_valid": validate_single_tool_schema(tool.inputSchema) if tool.inputSchema else False
            }
            tool_details.append(detail)
        
        score = sum(checks.values()) / len(checks) * 100
        success = all(checks.values())
        
        return {
            "checks": checks,
            "tool_details": tool_details,
            "tool_count": len(tools),
            "score": score,
            "success": success
        }
        
    except Exception as e:
        return {
            "checks": {"error": True},
            "error": str(e),
            "score": 0,
            "success": False
        }


def validate_single_tool_schema(schema: Dict[str, Any]) -> bool:
    """単一ツールスキーマの検証"""
    try:
        if not isinstance(schema, dict):
            return False
        if schema.get("type") != "object":
            return False
        if "properties" not in schema:
            return False
        return True
    except Exception:
        return False


def check_error_handling() -> Dict[str, Any]:
    """エラーハンドリングのチェック"""
    error_tests = []
    
    # 無効な引数でのテスト
    test_cases = [
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
    
    for test_case in test_cases:
        try:
            validate_tool_arguments(test_case["tool"], test_case["args"])
            error_tests.append({
                "tool": test_case["tool"],
                "error_caught": False,
                "expected": test_case["expected_error"],
                "actual": None
            })
        except ValueError as e:
            error_message = str(e)
            error_tests.append({
                "tool": test_case["tool"],
                "error_caught": True,
                "expected": test_case["expected_error"],
                "actual": error_message,
                "message_correct": test_case["expected_error"] in error_message
            })
        except Exception as e:
            error_tests.append({
                "tool": test_case["tool"],
                "error_caught": True,
                "expected": test_case["expected_error"],
                "actual": str(e),
                "message_correct": False
            })
    
    all_errors_caught = all(test["error_caught"] for test in error_tests)
    correct_messages = all(
        test.get("message_correct", False) for test in error_tests if test["error_caught"]
    )
    
    score = (sum(test["error_caught"] for test in error_tests) / len(error_tests)) * 100
    success = all_errors_caught and correct_messages
    
    return {
        "error_tests": error_tests,
        "all_errors_caught": all_errors_caught,
        "correct_messages": correct_messages,
        "score": score,
        "success": success
    }


def calculate_overall_score(results: Dict[str, Any]) -> Dict[str, Any]:
    """全体スコアの計算"""
    weights = {
        "protocol_version": 0.3,
        "server_capabilities": 0.25,
        "tool_definitions": 0.25,
        "error_handling": 0.2
    }
    
    total_score = 0
    for category, weight in weights.items():
        if category in results and "score" in results[category]:
            total_score += results[category]["score"] * weight
    
    # 成功判定
    all_success = all(
        results[category].get("success", False) 
        for category in weights.keys() 
        if category in results
    )
    
    # レベル判定
    if total_score >= 95:
        level = "EXCELLENT"
        message = "✅ 完全にMCP仕様に準拠しています"
    elif total_score >= 85:
        level = "GOOD"
        message = "✅ MCP仕様に十分準拠しています"
    elif total_score >= 70:
        level = "ACCEPTABLE"
        message = "⚠️ MCP仕様に概ね準拠していますが、改善の余地があります"
    else:
        level = "NEEDS_IMPROVEMENT"
        message = "❌ MCP仕様への準拠に問題があります"
    
    return {
        "total_score": round(total_score, 2),
        "level": level,
        "message": message,
        "success": all_success and total_score >= 85,
        "category_scores": {
            category: results[category].get("score", 0) 
            for category in weights.keys() 
            if category in results
        }
    }


def print_result_summary(category: str, result: Dict[str, Any]):
    """結果サマリーの表示"""
    success = result.get("success", False)
    score = result.get("score", 0)
    
    status = "✅ 合格" if success else "❌ 不合格"
    print(f"   結果: {status} (スコア: {score:.1f}/100)")
    
    if "checks" in result:
        for check_name, check_result in result["checks"].items():
            check_status = "✅" if check_result else "❌"
            print(f"   {check_name}: {check_status}")


def print_overall_assessment(overall: Dict[str, Any]):
    """全体評価の表示"""
    print(f"   総合スコア: {overall['total_score']}/100")
    print(f"   評価レベル: {overall['level']}")
    print(f"   ステータス: {overall['message']}")
    print()
    
    print("   カテゴリ別スコア:")
    for category, score in overall["category_scores"].items():
        print(f"     {category}: {score:.1f}")


def save_results(results: Dict[str, Any], overall: Dict[str, Any]):
    """結果をファイルに保存"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "server_info": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION
        },
        "test_results": results,
        "overall_assessment": overall
    }
    
    filename = f"mcp_compatibility_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"💾 詳細レポートを保存: {filename}")


async def main():
    """メイン実行関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 互換性チェック実行
    success = await check_protocol_compatibility()
    
    if success:
        print("\n🎉 MCP プロトコル互換性チェック完了 - すべて正常")
        return 0
    else:
        print("\n❌ MCP プロトコル互換性チェック完了 - 問題が検出されました")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)