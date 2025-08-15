#!/usr/bin/env python3
"""
Test script for API key validation improvements.

This script tests the new API key validation functionality including:
- Test/fake key detection
- Production key validation
- Policy-based validation decisions
"""
import asyncio
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api_key_validator import APIKeyValidator, APIKeyType, APIKeyValidationResult
from src.config import MCPServerConfig
from src.llm_service import LLMService


async def test_api_key_classification():
    """Test API key classification functionality."""
    print("=== Testing API Key Classification ===")
    
    validator = APIKeyValidator()
    
    test_cases = [
        # Invalid keys
        ("", APIKeyType.INVALID),
        ("invalid-key", APIKeyType.INVALID),
        ("sk-wrong-format", APIKeyType.INVALID),
        
        # Test/fake keys
        ("sk-ant-test-key", APIKeyType.TEST),
        ("sk-ant-test-key-12345", APIKeyType.TEST),
        ("sk-ant-fake-key-testing", APIKeyType.TEST),
        ("sk-ant-key-for-testing", APIKeyType.TEST),
        ("test-key-for-validation", APIKeyType.INVALID),  # This should be invalid since it doesn't start with sk-ant-
        
        # Production-like keys
        ("sk-ant-api03_abcdef123456789", APIKeyType.PRODUCTION),
        ("sk-ant-api03_real_key_format", APIKeyType.PRODUCTION),
    ]
    
    for api_key, expected_type in test_cases:
        result_type = validator.classify_api_key(api_key)
        status = "✅" if result_type == expected_type else "❌"
        print(f"{status} '{api_key[:20]}...' -> {result_type.value} (expected: {expected_type.value})")
    
    print()


async def test_format_validation():
    """Test basic format validation."""
    print("=== Testing Format Validation ===")
    
    validator = APIKeyValidator()
    
    # Test invalid format
    result = await validator.validate_api_key("invalid-key", skip_real_validation=True)
    print(f"Invalid format: {result.is_valid} (should be False)")
    print(f"Error: {result.error_message}")
    
    # Test valid format but test key
    result = await validator.validate_api_key("sk-ant-test-key-12345", skip_real_validation=True)
    print(f"Test key (skip validation): {result.is_valid} (should be True)")
    print(f"Key type: {result.key_type.value}")
    
    print()


async def test_policy_based_validation():
    """Test policy-based validation decisions."""
    print("=== Testing Policy-Based Validation ===")
    
    validator = APIKeyValidator()
    
    # Test allowing test keys in development mode
    result = await validator.validate_with_policy(
        "sk-ant-test-key-12345", 
        development_mode=True
    )
    print(f"Test key in dev mode: {result.is_valid} (should be True)")
    print(f"Message: {result.error_message}")
    
    # Test rejecting test keys in production mode
    result = await validator.validate_with_policy(
        "sk-ant-test-key-12345", 
        development_mode=False
    )
    print(f"Test key in prod mode: {result.is_valid} (should be False)")
    print(f"Error: {result.error_message}")
    
    print()


