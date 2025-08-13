"""
公式MCPライブラリを使用したDraw.io図表生成MCPサーバー

このモジュールは、公式MCP Python SDKを使用してDraw.io図表生成機能を提供する
MCPサーバーを実装します。Claude Codeや他のMCPクライアントとの完全な互換性を保証します。

標準的なMCPサーバー初期化パターンとライフサイクル管理を実装しています。
"""
import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

# 公式MCP SDKのインポート - 標準パターン
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    ServerCapabilities,
    Implementation,
)

from .config import MCPServerConfig, setup_logging
from .health import HealthChecker
from .dependency_checker import DependencyChecker
from .exceptions import (
    MCPServerError, 
    MCPServerErrorCode, 
    ConfigurationError, 
    InitializationError,
    handle_exception
)
from .api_key_validator import APIKeyValidator, APIKeyType
from .llm_service import LLMService
from .file_service import FileService
from .image_service import ImageService
from .tools import generate_drawio_xml, save_drawio_file, convert_to_png


# MCPサーバー設定とメタデータ - 標準パターン
SERVER_NAME = "drawio-mcp-server"
SERVER_VERSION = "1.0.0"
SERVER_DESCRIPTION = "Draw.io diagram generation MCP server with official MCP SDK"

# サーバー機能定義 - 標準MCPサーバーパターン
SERVER_CAPABILITIES = ServerCapabilities(
    tools={}  # ツール機能を有効化
)

# サーバー実装情報 - MCP標準
SERVER_IMPLEMENTATION = Implementation(
    name=SERVER_NAME,
    version=SERVER_VERSION
)

# グローバル設定とサービスインスタンス
config: Optional[MCPServerConfig] = None
logger: Optional[logging.Logger] = None
dependency_checker: Optional[DependencyChecker] = None
api_key_validator: Optional[APIKeyValidator] = None
llm_service: Optional[LLMService] = None
file_service: Optional[FileService] = None
image_service: Optional[ImageService] = None
health_checker: Optional[HealthChecker] = None
cleanup_task: Optional[asyncio.Task] = None
start_time: float = 0
shutdown_requested: bool = False

# 公式MCPサーバーインスタンス - 標準初期化パターン
server = Server(SERVER_NAME)


@asynccontextmanager
async def server_lifecycle():
    """
    標準MCPサーバーライフサイクル管理コンテキストマネージャー
    
    MCPサーバーの初期化、実行、クリーンアップを標準パターンで管理します。
    """
    global config, logger, llm_service, file_service, image_service, health_checker, start_time
    
    try:
        # 初期化フェーズ
        logger.info(f"🚀 {SERVER_NAME} v{SERVER_VERSION} 初期化開始")
        await initialize_services()
        
        # サーバー準備完了
        logger.info(f"✅ {SERVER_NAME} 初期化完了 - サーバー準備完了")
        yield
        
    except Exception as e:
        logger.error(f"❌ サーバーライフサイクルエラー: {str(e)}", exc_info=True)
        raise
    finally:
        # クリーンアップフェーズ
        logger.info("🔄 サーバーシャットダウン開始")
        await shutdown_services()
        logger.info("✅ サーバーシャットダウン完了")


