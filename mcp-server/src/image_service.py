"""
Image Service for converting Draw.io files to PNG using Draw.io CLI.
"""
import asyncio
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from .exceptions import LLMError, LLMErrorCode


@dataclass
class ImageGenerationResult:
    """Result of image generation operation."""
    success: bool
    image_file_id: Optional[str] = None
    png_file_path: Optional[str] = None
    base64_content: Optional[str] = None
    error: Optional[str] = None
    fallback_message: Optional[str] = None
    cli_available: bool = True


@dataclass
class CLIAvailabilityResult:
    """Result of CLI availability check."""
    available: bool
    version: Optional[str] = None
    error: Optional[str] = None
    installation_hint: Optional[str] = None


class ImageServiceError(Exception):
    """Exception raised by image service operations."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        self.name = "ImageServiceError"


class ImageService:
    """Service for converting Draw.io files to PNG images using Draw.io CLI."""
    
    def __init__(self, drawio_cli_path: str = "drawio", timeout_seconds: int = 30):
        """
        Initialize the image service.
        
        Args:
            drawio_cli_path: Path to Draw.io CLI executable.
            timeout_seconds: Timeout for CLI operations.
        """
        self.drawio_cli_path = drawio_cli_path
        self.timeout_seconds = timeout_seconds
        self.cli_availability_cache: Optional[Dict] = None
        self.cli_cache_ttl = 5 * 60  # 5 minutes cache
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    async def generate_png(self, drawio_file_path: str, output_dir: Optional[str] = None, 
                          include_base64: bool = False) -> ImageGenerationResult:
        """
        Generate PNG image from Draw.io file using CLI with fallback handling.
        
        Args:
            drawio_file_path: Path to the .drawio file.
            output_dir: Optional output directory. If None, uses same directory as input.
            include_base64: Whether to include Base64 encoded content in result.
            
        Returns:
            ImageGenerationResult with success status, file information, and fallback handling.
        """
        try:
            # Validate input file
            input_path = Path(drawio_file_path)
            if not input_path.exists():
                return ImageGenerationResult(
                    success=False,
                    error=f"Draw.io file not found: {drawio_file_path}",
                    cli_available=False
                )
            
            if not input_path.suffix.lower() == '.drawio':
                return ImageGenerationResult(
                    success=False,
                    error=f"Invalid file type. Expected .drawio file, got: {input_path.suffix}",
                    cli_available=False
                )
            
            # Check CLI availability
            cli_check = await self.is_drawio_cli_available()
            if not cli_check.available:
                # Generate comprehensive fallback message
                fallback_message = await self.get_fallback_message()
                
                # Log the CLI unavailability for troubleshooting
                self.logger.warning(f"Draw.io CLI not available for PNG conversion: {cli_check.error}")
                
                return ImageGenerationResult(
                    success=False,
                    error=f"Draw.io CLI not available: {cli_check.error or 'Unknown error'}",
                    fallback_message=fallback_message,
                    cli_available=False
                )
            
            # Determine output path
            if output_dir:
                output_directory = Path(output_dir)
                output_directory.mkdir(parents=True, exist_ok=True)
                output_path = output_directory / f"{input_path.stem}.png"
            else:
                output_path = input_path.parent / f"{input_path.stem}.png"
            
            # Remove existing output file if it exists
            if output_path.exists():
                output_path.unlink()
            
            # Execute Draw.io CLI conversion
            success = await self._execute_drawio_cli(str(input_path), str(output_path))
            
            if not success:
                return ImageGenerationResult(
                    success=False,
                    error="Draw.io CLI conversion failed",
                    cli_available=True
                )
            
            # Verify output file was created
            if not output_path.exists():
                return ImageGenerationResult(
                    success=False,
                    error="PNG file was not created by Draw.io CLI",
                    cli_available=True
                )
            
            # Generate file ID for the PNG
            png_file_id = f"png_{int(time.time())}_{output_path.stem}"
            
            # Optionally include Base64 content
            base64_content = None
            if include_base64:
                base64_content = await self.convert_to_base64(str(output_path))
                if base64_content is None:
                    self.logger.warning(f"Failed to convert PNG to Base64: {output_path}")
            
            self.logger.info(f"Successfully converted {drawio_file_path} to {output_path}")
            
            return ImageGenerationResult(
                success=True,
                image_file_id=png_file_id,
                png_file_path=str(output_path.absolute()),
                base64_content=base64_content,
                cli_available=True
            )
            
        except Exception as error:
            self.logger.error(f"Error generating PNG from {drawio_file_path}: {str(error)}")
            return ImageGenerationResult(
                success=False,
                error=f"Unexpected error during PNG generation: {str(error)}",
                cli_available=False
            )
    
    async def is_drawio_cli_available(self) -> CLIAvailabilityResult:
        """
        Check if Draw.io CLI is available and get version information.
        Uses caching to avoid repeated checks.
        
        Returns:
            CLIAvailabilityResult with availability status and version info.
        """
        try:
            # Check cache first
            if self._is_cli_cache_valid():
                cached_result = self.cli_availability_cache
                return CLIAvailabilityResult(
                    available=cached_result["available"],
                    version=cached_result.get("version"),
                    error=cached_result.get("error"),
                    installation_hint=cached_result.get("installation_hint")
                )
            
            # Check if CLI executable exists in PATH
            cli_path = shutil.which(self.drawio_cli_path)
            if not cli_path:
                result = CLIAvailabilityResult(
                    available=False,
                    error=f"Draw.io CLI '{self.drawio_cli_path}' not found in PATH",
                    installation_hint="Install Draw.io CLI with: npm install -g @drawio/drawio-desktop-cli"
                )
                self._cache_cli_result(result)
                return result
            
            # Try to get version information
            try:
                process = await asyncio.create_subprocess_exec(
                    self.drawio_cli_path, "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=10.0  # Short timeout for version check
                )
                
                if process.returncode == 0:
                    version = stdout.decode().strip()
                    result = CLIAvailabilityResult(
                        available=True,
                        version=version
                    )
                    self.logger.debug(f"Draw.io CLI available: {version}")
                else:
                    error_msg = stderr.decode().strip() if stderr else "Unknown error"
                    result = CLIAvailabilityResult(
                        available=False,
                        error=f"Draw.io CLI version check failed: {error_msg}",
                        installation_hint="Try reinstalling Draw.io CLI: npm install -g @drawio/drawio-desktop-cli"
                    )
                
            except asyncio.TimeoutError:
                result = CLIAvailabilityResult(
                    available=False,
                    error="Draw.io CLI version check timed out",
                    installation_hint="Draw.io CLI may be installed but not responding correctly"
                )
            except Exception as e:
                result = CLIAvailabilityResult(
                    available=False,
                    error=f"Error checking Draw.io CLI version: {str(e)}",
                    installation_hint="Install Draw.io CLI with: npm install -g @drawio/drawio-desktop-cli"
                )
            
            # Cache the result
            self._cache_cli_result(result)
            return result
            
        except Exception as error:
            self.logger.error(f"Unexpected error checking CLI availability: {str(error)}")
            result = CLIAvailabilityResult(
                available=False,
                error=f"Unexpected error: {str(error)}",
                installation_hint="Install Draw.io CLI with: npm install -g @drawio/drawio-desktop-cli"
            )
            self._cache_cli_result(result)
            return result
    
    async def get_fallback_message(self) -> str:
        """
        Get comprehensive fallback message when CLI is not available.
        
        Returns:
            Detailed message with installation instructions and alternatives.
        """
        cli_check = await self.is_drawio_cli_available()
        
        base_message = "🚫 Draw.io CLI is not available for PNG conversion."
        
        # Build detailed error information
        error_details = []
        if cli_check.error:
            error_details.append(f"Error: {cli_check.error}")
        
        # Enhanced installation instructions with dependency checking
        installation_steps = [
            "📋 To enable PNG conversion:",
            "",
            "🔍 Dependency Check:",
            "  Run: python -m src.server --check-all",
            "  This will show you exactly what's missing",
            "",
            "📦 Installation Steps:",
            "1. Install Node.js from https://nodejs.org/",
            "   • Minimum version: 14.0.0",
            "   • Verify: node --version",
            "",
            "2. Install Draw.io CLI:",
            "   npm install -g @drawio/drawio-desktop-cli",
            "",
            "3. Verify installation:",
            "   drawio --version",
            "",
            "4. Check dependencies again:",
            "   python -m src.server --check-dependencies",
            "",
            "5. Restart the MCP server"
        ]
        
        # Add custom installation hint if available
        if cli_check.installation_hint and "npm install" not in cli_check.installation_hint:
            installation_steps.insert(-2, f"   💡 Additional hint: {cli_check.installation_hint}")
        
        # Enhanced alternative options
        alternatives = [
            "",
            "🔄 Alternative options while setting up:",
            "• Save the .drawio file and open it manually in Draw.io Desktop",
            "• Use Draw.io web version (https://app.diagrams.net/)",
            "• Export PNG directly from Draw.io application",
            "• Use the XML content with other diagram tools",
            "",
            "🛠️ Troubleshooting:",
            "• Run: python -m src.server --setup-guide",
            "• Check system PATH includes npm global packages",
            "• On Windows: Restart terminal after Node.js installation",
            "• On macOS/Linux: May need to reload shell profile"
        ]
        
        # Combine all parts
        message_parts = [base_message]
        if error_details:
            message_parts.extend([""] + error_details)
        message_parts.extend([""] + installation_steps + alternatives)
        
        return "\n".join(message_parts)
    
    async def convert_to_base64(self, png_file_path: str) -> Optional[str]:
        """
        Convert PNG file to Base64 encoded string.
        
        Args:
            png_file_path: Path to the PNG file.
            
        Returns:
            Base64 encoded string or None if conversion fails.
        """
        try:
            png_path = Path(png_file_path)
            if not png_path.exists():
                self.logger.error(f"PNG file not found for Base64 conversion: {png_file_path}")
                return None
            
            # Check file size to avoid memory issues
            file_size = png_path.stat().st_size
            max_size = 10 * 1024 * 1024  # 10MB limit
            if file_size > max_size:
                self.logger.warning(f"PNG file too large for Base64 conversion: {file_size} bytes (max: {max_size})")
                return None
            
            # Read file and encode to Base64
            import base64
            
            def read_and_encode():
                with open(png_path, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            base64_content = await loop.run_in_executor(None, read_and_encode)
            
            self.logger.debug(f"Successfully converted {png_file_path} to Base64 ({len(base64_content)} chars)")
            return base64_content
            
        except Exception as error:
            self.logger.error(f"Error converting PNG to Base64: {str(error)}")
            return None
    
    async def save_png_with_metadata(self, png_file_path: str, file_service, 
                                   original_drawio_id: Optional[str] = None) -> Dict[str, any]:
        """
        Save PNG file with metadata management.
        
        Args:
            png_file_path: Path to the PNG file to save.
            file_service: FileService instance for file management.
            original_drawio_id: Optional ID of the original .drawio file.
            
        Returns:
            Dictionary with save result and metadata.
        """
        try:
            png_path = Path(png_file_path)
            if not png_path.exists():
                return {
                    "success": False,
                    "error": f"PNG file not found: {png_file_path}"
                }
            
            # Read PNG content
            with open(png_path, 'rb') as f:
                png_content = f.read()
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"diagram_{timestamp}.png"
            if original_drawio_id:
                filename = f"diagram_{original_drawio_id}_{timestamp}.png"
            
            # Save using FileService
            file_id = await file_service.save_file(
                content=png_content,
                filename=filename,
                file_type="png"
            )
            
            # Get file metadata
            file_info = await file_service.get_file_info(file_id)
            
            self.logger.info(f"Successfully saved PNG with ID: {file_id}")
            
            return {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "file_path": file_info.get("path") if file_info else None,
                "size_bytes": len(png_content),
                "original_drawio_id": original_drawio_id,
                "created_at": file_info.get("created_at") if file_info else None,
                "expires_at": file_info.get("expires_at") if file_info else None
            }
            
        except Exception as error:
            self.logger.error(f"Error saving PNG with metadata: {str(error)}")
            return {
                "success": False,
                "error": f"Failed to save PNG: {str(error)}"
            }
    
    async def _execute_drawio_cli(self, input_path: str, output_path: str) -> bool:
        """
        Execute Draw.io CLI to convert .drawio to PNG.
        
        Args:
            input_path: Path to input .drawio file.
            output_path: Path for output PNG file.
            
        Returns:
            True if conversion succeeded, False otherwise.
        """
        try:
            # Build CLI command
            # Format: drawio -x -f png -o output_path input_path
            cmd = [
                self.drawio_cli_path,
                "-x",  # Export mode
                "-f", "png",  # Format: PNG
                "-o", output_path,  # Output file
                input_path  # Input file
            ]
            
            self.logger.debug(f"Executing Draw.io CLI: {' '.join(cmd)}")
            
            # Execute command with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(input_path).parent  # Set working directory to input file directory
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                self.logger.error(f"Draw.io CLI timed out after {self.timeout_seconds} seconds")
                return False
            
            # Check return code
            if process.returncode != 0:
                error_output = stderr.decode() if stderr else "No error output"
                self.logger.error(f"Draw.io CLI failed with return code {process.returncode}: {error_output}")
                return False
            
            # Log success
            if stdout:
                output_text = stdout.decode().strip()
                if output_text:
                    self.logger.debug(f"Draw.io CLI output: {output_text}")
            
            return True
            
        except Exception as error:
            self.logger.error(f"Error executing Draw.io CLI: {str(error)}")
            return False
    
    def _is_cli_cache_valid(self) -> bool:
        """Check if CLI availability cache is still valid."""
        if not self.cli_availability_cache:
            return False
        
        cache_age = time.time() - self.cli_availability_cache.get("timestamp", 0)
        return cache_age < self.cli_cache_ttl
    
    def _cache_cli_result(self, result: CLIAvailabilityResult) -> None:
        """Cache CLI availability result."""
        self.cli_availability_cache = {
            "available": result.available,
            "version": result.version,
            "error": result.error,
            "installation_hint": result.installation_hint,
            "timestamp": time.time()
        }
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get image service statistics.
        
        Returns:
            Dictionary with service statistics.
        """
        return {
            "cli_path": self.drawio_cli_path,
            "timeout_seconds": self.timeout_seconds,
            "cli_cache_valid": self._is_cli_cache_valid(),
            "cli_cached_available": self.cli_availability_cache.get("available") if self.cli_availability_cache else None,
            "cli_cached_version": self.cli_availability_cache.get("version") if self.cli_availability_cache else None,
            "fallback_enabled": True,
            "base64_support": True
        }
    
    async def get_service_status(self) -> Dict[str, any]:
        """
        Get comprehensive service status including fallback capabilities.
        
        Returns:
            Dictionary with detailed service status.
        """
        try:
            cli_check = await self.is_drawio_cli_available()
            
            status = {
                "service_name": "ImageService",
                "status": "operational" if cli_check.available else "degraded",
                "cli_available": cli_check.available,
                "cli_version": cli_check.version,
                "cli_error": cli_check.error,
                "fallback_available": True,
                "base64_support": True,
                "features": {
                    "png_conversion": cli_check.available,
                    "fallback_messages": True,
                    "base64_encoding": True,
                    "file_metadata": True,
                    "comprehensive_workflow": True
                },
                "configuration": {
                    "cli_path": self.drawio_cli_path,
                    "timeout_seconds": self.timeout_seconds,
                    "cache_ttl_seconds": self.cli_cache_ttl
                }
            }
            
            if not cli_check.available:
                status["fallback_message"] = await self.get_fallback_message()
                status["alternatives"] = await self._get_alternative_options()
                status["troubleshooting"] = await self._get_troubleshooting_info()
            
            return status
            
        except Exception as error:
            self.logger.error(f"Error getting service status: {str(error)}")
            return {
                "service_name": "ImageService",
                "status": "error",
                "error": str(error),
                "fallback_available": True
            }
    
    def clear_cli_cache(self) -> None:
        """Clear CLI availability cache to force re-check."""
        self.cli_availability_cache = None
        self.logger.debug("Cleared CLI availability cache")
    
    async def generate_png_with_fallback(self, drawio_file_path: str, 
                                       output_dir: Optional[str] = None,
                                       include_base64: bool = False,
                                       file_service=None) -> Dict[str, any]:
        """
        Complete PNG generation workflow with comprehensive fallback handling.
        
        Args:
            drawio_file_path: Path to the .drawio file.
            output_dir: Optional output directory.
            include_base64: Whether to include Base64 encoded content.
            file_service: Optional FileService for managed file saving.
            
        Returns:
            Comprehensive result dictionary with success/failure status and fallback options.
        """
        try:
            # Generate PNG using CLI
            result = await self.generate_png(
                drawio_file_path=drawio_file_path,
                output_dir=output_dir,
                include_base64=include_base64
            )
            
            # If successful, optionally save with metadata
            if result.success and file_service and result.png_file_path:
                save_result = await self.save_png_with_metadata(
                    png_file_path=result.png_file_path,
                    file_service=file_service,
                    original_drawio_id=Path(drawio_file_path).stem
                )
                
                return {
                    "success": True,
                    "conversion_result": {
                        "image_file_id": result.image_file_id,
                        "png_file_path": result.png_file_path,
                        "base64_content": result.base64_content,
                        "cli_available": result.cli_available
                    },
                    "save_result": save_result,
                    "message": "PNG conversion completed successfully"
                }
            elif result.success:
                return {
                    "success": True,
                    "conversion_result": {
                        "image_file_id": result.image_file_id,
                        "png_file_path": result.png_file_path,
                        "base64_content": result.base64_content,
                        "cli_available": result.cli_available
                    },
                    "message": "PNG conversion completed successfully"
                }
            else:
                # Handle failure with fallback information
                return {
                    "success": False,
                    "error": result.error,
                    "cli_available": result.cli_available,
                    "fallback_message": result.fallback_message,
                    "alternatives": await self._get_alternative_options(),
                    "troubleshooting": await self._get_troubleshooting_info()
                }
                
        except Exception as error:
            self.logger.error(f"Error in PNG generation workflow: {str(error)}")
            return {
                "success": False,
                "error": f"Unexpected error in PNG generation workflow: {str(error)}",
                "cli_available": False,
                "fallback_message": await self.get_fallback_message(),
                "alternatives": await self._get_alternative_options()
            }
    
    async def _get_alternative_options(self) -> Dict[str, str]:
        """Get alternative options when CLI is not available."""
        return {
            "manual_export": "Open the .drawio file in Draw.io Desktop and export as PNG manually",
            "web_version": "Use Draw.io web version at https://app.diagrams.net/ to open and export",
            "xml_content": "Use the XML content with other compatible diagram tools",
            "save_for_later": "Save the .drawio file and convert when CLI becomes available"
        }
    
    async def _get_troubleshooting_info(self) -> Dict[str, str]:
        """Get troubleshooting information for common issues."""
        cli_check = await self.is_drawio_cli_available()
        
        troubleshooting = {
            "check_installation": "Verify Draw.io CLI is installed: drawio --version",
            "check_path": "Ensure Draw.io CLI is in your system PATH",
            "reinstall": "Try reinstalling: npm uninstall -g @drawio/drawio-desktop-cli && npm install -g @drawio/drawio-desktop-cli"
        }
        
        if cli_check.error:
            if "not found" in cli_check.error.lower():
                troubleshooting["primary_issue"] = "Draw.io CLI is not installed or not in PATH"
            elif "timeout" in cli_check.error.lower():
                troubleshooting["primary_issue"] = "Draw.io CLI is not responding (may be corrupted installation)"
            elif "permission" in cli_check.error.lower():
                troubleshooting["primary_issue"] = "Permission denied accessing Draw.io CLI"
            else:
                troubleshooting["primary_issue"] = f"CLI error: {cli_check.error}"
        
        return troubleshooting