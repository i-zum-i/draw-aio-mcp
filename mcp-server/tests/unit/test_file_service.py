"""
Unit tests for FileService class.
Tests file saving, retrieval, and cleanup functionality.
"""
import asyncio
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import threading

import pytest

from src.file_service import FileService, TempFile, FileServiceError


class TestFileServiceInitialization:
    """Test FileService initialization and configuration."""
    
    def test_singleton_pattern(self):
        """Test that FileService follows singleton pattern."""
        # Reset singleton state for testing
        FileService._instance = None
        FileService._initialized = False
        
        service1 = FileService(temp_dir="./test_temp1")
        service2 = FileService(temp_dir="./test_temp2")  # Different params should be ignored
        
        # Should be the same instance
        assert service1 is service2
        
        # Should use first initialization parameters
        assert str(service1.temp_dir).endswith("test_temp1")
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        temp_dir = "./custom_temp"
        file_expiry_hours = 48
        cleanup_interval_minutes = 30
        
        with patch('src.file_service.FileService._ensure_temp_directory'), \
             patch('src.file_service.FileService._start_cleanup_scheduler'):
            
            service = FileService(
                temp_dir=temp_dir,
                file_expiry_hours=file_expiry_hours,
                cleanup_interval_minutes=cleanup_interval_minutes
            )
            
            assert str(service.temp_dir).endswith("custom_temp")
            assert service.file_expiry_hours == file_expiry_hours
            assert service.cleanup_interval_minutes == cleanup_interval_minutes
            assert service.temp_files == {}
    
    def test_ensure_temp_directory_creation(self):
        """Test temporary directory creation."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_temp_dir = Path(temp_dir) / "test_temp"
            
            with patch('src.file_service.FileService._start_cleanup_scheduler'):
                service = FileService(temp_dir=str(test_temp_dir))
                
                # Directory should be created
                assert test_temp_dir.exists()
                assert test_temp_dir.is_dir()
    
    def test_ensure_temp_directory_error(self):
        """Test error handling during directory creation."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")), \
             patch('src.file_service.FileService._start_cleanup_scheduler'):
            
            with pytest.raises(FileServiceError) as exc_info:
                FileService(temp_dir="/invalid/path")
            
            assert "Failed to create temporary directory" in str(exc_info.value)
            assert exc_info.value.original_error is not None