async def initialize_services():
    """
    標準MCPサーバー初期化パターン
    
    すべてのサーバーサービスとコンポーネントを標準的な順序で初期化します。
    """
    global config, logger, dependency_checker, api_key_validator, llm_service, file_service, image_service, health_checker, start_time
    
    try:
        # 1. 設定とログの初期化
        config = MCPServerConfig.from_env()
        logger = setup_logging(config)
        start_time = time.time()
        
        logger.info(f"📋 {SERVER_NAME} v{SERVER_VERSION} 設定読み込み完了")
        logger.info(f"⚙️ 設定: temp_dir={config.temp_dir}, cache_ttl={config.cache_ttl}s")
        
        # 2. 依存関係チェックの実行
        logger.info("🔍 起動時依存関係チェック開始...")
        dependency_checker = DependencyChecker(logger)
        
        # 重要な依存関係のチェック
        dependencies_ok, dependency_errors = await dependency_checker.check_startup_dependencies()
        
        if not dependencies_ok:
            error_msg = "重要な依存関係が不足しています:\n" + "\n".join(dependency_errors)
            logger.error(f"❌ {error_msg}")
            
            # セットアップガイダンスを生成
            setup_guidance = await dependency_checker.get_setup_guidance(missing_only=True)
            logger.error(f"\n📋 セットアップガイダンス:\n{setup_guidance}")
            
            raise InitializationError(f"依存関係チェックに失敗: {len(dependency_errors)}個の重要な依存関係が不足")
        
        logger.info("✅ 起動時依存関係チェック完了")
        
        # 3. APIキー検証の実行
        logger.info("🔑 APIキー検証中...")
        api_key_validator = APIKeyValidator(logger)
        
        validation_result = await api_key_validator.validate_with_policy(
            api_key=config.anthropic_api_key,
            development_mode=config.development_mode,
            force_validation=False  # 開発モードではテストキーを許可
        )
        
        if not validation_result.is_valid:
            error_msg = f"APIキー検証に失敗: {validation_result.error_message}"
            logger.error(f"❌ {error_msg}")
            raise InitializationError(error_msg)
        
        # APIキー検証結果をログに記録
        if validation_result.key_type == APIKeyType.TEST:
            logger.warning(f"⚠️ テスト用APIキーを使用中 - 開発/テスト環境でのみ使用してください")
        elif validation_result.key_type == APIKeyType.PRODUCTION:
            logger.info(f"✅ 本番用APIキー検証完了")
            if validation_result.account_info:
                logger.debug(f"📊 アカウント情報: {validation_result.account_info}")
        
        # 4. コアサービスの初期化
        logger.info("🧠 LLMサービス初期化中...")
        llm_service = LLMService(api_key=config.anthropic_api_key)
        
        # キャッシュ設定の適用
        if hasattr(llm_service, 'CACHE_TTL') and config.cache_ttl != 3600:
            llm_service.CACHE_TTL = config.cache_ttl
        if hasattr(llm_service, 'MAX_CACHE_SIZE') and config.max_cache_size != 100:
            llm_service.MAX_CACHE_SIZE = config.max_cache_size
        
        logger.info("📁 ファイルサービス初期化中...")
        file_service = FileService(
            temp_dir=config.temp_dir,
            file_expiry_hours=config.file_expiry_hours
        )
        
        logger.info("🖼️ 画像サービス初期化中...")
        image_service = ImageService(
            drawio_cli_path=config.drawio_cli_path
        )
        
        # 5. ヘルスチェッカーとモニタリング
        logger.info("🏥 ヘルスチェッカー初期化中...")
        health_checker = HealthChecker(config)
        health_checker.set_services(llm_service, file_service, image_service)
        health_checker.set_dependency_checker(dependency_checker)
        
        # 6. バックグラウンドタスクの開始
        logger.info("🔄 バックグラウンドタスク開始中...")
        await start_background_tasks()
        
        # 7. 初期ヘルスチェック
        logger.info("🔍 初期ヘルスチェック実行中...")
        health_status = await health_checker.check_all(force_refresh=True)
        logger.info(f"✅ 初期ヘルスチェック完了: {health_status['status']}")
        
        # 8. 完全な依存関係チェック（オプション依存関係含む）
        logger.info("🔍 完全依存関係チェック実行中...")
        full_dependency_status = await dependency_checker.check_all_dependencies(force_refresh=True)
        
        # オプション依存関係の警告
        if full_dependency_status["summary"]["missing"] > 0 or full_dependency_status["summary"]["invalid"] > 0:
            missing_optional = []
            for dep_name, dep_info in full_dependency_status["dependencies"].items():
                if dep_info["status"] != "available" and not dep_info["required"]:
                    missing_optional.append(f"• {dep_name}: {dep_info['description']}")
            
            if missing_optional:
                logger.warning("⚠️ オプション依存関係が不足しています（機能制限あり）:")
                for warning in missing_optional:
                    logger.warning(f"  {warning}")
                logger.warning("  完全なセットアップガイダンスは --setup-guide オプションで確認できます")
        
        # 9. 初期化完了
        initialization_time = (time.time() - start_time) * 1000
        logger.info(f"🎉 サーバー初期化完了 ({initialization_time:.2f}ms)")
        
    except Exception as e:
        error_msg = f"サーバー初期化に失敗: {str(e)}"
        if logger:
            logger.error(error_msg, exc_info=True)
        raise InitializationError(error_msg, original_error=e)


async def start_background_tasks():
    """バックグラウンドメンテナンスタスクを開始"""
    global cleanup_task, file_service, logger
    
    try:
        if file_service:
            cleanup_task = asyncio.create_task(
                run_cleanup_loop(),
                name="file_cleanup"
            )
            logger.info("ファイルクリーンアップタスクを開始しました")
    except Exception as e:
        logger.error(f"バックグラウンドタスクの開始に失敗: {str(e)}", exc_info=True)
        raise


