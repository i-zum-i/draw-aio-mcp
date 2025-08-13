#!/usr/bin/env python3
"""Test MCP protocol compliance."""
import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_mcp_protocol():
    """Test MCP protocol requests and responses."""
    try:
        # Set test environment
        os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key-for-protocol-test')
        
        from src.server import MCPProtocolServer
        from src.config import MCPServerConfig
        
        # Create test config
        config = MCPServerConfig(
            anthropic_api_key='test-key-for-protocol-test',
            temp_dir='./test_temp',
            server_name='test-mcp-server',
            server_version='1.0.0-test'
        )
        
        # Initialize server
        server = MCPProtocolServer(config)
        print("✅ Server initialized")
        
        # Test initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = await server.handle_request(init_request)
        print("✅ Initialize request handled")
        
        # Verify initialize response structure
        assert init_response.get("jsonrpc") == "2.0"
        assert init_response.get("id") == 1
        assert "result" in init_response
        assert "protocolVersion" in init_response["result"]
        assert "capabilities" in init_response["result"]
        assert "serverInfo" in init_response["result"]
        print("✅ Initialize response structure correct")
        
        # Test tools/list request
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        list_response = await server.handle_request(list_request)
        print("✅ Tools/list request handled")
        
        # Verify tools/list response structure
        assert list_response.get("jsonrpc") == "2.0"
        assert list_response.get("id") == 2
        assert "result" in list_response
        assert "tools" in list_response["result"]
        assert len(list_response["result"]["tools"]) == 3
        print("✅ Tools/list response structure correct")
        
        # Test ping request
        ping_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "ping",
            "params": {}
        }
        
        ping_response = await server.handle_request(ping_request)
        print("✅ Ping request handled")
        
        # Verify ping response structure
        assert ping_response.get("jsonrpc") == "2.0"
        assert ping_response.get("id") == 3
        assert "result" in ping_response
        print("✅ Ping response structure correct")
        
        # Test invalid method
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "invalid/method",
            "params": {}
        }
        
        invalid_response = await server.handle_request(invalid_request)
        print("✅ Invalid method request handled")
        
        # Verify error response structure
        assert invalid_response.get("jsonrpc") == "2.0"
        assert invalid_response.get("id") == 4
        assert "error" in invalid_response
        assert invalid_response["error"]["code"] == -32601  # Method not found
        print("✅ Error response structure correct")
        
        print("🎉 All MCP protocol tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ MCP protocol test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_protocol())
    sys.exit(0 if success else 1)