class TestFileServiceDrawioOperations:
    """Test Draw.io file operations."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.file_service.FileService._start_cleanup_scheduler'):
                service = FileService(temp_dir=temp_dir, file_expiry_hours=24)
                yield service
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_success(self, file_service):
        """Test successful Draw.io file saving."""
        xml_content = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        
        file_id = await file_service.save_drawio_file(xml_content)
        
        # Should return a valid UUID
        assert isinstance(file_id, str)
        assert len(file_id) == 36  # UUID length
        
        # Should be stored in temp_files
        assert file_id in file_service.temp_files
        
        temp_file = file_service.temp_files[file_id]
        assert temp_file.file_type == "drawio"
        assert temp_file.id == file_id
        assert temp_file.path.endswith('.drawio')
        
        # File should exist on disk
        file_path = Path(temp_file.path)
        assert file_path.exists()
        
        # Content should match
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == xml_content
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_with_custom_filename(self, file_service):
        """Test saving Draw.io file with custom filename."""
        xml_content = "<mxfile>test</mxfile>"
        custom_filename = "my_diagram"
        
        file_id = await file_service.save_drawio_file(xml_content, custom_filename)
        
        temp_file = file_service.temp_files[file_id]
        assert temp_file.original_name == custom_filename
        assert temp_file.path.endswith('my_diagram.drawio')
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_filename_sanitization(self, file_service):
        """Test filename sanitization for security."""
        xml_content = "<mxfile>test</mxfile>"
        unsafe_filename = "../../../etc/passwd<>:|?*"
        
        file_id = await file_service.save_drawio_file(xml_content, unsafe_filename)
        
        temp_file = file_service.temp_files[file_id]
        # Should be sanitized
        assert "../" not in temp_file.path
        assert "<" not in temp_file.path
        assert ">" not in temp_file.path
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_duplicate_filename(self, file_service):
        """Test handling of duplicate filenames."""
        xml_content = "<mxfile>test</mxfile>"
        filename = "duplicate_test"
        
        # Save first file
        file_id1 = await file_service.save_drawio_file(xml_content, filename)
        
        # Save second file with same filename
        file_id2 = await file_service.save_drawio_file(xml_content, filename)
        
        temp_file1 = file_service.temp_files[file_id1]
        temp_file2 = file_service.temp_files[file_id2]
        
        # Paths should be different
        assert temp_file1.path != temp_file2.path
        assert temp_file1.path.endswith('duplicate_test.drawio')
        assert temp_file2.path.endswith('duplicate_test_1.drawio')
    
    @pytest.mark.asyncio
    async def test_save_drawio_file_write_error(self, file_service):
        """Test error handling during file writing."""
        xml_content = "<mxfile>test</mxfile>"
        
        with patch('src.file_service.FileService._write_file_async', side_effect=PermissionError("Permission denied")):
            with pytest.raises(FileServiceError) as exc_info:
                await file_service.save_drawio_file(xml_content)
            
            assert "Failed to save Draw.io file" in str(exc_info.value)
            assert exc_info.value.original_error is not None


class TestFileServiceRetrievalOperations:
    """Test file retrieval operations."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.file_service.FileService._start_cleanup_scheduler'):
                service = FileService(temp_dir=temp_dir, file_expiry_hours=24)
                yield service
    
    @pytest.mark.asyncio
    async def test_get_file_path_success(self, file_service):
        """Test successful file path retrieval."""
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        file_path = await file_service.get_file_path(file_id)
        
        assert isinstance(file_path, str)
        assert Path(file_path).exists()
        assert Path(file_path).is_absolute()
    
    @pytest.mark.asyncio
    async def test_get_file_path_not_found(self, file_service):
        """Test error when file ID not found."""
        with pytest.raises(FileServiceError) as exc_info:
            await file_service.get_file_path("non_existent_id")
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_file_path_expired(self, file_service):
        """Test error when file has expired."""
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        # Manually expire the file
        temp_file = file_service.temp_files[file_id]
        temp_file.expires_at = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(FileServiceError) as exc_info:
            await file_service.get_file_path(file_id)
        
        assert "expired" in str(exc_info.value).lower()
        # File should be removed from metadata
        assert file_id not in file_service.temp_files
    
    @pytest.mark.asyncio
    async def test_get_file_path_missing_from_disk(self, file_service):
        """Test error when file missing from disk."""
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        # Remove file from disk
        temp_file = file_service.temp_files[file_id]
        Path(temp_file.path).unlink()
        
        with pytest.raises(FileServiceError) as exc_info:
            await file_service.get_file_path(file_id)
        
        assert "no longer exists on disk" in str(exc_info.value).lower()
        # File should be removed from metadata
        assert file_id not in file_service.temp_files
    
    @pytest.mark.asyncio
    async def test_get_file_info_success(self, file_service):
        """Test successful file info retrieval."""
        xml_content = "<mxfile>test</mxfile>"
        filename = "test_diagram"
        file_id = await file_service.save_drawio_file(xml_content, filename)
        
        file_info = await file_service.get_file_info(file_id)
        
        assert isinstance(file_info, TempFile)
        assert file_info.id == file_id
        assert file_info.original_name == filename
        assert file_info.file_type == "drawio"
        assert isinstance(file_info.created_at, datetime)
        assert isinstance(file_info.expires_at, datetime)
    
    @pytest.mark.asyncio
    async def test_file_exists_true(self, file_service):
        """Test file_exists returns True for valid files."""
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        exists = await file_service.file_exists(file_id)
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_file_exists_false_not_found(self, file_service):
        """Test file_exists returns False for non-existent files."""
        exists = await file_service.file_exists("non_existent_id")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_file_exists_false_expired(self, file_service):
        """Test file_exists returns False for expired files."""
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        # Manually expire the file
        temp_file = file_service.temp_files[file_id]
        temp_file.expires_at = datetime.now() - timedelta(hours=1)
        
        exists = await file_service.file_exists(file_id)
        assert exists is False
        # File should be removed from metadata
        assert file_id not in file_service.temp_files