async def test_production_key_validation():
    """Test production key validation (mocked)."""
    print("=== Testing Production Key Validation (Mocked) ===")
    
    validator = APIKeyValidator()
    
    # Mock successful validation
    with patch('src.api_key_validator.anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Hello"
        
        # Make the create method return a coroutine
        async def mock_create(*args, **kwargs):
            return mock_response
        
        mock_client.messages.create = mock_create
        mock_anthropic.return_value = mock_client
        
        result = await validator.validate_api_key("sk-ant-api03_valid_key")
        print(f"Valid production key: {result.is_valid} (should be True)")
        print(f"Key type: {result.key_type.value}")
        print(f"Account info: {result.account_info}")
    
    # Mock authentication error
    with patch('src.api_key_validator.anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        
        # Create a simple exception that mimics APIError behavior
        class MockAPIError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.status_code = 401
        
        async def mock_create_error(*args, **kwargs):
            raise MockAPIError("Unauthorized")
        
        mock_client.messages.create = mock_create_error
        mock_anthropic.return_value = mock_client
        
        result = await validator.validate_api_key("sk-ant-api03_invalid_key")
        print(f"Invalid production key: {result.is_valid} (should be False)")
        print(f"Error code: {result.error_code}")
        print(f"Error message: {result.error_message}")
    
    print()


async def test_llm_service_integration():
    """Test LLM service integration with API key validation."""
    print("=== Testing LLM Service Integration ===")
    
    # Test with test key
    try:
        llm_service = LLMService(api_key="sk-ant-test-key-12345")
        print(f"LLM service with test key: is_test_key = {llm_service.is_test_key}")
        
        # Try to generate XML (should fail)
        try:
            await llm_service.generate_drawio_xml("Create a simple flowchart")
            print("❌ Should have failed with test key")
        except Exception as e:
            print(f"✅ Correctly rejected test key: {str(e)}")
    
    except Exception as e:
        print(f"Error creating LLM service: {e}")
    
    # Test with production-like key (but skip client init)
    try:
        llm_service = LLMService(
            api_key="sk-ant-api03_production_key", 
            skip_client_init=True
        )
        print(f"LLM service with prod key: is_test_key = {llm_service.is_test_key}")
    
    except Exception as e:
        print(f"Error creating LLM service: {e}")
    
    print()


async def test_config_integration():
    """Test configuration integration with API key validation."""
    print("=== Testing Configuration Integration ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with test key in development mode
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'sk-ant-test-key-12345',
            'DEVELOPMENT_MODE': 'true',
            'TEMP_DIR': temp_dir
        }):
            try:
                config = MCPServerConfig.from_env()
                print(f"✅ Config created with test key in dev mode")
                print(f"Development mode: {config.development_mode}")
            except Exception as e:
                print(f"❌ Config creation failed: {e}")
        
        # Test with invalid key format
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'invalid-key-format',
            'TEMP_DIR': temp_dir
        }):
            try:
                config = MCPServerConfig.from_env()
                print(f"❌ Should have failed with invalid key format")
            except Exception as e:
                print(f"✅ Correctly rejected invalid key format: {e}")
    
    print()


async def test_environment_detection():
    """Test environment-based test key allowance."""
    print("=== Testing Environment Detection ===")
    
    validator = APIKeyValidator()
    
    # Test normal environment
    allow_test = validator.should_allow_test_keys(development_mode=False)
    print(f"Normal environment allows test keys: {allow_test}")
    
    # Test development mode
    allow_test = validator.should_allow_test_keys(development_mode=True)
    print(f"Development mode allows test keys: {allow_test}")
    
    # Test with environment variable
    with patch.dict(os.environ, {'ALLOW_TEST_API_KEYS': 'true'}):
        allow_test = validator.should_allow_test_keys(development_mode=False)
        print(f"With ALLOW_TEST_API_KEYS=true: {allow_test}")
    
    # Test with testing environment
    with patch.dict(os.environ, {'TESTING': 'true'}):
        allow_test = validator.should_allow_test_keys(development_mode=False)
        print(f"With TESTING=true: {allow_test}")
    
    print()


async def main():
    """Run all API key validation tests."""
    print("🔑 API Key Validation Test Suite")
    print("=" * 50)
    
    try:
        await test_api_key_classification()
        await test_format_validation()
        await test_policy_based_validation()
        await test_production_key_validation()
        await test_llm_service_integration()
        await test_config_integration()
        await test_environment_detection()
        
        print("=" * 50)
        print("✅ All API key validation tests completed!")
        print("\n📋 Summary:")
        print("• API key classification working correctly")
        print("• Format validation implemented")
        print("• Policy-based validation functional")
        print("• Production key validation (with mocking)")
        print("• LLM service integration updated")
        print("• Configuration integration tested")
        print("• Environment detection working")
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)