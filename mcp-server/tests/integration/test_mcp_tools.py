"""
Integration tests for MCP tools.
Tests tool interactions, service integration, and end-to-end workflows.
"""
import asyncio
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest

from src.tools import (
    generate_drawio_xml,
    save_drawio_file,
    convert_to_png,
    sanitize_prompt,
    validate_drawio_xml
)
from src.llm_service import LLMService
from src.file_service import FileService
from src.image_service import ImageService, ImageGenerationResult, CLIAvailabilityResult
from src.exceptions import LLMError, LLMErrorCode
from tests.fixtures.sample_xml import MINIMAL_VALID_XML, VALID_DRAWIO_XML, INVALID_XML_NO_MXFILE
from tests.fixtures.sample_prompts import SIMPLE_FLOWCHART_PROMPT


class TestMCPToolInputValidation:
    """Test input validation for MCP tools."""
    
    def test_sanitize_prompt_valid(self):
        """Test prompt sanitization with valid input."""
        prompt = "Create a simple flowchart with three steps"
        result = sanitize_prompt(prompt)
        
        assert result == prompt
    
    def test_sanitize_prompt_whitespace(self):
        """Test prompt sanitization removes whitespace."""
        prompt = "  Create a diagram  \n\t  "
        result = sanitize_prompt(prompt)
        
        assert result == "Create a diagram"
    
    def test_sanitize_prompt_empty(self):
        """Test prompt sanitization with empty input."""
        with pytest.raises(ValueError) as exc_info:
            sanitize_prompt("")
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_sanitize_prompt_none(self):
        """Test prompt sanitization with None input."""
        with pytest.raises(ValueError) as exc_info:
            sanitize_prompt(None)
        
        assert "must be a non-empty string" in str(exc_info.value)
    
    def test_sanitize_prompt_too_long(self):
        """Test prompt sanitization with too long input."""
        long_prompt = "Create a diagram " * 1000  # > 10,000 chars
        
        with pytest.raises(ValueError) as exc_info:
            sanitize_prompt(long_prompt)
        
        assert "too long" in str(exc_info.value)
    
    def test_sanitize_prompt_too_short(self):
        """Test prompt sanitization with too short input."""
        with pytest.raises(ValueError) as exc_info:
            sanitize_prompt("Hi")
        
        assert "too short" in str(exc_info.value)
    
    def test_sanitize_prompt_control_characters(self):
        """Test prompt sanitization removes control characters."""
        prompt = "Create\x00a\x01diagram\x1f"
        result = sanitize_prompt(prompt)
        
        assert result == "Createadiagram"
    
    def test_validate_drawio_xml_valid(self):
        """Test XML validation with valid content."""
        # Should not raise any exception
        validate_drawio_xml(MINIMAL_VALID_XML)
    
    def test_validate_drawio_xml_empty(self):
        """Test XML validation with empty content."""
        with pytest.raises(ValueError) as exc_info:
            validate_drawio_xml("")
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_validate_drawio_xml_missing_elements(self):
        """Test XML validation with missing required elements."""
        with pytest.raises(ValueError) as exc_info:
            validate_drawio_xml(INVALID_XML_NO_MXFILE)
        
        assert "missing required element 'mxfile'" in str(exc_info.value)


class TestGenerateDrawioXMLTool:
    """Test generate-drawio-xml MCP tool."""
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_success(self):
        """Test successful XML generation."""
        prompt = SIMPLE_FLOWCHART_PROMPT
        
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(return_value=MINIMAL_VALID_XML)
            mock_llm_class.return_value = mock_llm
            
            result = await generate_drawio_xml(prompt)
            
            assert result["success"] is True
            assert result["xml_content"] == MINIMAL_VALID_XML
            assert result["error"] is None
            assert result["error_code"] is None
            assert "timestamp" in result
            
            # Verify LLM service was called correctly
            mock_llm.generate_drawio_xml.assert_called_once_with(prompt)
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_invalid_prompt(self):
        """Test XML generation with invalid prompt."""
        result = await generate_drawio_xml("")
        
        assert result["success"] is False
        assert "Invalid input" in result["error"]
        assert result["error_code"] == "INVALID_INPUT"
        assert result["xml_content"] is None
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_llm_error(self):
        """Test XML generation with LLM service error."""
        prompt = SIMPLE_FLOWCHART_PROMPT
        
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm_class.side_effect = LLMError("API key missing", LLMErrorCode.API_KEY_MISSING)
            
            result = await generate_drawio_xml(prompt)
            
            assert result["success"] is False
            assert "API key missing" in result["error"]
            assert result["error_code"] == "API_KEY_MISSING"
            assert result["xml_content"] is None
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_generation_error(self):
        """Test XML generation with generation error."""
        prompt = SIMPLE_FLOWCHART_PROMPT
        
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(
                side_effect=LLMError("Rate limit exceeded", LLMErrorCode.RATE_LIMIT_ERROR)
            )
            mock_llm_class.return_value = mock_llm
            
            result = await generate_drawio_xml(prompt)
            
            assert result["success"] is False
            assert "Rate limit exceeded" in result["error"]
            assert result["error_code"] == "RATE_LIMIT_ERROR"
            assert result["xml_content"] is None
    
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_unexpected_error(self):
        """Test XML generation with unexpected error."""
        prompt = SIMPLE_FLOWCHART_PROMPT
        
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm_class.side_effect = Exception("Unexpected error")
            
            result = await generate_drawio_xml(prompt)
            
            assert result["success"] is False
            assert "unexpected error occurred" in result["error"]
            assert result["error_code"] == "UNKNOWN_ERROR"
            assert result["xml_content"] is None