class TestFileServicePNGOperations:
    """Test PNG file operations."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.file_service.FileService._start_cleanup_scheduler'):
                service = FileService(temp_dir=temp_dir, file_expiry_hours=24)
                yield service
    
    @pytest.mark.asyncio
    async def test_save_png_file_success(self, file_service):
        """Test successful PNG file registration."""
        # Create a temporary PNG file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_png:
            temp_png.write(b'fake png data')
            png_file_path = temp_png.name
        
        try:
            original_file_id = "test_drawio_id"
            
            png_file_id = await file_service.save_png_file(original_file_id, png_file_path)
            
            # Should return PNG file ID
            assert png_file_id == f"{original_file_id}_png"
            
            # Should be stored in temp_files
            assert png_file_id in file_service.temp_files
            
            temp_file = file_service.temp_files[png_file_id]
            assert temp_file.file_type == "png"
            assert temp_file.id == png_file_id
            assert temp_file.original_name == f"{original_file_id}.png"
            assert temp_file.path == png_file_path
            
        finally:
            # Clean up
            Path(png_file_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_save_png_file_not_exists(self, file_service):
        """Test error when PNG file doesn't exist."""
        non_existent_path = "/path/to/non/existent/file.png"
        
        with pytest.raises(FileServiceError) as exc_info:
            await file_service.save_png_file("test_id", non_existent_path)
        
        assert "PNG file does not exist" in str(exc_info.value)


