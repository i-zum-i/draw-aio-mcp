#!/usr/bin/env python3
"""
Test script for save-drawio-file tool through MCP server.
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server import MCPServer


# Sample valid Draw.io XML content
SAMPLE_DRAWIO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="5.0" version="22.1.16" etag="test">
  <diagram name="Page-1" id="test-id">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="2" value="Test Box" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="340" y="280" width="120" height="60" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""


async def test_save_drawio_file_mcp():
    """Test save-drawio-file tool through MCP server."""
    print("Testing save-drawio-file tool through MCP server...")
    
    server = MCPServer()
    
    # Test tools/call request for save-drawio-file
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "save-drawio-file",
            "arguments": {
                "xml_content": SAMPLE_DRAWIO_XML,
                "filename": "test-mcp-diagram"
            }
        }
    }
    
    response = await server.handle_request(request)
    
    print("Save file response:")
    print(f"  Success: {response.get('result') is not None}")
    
    if response.get('result'):
        content = response['result']['content'][0]['text']
        print(f"  Content: {content}")
        
        # Extract file ID from response
        if "File ID:" in content:
            file_id = content.split("File ID: ")[1].split("\n")[0]
            print(f"  Extracted File ID: {file_id}")
            return file_id
    else:
        print(f"  Error: {response.get('error', {}).get('message', 'Unknown error')}")
        return None


async def test_save_invalid_xml_mcp():
    """Test save-drawio-file tool with invalid XML through MCP server."""
    print("\nTesting save-drawio-file tool with invalid XML...")
    
    server = MCPServer()
    
    # Test tools/call request with invalid XML
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "save-drawio-file",
            "arguments": {
                "xml_content": "<invalid>Not Draw.io XML</invalid>"
            }
        }
    }
    
    response = await server.handle_request(request)
    
    print("Invalid XML response:")
    print(f"  Success: {response.get('result') is not None}")
    
    if response.get('result'):
        content = response['result']['content'][0]['text']
        print(f"  Content: {content}")
        
        # Should contain error message
        if "Failed to execute" in content and "INVALID_XML" in content:
            print("  ✓ Correctly rejected invalid XML")
            return True
        else:
            print("  ✗ Did not properly reject invalid XML")
            return False
    else:
        print(f"  Error: {response.get('error', {}).get('message', 'Unknown error')}")
        return False


async def main():
    """Run MCP server tests for save-drawio-file tool."""
    print("Running save-drawio-file MCP server tests...\n")
    
    # Test successful save
    file_id = await test_save_drawio_file_mcp()
    success1 = file_id is not None
    
    # Test error handling
    success2 = await test_save_invalid_xml_mcp()
    
    print(f"\nTest Results:")
    print(f"  Valid XML save: {'✓' if success1 else '✗'}")
    print(f"  Invalid XML rejection: {'✓' if success2 else '✗'}")
    
    if success1 and success2:
        print("✓ All MCP server tests passed!")
        return 0
    else:
        print("✗ Some MCP server tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))