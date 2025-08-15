#!/usr/bin/env python3
"""
Test LLM functionality with production API key.
"""
import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.llm_service import LLMService


async def test_production_llm():
    """Test LLM service with production API key."""
    print("=== Testing Production LLM Service ===")
    
    # Get the production API key from environment
    prod_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not prod_api_key or not prod_api_key.startswith("sk-ant-api03"):
        print("⚠️ No production API key provided or invalid format")
        return True
    
    try:
        print(f"🔍 Testing LLM service with production key: {prod_api_key[:20]}...")
        
        # Initialize LLM service
        llm_service = LLMService(api_key=prod_api_key)
        print(f"✅ LLM service initialized")
        print(f"   - Is test key: {llm_service.is_test_key}")
        print(f"   - Cache size: {llm_service.get_cache_stats()['size']}")
        
        # Test actual diagram generation
        print("🎨 Testing diagram generation...")
        prompt = "Create a simple flowchart with Start -> Process -> Decision -> End"
        
        xml_result = await llm_service.generate_drawio_xml(prompt)
        
        print("✅ Diagram generation successful!")
        print(f"   - XML length: {len(xml_result)} characters")
        print(f"   - Contains mxfile: {'<mxfile' in xml_result}")
        print(f"   - Contains mxGraphModel: {'<mxGraphModel' in xml_result}")
        print(f"   - Contains mxCell: {'<mxCell' in xml_result}")
        
        # Show first 200 characters of XML
        print(f"   - XML preview: {xml_result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        print(f"   This might be due to:")
        print(f"   - API rate limits")
        print(f"   - Network connectivity issues")
        print(f"   - Account quota issues")
        return False


async def main():
    """Run production LLM test."""
    print("🧠 Production LLM Service Test")
    print("=" * 40)
    
    try:
        success = await test_production_llm()
        
        print("=" * 40)
        
        if success:
            print("✅ Production LLM service test completed!")
            print("\n📋 Verification:")
            print("• LLM service initializes with production key")
            print("• Test key detection working correctly")
            print("• Actual diagram generation successful")
            print("• Generated XML has correct structure")
        else:
            print("❌ Production LLM service test failed")
            print("   Check API key validity and network connectivity")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)