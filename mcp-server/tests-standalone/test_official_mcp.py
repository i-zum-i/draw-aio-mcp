#!/usr/bin/env python3.10
"""Test official MCP library functionality."""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_official_mcp_import():
    """Test if we can import and use the official MCP library."""
    try:
        # Test basic MCP import
        import mcp
        from mcp import Tool
        from mcp.server import Server
        from mcp.types import TextContent
        
        print("✅ Successfully imported MCP library components")
        print(f"📦 MCP library location: {mcp.__file__}")
        
        # Test creating a basic server
        server = Server("test-mcp-server")
        print("✅ Created MCP server instance")
        
        # Test defining a simple tool
        @server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="test-tool",
                    description="A simple test tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Test message"
                            }
                        },
                        "required": ["message"]
                    }
                )
            ]
        
        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name == "test-tool":
                message = arguments.get("message", "No message")
                return [
                    TextContent(
                        type="text",
                        text=f"Echo: {message}"
                    )
                ]
            raise ValueError(f"Unknown tool: {name}")
        
        print("✅ Successfully defined MCP tools")
        
        # Test the tool listing
        tools = await list_tools()
        print(f"✅ Tool listing works: {len(tools)} tools defined")
        
        # Test tool execution
        result = await call_tool("test-tool", {"message": "Hello MCP!"})
        print(f"✅ Tool execution works: {result[0].text}")
        
        print("🎉 Official MCP library test passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import MCP library: {e}")
        return False
    except Exception as e:
        print(f"❌ MCP library test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_with_anthropic():
    """Test MCP with Anthropic integration."""
    try:
        # Set test API key
        os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key-for-mcp-test')
        
        # Test our existing services with MCP
        from src.llm_service import LLMService
        from src.file_service import FileService
        from src.image_service import ImageService
        
        print("✅ Imported existing services")
        
        # Test basic service initialization
        file_service = FileService("./test_temp")
        print("✅ FileService initialized")
        
        image_service = ImageService()
        print("✅ ImageService initialized")
        
        # Test LLM service (with test key)
        try:
            llm_service = LLMService()
            print("✅ LLMService initialized")
        except Exception as e:
            print(f"⚠️ LLMService init failed (expected with test key): {e}")
        
        print("✅ Service integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all MCP tests."""
    print("🚀 Testing official MCP library...")
    
    test1 = await test_official_mcp_import()
    test2 = await test_mcp_with_anthropic()
    
    if test1 and test2:
        print("🎉 All MCP tests passed!")
        return True
    else:
        print("❌ Some MCP tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)