"""
Unit tests for ImageService class.
Tests PNG conversion, CLI availability checks, and fallback handling.
"""
import asyncio
import base64
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock, call

import pytest

from src.image_service import (
    ImageService, 
    ImageGenerationResult, 
    CLIAvailabilityResult, 
    ImageServiceError
)
from tests.fixtures.sample_xml import MINIMAL_VALID_XML


class TestImageServiceInitialization:
    """Test ImageService initialization and configuration."""
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        service = ImageService()
        
        assert service.drawio_cli_path == "drawio"
        assert service.timeout_seconds == 30
        assert service.cli_availability_cache is None
        assert service.cli_cache_ttl == 5 * 60  # 5 minutes
        assert service.logger is not None
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        service = ImageService(
            drawio_cli_path="/custom/path/drawio",
            timeout_seconds=60
        )
        
        assert service.drawio_cli_path == "/custom/path/drawio"
        assert service.timeout_seconds == 60
        assert service.cli_availability_cache is None


class TestImageServiceCLIAvailability:
    """Test CLI availability checking functionality."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.mark.asyncio
    async def test_cli_available_success(self, image_service):
        """Test successful CLI availability check."""
        with patch('shutil.which') as mock_which, \
             patch('asyncio.create_subprocess_exec') as mock_subprocess:
            
            # Mock CLI found in PATH
            mock_which.return_value = "/usr/local/bin/drawio"
            
            # Mock successful version check
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"drawio version 1.0.0\n", b"")
            mock_subprocess.return_value = mock_process
            
            result = await image_service.is_drawio_cli_available()
            
            assert result.available is True
            assert result.version == "drawio version 1.0.0"
            assert result.error is None
            assert result.installation_hint is None
            
            # Verify cache was set
            assert image_service.cli_availability_cache is not None
            assert image_service.cli_availability_cache["available"] is True
    
    @pytest.mark.asyncio
    async def test_cli_not_in_path(self, image_service):
        """Test CLI not found in PATH."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None
            
            result = await image_service.is_drawio_cli_available()
            
            assert result.available is False
            assert "not found in PATH" in result.error
            assert "npm install -g @drawio/drawio-desktop-cli" in result.installation_hint
    
    @pytest.mark.asyncio
    async def test_cli_version_check_fails(self, image_service):
        """Test CLI found but version check fails."""
        with patch('shutil.which') as mock_which, \
             patch('asyncio.create_subprocess_exec') as mock_subprocess:
            
            mock_which.return_value = "/usr/local/bin/drawio"
            
            # Mock failed version check
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"Command not found\n")
            mock_subprocess.return_value = mock_process
            
            result = await image_service.is_drawio_cli_available()
            
            assert result.available is False
            assert "version check failed" in result.error
            assert "Command not found" in result.error
    
    @pytest.mark.asyncio
    async def test_cli_version_check_timeout(self, image_service):
        """Test CLI version check timeout."""
        with patch('shutil.which') as mock_which, \
             patch('asyncio.create_subprocess_exec') as mock_subprocess:
            
            mock_which.return_value = "/usr/local/bin/drawio"
            
            # Mock timeout
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = asyncio.TimeoutError()
            mock_subprocess.return_value = mock_process
            
            result = await image_service.is_drawio_cli_available()
            
            assert result.available is False
            assert "timed out" in result.error
    
    @pytest.mark.asyncio
    async def test_cli_availability_cache_hit(self, image_service):
        """Test CLI availability check uses cache."""
        # Set up cache
        image_service.cli_availability_cache = {
            "available": True,
            "version": "cached version",
            "error": None,
            "installation_hint": None,
            "timestamp": time.time()
        }
        
        with patch('shutil.which') as mock_which:
            # This should not be called due to cache hit
            mock_which.return_value = "/usr/local/bin/drawio"
            
            result = await image_service.is_drawio_cli_available()
            
            assert result.available is True
            assert result.version == "cached version"
            
            # Verify which was not called
            mock_which.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cli_availability_cache_expired(self, image_service):
        """Test CLI availability check when cache is expired."""
        # Set up expired cache
        image_service.cli_availability_cache = {
            "available": True,
            "version": "old version",
            "error": None,
            "installation_hint": None,
            "timestamp": time.time() - (6 * 60)  # 6 minutes ago (expired)
        }
        
        with patch('shutil.which') as mock_which, \
             patch('asyncio.create_subprocess_exec') as mock_subprocess:
            
            mock_which.return_value = "/usr/local/bin/drawio"
            
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"new version\n", b"")
            mock_subprocess.return_value = mock_process
            
            result = await image_service.is_drawio_cli_available()
            
            assert result.available is True
            assert result.version == "new version"
            
            # Verify new check was performed
            mock_which.assert_called_once()
    
    def test_clear_cli_cache(self, image_service):
        """Test clearing CLI cache."""
        # Set up cache
        image_service.cli_availability_cache = {"test": "data"}
        
        image_service.clear_cli_cache()
        
        assert image_service.cli_availability_cache is None


