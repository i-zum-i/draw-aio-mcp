#!/usr/bin/env python3
"""
Test script to verify MCP server can load all tools including convert-to-png.
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server import MCPServer


async def test_server_tools():
    """Test that MCP server can load all tools."""
    print("🧪 Testing MCP Server Tool Loading")
    print("=" * 50)
    
    try:
        # Create server instance
        server = MCPServer()
        
        print("✅ Server created successfully")
        print(f"Available tools: {list(server.tools.keys())}")
        
        # Test tools/list request
        list_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        response = await server.handle_request(list_request)
        
        if response.get("result") and response["result"].get("tools"):
            tools = response["result"]["tools"]
            print(f"\n📋 Tools available via MCP protocol:")
            for tool in tools:
                print(f"   • {tool['name']}: {tool['description']}")
            
            # Check that convert-to-png is included
            tool_names = [tool['name'] for tool in tools]
            if 'convert-to-png' in tool_names:
                print("\n✅ convert-to-png tool is properly registered")
                
                # Find the convert-to-png tool schema
                convert_tool = next(tool for tool in tools if tool['name'] == 'convert-to-png')
                print(f"   Description: {convert_tool['description']}")
                print(f"   Input schema: {convert_tool['inputSchema']}")
                
                return True
            else:
                print("\n❌ convert-to-png tool is missing from tool list")
                return False
        else:
            print("\n❌ Failed to get tools list from server")
            print(f"Response: {response}")
            return False
    
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_server_tools()
    
    if success:
        print("\n🎉 All server tool tests passed!")
        return 0
    else:
        print("\n💥 Server tool tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)