class TestSaveDrawioFileTool:
    """Test save-drawio-file MCP tool."""
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_success(self):
        """Test successful file saving."""
        xml_content = MINIMAL_VALID_XML
        filename = "test-diagram"
        
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(return_value="file_123")
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="test-diagram.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/test-diagram.drawio")
            mock_file_class.return_value = mock_file_service
            
            result = await save_drawio_file(xml_content, filename)
            
            assert result["success"] is True
            assert result["file_id"] == "file_123"
            assert result["file_path"] == "/temp/test-diagram.drawio"
            assert result["filename"] == "test-diagram.drawio"
            assert result["expires_at"] == "2024-01-02T00:00:00Z"
            assert result["error"] is None
            
            # Verify file service was called correctly
            mock_file_service.save_drawio_file.assert_called_once_with(xml_content, filename)
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_no_filename(self):
        """Test file saving without custom filename."""
        xml_content = MINIMAL_VALID_XML
        
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(return_value="file_456")
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="auto-generated.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/auto-generated.drawio")
            mock_file_class.return_value = mock_file_service
            
            result = await save_drawio_file(xml_content)
            
            assert result["success"] is True
            assert result["file_id"] == "file_456"
            
            # Verify file service was called with None filename
            mock_file_service.save_drawio_file.assert_called_once_with(xml_content, None)
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_invalid_xml(self):
        """Test file saving with invalid XML."""
        invalid_xml = "<invalid>not drawio xml</invalid>"
        
        result = await save_drawio_file(invalid_xml)
        
        assert result["success"] is False
        assert "Invalid XML content" in result["error"]
        assert result["error_code"] == "INVALID_XML"
        assert result["file_id"] is None
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_invalid_filename(self):
        """Test file saving with invalid filename."""
        xml_content = MINIMAL_VALID_XML
        long_filename = "a" * 101  # Too long
        
        result = await save_drawio_file(xml_content, long_filename)
        
        assert result["success"] is False
        assert "too long" in result["error"]
        assert result["error_code"] == "INVALID_FILENAME"
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_service_error(self):
        """Test file saving with file service error."""
        xml_content = MINIMAL_VALID_XML
        
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_class.side_effect = Exception("Service initialization failed")
            
            result = await save_drawio_file(xml_content)
            
            assert result["success"] is False
            assert "Failed to initialize file service" in result["error"]
            assert result["error_code"] == "SERVICE_ERROR"
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_save_error(self):
        """Test file saving with save operation error."""
        xml_content = MINIMAL_VALID_XML
        
        with patch('src.tools.FileService') as mock_file_class:
            from src.file_service import FileServiceError
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(
                side_effect=FileServiceError("Disk full")
            )
            mock_file_class.return_value = mock_file_service
            
            result = await save_drawio_file(xml_content)
            
            assert result["success"] is False
            assert "Disk full" in result["error"]
            assert result["error_code"] == "FILE_SERVICE_ERROR"


