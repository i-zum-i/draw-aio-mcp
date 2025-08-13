"""
Unit tests for LLMService class.
Tests XML generation, error handling, and cache functionality.
"""
import asyncio
import hashlib
import os
import time
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta

import pytest
from anthropic import APIError, APIConnectionError, APITimeoutError, RateLimitError

from src.llm_service import LLMService, CacheEntry
from src.exceptions import LLMError, LLMErrorCode


class TestLLMServiceInitialization:
    """Test LLMService initialization and configuration."""
    
    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        api_key = "sk-ant-test-key"
        service = LLMService(api_key=api_key)
        
        assert service.api_key == api_key
        assert service.client is not None
        assert service.cache == {}
        assert service.CACHE_TTL == 3600  # 1 hour
        assert service.MAX_CACHE_SIZE == 100
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-env-key"})
    def test_init_with_env_var(self):
        """Test initialization using environment variable."""
        service = LLMService()
        
        assert service.api_key == "sk-ant-env-key"
        assert service.client is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_missing_api_key(self):
        """Test initialization fails when API key is missing."""
        with pytest.raises(LLMError) as exc_info:
            LLMService()
        
        assert exc_info.value.code == LLMErrorCode.API_KEY_MISSING
        assert "ANTHROPIC_API_KEY environment variable is required" in str(exc_info.value)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_empty_api_key(self):
        """Test initialization fails when API key is empty."""
        with pytest.raises(LLMError) as exc_info:
            LLMService(api_key=None)
        
        assert exc_info.value.code == LLMErrorCode.API_KEY_MISSING


class TestLLMServiceXMLGeneration:
    """Test XML generation functionality."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing."""
        return LLMService(api_key="sk-ant-test-key")
    
    @pytest.fixture
    def mock_anthropic_response(self):
        """Mock Anthropic API response."""
        mock_response = Mock()
        mock_content = Mock()
        mock_content.type = "text"
        mock_content.text = '''```xml
<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="AI" version="22.1.0">
  <diagram name="Page-1" id="page-id">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="Test Box" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```'''
        mock_response.content = [mock_content]
        return mock_response
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_success(self, llm_service, mock_anthropic_response):
        """Test successful XML generation."""
        prompt = "Create a simple flowchart with one box"
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_anthropic_response
            
            result = await llm_service.generate_drawio_xml(prompt)
            
            # Verify API call
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[1]['model'] == "claude-3-5-sonnet-20241022"
            assert call_args[1]['max_tokens'] == 8192
            assert call_args[1]['temperature'] == 0.2
            assert prompt in call_args[1]['messages'][0]['content']
            
            # Verify result
            assert '<mxfile' in result
            assert '</mxfile>' in result
            assert '<mxGraphModel' in result
            assert '<root>' in result
            assert 'Test Box' in result
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_with_cache(self, llm_service, mock_anthropic_response):
        """Test XML generation uses cache for repeated requests."""
        prompt = "Create a simple flowchart"
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_anthropic_response
            
            # First call
            result1 = await llm_service.generate_drawio_xml(prompt)
            
            # Second call with same prompt
            result2 = await llm_service.generate_drawio_xml(prompt)
            
            # API should only be called once
            mock_create.assert_called_once()
            
            # Results should be identical
            assert result1 == result2
            
            # Cache should contain the result
            cache_key = llm_service._generate_cache_key(prompt)
            assert cache_key in llm_service.cache
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_direct_xml_response(self, llm_service):
        """Test XML generation when response contains direct XML without code blocks."""
        prompt = "Create a diagram"
        
        mock_response = Mock()
        mock_content = Mock()
        mock_content.type = "text"
        mock_content.text = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        mock_response.content = [mock_content]
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await llm_service.generate_drawio_xml(prompt)
            
            assert '<mxfile' in result
            assert '</mxfile>' in result
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_invalid_response_format(self, llm_service):
        """Test error handling for invalid response format."""
        prompt = "Create a diagram"
        
        mock_response = Mock()
        mock_content = Mock()
        mock_content.type = "image"  # Invalid type
        mock_response.content = [mock_content]
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            with pytest.raises(LLMError) as exc_info:
                await llm_service.generate_drawio_xml(prompt)
            
            assert exc_info.value.code == LLMErrorCode.INVALID_RESPONSE
            assert "unexpected response format" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_no_xml_in_response(self, llm_service):
        """Test error handling when response contains no XML."""
        prompt = "Create a diagram"
        
        mock_response = Mock()
        mock_content = Mock()
        mock_content.type = "text"
        mock_content.text = "I cannot create a diagram for this request."
        mock_response.content = [mock_content]
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            with pytest.raises(LLMError) as exc_info:
                await llm_service.generate_drawio_xml(prompt)
            
            assert exc_info.value.code == LLMErrorCode.INVALID_RESPONSE
            assert "could not generate a valid diagram" in str(exc_info.value).lower()


