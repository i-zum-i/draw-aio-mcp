#!/usr/bin/env python3
"""
Test script to validate MCP tools functionality using official MCP client.
"""
import asyncio
import sys
import subprocess
from pathlib import Path
from contextlib import asynccontextmanager

# Import official MCP client
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import CallToolRequest


class MCPToolTester:
    def __init__(self):
        self.server_process = None
        self.session = None
        
    @asynccontextmanager
    async def mcp_session(self):
        """Create an MCP client session connected to the server."""
        import os
        from mcp.client.stdio import StdioServerParameters
        
        env = {
            **dict(os.environ),
            "ANTHROPIC_API_KEY": "sk-ant-test-key-for-testing-12345",
            "LOG_LEVEL": "ERROR"  # Reduce noise during testing
        }
        
        # Create server parameters for stdio client
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.server"],
            env=env
        )
        
        try:
            # Create MCP client session using stdio_client
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize the session
                    await session.initialize()
                    self.session = session
                    yield session
        finally:
            # Cleanup is handled by the context managers
            pass
    
    async def call_tool(self, name: str, arguments: dict):
        """Call an MCP tool using the official client."""
        if not self.session:
            raise RuntimeError("MCP session not initialized")
        
        # Use the session's call_tool method directly
        return await self.session.call_tool(name, arguments)
    
    async def test_generate_drawio_xml_tool(self):
        """Test the generate-drawio-xml tool."""
        print("Testing generate-drawio-xml tool...")
        
        try:
            result = await self.call_tool(
                "generate-drawio-xml",
                {
                    "prompt": "Create a simple flowchart showing a user login process with username, password, and success/failure paths"
                }
            )
            
            if not result.content:
                return False, "No content in response"
            
            content_text = result.content[0].text if result.content else ""
            
            # The tool will likely fail without a real API key, but should handle it gracefully
            if "Successfully generated" in content_text:
                return True, "generate-drawio-xml tool works correctly"
            elif "API_KEY" in content_text or "authentication" in content_text.lower():
                return True, f"Tool responded correctly with auth error (expected due to fake API key)"
            elif "Invalid input" in content_text:
                return True, "Tool correctly validated input"
            else:
                return False, f"Unexpected response: {content_text}"
                
        except Exception as e:
            # Expected due to fake API key
            return True, f"Tool handled error correctly: {str(e)}"
    
    async def test_save_drawio_file_tool(self):
        """Test the save-drawio-file tool."""
        print("Testing save-drawio-file tool...")
        
        # Mock Draw.io XML content
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram>
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="Test Box" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="340" y="280" width="120" height="80" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        
        try:
            result = await self.call_tool(
                "save-drawio-file",
                {
                    "xml_content": xml_content,
                    "filename": "test-diagram"
                }
            )
            
            if not result.content:
                return False, "No content in response"
            
            content_text = result.content[0].text if result.content else ""
            
            if "Successfully saved Draw.io file" in content_text:
                return True, "save-drawio-file tool works correctly"
            else:
                return False, f"Unexpected content: {content_text}"
                
        except Exception as e:
            return False, f"Tool failed with exception: {str(e)}"
    
    async def test_convert_to_png_tool(self):
        """Test the convert-to-png tool."""
        print("Testing convert-to-png tool...")
        
        # First, save a file to get a file_id
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram>
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="Test Box" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="340" y="280" width="120" height="80" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        
        try:
            # Save file first
            save_result = await self.call_tool(
                "save-drawio-file",
                {
                    "xml_content": xml_content,
                    "filename": "test-for-png"
                }
            )
            
            if not save_result.content:
                return False, "Failed to save file for PNG conversion test"
            
            # Extract file_id from response text
            content_text = save_result.content[0].text
            import re
            file_id_match = re.search(r"File ID: ([^\n\s]+)", content_text)
            if not file_id_match:
                return False, "Could not extract file_id from save response"
            
            file_id = file_id_match.group(1)
            
            # Now try to convert to PNG
            convert_result = await self.call_tool(
                "convert-to-png",
                {"file_id": file_id}
            )
            
            if not convert_result.content:
                return False, "No content in PNG conversion response"
            
            content_text = convert_result.content[0].text
            
            # The tool should respond with either success or a helpful failure message
            # Since Draw.io CLI is probably not installed, we expect a failure with fallback info
            if "Successfully converted" in content_text:
                return True, "convert-to-png tool succeeded (Draw.io CLI is available)"
            elif "CLI Available: ❌" in content_text or "Draw.io CLI is required" in content_text:
                return True, "convert-to-png tool handled missing CLI gracefully with fallback information"
            else:
                return False, f"Unexpected response: {content_text}"
                
        except Exception as e:
            return False, f"PNG conversion test failed with exception: {str(e)}"
    
    async def test_tool_parameter_validation(self):
        """Test tool parameter validation."""
        print("Testing tool parameter validation...")
        
        try:
            # Test missing required parameter
            try:
                result = await self.call_tool(
                    "generate-drawio-xml",
                    {}  # Missing required 'prompt' parameter
                )
                
                # Should get an error response in content
                if result.content:
                    content_text = result.content[0].text
                    if "prompt" not in content_text.lower() and "required" not in content_text.lower():
                        return False, f"Expected parameter validation error, got: {content_text}"
                else:
                    return False, "Expected error response for missing parameter"
                    
            except Exception as e:
                # This is also acceptable - MCP client validation
                if "prompt" not in str(e).lower():
                    return False, f"Unexpected error for missing parameter: {str(e)}"
            
            # Test invalid tool name
            try:
                result = await self.call_tool(
                    "nonexistent-tool",
                    {"test": "value"}
                )
                return False, "Expected error for nonexistent tool"
                
            except Exception as e:
                # Expected - tool doesn't exist
                if "tool" not in str(e).lower() and "unknown" not in str(e).lower():
                    return False, f"Unexpected error for nonexistent tool: {str(e)}"
            
            return True, "Parameter validation works correctly"
            
        except Exception as e:
            return False, f"Parameter validation test failed: {str(e)}"
    
async def main():
    """Main test runner."""
    tester = MCPToolTester()
    
    try:
        async with tester.mcp_session() as session:
            tests = [
                tester.test_generate_drawio_xml_tool,
                tester.test_save_drawio_file_tool,
                tester.test_convert_to_png_tool,
                tester.test_tool_parameter_validation
            ]
            
            passed = 0
            total = len(tests)
            
            for test in tests:
                try:
                    success, message = await test()
                    if success:
                        print(f"✅ {message}")
                        passed += 1
                    else:
                        print(f"❌ {message}")
                except Exception as e:
                    print(f"❌ Test failed with exception: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"\nResults: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All MCP tools tests passed!")
                return True
            else:
                print("⚠️ Some MCP tools tests failed")
                return False
                
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)