class TestConvertToPNGTool:
    """Test convert-to-png MCP tool."""
    
    @pytest.mark.asyncio
    async def test_convert_to_png_with_file_id_success(self):
        """Test successful PNG conversion using file_id."""
        file_id = "drawio_123"
        
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            # Mock FileService
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/test.drawio")
            mock_file_class.return_value = mock_file_service
            
            # Mock ImageService
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": True,
                "conversion_result": {
                    "image_file_id": "png_456",
                    "png_file_path": "/temp/test.png",
                    "base64_content": "base64data",
                    "cli_available": True
                },
                "save_result": {
                    "file_id": "saved_789",
                    "file_path": "/temp/saved.png",
                    "size_bytes": 1024,
                    "expires_at": "2024-01-02T00:00:00Z"
                },
                "message": "Conversion successful"
            })
            mock_image_class.return_value = mock_image_service
            
            result = await convert_to_png(file_id=file_id)
            
            assert result["success"] is True
            assert result["png_file_id"] == "saved_789"
            assert result["png_file_path"] == "/temp/saved.png"
            assert result["base64_content"] == "base64data"
            assert result["cli_available"] is True
            assert result["error"] is None
            
            # Verify services were called correctly
            mock_file_service.get_file_path.assert_called_once_with(file_id)
            mock_image_service.generate_png_with_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_convert_to_png_with_file_path_success(self):
        """Test successful PNG conversion using file_path."""
        file_path = "/path/to/test.drawio"
        
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.suffix', new_callable=lambda: Mock(return_value='.drawio')):
            
            mock_exists.return_value = True
            
            # Mock services
            mock_file_service = Mock()
            mock_file_class.return_value = mock_file_service
            
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": True,
                "conversion_result": {
                    "image_file_id": "png_456",
                    "png_file_path": "/path/to/test.png",
                    "cli_available": True
                },
                "message": "Conversion successful"
            })
            mock_image_class.return_value = mock_image_service
            
            result = await convert_to_png(file_path=file_path)
            
            assert result["success"] is True
            assert result["png_file_id"] == "png_456"
            assert result["cli_available"] is True
    
    @pytest.mark.asyncio
    async def test_convert_to_png_missing_parameters(self):
        """Test PNG conversion with missing parameters."""
        result = await convert_to_png()
        
        assert result["success"] is False
        assert "Must provide either file_id or file_path" in result["error"]
        assert result["error_code"] == "MISSING_PARAMETER"
    
    @pytest.mark.asyncio
    async def test_convert_to_png_conflicting_parameters(self):
        """Test PNG conversion with conflicting parameters."""
        result = await convert_to_png(file_id="123", file_path="/path/to/file.drawio")
        
        assert result["success"] is False
        assert "Cannot provide both" in result["error"]
        assert result["error_code"] == "CONFLICTING_PARAMETERS"
    
    @pytest.mark.asyncio
    async def test_convert_to_png_file_not_found(self):
        """Test PNG conversion with non-existent file."""
        with patch('src.tools.FileService') as mock_file_class:
            from src.file_service import FileServiceError
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(
                side_effect=FileServiceError("File not found")
            )
            mock_file_class.return_value = mock_file_service
            
            result = await convert_to_png(file_id="nonexistent")
            
            assert result["success"] is False
            assert "File not found" in result["error"]
            assert result["error_code"] == "FILE_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_convert_to_png_invalid_file_type(self):
        """Test PNG conversion with invalid file type."""
        file_path = "/path/to/test.txt"
        
        with patch('src.tools.FileService') as mock_file_class, \
             patch('pathlib.Path.exists') as mock_exists:
            
            mock_exists.return_value = True
            mock_file_class.return_value = Mock()
            
            # Mock Path.suffix to return .txt
            with patch('pathlib.Path.suffix', new_callable=lambda: Mock(return_value='.txt')):
                result = await convert_to_png(file_path=file_path)
            
            assert result["success"] is False
            assert "Invalid file type" in result["error"]
            assert result["error_code"] == "INVALID_FILE_TYPE"
    
    @pytest.mark.asyncio
    async def test_convert_to_png_cli_not_available(self):
        """Test PNG conversion when CLI is not available."""
        file_id = "drawio_123"
        
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            # Mock FileService
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/test.drawio")
            mock_file_class.return_value = mock_file_service
            
            # Mock ImageService with CLI not available
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": False,
                "error": "Draw.io CLI not available",
                "cli_available": False,
                "fallback_message": "Install CLI instructions",
                "alternatives": {"manual": "Use manual export"},
                "troubleshooting": {"issue": "CLI missing"}
            })
            mock_image_class.return_value = mock_image_service
            
            result = await convert_to_png(file_id=file_id)
            
            assert result["success"] is False
            assert "Draw.io CLI not available" in result["error"]
            assert result["cli_available"] is False
            assert result["fallback_message"] == "Install CLI instructions"
            assert result["alternatives"] == {"manual": "Use manual export"}
            assert result["troubleshooting"] == {"issue": "CLI missing"}
    
    @pytest.mark.asyncio
    async def test_convert_to_png_service_initialization_error(self):
        """Test PNG conversion with service initialization error."""
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_class.side_effect = Exception("Service init failed")
            
            result = await convert_to_png(file_id="test")
            
            assert result["success"] is False
            assert "Failed to initialize services" in result["error"]
            assert result["error_code"] == "SERVICE_INITIALIZATION_ERROR"


