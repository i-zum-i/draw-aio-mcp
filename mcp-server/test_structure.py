#!/usr/bin/env python3
"""
Test script to verify the MCP tool structure without requiring API key.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools import sanitize_prompt, GENERATE_DRAWIO_XML_TOOL_SCHEMA


def test_sanitize_prompt():
    """Test the prompt sanitization function."""
    print("Testing prompt sanitization...")
    
    # Test valid prompt
    try:
        result = sanitize_prompt("Create a simple flowchart")
        print(f"✓ Valid prompt sanitized: '{result}'")
    except Exception as e:
        print(f"✗ Valid prompt failed: {e}")
    
    # Test empty prompt
    try:
        result = sanitize_prompt("")
        print(f"✗ Empty prompt should fail but got: '{result}'")
    except ValueError as e:
        print(f"✓ Empty prompt correctly rejected: {e}")
    
    # Test short prompt
    try:
        result = sanitize_prompt("Hi")
        print(f"✗ Short prompt should fail but got: '{result}'")
    except ValueError as e:
        print(f"✓ Short prompt correctly rejected: {e}")
    
    # Test long prompt
    try:
        result = sanitize_prompt("A" * 15000)
        print(f"✗ Long prompt should fail but got length: {len(result)}")
    except ValueError as e:
        print(f"✓ Long prompt correctly rejected: {e}")
    
    # Test None input
    try:
        result = sanitize_prompt(None)
        print(f"✗ None input should fail but got: '{result}'")
    except ValueError as e:
        print(f"✓ None input correctly rejected: {e}")


def test_tool_schema():
    """Test the MCP tool schema."""
    print("\nTesting MCP tool schema...")
    
    schema = GENERATE_DRAWIO_XML_TOOL_SCHEMA
    
    # Check required fields
    required_fields = ["name", "description", "inputSchema"]
    for field in required_fields:
        if field in schema:
            print(f"✓ Schema has required field: {field}")
        else:
            print(f"✗ Schema missing required field: {field}")
    
    # Check tool name
    if schema.get("name") == "generate-drawio-xml":
        print("✓ Tool name is correct")
    else:
        print(f"✗ Tool name is incorrect: {schema.get('name')}")
    
    # Check input schema structure
    input_schema = schema.get("inputSchema", {})
    if input_schema.get("type") == "object":
        print("✓ Input schema type is object")
    else:
        print(f"✗ Input schema type is incorrect: {input_schema.get('type')}")
    
    # Check prompt parameter
    properties = input_schema.get("properties", {})
    if "prompt" in properties:
        print("✓ Prompt parameter is defined")
        prompt_def = properties["prompt"]
        if prompt_def.get("type") == "string":
            print("✓ Prompt parameter type is string")
        else:
            print(f"✗ Prompt parameter type is incorrect: {prompt_def.get('type')}")
    else:
        print("✗ Prompt parameter is missing")
    
    # Check required parameters
    required = input_schema.get("required", [])
    if "prompt" in required:
        print("✓ Prompt is marked as required")
    else:
        print("✗ Prompt is not marked as required")


def test_imports():
    """Test that all required modules can be imported."""
    print("\nTesting imports...")
    
    try:
        from src.exceptions import LLMError, LLMErrorCode
        print("✓ Exceptions imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import exceptions: {e}")
    
    try:
        from src.llm_service import LLMService
        print("✓ LLMService imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import LLMService: {e}")
    
    try:
        from src.server import MCPServer
        print("✓ MCPServer imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import MCPServer: {e}")


def main():
    """Main test function."""
    print("=== MCP Tool Structure Test ===")
    
    test_imports()
    test_sanitize_prompt()
    test_tool_schema()
    
    print("\n=== Test Summary ===")
    print("Structure tests completed!")
    print("Note: API functionality tests require ANTHROPIC_API_KEY to be set.")


if __name__ == "__main__":
    main()