class TestLLMServiceErrorHandling:
    """Test error handling for various API errors."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing."""
        return LLMService(api_key="sk-ant-test-key")
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, llm_service):
        """Test handling of rate limit errors."""
        prompt = "Create a diagram"
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            # Create a proper RateLimitError with required arguments
            mock_response = Mock()
            mock_response.status_code = 429
            mock_create.side_effect = RateLimitError("Rate limit exceeded", response=mock_response, body={})
            
            with pytest.raises(LLMError) as exc_info:
                await llm_service.generate_drawio_xml(prompt)
            
            assert exc_info.value.code == LLMErrorCode.RATE_LIMIT_ERROR
            assert "rate limit reached" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_connection_error(self, llm_service):
        """Test handling of connection errors."""
        prompt = "Create a diagram"
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_request = Mock()
            mock_create.side_effect = APIConnectionError(message="Connection failed", request=mock_request)
            
            with pytest.raises(LLMError) as exc_info:
                await llm_service.generate_drawio_xml(prompt)
            
            assert exc_info.value.code == LLMErrorCode.CONNECTION_ERROR
            assert "cannot connect" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_timeout_error(self, llm_service):
        """Test handling of timeout errors."""
        prompt = "Create a diagram"
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = APITimeoutError("Request timed out")
            
            with pytest.raises(LLMError) as exc_info:
                await llm_service.generate_drawio_xml(prompt)
            
            assert exc_info.value.code == LLMErrorCode.TIMEOUT_ERROR
            assert "timed out" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_error(self, llm_service):
        """Test handling of quota exceeded errors."""
        prompt = "Create a diagram"
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_request = Mock()
            mock_create.side_effect = APIError("Quota exceeded", request=mock_request, body={})
            
            with pytest.raises(LLMError) as exc_info:
                await llm_service.generate_drawio_xml(prompt)
            
            assert exc_info.value.code == LLMErrorCode.QUOTA_EXCEEDED
            assert "usage limit reached" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, llm_service):
        """Test handling of authentication errors."""
        prompt = "Create a diagram"
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_request = Mock()
            mock_create.side_effect = APIError("Unauthorized: Invalid API key", request=mock_request, body={})
            
            with pytest.raises(LLMError) as exc_info:
                await llm_service.generate_drawio_xml(prompt)
            
            assert exc_info.value.code == LLMErrorCode.API_KEY_MISSING
            assert "authentication failed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_unknown_error(self, llm_service):
        """Test handling of unknown errors."""
        prompt = "Create a diagram"
        
        with patch.object(llm_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Unexpected error")
            
            with pytest.raises(LLMError) as exc_info:
                await llm_service.generate_drawio_xml(prompt)
            
            assert exc_info.value.code == LLMErrorCode.UNKNOWN_ERROR
            assert "error occurred with the ai service" in str(exc_info.value).lower()


class TestLLMServiceXMLValidation:
    """Test XML validation functionality."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing."""
        return LLMService(api_key="sk-ant-test-key")
    
    def test_validate_valid_xml(self, llm_service):
        """Test validation of valid Draw.io XML."""
        valid_xml = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        
        # Should not raise any exception
        llm_service._validate_drawio_xml(valid_xml)
    
    def test_validate_missing_mxfile_tag(self, llm_service):
        """Test validation fails for missing mxfile tag."""
        invalid_xml = '''<diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
      </root>
    </mxGraphModel>
</diagram>'''
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._validate_drawio_xml(invalid_xml)
        
        assert exc_info.value.code == LLMErrorCode.INVALID_XML
        assert "mxfile tag not found" in str(exc_info.value).lower()
    
    def test_validate_missing_closing_mxfile_tag(self, llm_service):
        """Test validation fails for missing closing mxfile tag."""
        invalid_xml = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
      </root>
    </mxGraphModel>
  </diagram>'''
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._validate_drawio_xml(invalid_xml)
        
        assert exc_info.value.code == LLMErrorCode.INVALID_XML
        assert "mxfile closing tag not found" in str(exc_info.value).lower()
    
    def test_validate_missing_mxgraphmodel_tag(self, llm_service):
        """Test validation fails for missing mxGraphModel tag."""
        invalid_xml = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <root>
      <mxCell id="0"/>
    </root>
  </diagram>
</mxfile>'''
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._validate_drawio_xml(invalid_xml)
        
        assert exc_info.value.code == LLMErrorCode.INVALID_XML
        assert "mxgraphmodel tag not found" in str(exc_info.value).lower()
    
    def test_validate_missing_root_tag(self, llm_service):
        """Test validation fails for missing root tag."""
        invalid_xml = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <mxCell id="0"/>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._validate_drawio_xml(invalid_xml)
        
        assert exc_info.value.code == LLMErrorCode.INVALID_XML
        assert "root tag not found" in str(exc_info.value).lower()


class TestLLMServiceCaching:
    """Test caching functionality."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing."""
        return LLMService(api_key="sk-ant-test-key")
    
    def test_generate_cache_key(self, llm_service):
        """Test cache key generation."""
        prompt = "Create a simple diagram"
        cache_key = llm_service._generate_cache_key(prompt)
        
        # Should be a string starting with "llm_"
        assert isinstance(cache_key, str)
        assert cache_key.startswith("llm_")
        
        # Should be consistent for same prompt
        cache_key2 = llm_service._generate_cache_key(prompt)
        assert cache_key == cache_key2
        
        # Should be different for different prompts
        cache_key3 = llm_service._generate_cache_key("Different prompt")
        assert cache_key != cache_key3
    
    def test_save_to_cache(self, llm_service):
        """Test saving results to cache."""
        key = "test_key"
        xml = "<mxfile>test</mxfile>"
        
        llm_service._save_to_cache(key, xml)
        
        assert key in llm_service.cache
        entry = llm_service.cache[key]
        assert entry.xml == xml
        assert entry.timestamp <= time.time()
        assert entry.expires_at > time.time()
    
    def test_get_from_cache_valid(self, llm_service):
        """Test retrieving valid cache entries."""
        key = "test_key"
        xml = "<mxfile>test</mxfile>"
        
        # Save to cache
        llm_service._save_to_cache(key, xml)
        
        # Retrieve from cache
        result = llm_service._get_from_cache(key)
        assert result == xml
    
    def test_get_from_cache_expired(self, llm_service):
        """Test retrieving expired cache entries."""
        key = "test_key"
        xml = "<mxfile>test</mxfile>"
        
        # Create expired cache entry
        now = time.time()
        llm_service.cache[key] = CacheEntry(
            xml=xml,
            timestamp=now - 7200,  # 2 hours ago
            expires_at=now - 3600  # Expired 1 hour ago
        )
        
        # Should return None and remove from cache
        result = llm_service._get_from_cache(key)
        assert result is None
        assert key not in llm_service.cache
    
    def test_get_from_cache_missing(self, llm_service):
        """Test retrieving non-existent cache entries."""
        result = llm_service._get_from_cache("non_existent_key")
        assert result is None
    
    def test_cache_size_limit(self, llm_service):
        """Test cache size limit enforcement."""
        # Set small cache size for testing
        llm_service.MAX_CACHE_SIZE = 3
        
        # Add entries up to limit
        for i in range(3):
            llm_service._save_to_cache(f"key_{i}", f"<mxfile>test_{i}</mxfile>")
        
        assert len(llm_service.cache) == 3
        
        # Add one more entry - should remove oldest
        llm_service._save_to_cache("key_3", "<mxfile>test_3</mxfile>")
        
        assert len(llm_service.cache) == 3
        assert "key_3" in llm_service.cache
        # key_0 should be removed as it was the oldest
        assert "key_0" not in llm_service.cache
    
    def test_clean_cache(self, llm_service):
        """Test manual cache cleanup."""
        now = time.time()
        
        # Add valid entry
        llm_service.cache["valid"] = CacheEntry(
            xml="<mxfile>valid</mxfile>",
            timestamp=now,
            expires_at=now + 3600
        )
        
        # Add expired entry
        llm_service.cache["expired"] = CacheEntry(
            xml="<mxfile>expired</mxfile>",
            timestamp=now - 7200,
            expires_at=now - 3600
        )
        
        # Clean cache
        llm_service._clean_cache()
        
        # Valid entry should remain, expired should be removed
        assert "valid" in llm_service.cache
        assert "expired" not in llm_service.cache
    
    def test_get_cache_stats(self, llm_service):
        """Test cache statistics."""
        # Add some entries
        llm_service._save_to_cache("key1", "<mxfile>test1</mxfile>")
        llm_service._save_to_cache("key2", "<mxfile>test2</mxfile>")
        
        stats = llm_service.get_cache_stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == llm_service.MAX_CACHE_SIZE


class TestLLMServicePromptBuilding:
    """Test prompt building functionality."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing."""
        return LLMService(api_key="sk-ant-test-key")
    
    def test_build_system_prompt(self, llm_service):
        """Test system prompt building."""
        system_prompt = llm_service._build_system_prompt()
        
        # Should contain key instructions
        assert "Draw.io XML format" in system_prompt
        assert "<mxfile>" in system_prompt
        assert "AWS Diagram Rules" in system_prompt
        assert "UTF-8 character encoding" in system_prompt
    
    def test_build_user_prompt(self, llm_service):
        """Test user prompt building."""
        user_description = "Create a simple flowchart with two boxes"
        user_prompt = llm_service._build_user_prompt(user_description)
        
        # Should contain the user description
        assert user_description in user_prompt
        assert "Generate Draw.io XML format" in user_prompt
        assert "Output XML only" in user_prompt


class TestLLMServiceXMLExtraction:
    """Test XML extraction from responses."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing."""
        return LLMService(api_key="sk-ant-test-key")
    
    def test_extract_xml_from_code_block(self, llm_service):
        """Test extracting XML from code blocks."""
        response = '''Here's your diagram:

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

This should work for your needs.'''
        
        xml = llm_service._extract_xml_from_response(response)
        
        assert xml.startswith('<mxfile')
        assert xml.endswith('</mxfile>')
        assert '<mxGraphModel>' in xml
    
    def test_extract_xml_direct(self, llm_service):
        """Test extracting direct XML without code blocks."""
        response = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        
        xml = llm_service._extract_xml_from_response(response)
        
        assert xml == response.strip()
    
    def test_extract_xml_no_xml_found(self, llm_service):
        """Test error when no XML is found in response."""
        response = "I cannot create a diagram for this request."
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._extract_xml_from_response(response)
        
        assert exc_info.value.code == LLMErrorCode.INVALID_RESPONSE