class TestMCPToolsIntegration:
    """Test integration between MCP tools."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_generate_save_convert(self):
        """Test complete workflow: generate XML -> save file -> convert to PNG."""
        prompt = SIMPLE_FLOWCHART_PROMPT
        
        # Step 1: Generate XML
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(return_value=MINIMAL_VALID_XML)
            mock_llm_class.return_value = mock_llm
            
            xml_result = await generate_drawio_xml(prompt)
            
            assert xml_result["success"] is True
            xml_content = xml_result["xml_content"]
        
        # Step 2: Save file
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(return_value="file_123")
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="diagram.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/diagram.drawio")
            mock_file_class.return_value = mock_file_service
            
            save_result = await save_drawio_file(xml_content, "diagram")
            
            assert save_result["success"] is True
            file_id = save_result["file_id"]
        
        # Step 3: Convert to PNG
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            # Mock FileService
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/diagram.drawio")
            mock_file_class.return_value = mock_file_service
            
            # Mock ImageService
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": True,
                "conversion_result": {
                    "image_file_id": "png_456",
                    "png_file_path": "/temp/diagram.png",
                    "cli_available": True
                },
                "message": "Conversion successful"
            })
            mock_image_class.return_value = mock_image_service
            
            png_result = await convert_to_png(file_id=file_id)
            
            assert png_result["success"] is True
            assert png_result["png_file_id"] == "png_456"
    
    @pytest.mark.asyncio
    async def test_workflow_with_errors_at_each_step(self):
        """Test workflow error handling at each step."""
        prompt = SIMPLE_FLOWCHART_PROMPT
        
        # Step 1: Generate XML fails
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm_class.side_effect = LLMError("API error", LLMErrorCode.CONNECTION_ERROR)
            
            xml_result = await generate_drawio_xml(prompt)
            
            assert xml_result["success"] is False
            assert xml_result["error_code"] == "CONNECTION_ERROR"
        
        # Step 2: Save file fails (assuming XML generation succeeded)
        xml_content = MINIMAL_VALID_XML
        
        with patch('src.tools.FileService') as mock_file_class:
            from src.file_service import FileServiceError
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(
                side_effect=FileServiceError("Disk full")
            )
            mock_file_class.return_value = mock_file_service
            
            save_result = await save_drawio_file(xml_content)
            
            assert save_result["success"] is False
            assert save_result["error_code"] == "FILE_SERVICE_ERROR"
        
        # Step 3: Convert to PNG fails (assuming save succeeded)
        file_id = "test_file_123"
        
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/test.drawio")
            mock_file_class.return_value = mock_file_service
            
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": False,
                "error": "CLI not available",
                "cli_available": False,
                "fallback_message": "Install CLI"
            })
            mock_image_class.return_value = mock_image_service
            
            png_result = await convert_to_png(file_id=file_id)
            
            assert png_result["success"] is False
            assert png_result["cli_available"] is False
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(self):
        """Test concurrent execution of multiple tool operations."""
        prompts = [
            "Create a simple flowchart",
            "Create an AWS diagram",
            "Create a database schema"
        ]
        
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(return_value=MINIMAL_VALID_XML)
            mock_llm_class.return_value = mock_llm
            
            # Execute multiple XML generations concurrently
            tasks = [generate_drawio_xml(prompt) for prompt in prompts]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            for result in results:
                assert result["success"] is True
                assert result["xml_content"] == MINIMAL_VALID_XML
            
            # Verify LLM service was called for each prompt
            assert mock_llm.generate_drawio_xml.call_count == len(prompts)


class TestMCPToolsErrorRecovery:
    """Test error recovery and resilience in MCP tools."""
    
    @pytest.mark.asyncio
    async def test_generate_xml_retry_on_transient_error(self):
        """Test XML generation handles transient errors gracefully."""
        prompt = SIMPLE_FLOWCHART_PROMPT
        
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            # First call fails, but tool should handle it gracefully
            mock_llm.generate_drawio_xml = AsyncMock(
                side_effect=LLMError("Temporary error", LLMErrorCode.TIMEOUT_ERROR)
            )
            mock_llm_class.return_value = mock_llm
            
            result = await generate_drawio_xml(prompt)
            
            assert result["success"] is False
            assert result["error_code"] == "TIMEOUT_ERROR"
            # Tool should provide helpful error message
            assert "Temporary error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_save_file_handles_filesystem_errors(self):
        """Test file saving handles filesystem errors gracefully."""
        xml_content = MINIMAL_VALID_XML
        
        with patch('src.tools.FileService') as mock_file_class:
            from src.file_service import FileServiceError
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(
                side_effect=FileServiceError("Permission denied")
            )
            mock_file_class.return_value = mock_file_service
            
            result = await save_drawio_file(xml_content)
            
            assert result["success"] is False
            assert result["error_code"] == "FILE_SERVICE_ERROR"
            assert "Permission denied" in result["error"]
    
    @pytest.mark.asyncio
    async def test_convert_png_provides_fallback_options(self):
        """Test PNG conversion provides comprehensive fallback when CLI unavailable."""
        file_id = "test_123"
        
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/test.drawio")
            mock_file_class.return_value = mock_file_service
            
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": False,
                "error": "Draw.io CLI not available",
                "cli_available": False,
                "fallback_message": "Detailed installation instructions",
                "alternatives": {
                    "manual_export": "Open in Draw.io Desktop",
                    "web_version": "Use web version",
                    "xml_content": "Use XML with other tools"
                },
                "troubleshooting": {
                    "primary_issue": "CLI not installed",
                    "check_installation": "Run drawio --version",
                    "reinstall": "npm install -g @drawio/drawio-desktop-cli"
                }
            })
            mock_image_class.return_value = mock_image_service
            
            result = await convert_to_png(file_id=file_id)
            
            assert result["success"] is False
            assert result["cli_available"] is False
            assert "fallback_message" in result
            assert "alternatives" in result
            assert "troubleshooting" in result
            
            # Verify comprehensive fallback information
            assert len(result["alternatives"]) >= 3
            assert "manual_export" in result["alternatives"]
            assert "web_version" in result["alternatives"]
            assert "primary_issue" in result["troubleshooting"]


class TestMCPToolsPerformance:
    """Test performance characteristics of MCP tools."""
    
    @pytest.mark.asyncio
    async def test_tool_response_times(self):
        """Test that tools respond within reasonable time limits."""
        import time
        
        # Test generate_drawio_xml response time
        start_time = time.time()
        
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(return_value=MINIMAL_VALID_XML)
            mock_llm_class.return_value = mock_llm
            
            result = await generate_drawio_xml(SIMPLE_FLOWCHART_PROMPT)
            
            response_time = time.time() - start_time
            
            assert result["success"] is True
            # Should respond quickly when mocked
            assert response_time < 1.0  # Less than 1 second
    
    @pytest.mark.asyncio
    async def test_large_xml_handling(self):
        """Test tools can handle large XML content."""
        # Create large but valid XML
        large_xml = VALID_DRAWIO_XML
        # Add many elements to make it large
        for i in range(100):
            large_xml = large_xml.replace(
                '</root>',
                f'<mxCell id="large_{i}" value="Element {i}" style="rounded=0;" vertex="1" parent="1">'
                f'<mxGeometry x="{i*10}" y="{i*10}" width="120" height="60" as="geometry"/></mxCell></root>'
            )
        
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(return_value="large_file_123")
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="large-diagram.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/large-diagram.drawio")
            mock_file_class.return_value = mock_file_service
            
            result = await save_drawio_file(large_xml)
            
            assert result["success"] is True
            assert result["file_id"] == "large_file_123"
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_multiple_operations(self):
        """Test memory usage remains reasonable with multiple operations."""
        # This is a basic test - in a real scenario you'd use memory profiling
        xml_content = MINIMAL_VALID_XML
        
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(return_value="file_123")
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="test.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/test.drawio")
            mock_file_class.return_value = mock_file_service
            
            # Perform many save operations
            results = []
            for i in range(50):
                result = await save_drawio_file(xml_content, f"test_{i}")
                results.append(result)
            
            # All should succeed
            for result in results:
                assert result["success"] is True
            
            # Verify service was called for each operation
            assert mock_file_service.save_drawio_file.call_count == 50


class TestMCPToolsAdvancedIntegration:
    """Test advanced integration scenarios between MCP tools."""
    
    @pytest.mark.asyncio
    async def test_tool_chain_with_error_recovery(self):
        """Test tool chain with error recovery at each step."""
        prompt = SIMPLE_FLOWCHART_PROMPT
        
        # Step 1: Generate XML (success)
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(return_value=MINIMAL_VALID_XML)
            mock_llm_class.return_value = mock_llm
            
            xml_result = await generate_drawio_xml(prompt)
            assert xml_result["success"] is True
            xml_content = xml_result["xml_content"]
        
        # Step 2: Save file (failure, then retry with success)
        with patch('src.tools.FileService') as mock_file_class:
            from src.file_service import FileServiceError
            mock_file_service = Mock()
            # First call fails, second succeeds (simulating retry)
            mock_file_service.save_drawio_file = AsyncMock(
                side_effect=[FileServiceError("Temporary error"), "file_123"]
            )
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="diagram.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/diagram.drawio")
            mock_file_class.return_value = mock_file_service
            
            # First attempt fails
            save_result = await save_drawio_file(xml_content)
            assert save_result["success"] is False
            
            # Second attempt succeeds (simulating retry logic)
            save_result = await save_drawio_file(xml_content)
            assert save_result["success"] is True
            file_id = save_result["file_id"]
        
        # Step 3: Convert to PNG (success with fallback information)
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/diagram.drawio")
            mock_file_class.return_value = mock_file_service
            
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": True,
                "conversion_result": {
                    "image_file_id": "png_456",
                    "png_file_path": "/temp/diagram.png",
                    "cli_available": True
                },
                "message": "Conversion successful"
            })
            mock_image_class.return_value = mock_image_service
            
            png_result = await convert_to_png(file_id=file_id)
            assert png_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_operations_with_resource_contention(self):
        """Test concurrent tool operations with resource contention."""
        prompts = [
            "Create a flowchart for user registration",
            "Create an AWS architecture diagram",
            "Create a database schema diagram"
        ]
        
        # Simulate resource contention scenarios
        with patch('src.tools.LLMService') as mock_llm_class:
            # Mock LLM service with varying response times
            mock_llm = Mock()
            
            async def slow_generate_1(*args, **kwargs):
                await asyncio.sleep(0.1)
                return MINIMAL_VALID_XML
            
            async def slow_generate_2(*args, **kwargs):
                await asyncio.sleep(0.3)
                return MINIMAL_VALID_XML
            
            async def slow_generate_3(*args, **kwargs):
                await asyncio.sleep(0.2)
                return MINIMAL_VALID_XML
            
            mock_llm.generate_drawio_xml = AsyncMock(
                side_effect=[slow_generate_1(), slow_generate_2(), slow_generate_3()]
            )
            mock_llm_class.return_value = mock_llm
            
            # Execute concurrent XML generations
            tasks = [generate_drawio_xml(prompt) for prompt in prompts]
            results = await asyncio.gather(*tasks)
            
            # All should succeed despite varying response times
            for i, result in enumerate(results):
                assert result["success"] is True
                assert result["xml_content"] == MINIMAL_VALID_XML
    
    @pytest.mark.asyncio
    async def test_tool_parameter_validation_comprehensive(self):
        """Test comprehensive parameter validation across all tools."""
        # Test generate_drawio_xml parameter validation
        invalid_prompts = [
            "",  # Empty
            "Hi",  # Too short
            "A" * 15000,  # Too long
        ]
        
        for invalid_prompt in invalid_prompts:
            result = await generate_drawio_xml(invalid_prompt)
            assert result["success"] is False
            assert result["error_code"] == "INVALID_INPUT"
        
        # Test save_drawio_file parameter validation
        invalid_xml_contents = [
            "",  # Empty
            "<invalid>not drawio</invalid>",  # Invalid XML
        ]
        
        for invalid_xml in invalid_xml_contents:
            result = await save_drawio_file(invalid_xml)
            assert result["success"] is False
            assert result["error_code"] == "INVALID_XML"
        
        # Test convert_to_png parameter validation
        invalid_parameters = [
            {},  # No parameters
            {"file_id": "test", "file_path": "/path"},  # Both parameters
            {"file_id": ""},  # Empty file_id
            {"file_path": ""},  # Empty file_path
        ]
        
        for invalid_params in invalid_parameters:
            result = await convert_to_png(**invalid_params)
            assert result["success"] is False
            assert result["error_code"] in [
                "MISSING_PARAMETER", 
                "CONFLICTING_PARAMETERS", 
                "INVALID_FILE_ID", 
                "INVALID_FILE_PATH"
            ]
    
    @pytest.mark.asyncio
    async def test_tool_error_propagation_and_context(self):
        """Test error propagation and context preservation across tools."""
        # Test error context preservation in generate_drawio_xml
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm_class.side_effect = LLMError(
                "Rate limit exceeded. Please try again in 60 seconds.",
                LLMErrorCode.RATE_LIMIT_ERROR
            )
            
            result = await generate_drawio_xml("Create a diagram")
            
            assert result["success"] is False
            assert result["error_code"] == "RATE_LIMIT_ERROR"
            assert "Rate limit exceeded" in result["error"]
            assert "60 seconds" in result["error"]  # Context preserved
        
        # Test error context in save_drawio_file
        with patch('src.tools.FileService') as mock_file_class:
            from src.file_service import FileServiceError
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(
                side_effect=FileServiceError("Insufficient disk space: 0 bytes available")
            )
            mock_file_class.return_value = mock_file_service
            
            result = await save_drawio_file(MINIMAL_VALID_XML)
            
            assert result["success"] is False
            assert result["error_code"] == "FILE_SERVICE_ERROR"
            assert "Insufficient disk space" in result["error"]
            assert "0 bytes available" in result["error"]  # Detailed context
        
        # Test error context in convert_to_png
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/test.drawio")
            mock_file_class.return_value = mock_file_service
            
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": False,
                "error": "Draw.io CLI version 1.2.3 is incompatible with this system",
                "cli_available": False,
                "troubleshooting": {
                    "primary_issue": "Version incompatibility",
                    "recommended_version": "1.1.x",
                    "current_version": "1.2.3"
                }
            })
            mock_image_class.return_value = mock_image_service
            
            result = await convert_to_png(file_id="test_123")
            
            assert result["success"] is False
            assert "version 1.2.3 is incompatible" in result["error"]
            assert result["troubleshooting"]["current_version"] == "1.2.3"


class TestMCPToolsPerformanceAndReliability:
    """Test performance characteristics and reliability of MCP tools."""
    
    @pytest.mark.asyncio
    async def test_tool_timeout_handling(self):
        """Test tool behavior under timeout conditions."""
        # Test generate_drawio_xml with slow LLM response
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            
            async def slow_generate(*args, **kwargs):
                await asyncio.sleep(2)  # Simulate slow response
                return MINIMAL_VALID_XML
            
            mock_llm.generate_drawio_xml = slow_generate
            mock_llm_class.return_value = mock_llm
            
            # Should complete even with slow response (no timeout in current implementation)
            start_time = time.time()
            result = await generate_drawio_xml("Create a diagram")
            end_time = time.time()
            
            assert result["success"] is True
            assert end_time - start_time >= 2  # Verify it actually waited
    
    @pytest.mark.asyncio
    async def test_tool_memory_usage_patterns(self):
        """Test memory usage patterns with large data."""
        # Test with large XML content
        large_xml = MINIMAL_VALID_XML.replace(
            "<mxCell",
            "<mxCell" + " " * 1000  # Add padding to make XML larger
        ) * 100  # Repeat to make it very large
        
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(return_value="file_123")
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="large_diagram.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/large_diagram.drawio")
            mock_file_class.return_value = mock_file_service
            
            result = await save_drawio_file(large_xml)
            
            # Should handle large content without issues
            assert result["success"] is True
            assert result["file_id"] == "file_123"
    
    @pytest.mark.asyncio
    async def test_tool_error_recovery_patterns(self):
        """Test error recovery patterns and graceful degradation."""
        # Test graceful degradation in convert_to_png
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/test.drawio")
            mock_file_class.return_value = mock_file_service
            
            # Simulate progressive failure scenarios
            failure_scenarios = [
                {
                    "success": False,
                    "error": "CLI not found",
                    "cli_available": False,
                    "fallback_message": "Install CLI instructions",
                    "alternatives": {"manual": "Manual export"}
                },
                {
                    "success": False,
                    "error": "CLI timeout",
                    "cli_available": True,
                    "troubleshooting": {"issue": "CLI hanging"}
                },
                {
                    "success": False,
                    "error": "Insufficient memory",
                    "cli_available": True,
                    "alternatives": {"reduce_size": "Simplify diagram"}
                }
            ]
            
            for scenario in failure_scenarios:
                mock_image_service = Mock()
                mock_image_service.generate_png_with_fallback = AsyncMock(return_value=scenario)
                mock_image_class.return_value = mock_image_service
                
                result = await convert_to_png(file_id="test_123")
                
                # Should always provide structured error response
                assert result["success"] is False
                assert "error" in result
                assert "cli_available" in result
                
                # Should provide helpful information based on error type
                if "fallback_message" in scenario:
                    assert result["fallback_message"] == scenario["fallback_message"]
                if "alternatives" in scenario:
                    assert result["alternatives"] == scenario["alternatives"]
                if "troubleshooting" in scenario:
                    assert result["troubleshooting"] == scenario["troubleshooting"]


class TestMCPToolsRealWorldScenarios:
    """Test MCP tools with realistic real-world scenarios."""
    
    @pytest.mark.asyncio
    async def test_typical_user_workflow_success(self):
        """Test typical successful user workflow."""
        # Scenario: User creates AWS architecture diagram
        prompt = "Create an AWS architecture diagram showing a web application with load balancer, EC2 instances, RDS database, and S3 storage"
        
        # Step 1: Generate XML
        with patch('src.tools.LLMService') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(return_value=VALID_DRAWIO_XML)
            mock_llm_class.return_value = mock_llm
            
            xml_result = await generate_drawio_xml(prompt)
            assert xml_result["success"] is True
            xml_content = xml_result["xml_content"]
        
        # Step 2: Save with custom filename
        with patch('src.tools.FileService') as mock_file_class:
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(return_value="aws_arch_123")
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="aws-architecture.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/aws-architecture.drawio")
            mock_file_class.return_value = mock_file_service
            
            save_result = await save_drawio_file(xml_content, "aws-architecture")
            assert save_result["success"] is True
            assert save_result["filename"] == "aws-architecture.drawio"
            file_id = save_result["file_id"]
        
        # Step 3: Convert to PNG for presentation
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/aws-architecture.drawio")
            mock_file_class.return_value = mock_file_service
            
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": True,
                "conversion_result": {
                    "image_file_id": "aws_png_456",
                    "png_file_path": "/temp/aws-architecture.png",
                    "base64_content": "base64_encoded_png_data",
                    "cli_available": True
                },
                "save_result": {
                    "file_id": "aws_png_saved_789",
                    "file_path": "/temp/managed_aws-architecture.png",
                    "size_bytes": 2048,
                    "expires_at": "2024-01-02T00:00:00Z"
                },
                "message": "PNG conversion completed successfully"
            })
            mock_image_class.return_value = mock_image_service
            
            png_result = await convert_to_png(file_id=file_id)
            assert png_result["success"] is True
            assert png_result["base64_content"] == "base64_encoded_png_data"
            assert png_result["metadata"]["file_size_bytes"] == 2048
    
    @pytest.mark.asyncio
    async def test_user_workflow_with_cli_unavailable(self):
        """Test user workflow when Draw.io CLI is not available."""
        prompt = "Create a simple flowchart for order processing"
        
        # Steps 1-2: Generate and save XML (successful)
        with patch('src.tools.LLMService') as mock_llm_class, \
             patch('src.tools.FileService') as mock_file_class:
            
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(return_value=MINIMAL_VALID_XML)
            mock_llm_class.return_value = mock_llm
            
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(return_value="flowchart_123")
            mock_file_service.get_file_info = AsyncMock(return_value=Mock(
                original_name="order-processing.drawio",
                expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))
            ))
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/order-processing.drawio")
            mock_file_class.return_value = mock_file_service
            
            xml_result = await generate_drawio_xml(prompt)
            save_result = await save_drawio_file(xml_result["xml_content"], "order-processing")
            
            assert xml_result["success"] is True
            assert save_result["success"] is True
            file_id = save_result["file_id"]
        
        # Step 3: PNG conversion fails but provides helpful fallback
        with patch('src.tools.FileService') as mock_file_class, \
             patch('src.tools.ImageService') as mock_image_class:
            
            mock_file_service = Mock()
            mock_file_service.get_file_path = AsyncMock(return_value="/temp/order-processing.drawio")
            mock_file_class.return_value = mock_file_service
            
            mock_image_service = Mock()
            mock_image_service.generate_png_with_fallback = AsyncMock(return_value={
                "success": False,
                "error": "Draw.io CLI is not available for PNG conversion",
                "cli_available": False,
                "fallback_message": """🚫 Draw.io CLI is not available for PNG conversion.

