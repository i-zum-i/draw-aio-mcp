#!/usr/bin/env python3
"""
Test server integration with API key validation.
"""
import asyncio
import os
import sys
import tempfile
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_server_initialization_with_test_key():
    """Test server initialization with test key in development mode."""
    print("=== Testing Server Initialization with Test Key ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment for development mode with test key
        env_vars = {
            'ANTHROPIC_API_KEY': 'sk-ant-test-key-12345',
            'DEVELOPMENT_MODE': 'true',
            'TEMP_DIR': temp_dir,
            'LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, env_vars):
            try:
                from src.server import initialize_services
                
                # This should succeed in development mode
                await initialize_services()
                print("✅ Server initialized successfully with test key in development mode")
                
                # Clean up global state
                import src.server as server_module
                server_module.config = None
                server_module.logger = None
                server_module.api_key_validator = None
                server_module.llm_service = None
                server_module.file_service = None
                server_module.image_service = None
                server_module.health_checker = None
                
            except Exception as e:
                print(f"❌ Server initialization failed: {e}")
                return False
    
    return True


async def test_server_initialization_with_test_key_production():
    """Test server initialization with test key in production mode."""
    print("=== Testing Server Initialization with Test Key in Production ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment for production mode with test key
        env_vars = {
            'ANTHROPIC_API_KEY': 'sk-ant-test-key-12345',
            'DEVELOPMENT_MODE': 'false',
            'TEMP_DIR': temp_dir,
            'LOG_LEVEL': 'ERROR'  # Reduce noise
        }
        
        with patch.dict(os.environ, env_vars):
            try:
                from src.server import initialize_services
                
                # This should fail in production mode
                await initialize_services()
                print("❌ Server should have failed with test key in production mode")
                return False
                
            except Exception as e:
                if "APIキー検証に失敗" in str(e) or "Test/fake API key detected" in str(e):
                    print("✅ Server correctly rejected test key in production mode")
                    return True
                else:
                    print(f"❌ Unexpected error: {e}")
                    return False
    
    return False


async def test_server_initialization_with_invalid_key():
    """Test server initialization with invalid key format."""
    print("=== Testing Server Initialization with Invalid Key ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment with invalid key
        env_vars = {
            'ANTHROPIC_API_KEY': 'invalid-key-format',
            'TEMP_DIR': temp_dir,
            'LOG_LEVEL': 'ERROR'  # Reduce noise
        }
        
        with patch.dict(os.environ, env_vars):
            try:
                from src.config import MCPServerConfig
                
                # This should fail at config level
                config = MCPServerConfig.from_env()
                print("❌ Config should have failed with invalid key format")
                return False
                
            except Exception as e:
                if "must start with 'sk-ant-'" in str(e):
                    print("✅ Config correctly rejected invalid key format")
                    return True
                else:
                    print(f"❌ Unexpected error: {e}")
                    return False
    
    return False


async def main():
    """Run server integration tests."""
    print("🔧 Server API Key Integration Test Suite")
    print("=" * 50)
    
    try:
        success1 = await test_server_initialization_with_test_key()
        success2 = await test_server_initialization_with_test_key_production()
        success3 = await test_server_initialization_with_invalid_key()
        
        print("=" * 50)
        
        if success1 and success2 and success3:
            print("✅ All server integration tests passed!")
            print("\n📋 Summary:")
            print("• Test key allowed in development mode")
            print("• Test key rejected in production mode")
            print("• Invalid key format rejected at config level")
            return True
        else:
            print("❌ Some server integration tests failed")
            return False
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)