async def run_cleanup_loop():
    """期限切れファイルをクリーンアップするバックグラウンドタスク"""
    global config, file_service, logger, shutdown_requested
    
    cleanup_interval = config.cleanup_interval_minutes * 60  # 秒に変換
    
    while not shutdown_requested:
        try:
            await asyncio.sleep(cleanup_interval)
            
            if file_service and not shutdown_requested:
                logger.debug("スケジュールされたファイルクリーンアップを実行中...")
                await file_service.cleanup_expired_files()
                
        except asyncio.CancelledError:
            logger.info("クリーンアップタスクがキャンセルされました")
            break
        except Exception as e:
            logger.error(f"クリーンアップループでエラー: {str(e)}", exc_info=True)
            # エラーが発生しても実行を継続
            await asyncio.sleep(60)  # 1分待ってからリトライ


async def shutdown_services():
    """サーバーを正常にシャットダウン"""
    global cleanup_task, file_service, logger, shutdown_requested
    
    if shutdown_requested:
        logger.warning("シャットダウンは既に進行中です")
        return
    
    logger.info("正常なシャットダウンを開始中...")
    shutdown_requested = True
    
    try:
        # バックグラウンドタスクのキャンセル
        if cleanup_task and not cleanup_task.done():
            logger.info("クリーンアップタスクをキャンセル中...")
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 最終クリーンアップの実行
        if file_service:
            logger.info("最終ファイルクリーンアップを実行中...")
            await file_service.cleanup_expired_files()
        
        logger.info("サーバーシャットダウンが完了しました")
        
    except Exception as e:
        logger.error(f"シャットダウン中にエラー: {str(e)}", exc_info=True)


# 標準MCPツール定義 - ツールレジストリパターン
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


# 標準MCPツールハンドラー登録
@server.list_tools()
async def list_tools() -> List[Tool]:
    """
    標準MCPツールリストハンドラー
    
    利用可能なMCPツールのリストを標準形式で返します。
    """
    logger.debug(f"📋 ツールリスト要求 - {len(TOOL_DEFINITIONS)}個のツールを返却")
    return TOOL_DEFINITIONS


# 標準MCPサーバーユーティリティ
def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> None:
    """
    標準MCPツール引数検証ユーティリティ
    
    Args:
        tool_name: ツール名
        arguments: 引数辞書
        
    Raises:
        ValueError: 引数が無効な場合
    """
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


async def execute_tool_safely(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    標準MCPツール実行ヘルパー
    
    Args:
        tool_name: 実行するツール名
        arguments: ツール引数
        
    Returns:
        Dict[str, Any]: ツール実行結果
    """
    # 引数検証
    validate_tool_arguments(tool_name, arguments)
    
    # ツール実行
    if tool_name == "generate-drawio-xml":
        return await generate_drawio_xml(arguments["prompt"])
        
    elif tool_name == "save-drawio-file":
        filename = arguments.get("filename")
        return await save_drawio_file(arguments["xml_content"], filename)
        
    elif tool_name == "convert-to-png":
        file_id = arguments.get("file_id")
        file_path = arguments.get("file_path")
        return await convert_to_png(file_id=file_id, file_path=file_path)
        
    else:
        raise ValueError(f"不明なツール: {tool_name}")


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    標準MCPツール呼び出しハンドラー
    
    公式MCP SDKの標準パターンに従ってツールを実行します。
    """
    global logger
    
    start_time = time.time()
    
    try:
        logger.info(f"🔧 MCPツール実行開始: {name}")
        logger.debug(f"📝 引数: {list(arguments.keys())}")
        
        # 標準ツール実行パターン
        result = await execute_tool_safely(name, arguments)
        
        # 実行時間の計測とログ
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"✅ MCPツール {name} 実行完了 ({execution_time:.2f}ms)")
        
        # 標準レスポンス形式でフォーマット
        return format_tool_response(name, result)
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"❌ MCPツール {name} 実行エラー: {str(e)} ({execution_time:.2f}ms)", exc_info=True)
        
        # 標準エラーレスポンス
        return [TextContent(
            type="text",
            text=f"❌ ツール {name} の実行に失敗しました。\n\n🚨 エラー詳細:\n• エラー: {str(e)}\n• 実行時間: {execution_time:.2f}ms\n• タイムスタンプ: {datetime.now().isoformat()}"
        )]


