#!/usr/bin/env python3
"""
Test script for the MCP server functionality.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.server import MCPServer


async def test_mcp_server():
    """Test the MCP server request handling."""
    print("Testing MCP server...")
    
    server = MCPServer()
    
    # Test initialize request
    print("\n1. Testing initialize request...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = await server.handle_request(init_request)
    print(f"Initialize response: {json.dumps(response, indent=2)}")
    
    # Test tools/list request
    print("\n2. Testing tools/list request...")
    list_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = await server.handle_request(list_request)
    print(f"Tools list response: {json.dumps(response, indent=2)}")
    
    # Test tools/call request (without API key - should fail gracefully)
    print("\n3. Testing tools/call request (without API key)...")
    call_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "generate-drawio-xml",
            "arguments": {
                "prompt": "Create a simple flowchart showing user login process"
            }
        }
    }
    
    response = await server.handle_request(call_request)
    print(f"Tools call response: {json.dumps(response, indent=2)}")
    
    # Test invalid method
    print("\n4. Testing invalid method...")
    invalid_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "invalid/method",
        "params": {}
    }
    
    response = await server.handle_request(invalid_request)
    print(f"Invalid method response: {json.dumps(response, indent=2)}")
    
    # Test invalid tool name
    print("\n5. Testing invalid tool name...")
    invalid_tool_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "invalid-tool",
            "arguments": {
                "prompt": "test"
            }
        }
    }
    
    response = await server.handle_request(invalid_tool_request)
    print(f"Invalid tool response: {json.dumps(response, indent=2)}")


def test_server_tools():
    """Test server tool registration."""
    print("\nTesting server tool registration...")
    
    server = MCPServer()
    
    # Check that tools are registered
    if "generate-drawio-xml" in server.tools:
        print("✓ generate-drawio-xml tool is registered")
        
        tool_info = server.tools["generate-drawio-xml"]
        if "schema" in tool_info and "handler" in tool_info:
            print("✓ Tool has schema and handler")
        else:
            print("✗ Tool missing schema or handler")
    else:
        print("✗ generate-drawio-xml tool is not registered")


async def main():
    """Main test function."""
    print("=== MCP Server Test ===")
    
    test_server_tools()
    await test_mcp_server()
    
    print("\n=== Test Summary ===")
    print("MCP server tests completed!")
    print("Note: Tool execution tests require ANTHROPIC_API_KEY to be set.")


if __name__ == "__main__":
    asyncio.run(main())