class TestFileServiceCleanupOperations:
    """Test cleanup operations."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.file_service.FileService._start_cleanup_scheduler'):
                service = FileService(temp_dir=temp_dir, file_expiry_hours=24)
                yield service
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_files_success(self, file_service):
        """Test successful cleanup of expired files."""
        # Create valid file
        xml_content = "<mxfile>valid</mxfile>"
        valid_file_id = await file_service.save_drawio_file(xml_content)
        
        # Create expired file
        expired_file_id = await file_service.save_drawio_file(xml_content)
        expired_temp_file = file_service.temp_files[expired_file_id]
        expired_temp_file.expires_at = datetime.now() - timedelta(hours=1)
        
        # Run cleanup
        cleanup_count = await file_service.cleanup_expired_files()
        
        # Should have cleaned up 1 file
        assert cleanup_count == 1
        
        # Valid file should remain
        assert valid_file_id in file_service.temp_files
        
        # Expired file should be removed
        assert expired_file_id not in file_service.temp_files
        assert not Path(expired_temp_file.path).exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_files(self, file_service):
        """Test cleanup of orphaned files (files without metadata)."""
        # Create orphaned file directly in temp directory
        orphaned_file = file_service.temp_dir / "orphaned.drawio"
        orphaned_file.write_text("<mxfile>orphaned</mxfile>")
        
        # Run cleanup
        cleanup_count = await file_service.cleanup_expired_files()
        
        # Should have cleaned up the orphaned file
        assert cleanup_count == 1
        assert not orphaned_file.exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_no_files_to_clean(self, file_service):
        """Test cleanup when no files need cleaning."""
        # Create valid file
        xml_content = "<mxfile>valid</mxfile>"
        await file_service.save_drawio_file(xml_content)
        
        # Run cleanup
        cleanup_count = await file_service.cleanup_expired_files()
        
        # Should have cleaned up 0 files
        assert cleanup_count == 0
    
    @pytest.mark.asyncio
    async def test_check_file_expiration(self, file_service):
        """Test file expiration checking."""
        # Create valid file
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        # Should not be expired
        is_expired = await file_service.check_file_expiration(file_id)
        assert is_expired is False
        
        # Manually expire the file
        temp_file = file_service.temp_files[file_id]
        temp_file.expires_at = datetime.now() - timedelta(hours=1)
        
        # Should be expired
        is_expired = await file_service.check_file_expiration(file_id)
        assert is_expired is True
        
        # Non-existent file should be considered expired
        is_expired = await file_service.check_file_expiration("non_existent")
        assert is_expired is True
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_success(self, file_service):
        """Test successful file integrity verification."""
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        is_valid = await file_service.verify_file_integrity(file_id)
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_missing_metadata(self, file_service):
        """Test file integrity when metadata is missing."""
        is_valid = await file_service.verify_file_integrity("non_existent")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_missing_file(self, file_service):
        """Test file integrity when file is missing from disk."""
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        # Remove file from disk
        temp_file = file_service.temp_files[file_id]
        Path(temp_file.path).unlink()
        
        is_valid = await file_service.verify_file_integrity(file_id)
        assert is_valid is False
        
        # Metadata should be cleaned up
        assert file_id not in file_service.temp_files
    
    @pytest.mark.asyncio
    async def test_emergency_cleanup(self, file_service):
        """Test emergency cleanup functionality."""
        # Create multiple files
        file_ids = []
        for i in range(5):
            xml_content = f"<mxfile>test_{i}</mxfile>"
            file_id = await file_service.save_drawio_file(xml_content)
            file_ids.append(file_id)
            
            # Add small delay to ensure different creation times
            await asyncio.sleep(0.01)
        
        # Run emergency cleanup for 3 files
        cleanup_count = await file_service.emergency_cleanup(target_cleanup_count=3)
        
        # Should have cleaned up 3 files
        assert cleanup_count == 3
        
        # Should have 2 files remaining
        remaining_files = len(file_service.temp_files)
        assert remaining_files == 2
        
        # Oldest files should be removed first
        assert file_ids[0] not in file_service.temp_files
        assert file_ids[1] not in file_service.temp_files
        assert file_ids[2] not in file_service.temp_files
        assert file_ids[3] in file_service.temp_files
        assert file_ids[4] in file_service.temp_files
    
    @pytest.mark.asyncio
    async def test_cleanup_by_age(self, file_service):
        """Test age-based cleanup functionality."""
        # Create old file
        xml_content = "<mxfile>old</mxfile>"
        old_file_id = await file_service.save_drawio_file(xml_content)
        old_temp_file = file_service.temp_files[old_file_id]
        old_temp_file.created_at = datetime.now() - timedelta(hours=25)  # Older than 24 hours
        
        # Create new file
        new_file_id = await file_service.save_drawio_file(xml_content)
        
        # Run age-based cleanup (24 hours)
        cleanup_count = await file_service.cleanup_by_age(max_age_hours=24)
        
        # Should have cleaned up 1 file
        assert cleanup_count == 1
        
        # Old file should be removed
        assert old_file_id not in file_service.temp_files
        
        # New file should remain
        assert new_file_id in file_service.temp_files


class TestFileServiceStatistics:
    """Test statistics and monitoring functionality."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.file_service.FileService._start_cleanup_scheduler'):
                service = FileService(temp_dir=temp_dir, file_expiry_hours=24)
                yield service
    
    @pytest.mark.asyncio
    async def test_get_stats_empty(self, file_service):
        """Test statistics when no files exist."""
        stats = file_service.get_stats()
        
        assert stats["total_files"] == 0
        assert stats["active_files"] == 0
        assert stats["expired_files"] == 0
        assert stats["drawio_files"] == 0
        assert stats["png_files"] == 0
        assert "cleanup_running" in stats
    
    @pytest.mark.asyncio
    async def test_get_stats_with_files(self, file_service):
        """Test statistics with various file types."""
        # Create Draw.io file
        xml_content = "<mxfile>test</mxfile>"
        drawio_file_id = await file_service.save_drawio_file(xml_content)
        
        # Create PNG file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_png:
            temp_png.write(b'fake png data')
            png_file_path = temp_png.name
        
        try:
            await file_service.save_png_file("test_id", png_file_path)
            
            # Create expired file
            expired_file_id = await file_service.save_drawio_file(xml_content)
            expired_temp_file = file_service.temp_files[expired_file_id]
            expired_temp_file.expires_at = datetime.now() - timedelta(hours=1)
            
            stats = file_service.get_stats()
            
            assert stats["total_files"] == 3
            assert stats["active_files"] == 2  # drawio + png
            assert stats["expired_files"] == 1
            assert stats["drawio_files"] == 2
            assert stats["png_files"] == 1
            
        finally:
            Path(png_file_path).unlink(missing_ok=True)