def format_tool_response(tool_name: str, result: Dict[str, Any]) -> List[TextContent]:
    """
    標準MCPレスポンスフォーマッター
    
    ツール実行結果を標準的なMCPレスポンス形式でフォーマットします。
    
    Args:
        tool_name: 実行されたツール名
        result: ツール実行結果
        
    Returns:
        List[TextContent]: フォーマットされたMCPレスポンス
    """
    timestamp = datetime.now().isoformat()
    
    if result.get("success"):
        # 成功レスポンス - 標準パターン
        success_responses = {
            "generate-drawio-xml": lambda r: f"""✅ Draw.io XML図表の生成に成功しました。

📄 XMLコンテンツ:
{r['xml_content']}

⏱️ 生成時刻: {timestamp}""",
            
            "save-drawio-file": lambda r: f"""✅ Draw.ioファイルの保存に成功しました。

📁 ファイル詳細:
• ファイルID: {r['file_id']}
• ファイルパス: {r['file_path']}
• ファイル名: {r['filename']}
• 有効期限: {r['expires_at']}

⏱️ 保存時刻: {timestamp}""",
            
            "convert-to-png": lambda r: f"""✅ Draw.ioファイルのPNG変換に成功しました。

🖼️ PNG詳細:
• PNGファイルID: {r['png_file_id']}
• PNGファイルパス: {r['png_file_path']}
• CLI利用可能: {r.get('cli_available', '不明')}
• Base64コンテンツ: {'✅ 利用可能' if r.get('base64_content') else '❌ 含まれていません'}

⏱️ 変換時刻: {timestamp}"""
        }
        
        formatter = success_responses.get(tool_name)
        if formatter:
            text = formatter(result)
        else:
            text = f"✅ ツール {tool_name} の実行に成功しました。\n\n⏱️ 実行時刻: {timestamp}"
            
        return [TextContent(type="text", text=text)]
        
    else:
        # エラーレスポンス - 標準パターン
        error_text = f"""❌ {tool_name} の実行に失敗しました。

🚨 エラー詳細:
• エラー: {result.get('error', '不明なエラー')}
• エラーコード: {result.get('error_code', 'UNKNOWN')}
• タイムスタンプ: {timestamp}"""
        
        # ツール固有のエラー情報を追加
        if tool_name == "convert-to-png":
            cli_available = result.get('cli_available', False)
            error_text += f"\n• CLI利用可能: {'✅ はい' if cli_available else '❌ いいえ'}"
            
            if result.get('fallback_message'):
                error_text += f"\n\n💡 フォールバック手順:\n{result['fallback_message']}"
            
            if result.get('alternatives'):
                error_text += "\n\n🔄 代替オプション:"
                for key, value in result['alternatives'].items():
                    error_text += f"\n• {key}: {value}"
            
            if result.get('troubleshooting'):
                error_text += f"\n\n🔧 トラブルシューティング:\n{result['troubleshooting']}"
        
        return [TextContent(type="text", text=error_text)]


def create_initialization_options() -> InitializationOptions:
    """
    標準MCPサーバー初期化オプションを作成
    
    Returns:
        InitializationOptions: MCP標準の初期化オプション
    """
    return InitializationOptions(
        server_name=SERVER_NAME,
        server_version=SERVER_VERSION,
        capabilities=SERVER_CAPABILITIES
    )


def setup_signal_handlers():
    """
    標準的なシグナルハンドラーを設定
    
    SIGINT (Ctrl+C) と SIGTERM の適切な処理を行います。
    """
    global logger, shutdown_requested
    
    def signal_handler(signum, frame):
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logger.info(f"📡 {signal_name} シグナル受信 - 正常シャットダウン開始")
        shutdown_requested = True
        # asyncio.create_task は main() 内で処理
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logger.info("📡 シグナルハンドラー設定完了")


async def run_mcp_server():
    """
    標準MCPサーバー実行パターン
    
    公式MCP SDKを使用してサーバーを実行し、標準的なライフサイクル管理を行います。
    """
    global logger, shutdown_requested
    
    try:
        # 標準MCPサーバー情報の表示
        logger.info(f"🚀 {SERVER_NAME} v{SERVER_VERSION} 開始")
        logger.info(f"📝 {SERVER_DESCRIPTION}")
        logger.info(f"📋 利用可能なツール: generate-drawio-xml, save-drawio-file, convert-to-png")
        logger.info(f"🔌 公式MCP SDK使用")
        
        # シグナルハンドラーの設定
        setup_signal_handlers()
        
        # 標準MCP stdio サーバーパターン
        async with stdio_server() as (read_stream, write_stream):
            logger.info("🔗 MCP stdio接続確立")
            
            # 標準初期化オプションでサーバー実行
            initialization_options = create_initialization_options()
            logger.info(f"⚙️ 初期化オプション: {initialization_options}")
            
            await server.run(
                read_stream,
                write_stream,
                initialization_options
            )
            
    except Exception as e:
        logger.error(f"❌ MCPサーバー実行エラー: {str(e)}", exc_info=True)
        raise


