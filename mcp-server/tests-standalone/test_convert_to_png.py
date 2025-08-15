#!/usr/bin/env python3
"""
Test script for convert-to-png MCP tool.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools import convert_to_png, save_drawio_file
from src.file_service import FileService
from src.image_service import ImageService


# Sample Draw.io XML content for testing
SAMPLE_DRAWIO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="5.0" version="22.1.16" etag="test">
  <diagram name="Page-1" id="test-diagram">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="2" value="Start" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="364" y="40" width="100" height="60" as="geometry" />
        </mxCell>
        <mxCell id="3" value="Process" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="354" y="140" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="4" value="End" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="364" y="240" width="100" height="60" as="geometry" />
        </mxCell>
        <mxCell id="5" value="" style="endArrow=classic;html=1;rounded=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="2" target="3">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="390" y="180" as="sourcePoint" />
            <mxPoint x="440" y="130" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="6" value="" style="endArrow=classic;html=1;rounded=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="3" target="4">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="390" y="280" as="sourcePoint" />
            <mxPoint x="440" y="230" as="targetPoint" />
          </mxGeometry>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""


async def test_convert_to_png_with_file_id():
    """Test convert-to-png tool using file_id parameter."""
    print("=== Testing convert-to-png with file_id ===")
    
    try:
        # First, save a Draw.io file to get a file_id
        print("1. Saving sample Draw.io file...")
        save_result = await save_drawio_file(SAMPLE_DRAWIO_XML, "test-diagram")
        
        if not save_result["success"]:
            print(f"❌ Failed to save Draw.io file: {save_result['error']}")
            return False
        
        file_id = save_result["file_id"]
        print(f"✅ Saved Draw.io file with ID: {file_id}")
        print(f"   File path: {save_result['file_path']}")
        
        # Now test PNG conversion
        print("\n2. Converting to PNG using file_id...")
        convert_result = await convert_to_png(file_id=file_id)
        
        print(f"Success: {convert_result['success']}")
        print(f"CLI Available: {convert_result['cli_available']}")
        
        if convert_result["success"]:
            print(f"✅ PNG conversion successful!")
            print(f"   PNG File ID: {convert_result['png_file_id']}")
            print(f"   PNG File Path: {convert_result['png_file_path']}")
            print(f"   Base64 Content: {'Available' if convert_result['base64_content'] else 'Not included'}")
            
            # Check if PNG file actually exists
            png_path = convert_result['png_file_path']
            if png_path and Path(png_path).exists():
                print(f"✅ PNG file exists at: {png_path}")
                file_size = Path(png_path).stat().st_size
                print(f"   File size: {file_size} bytes")
            else:
                print(f"⚠️  PNG file not found at: {png_path}")
            
            return True
        else:
            print(f"❌ PNG conversion failed: {convert_result['error']}")
            print(f"   Error code: {convert_result['error_code']}")
            
            if convert_result.get('fallback_message'):
                print(f"\n📋 Fallback Instructions:")
                print(convert_result['fallback_message'])
            
            if convert_result.get('alternatives'):
                print(f"\n🔄 Alternative Options:")
                for key, value in convert_result['alternatives'].items():
                    print(f"   • {key}: {value}")
            
            return False
    
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_convert_to_png_with_file_path():
    """Test convert-to-png tool using file_path parameter."""
    print("\n=== Testing convert-to-png with file_path ===")
    
    try:
        # Create a temporary .drawio file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.drawio', delete=False) as f:
            f.write(SAMPLE_DRAWIO_XML)
            temp_file_path = f.name
        
        print(f"1. Created temporary .drawio file: {temp_file_path}")
        
        # Test PNG conversion using file_path
        print("2. Converting to PNG using file_path...")
        convert_result = await convert_to_png(file_path=temp_file_path)
        
        print(f"Success: {convert_result['success']}")
        print(f"CLI Available: {convert_result['cli_available']}")
        
        if convert_result["success"]:
            print(f"✅ PNG conversion successful!")
            print(f"   PNG File ID: {convert_result['png_file_id']}")
            print(f"   PNG File Path: {convert_result['png_file_path']}")
            print(f"   Base64 Content: {'Available' if convert_result['base64_content'] else 'Not included'}")
            
            # Check if PNG file actually exists
            png_path = convert_result['png_file_path']
            if png_path and Path(png_path).exists():
                print(f"✅ PNG file exists at: {png_path}")
                file_size = Path(png_path).stat().st_size
                print(f"   File size: {file_size} bytes")
            else:
                print(f"⚠️  PNG file not found at: {png_path}")
            
            result = True
        else:
            print(f"❌ PNG conversion failed: {convert_result['error']}")
            print(f"   Error code: {convert_result['error_code']}")
            
            if convert_result.get('fallback_message'):
                print(f"\n📋 Fallback Instructions:")
                print(convert_result['fallback_message'])
            
            if convert_result.get('alternatives'):
                print(f"\n🔄 Alternative Options:")
                for key, value in convert_result['alternatives'].items():
                    print(f"   • {key}: {value}")
            
            result = False
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
            print(f"🧹 Cleaned up temporary file: {temp_file_path}")
        except:
            pass
        
        return result
    
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_convert_to_png_error_cases():
    """Test convert-to-png tool error handling."""
    print("\n=== Testing convert-to-png error cases ===")
    
    test_cases = [
        {
            "name": "No parameters",
            "params": {},
            "expected_error": "MISSING_PARAMETER"
        },
        {
            "name": "Both parameters",
            "params": {"file_id": "test", "file_path": "/test/path"},
            "expected_error": "CONFLICTING_PARAMETERS"
        },
        {
            "name": "Invalid file_id",
            "params": {"file_id": "nonexistent-id"},
            "expected_error": "FILE_NOT_FOUND"
        },
        {
            "name": "Invalid file_path",
            "params": {"file_path": "/nonexistent/path.drawio"},
            "expected_error": "FILE_NOT_FOUND"
        },
        {
            "name": "Wrong file extension",
            "params": {"file_path": "test_convert_to_png.py"},  # This file exists but has wrong extension
            "expected_error": "INVALID_FILE_TYPE"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        
        try:
            result = await convert_to_png(**test_case['params'])
            
            if result["success"]:
                print(f"❌ Expected failure but got success")
                all_passed = False
            elif result["error_code"] == test_case['expected_error']:
                print(f"✅ Got expected error: {result['error_code']}")
                print(f"   Error message: {result['error']}")
            else:
                print(f"❌ Expected error '{test_case['expected_error']}' but got '{result['error_code']}'")
                print(f"   Error message: {result['error']}")
                all_passed = False
        
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            all_passed = False
    
    return all_passed


async def test_image_service_status():
    """Test ImageService status and CLI availability."""
    print("\n=== Testing ImageService Status ===")
    
    try:
        image_service = ImageService()
        
        print("1. Checking CLI availability...")
        cli_check = await image_service.is_drawio_cli_available()
        
        print(f"CLI Available: {cli_check.available}")
        if cli_check.version:
            print(f"CLI Version: {cli_check.version}")
        if cli_check.error:
            print(f"CLI Error: {cli_check.error}")
        if cli_check.installation_hint:
            print(f"Installation Hint: {cli_check.installation_hint}")
        
        print("\n2. Getting service status...")
        status = await image_service.get_service_status()
        
        print(f"Service Status: {status['status']}")
        print(f"Features: {status.get('features', {})}")
        
        if not cli_check.available:
            print("\n3. Getting fallback message...")
            fallback = await image_service.get_fallback_message()
            print("Fallback Message:")
            print(fallback)
        
        return True
    
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing convert-to-png MCP Tool Implementation")
    print("=" * 60)
    
    # Set up environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set. Some tests may fail.")
        print("   Set it with: export ANTHROPIC_API_KEY=your-key-here")
    
    tests = [
        ("ImageService Status", test_image_service_status),
        ("Convert with file_id", test_convert_to_png_with_file_id),
        ("Convert with file_path", test_convert_to_png_with_file_path),
        ("Error cases", test_convert_to_png_error_cases),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
            print(f"\n{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"\n❌ {test_name}: FAILED with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 Test Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:12} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)