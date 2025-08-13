"""
Anthropic API Key Validation Service

This module provides comprehensive API key validation functionality including:
- Real API key validation through actual API calls
- Test/fake key detection and appropriate handling
- Pre-connection testing and validation
"""
import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from enum import Enum

import anthropic
from anthropic import APIError, APIConnectionError, APITimeoutError, RateLimitError

from .exceptions import LLMError, LLMErrorCode


class APIKeyType(Enum):
    """Types of API keys."""
    PRODUCTION = "production"
    TEST = "test"
    FAKE = "fake"
    INVALID = "invalid"


@dataclass
class APIKeyValidationResult:
    """Result of API key validation."""
    is_valid: bool
    key_type: APIKeyType
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    account_info: Optional[Dict[str, Any]] = None
    rate_limit_info: Optional[Dict[str, Any]] = None


class APIKeyValidator:
    """Service for validating Anthropic API keys."""
    
    # Known test/fake key patterns
    TEST_KEY_PATTERNS = [
        r"sk-ant-test-.*",
        r"sk-ant-.*-test.*",
        r"sk-ant-.*-fake.*",
        r"sk-ant-.*-12345.*",
        r"sk-ant-.*-testing.*",
        r"test-key-.*",
        r"fake-key-.*",
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the API key validator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def classify_api_key(self, api_key: str) -> APIKeyType:
        """
        Classify the type of API key.
        
        Args:
            api_key: The API key to classify
            
        Returns:
            APIKeyType: The classification of the key
        """
        if not api_key:
            return APIKeyType.INVALID
        
        # Check basic format
        if not api_key.startswith("sk-ant-"):
            return APIKeyType.INVALID
        
        # Check for test/fake patterns
        api_key_lower = api_key.lower()
        for pattern in self.TEST_KEY_PATTERNS:
            if re.match(pattern, api_key_lower):
                return APIKeyType.TEST
        
        # If it has the correct format but isn't a known test pattern,
        # assume it's intended to be a production key
        return APIKeyType.PRODUCTION
    
    async def validate_api_key(
        self, 
        api_key: str, 
        skip_real_validation: bool = False
    ) -> APIKeyValidationResult:
        """
        Comprehensive API key validation.
        
        Args:
            api_key: The API key to validate
            skip_real_validation: If True, only perform format validation
            
        Returns:
            APIKeyValidationResult: Detailed validation result
        """
        self.logger.debug(f"🔑 API キー検証開始")
        
        # Step 1: Basic format validation
        key_type = self.classify_api_key(api_key)
        
        if key_type == APIKeyType.INVALID:
            return APIKeyValidationResult(
                is_valid=False,
                key_type=key_type,
                error_message="API key format is invalid. Must start with 'sk-ant-'",
                error_code="INVALID_FORMAT"
            )
        
        # Step 2: Handle test/fake keys
        if key_type == APIKeyType.TEST:
            self.logger.warning(f"⚠️ テスト用APIキーが検出されました")
            
            if skip_real_validation:
                return APIKeyValidationResult(
                    is_valid=True,
                    key_type=key_type,
                    error_message="Test API key detected - real validation skipped"
                )
            else:
                return APIKeyValidationResult(
                    is_valid=False,
                    key_type=key_type,
                    error_message="Test/fake API key detected. Please provide a valid production API key.",
                    error_code="TEST_KEY_NOT_ALLOWED"
                )
        
        # Step 3: Real API validation for production keys
        if not skip_real_validation and key_type == APIKeyType.PRODUCTION:
            return await self._validate_production_key(api_key)
        
        # If skipping real validation, assume production key is valid
        return APIKeyValidationResult(
            is_valid=True,
            key_type=key_type,
            error_message="Production API key format valid - real validation skipped"
        )
    
    async def _validate_production_key(self, api_key: str) -> APIKeyValidationResult:
        """
        Validate a production API key by making a real API call.
        
        Args:
            api_key: The production API key to validate
            
        Returns:
            APIKeyValidationResult: Validation result with API response details
        """
        self.logger.info(f"🔍 本番APIキーの実際の検証を実行中...")
        
        try:
            # Create client with the key
            client = anthropic.Anthropic(
                api_key=api_key,
                timeout=10.0  # Short timeout for validation
            )
            
            # Make a minimal API call to validate the key
            # Use a very simple prompt to minimize token usage
            response = client.messages.create(
                model="claude-3-haiku-20240307",  # Use cheapest model
                max_tokens=10,  # Minimal tokens
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": "Hi"  # Minimal prompt
                    }
                ],
            )
            
            # If we get here, the key is valid
            self.logger.info(f"✅ APIキー検証成功")
            
            # Extract any useful information from the response
            account_info = {
                "model_used": "claude-3-haiku-20240307",
                "response_received": True,
                "validation_timestamp": asyncio.get_event_loop().time()
            }
            
            return APIKeyValidationResult(
                is_valid=True,
                key_type=APIKeyType.PRODUCTION,
                account_info=account_info
            )
            
        except Exception as error:
            self.logger.error(f"❌ APIキー検証エラー: {str(error)}")
            return self._handle_validation_error(error)
    
    def _handle_validation_error(self, error: Exception) -> APIKeyValidationResult:
        """
        Handle API validation errors and classify them.
        
        Args:
            error: The exception that occurred during validation
            
        Returns:
            APIKeyValidationResult: Classified error result
        """
        error_message = str(error).lower()
        
        # Authentication/API key errors
        if (isinstance(error, APIError) and error.status_code == 401) or \
           any(term in error_message for term in ["unauthorized", "authentication", "api key", "401"]):
            return APIKeyValidationResult(
                is_valid=False,
                key_type=APIKeyType.PRODUCTION,
                error_message="API key is invalid or unauthorized. Please check your Anthropic API key.",
                error_code="UNAUTHORIZED"
            )
        
        # Rate limit errors (key might be valid but limited)
        if isinstance(error, RateLimitError) or "rate limit" in error_message or "429" in error_message:
            return APIKeyValidationResult(
                is_valid=True,  # Key is probably valid, just rate limited
                key_type=APIKeyType.PRODUCTION,
                error_message="API key validation hit rate limit. Key appears valid but is currently rate limited.",
                error_code="RATE_LIMITED"
            )
        
        # Quota/billing errors (key is valid but account has issues)
        if "quota" in error_message or "billing" in error_message or "credits" in error_message:
            return APIKeyValidationResult(
                is_valid=True,  # Key is valid but account has billing issues
                key_type=APIKeyType.PRODUCTION,
                error_message="API key is valid but account has quota or billing issues. Please check your Anthropic account.",
                error_code="QUOTA_EXCEEDED"
            )
        
        # Connection/network errors (can't determine key validity)
        if (isinstance(error, APIConnectionError) or 
            any(term in error_message for term in ["network", "connection", "econnreset", "enotfound", "fetch"])):
            return APIKeyValidationResult(
                is_valid=False,  # Can't validate due to connection issues
                key_type=APIKeyType.PRODUCTION,
                error_message="Cannot validate API key due to network connection issues. Please check your internet connection and try again.",
                error_code="CONNECTION_ERROR"
            )
        
        # Timeout errors
        if isinstance(error, APITimeoutError) or "timeout" in error_message:
            return APIKeyValidationResult(
                is_valid=False,  # Can't validate due to timeout
                key_type=APIKeyType.PRODUCTION,
                error_message="API key validation timed out. Please try again.",
                error_code="TIMEOUT"
            )
        
        # Unknown errors
        return APIKeyValidationResult(
            is_valid=False,
            key_type=APIKeyType.PRODUCTION,
            error_message=f"API key validation failed with unknown error: {str(error)}",
            error_code="UNKNOWN_ERROR"
        )
    
    def should_allow_test_keys(self, development_mode: bool = False) -> bool:
        """
        Determine if test keys should be allowed based on environment.
        
        Args:
            development_mode: Whether the server is in development mode
            
        Returns:
            bool: True if test keys should be allowed
        """
        import os
        
        # Allow test keys in development mode
        if development_mode:
            return True
        
        # Allow test keys if explicitly enabled via environment variable
        if os.getenv("ALLOW_TEST_API_KEYS", "false").lower() in ("true", "1", "yes", "on"):
            return True
        
        # Allow test keys in testing environments
        if os.getenv("TESTING", "false").lower() in ("true", "1", "yes", "on"):
            return True
        
        # Check for pytest or other test runners
        if "pytest" in str(os.getenv("_", "")).lower():
            return True
        
        return False
    
    async def validate_with_policy(
        self, 
        api_key: str, 
        development_mode: bool = False,
        force_validation: bool = False
    ) -> APIKeyValidationResult:
        """
        Validate API key with policy-based decisions.
        
        Args:
            api_key: The API key to validate
            development_mode: Whether server is in development mode
            force_validation: Force real validation even for test keys
            
        Returns:
            APIKeyValidationResult: Validation result following policy
        """
        # Classify the key first
        key_type = self.classify_api_key(api_key)
        
        # Handle test keys based on policy
        if key_type == APIKeyType.TEST:
            if self.should_allow_test_keys(development_mode) and not force_validation:
                self.logger.info(f"✅ テストキーが許可されました (開発モード: {development_mode})")
                return APIKeyValidationResult(
                    is_valid=True,
                    key_type=key_type,
                    error_message="Test API key allowed in development/testing environment"
                )
        
        # For production keys or when forced, do real validation
        return await self.validate_api_key(
            api_key, 
            skip_real_validation=False
        )