#!/usr/bin/env python3
"""
Test script to validate error handling and edge cases using official MCP client.
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


class ErrorHandlingTester:
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
    
    async def test_invalid_xml_content(self):
        """Test save tool with invalid XML content."""
        print("Testing invalid XML content handling...")
        
        invalid_xml_cases = [
            ("Empty string", ""),
            ("Non-XML content", "This is not XML"),
            ("Malformed XML", "<not>valid</xml>"),
            ("Missing mxfile", "<xml><something/></xml>"),
            ("Missing mxGraphModel", "<mxfile><something/></mxfile>"),
            ("Missing root", "<mxfile><mxGraphModel><something/></mxGraphModel></mxfile>"),
        ]
        
        for case_name, xml_content in invalid_xml_cases:
            try:
                result = await self.call_tool(
                    "save-drawio-file",
                    {"xml_content": xml_content}
                )
                
                if not result.content:
                    return False, f"No content for {case_name}"
                
                content_text = result.content[0].text
                
                if "Successfully saved" in content_text:
                    return False, f"Expected error for {case_name}, but got success"
                elif "Invalid XML content" not in content_text and "Invalid input" not in content_text:
                    return False, f"Expected XML validation error for {case_name}, got: {content_text}"
                    
            except Exception as e:
                # Also acceptable - client-side validation or server error
                if "xml" not in str(e).lower() and "invalid" not in str(e).lower():
                    return False, f"Unexpected error for {case_name}: {str(e)}"
        
        return True, "Invalid XML content handling works correctly"
    
    async def test_prompt_validation(self):
        """Test generate tool with invalid prompts."""
        print("Testing prompt validation...")
        
        invalid_prompts = [
            ("Empty string", ""),
            ("Only whitespace", "   "),
            ("Too short", "hi"),
            ("Too long", "x" * 20000),
        ]
        
        for case_name, prompt in invalid_prompts:
            try:
                result = await self.call_tool(
                    "generate-drawio-xml",
                    {"prompt": prompt}
                )
                
                if not result.content:
                    return False, f"No content for {case_name}"
                
                content_text = result.content[0].text
                
                if "Successfully generated" in content_text:
                    return False, f"Expected error for {case_name}, but got success"
                elif "Invalid input" not in content_text and "too short" not in content_text.lower() and "too long" not in content_text.lower():
                    return False, f"Expected input validation error for {case_name}, got: {content_text}"
                    
            except Exception as e:
                # Also acceptable - client-side or server validation
                if "prompt" not in str(e).lower() and "invalid" not in str(e).lower():
                    return False, f"Unexpected error for {case_name}: {str(e)}"
        
        return True, "Prompt validation works correctly"
    
    async def test_file_not_found_conversion(self):
        """Test PNG conversion with non-existent file."""
        print("Testing PNG conversion with non-existent file...")
        
        try:
            result = await self.call_tool(
                "convert-to-png",
                {"file_id": "nonexistent-file-id-12345"}
            )
            
            if not result.content:
                return False, "No content for non-existent file"
            
            content_text = result.content[0].text
            
            if "File not found" not in content_text and "expired" not in content_text:
                return False, f"Expected file not found error, got: {content_text}"
            
            return True, "File not found handling works correctly"
            
        except Exception as e:
            # Also acceptable if client/server handles it as exception
            if "file" not in str(e).lower() and "not found" not in str(e).lower():
                return False, f"Unexpected error: {str(e)}"
            return True, "File not found handling works correctly"
    
    async def test_conflicting_parameters(self):
        """Test PNG conversion with conflicting parameters."""
        print("Testing PNG conversion with conflicting parameters...")
        
        try:
            result = await self.call_tool(
                "convert-to-png",
                {
                    "file_id": "some-id",
                    "file_path": "/some/path"
                }
            )
            
            if not result.content:
                return False, "No content for conflicting parameters"
            
            content_text = result.content[0].text
            
            if "Cannot provide both" not in content_text:
                return False, f"Expected conflicting parameters error, got: {content_text}"
            
            return True, "Conflicting parameters handling works correctly"
            
        except Exception as e:
            # Also acceptable if validation happens at client/server level
            if "parameter" not in str(e).lower() and "conflict" not in str(e).lower():
                return False, f"Unexpected error: {str(e)}"
            return True, "Conflicting parameters handling works correctly"
    
    async def test_missing_parameters_png(self):
        """Test PNG conversion without required parameters."""
        print("Testing PNG conversion with missing parameters...")
        
        try:
            result = await self.call_tool(
                "convert-to-png",
                {}  # No file_id or file_path
            )
            
            if not result.content:
                return False, "No content for missing parameters"
            
            content_text = result.content[0].text
            
            if "Must provide either" not in content_text:
                return False, f"Expected missing parameters error, got: {content_text}"
            
            return True, "Missing parameters handling works correctly"
            
        except Exception as e:
            # Also acceptable if validation happens at client/server level
            if "parameter" not in str(e).lower() and "required" not in str(e).lower():
                return False, f"Unexpected error: {str(e)}"
            return True, "Missing parameters handling works correctly"
    
    async def test_tools_list(self):
        """Test that the server provides the expected tools."""
        print("Testing tools list...")
        
        try:
            tools = await self.session.list_tools()
            
            if not tools.tools:
                return False, "No tools returned"
            
            tool_names = [tool.name for tool in tools.tools]
            expected_tools = ["generate-drawio-xml", "save-drawio-file", "convert-to-png"]
            
            for expected_tool in expected_tools:
                if expected_tool not in tool_names:
                    return False, f"Missing expected tool: {expected_tool}"
            
            return True, f"Tools list correct: {tool_names}"
            
        except Exception as e:
            return False, f"Failed to list tools: {str(e)}"
    
async def main():
    """Main test runner."""
    tester = ErrorHandlingTester()
    
    try:
        async with tester.mcp_session() as session:
            tests = [
                tester.test_invalid_xml_content,
                tester.test_prompt_validation,
                tester.test_file_not_found_conversion,
                tester.test_conflicting_parameters,
                tester.test_missing_parameters_png,
                tester.test_tools_list
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
                print("🎉 All error handling tests passed!")
                return True
            else:
                print("⚠️ Some error handling tests failed")
                return False
                
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)