class TestImageServicePNGGeneration:
    """Test PNG generation functionality."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.fixture
    def temp_drawio_file(self, temp_directory):
        """Create a temporary .drawio file for testing."""
        drawio_path = Path(temp_directory) / "test.drawio"
        drawio_path.write_text(MINIMAL_VALID_XML, encoding='utf-8')
        return str(drawio_path)
    
    @pytest.mark.asyncio
    async def test_generate_png_success(self, image_service, temp_drawio_file):
        """Test successful PNG generation."""
        output_path = Path(temp_drawio_file).parent / "test.png"
        
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, '_execute_drawio_cli') as mock_execute, \
             patch.object(image_service, 'convert_to_base64') as mock_base64:
            
            # Mock CLI available
            mock_cli_check.return_value = CLIAvailabilityResult(available=True, version="1.0.0")
            
            # Mock successful CLI execution
            mock_execute.return_value = True
            
            # Mock PNG file creation
            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.side_effect = lambda: str(output_path) in str(mock_exists.call_args[0][0])
            
            # Mock base64 conversion
            mock_base64.return_value = "base64content"
            
            result = await image_service.generate_png(
                drawio_file_path=temp_drawio_file,
                include_base64=True
            )
            
            assert result.success is True
            assert result.image_file_id is not None
            assert result.png_file_path is not None
            assert result.base64_content == "base64content"
            assert result.cli_available is True
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_generate_png_file_not_found(self, image_service):
        """Test PNG generation with non-existent file."""
        result = await image_service.generate_png("/nonexistent/file.drawio")
        
        assert result.success is False
        assert "not found" in result.error
        assert result.cli_available is False
    
    @pytest.mark.asyncio
    async def test_generate_png_invalid_file_type(self, image_service, temp_directory):
        """Test PNG generation with invalid file type."""
        txt_file = Path(temp_directory) / "test.txt"
        txt_file.write_text("not a drawio file")
        
        result = await image_service.generate_png(str(txt_file))
        
        assert result.success is False
        assert "Invalid file type" in result.error
        assert ".txt" in result.error
    
    @pytest.mark.asyncio
    async def test_generate_png_cli_not_available(self, image_service, temp_drawio_file):
        """Test PNG generation when CLI is not available."""
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, 'get_fallback_message') as mock_fallback:
            
            # Mock CLI not available
            mock_cli_check.return_value = CLIAvailabilityResult(
                available=False, 
                error="CLI not found"
            )
            
            mock_fallback.return_value = "Fallback instructions"
            
            result = await image_service.generate_png(temp_drawio_file)
            
            assert result.success is False
            assert "CLI not available" in result.error
            assert result.fallback_message == "Fallback instructions"
            assert result.cli_available is False
    
    @pytest.mark.asyncio
    async def test_generate_png_cli_execution_fails(self, image_service, temp_drawio_file):
        """Test PNG generation when CLI execution fails."""
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, '_execute_drawio_cli') as mock_execute:
            
            mock_cli_check.return_value = CLIAvailabilityResult(available=True)
            mock_execute.return_value = False
            
            result = await image_service.generate_png(temp_drawio_file)
            
            assert result.success is False
            assert "conversion failed" in result.error
            assert result.cli_available is True
    
    @pytest.mark.asyncio
    async def test_generate_png_output_file_not_created(self, image_service, temp_drawio_file):
        """Test PNG generation when output file is not created."""
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, '_execute_drawio_cli') as mock_execute:
            
            mock_cli_check.return_value = CLIAvailabilityResult(available=True)
            mock_execute.return_value = True
            
            # Mock output file doesn't exist
            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.return_value = False
            
            result = await image_service.generate_png(temp_drawio_file)
            
            assert result.success is False
            assert "was not created" in result.error
    
    @pytest.mark.asyncio
    async def test_generate_png_with_custom_output_dir(self, image_service, temp_drawio_file, temp_directory):
        """Test PNG generation with custom output directory."""
        output_dir = Path(temp_directory) / "output"
        
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, '_execute_drawio_cli') as mock_execute, \
             patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('pathlib.Path.exists') as mock_exists:
            
            mock_cli_check.return_value = CLIAvailabilityResult(available=True)
            mock_execute.return_value = True
            mock_exists.return_value = True
            
            result = await image_service.generate_png(
                drawio_file_path=temp_drawio_file,
                output_dir=str(output_dir)
            )
            
            assert result.success is True
            assert str(output_dir) in result.png_file_path
            mock_mkdir.assert_called_once()


class TestImageServiceCLIExecution:
    """Test CLI execution functionality."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.mark.asyncio
    async def test_execute_drawio_cli_success(self, image_service):
        """Test successful CLI execution."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Export successful\n", b"")
            mock_subprocess.return_value = mock_process
            
            result = await image_service._execute_drawio_cli(
                "/input/test.drawio",
                "/output/test.png"
            )
            
            assert result is True
            
            # Verify correct command was called
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0]
            assert "drawio" in call_args
            assert "-x" in call_args
            assert "-f" in call_args
            assert "png" in call_args
            assert "-o" in call_args
            assert "/output/test.png" in call_args
            assert "/input/test.drawio" in call_args
    
    @pytest.mark.asyncio
    async def test_execute_drawio_cli_failure(self, image_service):
        """Test CLI execution failure."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"Error: Invalid file\n")
            mock_subprocess.return_value = mock_process
            
            result = await image_service._execute_drawio_cli(
                "/input/test.drawio",
                "/output/test.png"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_execute_drawio_cli_timeout(self, image_service):
        """Test CLI execution timeout."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = asyncio.TimeoutError()
            mock_subprocess.return_value = mock_process
            
            result = await image_service._execute_drawio_cli(
                "/input/test.drawio",
                "/output/test.png"
            )
            
            assert result is False
            
            # Verify process was killed
            mock_process.kill.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_drawio_cli_exception(self, image_service):
        """Test CLI execution with exception."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_subprocess.side_effect = Exception("Process creation failed")
            
            result = await image_service._execute_drawio_cli(
                "/input/test.drawio",
                "/output/test.png"
            )
            
            assert result is False


class TestImageServiceBase64Conversion:
    """Test Base64 conversion functionality."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.fixture
    def temp_png_file(self, temp_directory):
        """Create a temporary PNG file for testing."""
        png_path = Path(temp_directory) / "test.png"
        # Create a small fake PNG file
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        png_path.write_bytes(png_content)
        return str(png_path)
    
    @pytest.mark.asyncio
    async def test_convert_to_base64_success(self, image_service, temp_png_file):
        """Test successful Base64 conversion."""
        result = await image_service.convert_to_base64(temp_png_file)
        
        assert result is not None
        assert isinstance(result, str)
        
        # Verify it's valid base64
        try:
            decoded = base64.b64decode(result)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("Result is not valid base64")
    
    @pytest.mark.asyncio
    async def test_convert_to_base64_file_not_found(self, image_service):
        """Test Base64 conversion with non-existent file."""
        result = await image_service.convert_to_base64("/nonexistent/file.png")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_convert_to_base64_file_too_large(self, image_service, temp_directory):
        """Test Base64 conversion with file too large."""
        large_file = Path(temp_directory) / "large.png"
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value = Mock(st_size=11 * 1024 * 1024)  # 11MB
            
            result = await image_service.convert_to_base64(str(large_file))
            
            assert result is None


class TestImageServiceFallbackHandling:
    """Test fallback message and alternative options."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.mark.asyncio
    async def test_get_fallback_message(self, image_service):
        """Test fallback message generation."""
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check:
            mock_cli_check.return_value = CLIAvailabilityResult(
                available=False,
                error="CLI not found",
                installation_hint="Install with npm"
            )
            
            message = await image_service.get_fallback_message()
            
            assert "Draw.io CLI is not available" in message
            assert "Install Node.js" in message
            assert "npm install -g @drawio/drawio-desktop-cli" in message
            assert "Alternative options" in message
    
    @pytest.mark.asyncio
    async def test_get_alternative_options(self, image_service):
        """Test alternative options generation."""
        alternatives = await image_service._get_alternative_options()
        
        assert "manual_export" in alternatives
        assert "web_version" in alternatives
        assert "xml_content" in alternatives
        assert "save_for_later" in alternatives
        assert "https://app.diagrams.net/" in alternatives["web_version"]
    
    @pytest.mark.asyncio
    async def test_get_troubleshooting_info(self, image_service):
        """Test troubleshooting information generation."""
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check:
            mock_cli_check.return_value = CLIAvailabilityResult(
                available=False,
                error="Command not found"
            )
            
            troubleshooting = await image_service._get_troubleshooting_info()
            
            assert "check_installation" in troubleshooting
            assert "check_path" in troubleshooting
            assert "reinstall" in troubleshooting
            assert "primary_issue" in troubleshooting
            assert "not installed or not in PATH" in troubleshooting["primary_issue"]


class TestImageServiceComprehensiveWorkflow:
    """Test comprehensive PNG generation workflow."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.fixture
    def mock_file_service(self):
        """Create mock FileService for testing."""
        mock_service = Mock()
        mock_service.save_file = AsyncMock(return_value="file_123")
        mock_service.get_file_info = AsyncMock(return_value={
            "path": "/temp/saved_file.png",
            "created_at": "2024-01-01T00:00:00Z",
            "expires_at": "2024-01-02T00:00:00Z"
        })
        return mock_service
    
    @pytest.fixture
    def temp_drawio_file(self, temp_directory):
        """Create a temporary .drawio file for testing."""
        drawio_path = Path(temp_directory) / "test.drawio"
        drawio_path.write_text(MINIMAL_VALID_XML, encoding='utf-8')
        return str(drawio_path)
    
    @pytest.mark.asyncio
    async def test_generate_png_with_fallback_success(self, image_service, temp_drawio_file, mock_file_service):
        """Test successful comprehensive PNG generation workflow."""
        with patch.object(image_service, 'generate_png') as mock_generate, \
             patch.object(image_service, 'save_png_with_metadata') as mock_save:
            
            # Mock successful generation
            mock_generate.return_value = ImageGenerationResult(
                success=True,
                image_file_id="img_123",
                png_file_path="/temp/test.png",
                base64_content="base64data",
                cli_available=True
            )
            
            # Mock successful save
            mock_save.return_value = {
                "success": True,
                "file_id": "saved_123",
                "file_path": "/temp/saved.png"
            }
            
            result = await image_service.generate_png_with_fallback(
                drawio_file_path=temp_drawio_file,
                include_base64=True,
                file_service=mock_file_service
            )
            
            assert result["success"] is True
            assert "conversion_result" in result
            assert "save_result" in result
            assert result["conversion_result"]["image_file_id"] == "img_123"
            assert result["save_result"]["file_id"] == "saved_123"
    
    @pytest.mark.asyncio
    async def test_generate_png_with_fallback_failure(self, image_service, temp_drawio_file):
        """Test comprehensive PNG generation workflow with failure."""
        with patch.object(image_service, 'generate_png') as mock_generate, \
             patch.object(image_service, '_get_alternative_options') as mock_alternatives, \
             patch.object(image_service, '_get_troubleshooting_info') as mock_troubleshooting:
            
            # Mock failed generation
            mock_generate.return_value = ImageGenerationResult(
                success=False,
                error="CLI not available",
                fallback_message="Install CLI",
                cli_available=False
            )
            
            mock_alternatives.return_value = {"manual": "Use manual export"}
            mock_troubleshooting.return_value = {"issue": "CLI missing"}
            
            result = await image_service.generate_png_with_fallback(
                drawio_file_path=temp_drawio_file
            )
            
            assert result["success"] is False
            assert result["error"] == "CLI not available"
            assert result["fallback_message"] == "Install CLI"
            assert result["alternatives"] == {"manual": "Use manual export"}
            assert result["troubleshooting"] == {"issue": "CLI missing"}


class TestImageServiceServiceStatus:
    """Test service status and statistics."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    def test_get_stats(self, image_service):
        """Test service statistics."""
        stats = image_service.get_stats()
        
        assert "cli_path" in stats
        assert "timeout_seconds" in stats
        assert "cli_cache_valid" in stats
        assert "fallback_enabled" in stats
        assert "base64_support" in stats
        assert stats["cli_path"] == "drawio"
        assert stats["timeout_seconds"] == 30
        assert stats["fallback_enabled"] is True
        assert stats["base64_support"] is True
    
    @pytest.mark.asyncio
    async def test_get_service_status_operational(self, image_service):
        """Test service status when operational."""
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check:
            mock_cli_check.return_value = CLIAvailabilityResult(
                available=True,
                version="1.0.0"
            )
            
            status = await image_service.get_service_status()
            
            assert status["service_name"] == "ImageService"
            assert status["status"] == "operational"
            assert status["cli_available"] is True
            assert status["cli_version"] == "1.0.0"
            assert "features" in status
            assert status["features"]["png_conversion"] is True
    
    @pytest.mark.asyncio
    async def test_get_service_status_degraded(self, image_service):
        """Test service status when degraded."""
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, 'get_fallback_message') as mock_fallback, \
             patch.object(image_service, '_get_alternative_options') as mock_alternatives, \
             patch.object(image_service, '_get_troubleshooting_info') as mock_troubleshooting:
            
            mock_cli_check.return_value = CLIAvailabilityResult(
                available=False,
                error="CLI not found"
            )
            mock_fallback.return_value = "Fallback message"
            mock_alternatives.return_value = {"manual": "Manual export"}
            mock_troubleshooting.return_value = {"issue": "CLI missing"}
            
            status = await image_service.get_service_status()
            
            assert status["service_name"] == "ImageService"
            assert status["status"] == "degraded"
            assert status["cli_available"] is False
            assert status["cli_error"] == "CLI not found"
            assert "fallback_message" in status
            assert "alternatives" in status
            assert "troubleshooting" in status


