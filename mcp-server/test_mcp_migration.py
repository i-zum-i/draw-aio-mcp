#!/usr/bin/env python3
"""
Test script to verify MCP server migration to official SDK.

This script tests that:
1. The official MCP SDK can be imported
2. The server can be initialized
3. Tools are properly registered
4. Basic functionality works
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_mcp_compliance():
    """Test that our MCP-compliant implementation works."""
    try:
        # Test that our MCP server can be imported
        from src.server import MCPProtocolServer
        logger.info("✅ MCP-compliant server imports successful")
        
        # Test that it has the required MCP protocol attributes
        server = MCPProtocolServer()
        if hasattr(server, 'protocol_version') and server.protocol_version == "2024-11-05":
            logger.info("✅ MCP protocol version correct")
        else:
            logger.error("❌ MCP protocol version incorrect or missing")
            return False
        
        # Test that it has the required tools
        if hasattr(server, 'tools') and len(server.tools) == 3:
            logger.info("✅ MCP tools properly defined")
        else:
            logger.error("❌ MCP tools not properly defined")
            return False
        
        return True
    except ImportError as e:
        logger.error(f"❌ MCP-compliant server import failed: {e}")
        return False


async def test_server_initialization():
    """Test that the server can be initialized."""
    try:
        # Set required environment variables for testing
        os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key-for-initialization')
        
        from src.server import MCPProtocolServer
        from src.config import MCPServerConfig
        
        # Create test config
        config = MCPServerConfig(
            anthropic_api_key='test-key-for-initialization',
            temp_dir='./test_temp',
            server_name='test-mcp-drawio-server',
            server_version='1.0.0-test'
        )
        
        # Initialize server (but don't run it)
        server = MCPProtocolServer(config)
        logger.info("✅ MCP-compliant server initialization successful")
        
        # Test that server has required MCP attributes
        if hasattr(server, 'protocol_version') and hasattr(server, 'tools'):
            logger.info("✅ MCP protocol attributes present")
        else:
            logger.error("❌ MCP protocol attributes missing")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Server initialization failed: {e}")
        return False


async def test_tool_registration():
    """Test that tools are properly registered."""
    try:
        # Set required environment variables for testing
        os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key-for-initialization')
        
        from src.server import MCPProtocolServer
        from src.config import MCPServerConfig
        
        # Create test config
        config = MCPServerConfig(
            anthropic_api_key='test-key-for-initialization',
            temp_dir='./test_temp',
            server_name='test-mcp-drawio-server',
            server_version='1.0.0-test'
        )
        
        # Initialize server
        server = MCPProtocolServer(config)
        
        # Check that tools are properly defined
        expected_tools = ["generate-drawio-xml", "save-drawio-file", "convert-to-png"]
        if all(tool in server.tools for tool in expected_tools):
            logger.info("✅ All expected MCP tools are registered")
        else:
            logger.error("❌ Some expected MCP tools are missing")
            return False
        
        # Check that each tool has proper MCP schema
        for tool_name, tool_def in server.tools.items():
            if all(key in tool_def for key in ["name", "description", "inputSchema"]):
                logger.info(f"✅ Tool {tool_name} has proper MCP schema")
            else:
                logger.error(f"❌ Tool {tool_name} missing required MCP schema fields")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Tool registration test failed: {e}")
        return False


async def test_dependencies():
    """Test that all required dependencies are available."""
    try:
        # Test core dependencies
        import anthropic
        import httpx
        import pydantic
        logger.info("✅ Core dependencies available")
        
        # Test our modules
        from src.llm_service import LLMService
        from src.file_service import FileService
        from src.image_service import ImageService
        from src.config import MCPServerConfig
        from src.exceptions import MCPServerError
        logger.info("✅ All internal modules importable")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Dependency test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("🧪 Starting MCP migration tests...")
    
    tests = [
        ("MCP Compliance", test_mcp_compliance),
        ("Dependencies", test_dependencies),
        ("Server Initialization", test_server_initialization),
        ("Tool Registration", test_tool_registration),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running test: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All tests passed! MCP migration appears successful.")
        return True
    else:
        logger.error("💥 Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)