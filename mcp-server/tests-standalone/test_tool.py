#!/usr/bin/env python3
"""
Test script for the generate-drawio-xml MCP tool.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools import generate_drawio_xml


async def test_generate_drawio_xml():
    """Test the generate-drawio-xml tool."""
    print("Testing generate-drawio-xml tool...")
    
    # Test with a simple prompt
    test_prompt = "Create a simple flowchart showing a user login process with username, password, validation, and success/failure paths"
    
    print(f"Test prompt: {test_prompt}")
    print("Generating XML...")
    
    try:
        result = await generate_drawio_xml(test_prompt)
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"XML length: {len(result['xml_content'])} characters")
            print("XML preview (first 500 chars):")
            print(result['xml_content'][:500] + "..." if len(result['xml_content']) > 500 else result['xml_content'])
        else:
            print(f"Error: {result['error']}")
            print(f"Error code: {result['error_code']}")
        
        print(f"Timestamp: {result['timestamp']}")
        
    except Exception as e:
        print(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_input_validation():
    """Test input validation."""
    print("\nTesting input validation...")
    
    # Test empty prompt
    result = await generate_drawio_xml("")
    print(f"Empty prompt - Success: {result['success']}, Error: {result.get('error', 'None')}")
    
    # Test very short prompt
    result = await generate_drawio_xml("Hi")
    print(f"Short prompt - Success: {result['success']}, Error: {result.get('error', 'None')}")
    
    # Test very long prompt
    long_prompt = "A" * 15000
    result = await generate_drawio_xml(long_prompt)
    print(f"Long prompt - Success: {result['success']}, Error: {result.get('error', 'None')}")


async def main():
    """Main test function."""
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is required")
        print("Please set it before running the test:")
        print("export ANTHROPIC_API_KEY=your_api_key_here")
        return
    
    await test_generate_drawio_xml()
    await test_input_validation()
    
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())