#!/usr/bin/env python3
"""Simple test to verify MCP server can be imported."""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.server import MCPProtocolServer
    print("✅ MCPProtocolServer imported successfully")
    
    # Test basic initialization
    server = MCPProtocolServer()
    print(f"✅ Server initialized with protocol version: {server.protocol_version}")
    print(f"✅ Server has {len(server.tools)} tools: {list(server.tools.keys())}")
    
    print("🎉 MCP migration test passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)