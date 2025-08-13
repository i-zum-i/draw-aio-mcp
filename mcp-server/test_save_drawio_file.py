#!/usr/bin/env python3
"""
Test script for save-drawio-file MCP tool.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools import save_drawio_file, validate_drawio_xml
from src.file_service import FileService


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

INVALID_XML = """<invalid>This is not valid Draw.io XML</invalid>"""


async def test_validate_drawio_xml():
    """Test XML validation function."""
    print("Testing XML validation...")
    
    # Test valid XML
    try:
        validate_drawio_xml(SAMPLE_DRAWIO_XML)
        print("✓ Valid XML passed validation")
    except ValueError as e:
        print(f"✗ Valid XML failed validation: {e}")
        return False
    
    # Test invalid XML
    try:
        validate_drawio_xml(INVALID_XML)
        print("✗ Invalid XML passed validation (should have failed)")
        return False
    except ValueError:
        print("✓ Invalid XML correctly rejected")
    
    # Test empty XML
    try:
        validate_drawio_xml("")
        print("✗ Empty XML passed validation (should have failed)")
        return False
    except ValueError:
        print("✓ Empty XML correctly rejected")
    
    # Test None XML
    try:
        validate_drawio_xml(None)
        print("✗ None XML passed validation (should have failed)")
        return False
    except ValueError:
        print("✓ None XML correctly rejected")
    
    return True


async def test_save_drawio_file_success():
    """Test successful file saving."""
    print("\nTesting successful file saving...")
    
    # Test with default filename
    result = await save_drawio_file(SAMPLE_DRAWIO_XML)
    
    if not result["success"]:
        print(f"✗ File saving failed: {result['error']}")
        return False
    
    print(f"✓ File saved successfully with ID: {result['file_id']}")
    print(f"  File path: {result['file_path']}")
    print(f"  Filename: {result['filename']}")
    print(f"  Expires at: {result['expires_at']}")
    
    # Verify file exists
    if not Path(result['file_path']).exists():
        print("✗ Saved file does not exist on disk")
        return False
    
    print("✓ File exists on disk")
    
    # Test with custom filename
    result2 = await save_drawio_file(SAMPLE_DRAWIO_XML, "test-diagram")
    
    if not result2["success"]:
        print(f"✗ File saving with custom filename failed: {result2['error']}")
        return False
    
    print(f"✓ File saved with custom filename: {result2['filename']}")
    
    return True


async def test_save_drawio_file_errors():
    """Test error handling."""
    print("\nTesting error handling...")
    
    # Test invalid XML
    result = await save_drawio_file(INVALID_XML)
    
    if result["success"]:
        print("✗ Invalid XML was accepted (should have failed)")
        return False
    
    if result["error_code"] != "INVALID_XML":
        print(f"✗ Wrong error code for invalid XML: {result['error_code']}")
        return False
    
    print("✓ Invalid XML correctly rejected")
    
    # Test empty XML
    result = await save_drawio_file("")
    
    if result["success"]:
        print("✗ Empty XML was accepted (should have failed)")
        return False
    
    print("✓ Empty XML correctly rejected")
    
    # Test invalid filename type
    result = await save_drawio_file(SAMPLE_DRAWIO_XML, 123)
    
    if result["success"]:
        print("✗ Invalid filename type was accepted (should have failed)")
        return False
    
    if result["error_code"] != "INVALID_FILENAME":
        print(f"✗ Wrong error code for invalid filename: {result['error_code']}")
        return False
    
    print("✓ Invalid filename type correctly rejected")
    
    # Test filename too long
    long_filename = "a" * 101
    result = await save_drawio_file(SAMPLE_DRAWIO_XML, long_filename)
    
    if result["success"]:
        print("✗ Too long filename was accepted (should have failed)")
        return False
    
    print("✓ Too long filename correctly rejected")
    
    return True


async def test_file_service_integration():
    """Test integration with FileService."""
    print("\nTesting FileService integration...")
    
    # Save a file
    result = await save_drawio_file(SAMPLE_DRAWIO_XML, "integration-test")
    
    if not result["success"]:
        print(f"✗ Failed to save file: {result['error']}")
        return False
    
    file_id = result["file_id"]
    
    # Test file service can retrieve the file
    file_service = FileService()
    
    try:
        file_path = await file_service.get_file_path(file_id)
        print(f"✓ FileService can retrieve file path: {file_path}")
        
        file_info = await file_service.get_file_info(file_id)
        print(f"✓ FileService can retrieve file info: {file_info.original_name}")
        
        exists = await file_service.file_exists(file_id)
        if not exists:
            print("✗ FileService reports file doesn't exist")
            return False
        
        print("✓ FileService confirms file exists")
        
    except Exception as e:
        print(f"✗ FileService integration failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("Running save-drawio-file tool tests...\n")
    
    tests = [
        test_validate_drawio_xml,
        test_save_drawio_file_success,
        test_save_drawio_file_errors,
        test_file_service_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
            else:
                print(f"Test {test.__name__} failed")
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))