class TestFileServiceCleanupScheduler:
    """Test automatic cleanup scheduler."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't patch the scheduler for these tests
            service = FileService(temp_dir=temp_dir, cleanup_interval_minutes=1)
            yield service
            # Stop scheduler after test
            service.stop_cleanup_scheduler()
    
    def test_cleanup_scheduler_starts(self, file_service):
        """Test that cleanup scheduler starts automatically."""
        # Scheduler should be running
        assert file_service._cleanup_thread is not None
        assert file_service._cleanup_thread.is_alive()
    
    def test_stop_cleanup_scheduler(self, file_service):
        """Test stopping the cleanup scheduler."""
        # Should be running initially
        assert file_service._cleanup_thread.is_alive()
        
        # Stop scheduler
        file_service.stop_cleanup_scheduler()
        
        # Should stop within reasonable time
        time.sleep(0.1)
        assert not file_service._cleanup_thread.is_alive()


class TestFileServiceErrorHandling:
    """Test error handling in various scenarios."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.file_service.FileService._start_cleanup_scheduler'):
                service = FileService(temp_dir=temp_dir, file_expiry_hours=24)
                yield service
    
    @pytest.mark.asyncio
    async def test_cleanup_with_file_removal_error(self, file_service):
        """Test cleanup continues even when file removal fails."""
        # Create file
        xml_content = "<mxfile>test</mxfile>"
        file_id = await file_service.save_drawio_file(xml_content)
        
        # Expire the file
        temp_file = file_service.temp_files[file_id]
        temp_file.expires_at = datetime.now() - timedelta(hours=1)
        
        # Mock file removal to fail
        with patch('pathlib.Path.unlink', side_effect=PermissionError("Permission denied")):
            # Should not raise exception
            cleanup_count = await file_service.cleanup_expired_files()
            
            # Should still remove from metadata even if file removal fails
            assert file_id not in file_service.temp_files
    
    def test_sanitize_filename_edge_cases(self, file_service):
        """Test filename sanitization edge cases."""
        # Empty filename
        result = file_service._sanitize_filename("")
        assert result == "unnamed"
        
        # Only invalid characters
        result = file_service._sanitize_filename("<>:|?*")
        assert result == "unnamed"
        
        # Very long filename
        long_name = "a" * 200
        result = file_service._sanitize_filename(long_name)
        assert len(result) <= 100
        
        # Filename with leading/trailing dots and spaces
        result = file_service._sanitize_filename("  ..test..  ")
        assert result == "test"


class TestFileServiceAsyncOperations:
    """Test asynchronous file operations."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        # Reset singleton state
        FileService._instance = None
        FileService._initialized = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.file_service.FileService._start_cleanup_scheduler'):
                service = FileService(temp_dir=temp_dir, file_expiry_hours=24)
                yield service
    
    @pytest.mark.asyncio
    async def test_write_file_async(self, file_service):
        """Test asynchronous file writing."""
        test_content = "<mxfile>async test</mxfile>"
        test_path = file_service.temp_dir / "async_test.drawio"
        
        # Should complete without blocking
        await file_service._write_file_async(test_path, test_content)
        
        # File should exist with correct content
        assert test_path.exists()
        with open(test_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == test_content
    
    @pytest.mark.asyncio
    async def test_concurrent_file_operations(self, file_service):
        """Test concurrent file operations."""
        xml_content = "<mxfile>concurrent test</mxfile>"
        
        # Create multiple files concurrently
        tasks = []
        for i in range(10):
            task = file_service.save_drawio_file(xml_content, f"concurrent_{i}")
            tasks.append(task)
        
        # Wait for all to complete
        file_ids = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(file_ids) == 10
        assert len(set(file_ids)) == 10  # All unique
        
        # All files should exist
        for file_id in file_ids:
            assert file_id in file_service.temp_files
            file_path = await file_service.get_file_path(file_id)
            assert Path(file_path).exists()