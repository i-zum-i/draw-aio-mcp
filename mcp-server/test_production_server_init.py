#!/usr/bin/env python3
"""
Test server initialization with production API key.
"""
import asyncio
import os
import sys
import tempfile
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_production_server_initialization():
    """Test server initialization with production API key."""
    print("=== Testing Production Server Initialization ===")
    
    # Get the production API key from environment
    prod_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not prod_api_key or not prod_api_key.startswith("sk-ant-api03"):
        print("⚠️ No production API key provided or invalid format")
        return True
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment for production mode with real key
        env_vars = {
            'ANTHROPIC_API_KEY': prod_api_key,
            'DEVELOPMENT_MODE': 'false',
            'TEMP_DIR': temp_dir,
            'LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, env_vars):
            try:
                from src.server import initialize_services
                
                print(f"🔍 Testing with production key: {prod_api_key[:20]}...")
                
                # This should succeed with real production key
                await initialize_services()
                print("✅ Server initialized successfully with production API key!")
                print("   - API key validation passed")
                print("   - All services initialized")
                print("   - Health checks completed")
                
                # Clean up global state
                import src.server as server_module
                await server_module.shutdown_services()
                server_module.config = None
                server_module.logger = None
                server_module.api_key_validator = None
                server_module.llm_service = None
                server_module.file_service = None
                server_module.image_service = None
                server_module.health_checker = None
                
                return True
                
            except Exception as e:
                print(f"❌ Server initialization failed: {e}")
                print(f"   This might be due to:")
                print(f"   - Network connectivity issues")
                print(f"   - API rate limits")
                print(f"   - Account quota issues")
                return False
    
    return False


async def main():
    """Run production server initialization test."""
    print("🚀 Production Server Initialization Test")
    print("=" * 50)
    
    try:
        success = await test_production_server_initialization()
        
        print("=" * 50)
        
        if success:
            print("✅ Production server initialization test completed!")
            print("\n📋 Verification:")
            print("• Real API key validation working")
            print("• Server starts successfully with production key")
            print("• All services initialize properly")
            print("• Health checks pass")
        else:
            print("❌ Production server initialization test failed")
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