class TestImageServiceFileMetadata:
    """Test PNG file saving with metadata."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.fixture
    def mock_file_service(self):
        """Create mock FileService for testing."""
        mock_service = Mock()
        mock_service.save_file = AsyncMock(return_value="file_123")
        mock_service.get_file_info = AsyncMock(return_value={
            "path": "/temp/saved_file.png",
            "created_at": "2024-01-01T00:00:00Z",
            "expires_at": "2024-01-02T00:00:00Z"
        })
        return mock_service
    
    @pytest.fixture
    def temp_png_file(self, temp_directory):
        """Create a temporary PNG file for testing."""
        png_path = Path(temp_directory) / "test.png"
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        png_path.write_bytes(png_content)
        return str(png_path)
    
    @pytest.mark.asyncio
    async def test_save_png_with_metadata_success(self, image_service, temp_png_file, mock_file_service):
        """Test successful PNG saving with metadata."""
        result = await image_service.save_png_with_metadata(
            png_file_path=temp_png_file,
            file_service=mock_file_service,
            original_drawio_id="drawio_123"
        )
        
        assert result["success"] is True
        assert result["file_id"] == "file_123"
        assert result["original_drawio_id"] == "drawio_123"
        assert "size_bytes" in result
        assert result["size_bytes"] > 0
        
        # Verify file service was called correctly
        mock_file_service.save_file.assert_called_once()
        call_args = mock_file_service.save_file.call_args
        assert call_args[1]["file_type"] == "png"
        assert "drawio_123" in call_args[1]["filename"]
    
    @pytest.mark.asyncio
    async def test_save_png_with_metadata_file_not_found(self, image_service, mock_file_service):
        """Test PNG saving with non-existent file."""
        result = await image_service.save_png_with_metadata(
            png_file_path="/nonexistent/file.png",
            file_service=mock_file_service
        )
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_save_png_with_metadata_service_error(self, image_service, temp_png_file, mock_file_service):
        """Test PNG saving with file service error."""
        mock_file_service.save_file.side_effect = Exception("Save failed")
        
        result = await image_service.save_png_with_metadata(
            png_file_path=temp_png_file,
            file_service=mock_file_service
        )
        
        assert result["success"] is False
        assert "Failed to save PNG" in result["error"]


class TestImageServiceAdvancedFeatures:
    """Test advanced ImageService features and edge cases."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.mark.asyncio
    async def test_concurrent_png_generation(self, image_service, temp_directory):
        """Test concurrent PNG generation operations."""
        # Create multiple test files
        test_files = []
        for i in range(3):
            drawio_path = Path(temp_directory) / f"test_{i}.drawio"
            drawio_path.write_text(MINIMAL_VALID_XML, encoding='utf-8')
            test_files.append(str(drawio_path))
        
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, '_execute_drawio_cli') as mock_execute, \
             patch('pathlib.Path.exists') as mock_exists:
            
            mock_cli_check.return_value = CLIAvailabilityResult(available=True)
            mock_execute.return_value = True
            mock_exists.return_value = True
            
            # Execute concurrent PNG generations
            tasks = [
                image_service.generate_png(file_path)
                for file_path in test_files
            ]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            for result in results:
                assert result.success is True
                assert result.cli_available is True
    
    @pytest.mark.asyncio
    async def test_png_generation_with_custom_timeout(self, image_service, temp_directory):
        """Test PNG generation with custom timeout settings."""
        # Create custom service with short timeout
        short_timeout_service = ImageService(timeout_seconds=1)
        
        drawio_path = Path(temp_directory) / "test.drawio"
        drawio_path.write_text(MINIMAL_VALID_XML, encoding='utf-8')
        
        with patch.object(short_timeout_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(short_timeout_service, '_execute_drawio_cli') as mock_execute:
            
            mock_cli_check.return_value = CLIAvailabilityResult(available=True)
            # Mock timeout scenario
            mock_execute.return_value = False
            
            result = await short_timeout_service.generate_png(str(drawio_path))
            
            assert result.success is False
            assert "conversion failed" in result.error
    
    @pytest.mark.asyncio
    async def test_cache_management_operations(self, image_service):
        """Test CLI cache management operations."""
        # Initially no cache
        assert not image_service._is_cli_cache_valid()
        
        # Set up cache
        result = CLIAvailabilityResult(available=True, version="1.0.0")
        image_service._cache_cli_result(result)
        
        # Cache should be valid
        assert image_service._is_cli_cache_valid()
        assert image_service.cli_availability_cache["available"] is True
        
        # Clear cache
        image_service.clear_cli_cache()
        assert image_service.cli_availability_cache is None
        assert not image_service._is_cli_cache_valid()
    
    @pytest.mark.asyncio
    async def test_error_handling_edge_cases(self, image_service, temp_directory):
        """Test error handling for edge cases."""
        # Test with empty file
        empty_file = Path(temp_directory) / "empty.drawio"
        empty_file.write_text("", encoding='utf-8')
        
        result = await image_service.generate_png(str(empty_file))
        assert result.success is False
        
        # Test with very large filename
        long_name = "a" * 300 + ".drawio"
        long_file = Path(temp_directory) / long_name
        long_file.write_text(MINIMAL_VALID_XML, encoding='utf-8')
        
        # Should still work (filename length is handled by filesystem)
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check:
            mock_cli_check.return_value = CLIAvailabilityResult(available=False)
            result = await image_service.generate_png(str(long_file))
            assert result.success is False
            assert result.cli_available is False
    
    @pytest.mark.asyncio
    async def test_base64_conversion_edge_cases(self, image_service, temp_directory):
        """Test Base64 conversion edge cases."""
        # Test with empty PNG file
        empty_png = Path(temp_directory) / "empty.png"
        empty_png.write_bytes(b"")
        
        result = await image_service.convert_to_base64(str(empty_png))
        assert result == ""  # Empty file should return empty base64
        
        # Test with binary data that's not actually PNG
        fake_png = Path(temp_directory) / "fake.png"
        fake_png.write_bytes(b"not a real png file")
        
        result = await image_service.convert_to_base64(str(fake_png))
        assert result is not None  # Should still encode, even if not valid PNG
        
        # Verify it's valid base64
        import base64
        decoded = base64.b64decode(result)
        assert decoded == b"not a real png file"


class TestImageServiceIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    @pytest.fixture
    def image_service(self):
        """Create ImageService instance for testing."""
        return ImageService()
    
    @pytest.fixture
    def mock_file_service(self):
        """Create comprehensive mock FileService."""
        mock_service = Mock()
        mock_service.save_file = AsyncMock(return_value="file_123")
        mock_service.get_file_info = AsyncMock(return_value={
            "path": "/temp/saved_file.png",
            "created_at": "2024-01-01T00:00:00Z",
            "expires_at": "2024-01-02T00:00:00Z",
            "size_bytes": 1024
        })
        return mock_service
    
    @pytest.mark.asyncio
    async def test_full_workflow_cli_available(self, image_service, temp_directory, mock_file_service):
        """Test complete workflow when CLI is available."""
        # Create test file
        drawio_path = Path(temp_directory) / "workflow_test.drawio"
        drawio_path.write_text(MINIMAL_VALID_XML, encoding='utf-8')
        
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, '_execute_drawio_cli') as mock_execute, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch.object(image_service, 'convert_to_base64') as mock_base64:
            
            # Mock successful CLI operations
            mock_cli_check.return_value = CLIAvailabilityResult(
                available=True,
                version="1.0.0"
            )
            mock_execute.return_value = True
            mock_exists.return_value = True
            mock_base64.return_value = "base64content"
            
            # Execute full workflow
            result = await image_service.generate_png_with_fallback(
                drawio_file_path=str(drawio_path),
                include_base64=True,
                file_service=mock_file_service
            )
            
            # Verify successful workflow
            assert result["success"] is True
            assert "conversion_result" in result
            assert "save_result" in result
            assert result["conversion_result"]["cli_available"] is True
            assert result["conversion_result"]["base64_content"] == "base64content"
            assert result["save_result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_full_workflow_cli_unavailable(self, image_service, temp_directory):
        """Test complete workflow when CLI is unavailable."""
        # Create test file
        drawio_path = Path(temp_directory) / "workflow_test.drawio"
        drawio_path.write_text(MINIMAL_VALID_XML, encoding='utf-8')
        
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check, \
             patch.object(image_service, 'get_fallback_message') as mock_fallback, \
             patch.object(image_service, '_get_alternative_options') as mock_alternatives, \
             patch.object(image_service, '_get_troubleshooting_info') as mock_troubleshooting:
            
            # Mock CLI unavailable
            mock_cli_check.return_value = CLIAvailabilityResult(
                available=False,
                error="CLI not found in PATH",
                installation_hint="Install with npm"
            )
            mock_fallback.return_value = "Detailed fallback instructions"
            mock_alternatives.return_value = {
                "manual_export": "Use Draw.io Desktop",
                "web_version": "Use web version"
            }
            mock_troubleshooting.return_value = {
                "primary_issue": "CLI not installed",
                "check_installation": "Run drawio --version"
            }
            
            # Execute workflow
            result = await image_service.generate_png_with_fallback(
                drawio_file_path=str(drawio_path)
            )
            
            # Verify fallback response
            assert result["success"] is False
            assert result["cli_available"] is False
            assert result["fallback_message"] == "Detailed fallback instructions"
            assert "manual_export" in result["alternatives"]
            assert "primary_issue" in result["troubleshooting"]
    
    @pytest.mark.asyncio
    async def test_workflow_partial_failure_scenarios(self, image_service, temp_directory, mock_file_service):
        """Test workflow with partial failures."""
        drawio_path = Path(temp_directory) / "test.drawio"
        drawio_path.write_text(MINIMAL_VALID_XML, encoding='utf-8')
        
        # Scenario 1: PNG generation succeeds but file saving fails
        with patch.object(image_service, 'generate_png') as mock_generate, \
             patch.object(image_service, 'save_png_with_metadata') as mock_save:
            
            mock_generate.return_value = ImageGenerationResult(
                success=True,
                image_file_id="img_123",
                png_file_path="/temp/test.png",
                cli_available=True
            )
            mock_save.return_value = {
                "success": False,
                "error": "Disk full"
            }
            
            result = await image_service.generate_png_with_fallback(
                drawio_file_path=str(drawio_path),
                file_service=mock_file_service
            )
            
            # Should still report success for conversion, but include save error
            assert result["success"] is True
            assert result["conversion_result"]["success"] is True
            assert result["save_result"]["success"] is False
    
    @pytest.mark.asyncio
    async def test_service_resilience_under_load(self, image_service, temp_directory):
        """Test service resilience under concurrent load."""
        # Create multiple test files
        test_files = []
        for i in range(10):
            drawio_path = Path(temp_directory) / f"load_test_{i}.drawio"
            drawio_path.write_text(MINIMAL_VALID_XML, encoding='utf-8')
            test_files.append(str(drawio_path))
        
        with patch.object(image_service, 'is_drawio_cli_available') as mock_cli_check:
            # Mix of available and unavailable CLI responses
            mock_cli_check.side_effect = [
                CLIAvailabilityResult(available=True, version="1.0.0"),
                CLIAvailabilityResult(available=False, error="Temporary error"),
                CLIAvailabilityResult(available=True, version="1.0.0"),
            ] * 4  # Repeat pattern
            
            # Execute concurrent operations
            tasks = [
                image_service.generate_png_with_fallback(file_path)
                for file_path in test_files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify no exceptions were raised
            for result in results:
                assert not isinstance(result, Exception)
                assert isinstance(result, dict)
                assert "success" in result