📋 To enable PNG conversion:
1. Install Node.js from https://nodejs.org/
2. Run: npm install -g @drawio/drawio-desktop-cli
3. Verify installation: drawio --version
4. Restart the MCP server

🔄 Alternative options:
• Save the .drawio file and open it manually in Draw.io Desktop
• Use Draw.io web version (https://app.diagrams.net/)
• Export PNG directly from Draw.io application
• Use the XML content with other diagram tools""",
                "alternatives": {
                    "manual_export": "Open the .drawio file in Draw.io Desktop and export as PNG manually",
                    "web_version": "Use Draw.io web version at https://app.diagrams.net/",
                    "xml_content": "Use the XML content with other compatible diagram tools",
                    "save_for_later": "Save the .drawio file and convert when CLI becomes available"
                },
                "troubleshooting": {
                    "primary_issue": "Draw.io CLI is not installed or not in PATH",
                    "check_installation": "Verify Draw.io CLI is installed: drawio --version",
                    "check_path": "Ensure Draw.io CLI is in your system PATH",
                    "reinstall": "Try reinstalling: npm uninstall -g @drawio/drawio-desktop-cli && npm install -g @drawio/drawio-desktop-cli"
                }
            })
            mock_image_class.return_value = mock_image_service
            
            png_result = await convert_to_png(file_id=file_id)
            
            # Should provide comprehensive fallback information
            assert png_result["success"] is False
            assert png_result["cli_available"] is False
            assert "Draw.io CLI is not available" in png_result["error"]
            assert "Install Node.js" in png_result["fallback_message"]
            assert "manual_export" in png_result["alternatives"]
            assert "primary_issue" in png_result["troubleshooting"]
            assert png_result["troubleshooting"]["primary_issue"] == "Draw.io CLI is not installed or not in PATH"
    
    @pytest.mark.asyncio
    async def test_batch_diagram_processing(self):
        """Test processing multiple diagrams in batch."""
        diagram_requests = [
            {"prompt": "Create a user login flowchart", "filename": "login-flow"},
            {"prompt": "Create a database schema diagram", "filename": "db-schema"},
            {"prompt": "Create a system architecture overview", "filename": "system-arch"}
        ]
        
        # Process all diagrams
        results = []
        
        with patch('src.tools.LLMService') as mock_llm_class, \
             patch('src.tools.FileService') as mock_file_class:
            
            mock_llm = Mock()
            mock_llm.generate_drawio_xml = AsyncMock(return_value=MINIMAL_VALID_XML)
            mock_llm_class.return_value = mock_llm
            
            mock_file_service = Mock()
            mock_file_service.save_drawio_file = AsyncMock(
                side_effect=["file_1", "file_2", "file_3"]
            )
            mock_file_service.get_file_info = AsyncMock(
                side_effect=[
                    Mock(original_name="login-flow.drawio", expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))),
                    Mock(original_name="db-schema.drawio", expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00"))),
                    Mock(original_name="system-arch.drawio", expires_at=Mock(isoformat=Mock(return_value="2024-01-02T00:00:00")))
                ]
            )
            mock_file_service.get_file_path = AsyncMock(
                side_effect=["/temp/login-flow.drawio", "/temp/db-schema.drawio", "/temp/system-arch.drawio"]
            )
            mock_file_class.return_value = mock_file_service
            
            for request in diagram_requests:
                # Generate XML
                xml_result = await generate_drawio_xml(request["prompt"])
                assert xml_result["success"] is True
                
                # Save file
                save_result = await save_drawio_file(xml_result["xml_content"], request["filename"])
                assert save_result["success"] is True
                
                results.append({
                    "request": request,
                    "xml_result": xml_result,
                    "save_result": save_result
                })
        
        # Verify all processed successfully
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["xml_result"]["success"] is True
            assert result["save_result"]["success"] is True
            assert result["save_result"]["file_id"] == f"file_{i+1}"
            assert diagram_requests[i]["filename"] in result["save_result"]["filename"]