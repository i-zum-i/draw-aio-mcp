"""
File Service for managing temporary Draw.io files.
"""
import asyncio
import os
import uuid
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Literal
import threading
import time


@dataclass
class TempFile:
    """Temporary file metadata."""
    id: str
    original_name: str
    path: str
    file_type: Literal["drawio", "png"]
    created_at: datetime
    expires_at: datetime


class FileServiceError(Exception):
    """Exception raised by file service operations."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        self.name = "FileServiceError"


class FileService:
    """Service for managing temporary Draw.io and PNG files."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, temp_dir: str = "./temp", file_expiry_hours: int = 24, cleanup_interval_minutes: int = 60):
        """Singleton pattern to ensure only one FileService instance."""
        if cls._instance is None:
            cls._instance = super(FileService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, temp_dir: str = "./temp", file_expiry_hours: int = 24, cleanup_interval_minutes: int = 60):
        """
        Initialize the file service.
        
        Args:
            temp_dir: Directory for temporary files.
            file_expiry_hours: Hours after which files expire.
            cleanup_interval_minutes: Minutes between automatic cleanup runs.
        """
        # Only initialize once
        if FileService._initialized:
            return
            
        self.temp_dir = Path(temp_dir)
        self.file_expiry_hours = file_expiry_hours
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.temp_files: Dict[str, TempFile] = {}
        self._cleanup_running = False
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Ensure temp directory exists
        self._ensure_temp_directory()
        
        # Start cleanup task
        self._start_cleanup_scheduler()
        
        FileService._initialized = True
    
    async def save_png_file(self, file_id: str, png_file_path: str) -> str:
        """
        Register a PNG file in the file service for cleanup management.
        
        Args:
            file_id: Original file ID (for reference).
            png_file_path: Path to the PNG file.
            
        Returns:
            PNG file ID for future reference.
            
        Raises:
            FileServiceError: If file registration fails.
        """
        try:
            # Generate unique PNG file ID
            png_file_id = f"{file_id}_png"
            
            # Ensure PNG file exists
            png_path = Path(png_file_path)
            if not png_path.exists():
                raise FileServiceError(f"PNG file does not exist: {png_file_path}")
            
            # Create metadata
            now = datetime.now()
            temp_file = TempFile(
                id=png_file_id,
                original_name=f"{file_id}.png",
                path=str(png_path),
                file_type="png",
                created_at=now,
                expires_at=now + timedelta(hours=self.file_expiry_hours)
            )
            
            # Store metadata
            self.temp_files[png_file_id] = temp_file
            
            self.logger.debug(f"Registered PNG file: {png_file_id} -> {png_file_path}")
            return png_file_id
            
        except Exception as error:
            raise FileServiceError(
                f"Failed to register PNG file: {str(error)}",
                error
            )

    async def save_drawio_file(self, xml_content: str, filename: Optional[str] = None) -> str:
        """
        Save Draw.io XML content to a temporary file.
        
        Args:
            xml_content: Valid Draw.io XML content.
            filename: Optional custom filename (without extension).
            
        Returns:
            File ID for future reference.
            
        Raises:
            FileServiceError: If file saving fails.
        """
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Determine filename
            if filename:
                # Sanitize filename
                safe_filename = self._sanitize_filename(filename)
                if not safe_filename.endswith('.drawio'):
                    safe_filename += '.drawio'
            else:
                safe_filename = f"{file_id}.drawio"
            
            # Create file path
            file_path = self.temp_dir / safe_filename
            
            # Ensure unique filename
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                if stem.endswith('.drawio'):
                    stem = stem[:-7]  # Remove .drawio
                file_path = self.temp_dir / f"{stem}_{counter}.drawio"
                counter += 1
            
            # Write XML content to file
            await self._write_file_async(file_path, xml_content)
            
            # Set appropriate file permissions (readable by owner and group)
            os.chmod(file_path, 0o644)
            
            # Create metadata
            now = datetime.now()
            temp_file = TempFile(
                id=file_id,
                original_name=filename or file_id,
                path=str(file_path),
                file_type="drawio",
                created_at=now,
                expires_at=now + timedelta(hours=self.file_expiry_hours)
            )
            
            # Store metadata
            self.temp_files[file_id] = temp_file
            
            return file_id
            
        except Exception as error:
            raise FileServiceError(
                f"Failed to save Draw.io file: {str(error)}",
                error
            )
    
    async def get_file_path(self, file_id: str) -> str:
        """
        Get file path by file ID.
        
        Args:
            file_id: File ID returned from save_drawio_file.
            
        Returns:
            Absolute file path.
            
        Raises:
            FileServiceError: If file not found or expired.
        """
        try:
            temp_file = self.temp_files.get(file_id)
            if not temp_file:
                raise FileServiceError(f"File with ID '{file_id}' not found")
            
            # Check if file has expired
            if datetime.now() > temp_file.expires_at:
                # Clean up expired file
                await self._remove_file(file_id)
                raise FileServiceError(f"File with ID '{file_id}' has expired")
            
            # Check if file still exists on disk
            file_path = Path(temp_file.path)
            if not file_path.exists():
                # Clean up missing file from metadata
                del self.temp_files[file_id]
                raise FileServiceError(f"File with ID '{file_id}' no longer exists on disk")
            
            return str(file_path.absolute())
            
        except FileServiceError:
            raise
        except Exception as error:
            raise FileServiceError(
                f"Failed to get file path for ID '{file_id}': {str(error)}",
                error
            )
    
    async def get_file_info(self, file_id: str) -> TempFile:
        """
        Get file information by file ID.
        
        Args:
            file_id: File ID returned from save_drawio_file.
            
        Returns:
            TempFile metadata.
            
        Raises:
            FileServiceError: If file not found or expired.
        """
        try:
            temp_file = self.temp_files.get(file_id)
            if not temp_file:
                raise FileServiceError(f"File with ID '{file_id}' not found")
            
            # Check if file has expired
            if datetime.now() > temp_file.expires_at:
                # Clean up expired file
                await self._remove_file(file_id)
                raise FileServiceError(f"File with ID '{file_id}' has expired")
            
            return temp_file
            
        except FileServiceError:
            raise
        except Exception as error:
            raise FileServiceError(
                f"Failed to get file info for ID '{file_id}': {str(error)}",
                error
            )
    
    async def file_exists(self, file_id: str) -> bool:
        """
        Check if file exists and is not expired.
        
        Args:
            file_id: File ID to check.
            
        Returns:
            True if file exists and is not expired, False otherwise.
        """
        try:
            temp_file = self.temp_files.get(file_id)
            if not temp_file:
                return False
            
            # Check if file has expired
            if datetime.now() > temp_file.expires_at:
                # Clean up expired file
                await self._remove_file(file_id)
                return False
            
            # Check if file still exists on disk
            file_path = Path(temp_file.path)
            if not file_path.exists():
                # Clean up missing file from metadata
                del self.temp_files[file_id]
                return False
            
            return True
            
        except Exception:
            return False
    
    async def cleanup_expired_files(self) -> int:
        """
        Clean up expired temporary files with detailed logging.
        
        Returns:
            Number of files cleaned up.
        """
        try:
            cleanup_start = datetime.now()
            self.logger.info("Starting automatic cleanup of expired files")
            
            now = datetime.now()
            expired_ids = []
            orphaned_files = []
            
            # Find expired files in metadata
            for file_id, temp_file in self.temp_files.items():
                if now > temp_file.expires_at:
                    expired_ids.append(file_id)
                    self.logger.debug(f"Found expired file: {file_id} (expired at {temp_file.expires_at})")
            
            # Find orphaned files on disk (files without metadata)
            if self.temp_dir.exists():
                for file_path in self.temp_dir.iterdir():
                    if file_path.is_file():
                        # Check if file has corresponding metadata
                        file_has_metadata = any(
                            temp_file.path == str(file_path) 
                            for temp_file in self.temp_files.values()
                        )
                        if not file_has_metadata:
                            orphaned_files.append(file_path)
                            self.logger.debug(f"Found orphaned file: {file_path}")
            
            # Remove expired files
            cleanup_count = 0
            failed_removals = 0
            
            for file_id in expired_ids:
                try:
                    temp_file = self.temp_files.get(file_id)
                    if temp_file:
                        self.logger.debug(f"Removing expired file: {temp_file.path}")
                        await self._remove_file(file_id)
                        cleanup_count += 1
                except Exception as e:
                    failed_removals += 1
                    self.logger.warning(f"Failed to remove expired file {file_id}: {str(e)}")
            
            # Remove orphaned files
            for file_path in orphaned_files:
                try:
                    self.logger.debug(f"Removing orphaned file: {file_path}")
                    file_path.unlink()
                    cleanup_count += 1
                except Exception as e:
                    failed_removals += 1
                    self.logger.warning(f"Failed to remove orphaned file {file_path}: {str(e)}")
            
            cleanup_duration = (datetime.now() - cleanup_start).total_seconds()
            
            # Log cleanup results (requirement 7.3)
            if cleanup_count > 0 or failed_removals > 0:
                self.logger.info(
                    f"Cleanup completed: {cleanup_count} files removed, "
                    f"{failed_removals} failures, duration: {cleanup_duration:.2f}s"
                )
            else:
                self.logger.debug(f"Cleanup completed: no files to remove, duration: {cleanup_duration:.2f}s")
            
            return cleanup_count
            
        except Exception as error:
            self.logger.error(f"Failed to cleanup expired files: {str(error)}")
            raise FileServiceError(
                f"Failed to cleanup expired files: {str(error)}",
                error
            )
    
    async def check_file_expiration(self, file_id: str) -> bool:
        """
        Check if a specific file has expired.
        
        Args:
            file_id: File ID to check.
            
        Returns:
            True if file has expired, False otherwise.
        """
        try:
            temp_file = self.temp_files.get(file_id)
            if not temp_file:
                return True  # Non-existent files are considered expired
            
            return datetime.now() > temp_file.expires_at
            
        except Exception as e:
            self.logger.warning(f"Error checking expiration for file {file_id}: {str(e)}")
            return True  # Assume expired on error
    
    async def verify_file_integrity(self, file_id: str) -> bool:
        """
        Verify that a file exists both in metadata and on disk.
        
        Args:
            file_id: File ID to verify.
            
        Returns:
            True if file exists and is accessible, False otherwise.
        """
        try:
            temp_file = self.temp_files.get(file_id)
            if not temp_file:
                return False
            
            # Check if file exists on disk
            file_path = Path(temp_file.path)
            if not file_path.exists():
                self.logger.warning(f"File {file_id} missing from disk: {temp_file.path}")
                # Clean up missing file from metadata
                del self.temp_files[file_id]
                return False
            
            # Check if file is readable
            try:
                file_path.stat()
                return True
            except OSError as e:
                self.logger.warning(f"File {file_id} not accessible: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Error verifying file integrity for {file_id}: {str(e)}")
            return False
    
    async def emergency_cleanup(self, target_cleanup_count: int = 10) -> int:
        """
        Emergency cleanup that removes oldest files first, regardless of expiration.
        Used when storage is low (requirement 7.4).
        
        Args:
            target_cleanup_count: Number of files to attempt to remove.
            
        Returns:
            Number of files actually cleaned up.
        """
        try:
            self.logger.warning(f"Starting emergency cleanup (target: {target_cleanup_count} files)")
            
            # Sort files by creation time (oldest first)
            sorted_files = sorted(
                self.temp_files.items(),
                key=lambda x: x[1].created_at
            )
            
            cleanup_count = 0
            for file_id, temp_file in sorted_files[:target_cleanup_count]:
                try:
                    self.logger.info(f"Emergency cleanup removing: {file_id} (created: {temp_file.created_at})")
                    await self._remove_file(file_id)
                    cleanup_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to remove file during emergency cleanup {file_id}: {str(e)}")
            
            self.logger.warning(f"Emergency cleanup completed: {cleanup_count} files removed")
            return cleanup_count
            
        except Exception as error:
            self.logger.error(f"Emergency cleanup failed: {str(error)}")
            raise FileServiceError(
                f"Emergency cleanup failed: {str(error)}",
                error
            )

    async def cleanup_by_age(self, max_age_hours: Optional[int] = None) -> int:
        """
        Clean up files older than specified age, regardless of expiration.
        Useful for emergency cleanup when storage is low.
        
        Args:
            max_age_hours: Maximum age in hours. If None, uses file_expiry_hours.
            
        Returns:
            Number of files cleaned up.
        """
        try:
            max_age = max_age_hours or self.file_expiry_hours
            cutoff_time = datetime.now() - timedelta(hours=max_age)
            
            self.logger.info(f"Starting age-based cleanup (max age: {max_age} hours)")
            
            old_file_ids = []
            for file_id, temp_file in self.temp_files.items():
                if temp_file.created_at < cutoff_time:
                    old_file_ids.append(file_id)
            
            cleanup_count = 0
            for file_id in old_file_ids:
                try:
                    await self._remove_file(file_id)
                    cleanup_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to remove old file {file_id}: {str(e)}")
            
            self.logger.info(f"Age-based cleanup completed: {cleanup_count} files removed")
            return cleanup_count
            
        except Exception as error:
            self.logger.error(f"Failed age-based cleanup: {str(error)}")
            raise FileServiceError(
                f"Failed age-based cleanup: {str(error)}",
                error
            )
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get file service statistics.
        
        Returns:
            Dictionary with statistics.
        """
        now = datetime.now()
        active_files = sum(1 for f in self.temp_files.values() if now <= f.expires_at)
        expired_files = len(self.temp_files) - active_files
        
        # Count files by type
        drawio_files = sum(1 for f in self.temp_files.values() if f.file_type == "drawio")
        png_files = sum(1 for f in self.temp_files.values() if f.file_type == "png")
        
        return {
            "total_files": len(self.temp_files),
            "active_files": active_files,
            "expired_files": expired_files,
            "drawio_files": drawio_files,
            "png_files": png_files,
            "cleanup_running": self._cleanup_running
        }
    
    def stop_cleanup_scheduler(self) -> None:
        """Stop the automatic cleanup scheduler."""
        self.logger.info("Stopping cleanup scheduler")
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)
    
    def _ensure_temp_directory(self) -> None:
        """Ensure temporary directory exists."""
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            # Set directory permissions (readable/writable by owner and group)
            os.chmod(self.temp_dir, 0o755)
        except Exception as error:
            raise FileServiceError(
                f"Failed to create temporary directory '{self.temp_dir}': {str(error)}",
                error
            )
    
    async def _write_file_async(self, file_path: Path, content: str) -> None:
        """Write content to file asynchronously."""
        def write_file():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Run file writing in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, write_file)
    
    async def _remove_file(self, file_id: str) -> None:
        """Remove file and its metadata with detailed logging."""
        temp_file = self.temp_files.get(file_id)
        if not temp_file:
            self.logger.debug(f"File {file_id} not found in metadata, skipping removal")
            return
        
        file_path = Path(temp_file.path)
        
        try:
            # Remove file from disk
            if file_path.exists():
                file_size = file_path.stat().st_size
                file_path.unlink()
                self.logger.debug(f"Removed file from disk: {file_path} ({file_size} bytes)")
            else:
                self.logger.debug(f"File already missing from disk: {file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to remove file from disk {file_path}: {str(e)}")
            # Continue even if file removal fails
        
        # Remove from metadata
        if file_id in self.temp_files:
            del self.temp_files[file_id]
            self.logger.debug(f"Removed file metadata: {file_id}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and invalid characters."""
        # Remove path separators and invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = ''.join(c for c in filename if c not in invalid_chars)
        
        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip(' .')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed"
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    def _start_cleanup_scheduler(self) -> None:
        """Start the automatic cleanup scheduler with improved resource management."""
        def cleanup_scheduler():
            self.logger.info(f"Starting cleanup scheduler (interval: {self.cleanup_interval_minutes} minutes)")
            
            while not self._stop_cleanup.is_set():
                try:
                    # Wait for the specified interval or until stop is requested
                    if self._stop_cleanup.wait(timeout=self.cleanup_interval_minutes * 60):
                        # Stop was requested
                        break
                    
                    # Set cleanup running flag
                    self._cleanup_running = True
                    
                    # Run cleanup in a new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.cleanup_expired_files())
                    finally:
                        loop.close()
                        self._cleanup_running = False
                        
                except Exception as e:
                    self.logger.error(f"Error in cleanup scheduler: {str(e)}")
                    self._cleanup_running = False
                    # Continue running even if cleanup fails
                    
            self.logger.info("Cleanup scheduler stopped")
        
        self._cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True, name="FileService-Cleanup")
        self._cleanup_thread.start()