async def handle_dependency_commands():
    """
    依存関係チェック関連のコマンドライン操作を処理
    
    Returns:
        bool: True if command was handled, False if normal server startup should continue
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Draw.io Server")
    parser.add_argument("--check-dependencies", action="store_true", 
                       help="依存関係をチェックして結果を表示")
    parser.add_argument("--setup-guide", action="store_true",
                       help="セットアップガイダンスを表示")
    parser.add_argument("--check-all", action="store_true",
                       help="すべての依存関係（オプション含む）をチェック")
    
    args = parser.parse_args()
    
    # 依存関係チェックコマンドの処理
    if args.check_dependencies or args.setup_guide or args.check_all:
        # 基本設定の初期化（ログ用）
        try:
            config = MCPServerConfig.from_env()
            logger = setup_logging(config)
        except Exception as e:
            print(f"❌ 設定初期化エラー: {str(e)}", file=sys.stderr)
            return True
        
        dependency_checker = DependencyChecker(logger)
        
        if args.check_dependencies:
            print("🔍 重要な依存関係をチェック中...")
            dependencies_ok, dependency_errors = await dependency_checker.check_startup_dependencies()
            
            if dependencies_ok:
                print("✅ すべての重要な依存関係が利用可能です")
                return True
            else:
                print("❌ 重要な依存関係が不足しています:")
                for error in dependency_errors:
                    print(f"  {error}")
                return True
        
        elif args.check_all:
            print("🔍 すべての依存関係をチェック中...")
            results = await dependency_checker.check_all_dependencies(force_refresh=True)
            
            print(f"\n📊 依存関係チェック結果:")
            print(f"  総数: {results['summary']['total']}")
            print(f"  利用可能: {results['summary']['available']}")
            print(f"  不足: {results['summary']['missing']}")
            print(f"  無効: {results['summary']['invalid']}")
            print(f"  エラー: {results['summary']['errors']}")
            print(f"  重要な問題: {results['summary']['critical_issues']}")
            
            if results['summary']['critical_issues'] > 0:
                print(f"\n❌ 重要な問題:")
                for issue in results['critical_issues']:
                    print(f"  • {issue['name']}: {issue['error']}")
                    if issue['guidance']:
                        print(f"    💡 {issue['guidance']}")
            
            print(f"\n📋 詳細:")
            for dep_name, dep_info in results['dependencies'].items():
                status_emoji = "✅" if dep_info['status'] == 'available' else "❌"
                required_text = " (必須)" if dep_info['required'] else " (オプション)"
                print(f"  {status_emoji} {dep_name}{required_text}: {dep_info['status']}")
                if dep_info['version']:
                    print(f"    バージョン: {dep_info['version']}")
                if dep_info['error']:
                    print(f"    エラー: {dep_info['error']}")
            
            return True
        
        elif args.setup_guide:
            print("📋 セットアップガイダンスを生成中...")
            guidance = await dependency_checker.get_setup_guidance(missing_only=False)
            print(guidance)
            return True
    
    return False


async def main():
    """
    標準MCPサーバーメイン関数
    
    公式MCP SDKの標準パターンに従ってサーバーを初期化・実行します。
    """
    global logger, shutdown_requested
    
    try:
        # コマンドライン引数の処理
        if await handle_dependency_commands():
            return  # 依存関係チェックコマンドが実行された場合は終了
        
        # 標準ライフサイクル管理でサーバー実行
        async with server_lifecycle():
            await run_mcp_server()
            
    except KeyboardInterrupt:
        logger.info("⌨️ キーボード割り込み受信")
    except Exception as e:
        if logger:
            logger.error(f"❌ メイン実行エラー: {str(e)}", exc_info=True)
        else:
            print(f"❌ メイン実行エラー: {str(e)}", file=sys.stderr)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nサーバーが中断されました", file=sys.stderr)
    except Exception as e:
        print(f"致命的エラー: {str(e)}", file=sys.stderr)
        sys.exit(1)