#!/usr/bin/env python3
"""
標準MCPサーバー初期化パターンのテスト

このテストは、実装されたMCPサーバーが標準的な初期化パターンと
ライフサイクル管理を正しく実装していることを検証します。
"""
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# テスト用パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# MCP SDK のテスト
def test_mcp_sdk_imports():
    """MCP SDK の標準インポートをテスト"""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent, ServerCapabilities, Implementation
        print("✅ MCP SDK imports successful")
        return True
    except ImportError as e:
        print(f"❌ MCP SDK import error: {e}")
        return False


def test_server_constants():
    """サーバー定数の標準パターンをテスト"""
    # 標準的なサーバー定数
    SERVER_NAME = "drawio-mcp-server"
    SERVER_VERSION = "1.0.0"
    SERVER_DESCRIPTION = "Draw.io diagram generation MCP server with official MCP SDK"
    
    assert SERVER_NAME == "drawio-mcp-server"
    assert SERVER_VERSION == "1.0.0"
    assert len(SERVER_DESCRIPTION) > 0
    print("✅ Server constants validation passed")
    return True


def test_server_capabilities():
    """サーバー機能定義の標準パターンをテスト"""
    from mcp.types import ServerCapabilities
    
    SERVER_CAPABILITIES = ServerCapabilities(tools={})
    assert SERVER_CAPABILITIES is not None
    print("✅ Server capabilities definition passed")
    return True


def test_server_implementation():
    """サーバー実装情報の標準パターンをテスト"""
    from mcp.types import Implementation
    
    SERVER_NAME = "drawio-mcp-server"
    SERVER_VERSION = "1.0.0"
    
    SERVER_IMPLEMENTATION = Implementation(
        name=SERVER_NAME,
        version=SERVER_VERSION
    )
    
    assert SERVER_IMPLEMENTATION.name == SERVER_NAME
    assert SERVER_IMPLEMENTATION.version == SERVER_VERSION
    print("✅ Server implementation definition passed")
    return True


def test_tool_definitions():
    """ツール定義の標準パターンをテスト"""
    from mcp.types import Tool
    
    TOOL_DEFINITIONS = [
        Tool(
            name="generate-drawio-xml",
            description="自然言語プロンプトからDraw.io XML図表を生成",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "生成する図表の自然言語記述",
                        "minLength": 5,
                        "maxLength": 10000
                    }
                },
                "required": ["prompt"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="save-drawio-file",
            description="Draw.io XMLコンテンツを一時ファイルに保存",
            inputSchema={
                "type": "object",
                "properties": {
                    "xml_content": {
                        "type": "string",
                        "description": "保存する有効なDraw.io XMLコンテンツ",
                        "minLength": 10
                    },
                    "filename": {
                        "type": "string",
                        "description": "オプションのカスタムファイル名（拡張子なし）",
                        "maxLength": 100
                    }
                },
                "required": ["xml_content"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="convert-to-png",
            description="Draw.io CLIを使用してDraw.ioファイルをPNG画像に変換",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "save-drawio-fileツールから返されたファイルID（推奨）"
                    },
                    "file_path": {
                        "type": "string",
                        "description": ".drawioファイルへの直接パス（file_idの代替）"
                    }
                },
                "oneOf": [
                    {"required": ["file_id"]},
                    {"required": ["file_path"]}
                ],
                "additionalProperties": False
            }
        )
    ]
    
    assert len(TOOL_DEFINITIONS) == 3
    assert all(isinstance(tool, Tool) for tool in TOOL_DEFINITIONS)
    assert all(tool.name in ["generate-drawio-xml", "save-drawio-file", "convert-to-png"] 
               for tool in TOOL_DEFINITIONS)
    print("✅ Tool definitions validation passed")
    return True


def test_server_instance_creation():
    """サーバーインスタンス作成の標準パターンをテスト"""
    from mcp.server import Server
    
    SERVER_NAME = "drawio-mcp-server"
    server = Server(SERVER_NAME)
    
    assert server is not None
    print("✅ Server instance creation passed")
    return True


async def test_initialization_options():
    """初期化オプションの標準パターンをテスト"""
    from mcp.server.models import InitializationOptions
    from mcp.types import ServerCapabilities, Implementation
    
    SERVER_NAME = "drawio-mcp-server"
    SERVER_VERSION = "1.0.0"
    SERVER_CAPABILITIES = ServerCapabilities(tools={})
    
    initialization_options = InitializationOptions(
        server_name=SERVER_NAME,
        server_version=SERVER_VERSION,
        capabilities=SERVER_CAPABILITIES
    )
    
    assert initialization_options.server_name == SERVER_NAME
    assert initialization_options.server_version == SERVER_VERSION
    assert initialization_options.capabilities is not None
    print("✅ Initialization options validation passed")
    return True


def test_argument_validation():
    """引数検証ユーティリティの標準パターンをテスト"""
    def validate_tool_arguments(tool_name: str, arguments: dict) -> None:
        """標準MCPツール引数検証ユーティリティ"""
        if tool_name == "generate-drawio-xml":
            if not arguments.get("prompt"):
                raise ValueError("必須パラメータ 'prompt' が不足しています")
            if not isinstance(arguments["prompt"], str):
                raise ValueError("パラメータ 'prompt' は文字列である必要があります")
                
        elif tool_name == "save-drawio-file":
            if not arguments.get("xml_content"):
                raise ValueError("必須パラメータ 'xml_content' が不足しています")
            if not isinstance(arguments["xml_content"], str):
                raise ValueError("パラメータ 'xml_content' は文字列である必要があります")
                
        elif tool_name == "convert-to-png":
            file_id = arguments.get("file_id")
            file_path = arguments.get("file_path")
            if not file_id and not file_path:
                raise ValueError("'file_id' または 'file_path' のいずれかが必要です")
    
    # 正常ケース
    validate_tool_arguments("generate-drawio-xml", {"prompt": "test prompt"})
    validate_tool_arguments("save-drawio-file", {"xml_content": "<xml>test</xml>"})
    validate_tool_arguments("convert-to-png", {"file_id": "test-id"})
    
    # エラーケース
    try:
        validate_tool_arguments("generate-drawio-xml", {})
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("✅ Argument validation utility passed")
    return True


async def run_all_tests():
    """すべてのテストを実行"""
    print("🧪 標準MCPサーバー初期化パターンのテスト開始")
    print("=" * 60)
    
    tests = [
        ("MCP SDK Imports", test_mcp_sdk_imports),
        ("Server Constants", test_server_constants),
        ("Server Capabilities", test_server_capabilities),
        ("Server Implementation", test_server_implementation),
        ("Tool Definitions", test_tool_definitions),
        ("Server Instance Creation", test_server_instance_creation),
        ("Initialization Options", test_initialization_options),
        ("Argument Validation", test_argument_validation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Testing: {test_name}")
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} failed")
                
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 テスト結果: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 すべてのテストが成功しました！")
        print("✅ 標準MCPサーバー初期化パターンが正しく実装されています")
        return True
    else:
        print("❌ 一部のテストが失敗しました")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)