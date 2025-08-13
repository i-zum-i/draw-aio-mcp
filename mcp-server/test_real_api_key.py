#!/usr/bin/env python3
"""
Test real API key validation (optional - only runs if real key is provided).
"""
import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api_key_validator import APIKeyValidator, APIKeyType


async def test_real_api_key():
    """Test with a real API key if provided."""
    print("=== Testing Real API Key Validation ===")
    
    # Check if a real API key is provided
    real_api_key = os.getenv("REAL_ANTHROPIC_API_KEY")
    
    if not real_api_key:
        print("ℹ️ No real API key provided (REAL_ANTHROPIC_API_KEY not set)")
        print("   This test is optional and only runs with a real key")
        return True
    
    if not real_api_key.startswith("sk-ant-"):
        print("⚠️ REAL_ANTHROPIC_API_KEY doesn't look like a valid format")
        return True
    
    # Check if it looks like a test key
    validator = APIKeyValidator()
    key_type = validator.classify_api_key(real_api_key)
    
    if key_type == APIKeyType.TEST:
        print("⚠️ Provided key appears to be a test key, skipping real validation")
        return True
    
    print(f"🔍 Testing real API key validation...")
    print(f"   Key type: {key_type.value}")
    print(f"   Key prefix: {real_api_key[:15]}...")
    
    try:
        result = await validator.validate_api_key(real_api_key)
        
        if result.is_valid:
            print("✅ Real API key validation successful!")
            print(f"   Key type: {result.key_type.value}")
            if result.account_info:
                print(f"   Account info: {result.account_info}")
        else:
            print("❌ Real API key validation failed")
            print(f"   Error: {result.error_message}")
            print(f"   Error code: {result.error_code}")
            
            # This might be expected (rate limits, quota issues, etc.)
            if result.error_code in ["RATE_LIMITED", "QUOTA_EXCEEDED"]:
                print("   (This may be expected due to rate limits or quota)")
                return True
        
        return result.is_valid
        
    except Exception as e:
        print(f"❌ Exception during real API key validation: {e}")
        return False


async def main():
    """Run real API key test."""
    print("🔑 Real API Key Validation Test")
    print("=" * 40)
    
    try:
        success = await test_real_api_key()
        
        print("=" * 40)
        
        if success:
            print("✅ Real API key test completed successfully!")
            print("\n💡 To test with your real API key:")
            print("   export REAL_ANTHROPIC_API_KEY=sk-ant-your-real-key")
            print("   python test_real_api_key.py")
        else:
            print("❌ Real API key test failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)