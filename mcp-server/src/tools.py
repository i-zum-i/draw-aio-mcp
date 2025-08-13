"""
MCP Tools for Draw.io diagram generation.

This module provides the core tool implementations for the MCP server.
These tools are called by the official MCP server implementation.
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from .exceptions import LLMError, LLMErrorCode
from .llm_service import LLMService
from .file_service import FileService, FileServiceError
from .image_service import ImageService, ImageServiceError

# Configure logging
logger = logging.getLogger(__name__)


def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize and validate the input prompt.
    
    Args:
        prompt: Raw input prompt from user
        
    Returns:
        Sanitized prompt string
        
    Raises:
        ValueError: If prompt is invalid
    """
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Prompt must be a non-empty string")
    
    # Strip whitespace
    prompt = prompt.strip()
    
    if not prompt:
        raise ValueError("Prompt cannot be empty or only whitespace")
    
    # Check length limits (reasonable limits for diagram descriptions)
    if len(prompt) > 10000:
        raise ValueError("Prompt is too long (maximum 10,000 characters)")
    
    if len(prompt) < 5:
        raise ValueError("Prompt is too short (minimum 5 characters)")
    
    # Basic sanitization - remove potentially problematic characters
    # but preserve most characters for natural language descriptions
    # Remove control characters except newlines and tabs
    prompt = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', prompt)
    
    return prompt


async def generate_drawio_xml(prompt: str) -> Dict[str, Any]:
    """
    Generate Draw.io XML diagram from natural language prompt.
    
    This tool converts natural language descriptions into valid Draw.io XML format
    that can be opened in diagrams.net. It supports various diagram types including
    flowcharts, system diagrams, AWS architecture diagrams, and more.
    
    Args:
        prompt: Natural language description of the diagram to generate.
                Should be descriptive and specific about the elements and
                relationships you want in the diagram.
    
    Returns:
        Dictionary containing:
        - success (bool): Whether the generation was successful
        - xml_content (str): Valid Draw.io XML content (if successful)
        - error (str): Error message (if failed)
        - error_code (str): Specific error code for programmatic handling (if failed)
        - timestamp (str): ISO timestamp of the generation
    
    Example:
        >>> result = await generate_drawio_xml("Create a simple flowchart showing user login process")
        >>> if result["success"]:
        ...     print("Generated XML:", result["xml_content"])
        ... else:
        ...     print("Error:", result["error"])
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        # Input validation and sanitization
        try:
            sanitized_prompt = sanitize_prompt(prompt)
        except ValueError as e:
            return {
                "success": False,
                "xml_content": None,
                "error": f"Invalid input: {str(e)}",
                "error_code": "INVALID_INPUT",
                "timestamp": timestamp
            }
        
        # グローバルLLMサービスを使用
        from .server import llm_service
        if not llm_service:
            return {
                "success": False,
                "xml_content": None,
                "error": "LLMサービスが初期化されていません",
                "error_code": "SERVICE_NOT_INITIALIZED",
                "timestamp": timestamp
            }
        
        try:
            pass  # LLMサービスは既に初期化済み
        except Exception as e:
            return {
                "success": False,
                "xml_content": None,
                "error": str(e),
                "error_code": e.code.value,
                "timestamp": timestamp
            }
        
        # Generate XML
        try:
            logger.info(f"Generating Draw.io XML for prompt: {sanitized_prompt[:100]}...")
            xml_content = await llm_service.generate_drawio_xml(sanitized_prompt)
            
            logger.info("Successfully generated Draw.io XML")
            return {
                "success": True,
                "xml_content": xml_content,
                "error": None,
                "error_code": None,
                "timestamp": timestamp
            }
            
        except LLMError as e:
            logger.error(f"LLM service error: {e.code.value} - {str(e)}")
            return {
                "success": False,
                "xml_content": None,
                "error": str(e),
                "error_code": e.code.value,
                "timestamp": timestamp
            }
    
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in generate_drawio_xml: {str(e)}", exc_info=True)
        return {
            "success": False,
            "xml_content": None,
            "error": "An unexpected error occurred. Please try again.",
            "error_code": "UNKNOWN_ERROR",
            "timestamp": timestamp
        }


def validate_drawio_xml(xml_content: str) -> None:
    """
    Validate Draw.io XML content structure.
    
    Args:
        xml_content: XML content to validate
        
    Raises:
        ValueError: If XML structure is invalid
    """
    if not xml_content or not isinstance(xml_content, str):
        raise ValueError("XML content must be a non-empty string")
    
    xml_content = xml_content.strip()
    if not xml_content:
        raise ValueError("XML content cannot be empty or only whitespace")
    
    # Check for required Draw.io XML elements
    required_elements = ['mxfile', 'mxGraphModel', 'root']
    for element in required_elements:
        if f'<{element}' not in xml_content:
            raise ValueError(f"Invalid Draw.io XML: missing required element '{element}'")
    
    # Basic XML structure validation
    if not xml_content.startswith('<?xml') and not xml_content.startswith('<mxfile'):
        raise ValueError("Invalid XML: must start with XML declaration or mxfile element")


async def save_drawio_file(xml_content: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Save Draw.io XML content to a temporary file.
    
    This tool saves valid Draw.io XML content to a temporary file and returns
    a file ID that can be used to reference the file in other operations like
    PNG conversion. Files are automatically cleaned up after expiration.
    
    Args:
        xml_content: Valid Draw.io XML content to save. Must contain required
                    elements (mxfile, mxGraphModel, root).
        filename: Optional custom filename (without extension). If not provided,
                 a UUID-based filename will be generated.
    
    Returns:
        Dictionary containing:
        - success (bool): Whether the save operation was successful
        - file_id (str): Unique identifier for the saved file (if successful)
        - file_path (str): Absolute path to the saved file (if successful)
        - filename (str): Final filename used (if successful)
        - expires_at (str): ISO timestamp when file will expire (if successful)
        - error (str): Error message (if failed)
        - error_code (str): Specific error code for programmatic handling (if failed)
        - timestamp (str): ISO timestamp of the operation
    
    Example:
        >>> result = await save_drawio_file(xml_content, "my-diagram")
        >>> if result["success"]:
        ...     print("File saved with ID:", result["file_id"])
        ...     print("File path:", result["file_path"])
        ... else:
        ...     print("Error:", result["error"])
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        # Input validation
        try:
            validate_drawio_xml(xml_content)
        except ValueError as e:
            return {
                "success": False,
                "file_id": None,
                "file_path": None,
                "filename": None,
                "expires_at": None,
                "error": f"Invalid XML content: {str(e)}",
                "error_code": "INVALID_XML",
                "timestamp": timestamp
            }
        
        # Validate filename if provided
        if filename is not None:
            if not isinstance(filename, str):
                return {
                    "success": False,
                    "file_id": None,
                    "file_path": None,
                    "filename": None,
                    "expires_at": None,
                    "error": "Filename must be a string",
                    "error_code": "INVALID_FILENAME",
                    "timestamp": timestamp
                }
            
            filename = filename.strip()
            if not filename:
                filename = None  # Use default UUID-based naming
            elif len(filename) > 100:
                return {
                    "success": False,
                    "file_id": None,
                    "file_path": None,
                    "filename": None,
                    "expires_at": None,
                    "error": "Filename is too long (maximum 100 characters)",
                    "error_code": "INVALID_FILENAME",
                    "timestamp": timestamp
                }
        
        # グローバルファイルサービスを使用
        from .server import file_service
        if not file_service:
            return {
                "success": False,
                "file_id": None,
                "file_path": None,
                "filename": None,
                "expires_at": None,
                "error": "ファイルサービスが初期化されていません",
                "error_code": "SERVICE_NOT_INITIALIZED",
                "timestamp": timestamp
            }
        
        try:
            pass  # ファイルサービスは既に初期化済み
        except Exception as e:
            return {
                "success": False,
                "file_id": None,
                "file_path": None,
                "filename": None,
                "expires_at": None,
                "error": f"Failed to initialize file service: {str(e)}",
                "error_code": "SERVICE_ERROR",
                "timestamp": timestamp
            }
        
        # Save file
        try:
            logger.info(f"Saving Draw.io file with filename: {filename or 'auto-generated'}")
            file_id = await file_service.save_drawio_file(xml_content, filename)
            
            # Get file information for response
            file_info = await file_service.get_file_info(file_id)
            file_path = await file_service.get_file_path(file_id)
            
            logger.info(f"Successfully saved Draw.io file with ID: {file_id}")
            return {
                "success": True,
                "file_id": file_id,
                "file_path": file_path,
                "filename": file_info.original_name,
                "expires_at": file_info.expires_at.isoformat() + "Z",
                "error": None,
                "error_code": None,
                "timestamp": timestamp
            }
            
        except FileServiceError as e:
            logger.error(f"File service error: {str(e)}")
            return {
                "success": False,
                "file_id": None,
                "file_path": None,
                "filename": None,
                "expires_at": None,
                "error": str(e),
                "error_code": "FILE_SERVICE_ERROR",
                "timestamp": timestamp
            }
    
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in save_drawio_file: {str(e)}", exc_info=True)
        return {
            "success": False,
            "file_id": None,
            "file_path": None,
            "filename": None,
            "expires_at": None,
            "error": "An unexpected error occurred. Please try again.",
            "error_code": "UNKNOWN_ERROR",
            "timestamp": timestamp
        }


async def convert_to_png(file_id: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert Draw.io file to PNG image using Draw.io CLI.
    
    This tool converts a Draw.io (.drawio) file to PNG format using the Draw.io CLI.
    You can specify either a file_id (from save-drawio-file) or a direct file_path.
    If Draw.io CLI is not available, the tool provides comprehensive fallback information.
    
    Args:
        file_id: File ID returned from save-drawio-file tool (recommended).
        file_path: Direct path to .drawio file (alternative to file_id).
    
    Returns:
        Dictionary containing:
        - success (bool): Whether the conversion was successful
        - png_file_id (str): Unique identifier for the PNG file (if successful)
        - png_file_path (str): Absolute path to the PNG file (if successful)
        - base64_content (str): Base64 encoded PNG content (if successful, optional)
        - error (str): Error message (if failed)
        - error_code (str): Specific error code for programmatic handling (if failed)
        - cli_available (bool): Whether Draw.io CLI is available
        - fallback_message (str): Detailed fallback instructions (if CLI unavailable)
        - alternatives (dict): Alternative options when CLI is unavailable
        - timestamp (str): ISO timestamp of the operation
    
    Example:
        >>> # Using file_id from save-drawio-file
        >>> result = await convert_to_png(file_id="abc123")
        >>> if result["success"]:
        ...     print("PNG created:", result["png_file_path"])
        ... else:
        ...     print("Error:", result["error"])
        ...     if not result["cli_available"]:
        ...         print("Fallback:", result["fallback_message"])
        
        >>> # Using direct file path
        >>> result = await convert_to_png(file_path="/path/to/diagram.drawio")
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        # Input validation - must provide either file_id or file_path
        if not file_id and not file_path:
            return {
                "success": False,
                "png_file_id": None,
                "png_file_path": None,
                "base64_content": None,
                "error": "Must provide either file_id or file_path parameter",
                "error_code": "MISSING_PARAMETER",
                "cli_available": False,
                "fallback_message": None,
                "alternatives": None,
                "timestamp": timestamp
            }
        
        if file_id and file_path:
            return {
                "success": False,
                "png_file_id": None,
                "png_file_path": None,
                "base64_content": None,
                "error": "Cannot provide both file_id and file_path parameters",
                "error_code": "CONFLICTING_PARAMETERS",
                "cli_available": False,
                "fallback_message": None,
                "alternatives": None,
                "timestamp": timestamp
            }
        
        # グローバルサービスを使用
        from .server import file_service, image_service
        if not file_service or not image_service:
            return {
                "success": False,
                "png_file_id": None,
                "png_file_path": None,
                "base64_content": None,
                "error": "サービスが初期化されていません",
                "error_code": "SERVICE_NOT_INITIALIZED",
                "cli_available": False,
                "fallback_message": None,
                "alternatives": None,
                "timestamp": timestamp
            }
        
        try:
            pass  # サービスは既に初期化済み
        except Exception as e:
            return {
                "success": False,
                "png_file_id": None,
                "png_file_path": None,
                "base64_content": None,
                "error": f"Failed to initialize services: {str(e)}",
                "error_code": "SERVICE_INITIALIZATION_ERROR",
                "cli_available": False,
                "fallback_message": None,
                "alternatives": None,
                "timestamp": timestamp
            }
        
        # Resolve file path
        drawio_file_path = None
        original_file_id = None
        
        if file_id:
            try:
                # Validate file_id format
                if not isinstance(file_id, str) or not file_id.strip():
                    return {
                        "success": False,
                        "png_file_id": None,
                        "png_file_path": None,
                        "base64_content": None,
                        "error": "file_id must be a non-empty string",
                        "error_code": "INVALID_FILE_ID",
                        "cli_available": False,
                        "fallback_message": None,
                        "alternatives": None,
                        "timestamp": timestamp
                    }
                
                # Get file path from file service
                drawio_file_path = await file_service.get_file_path(file_id.strip())
                original_file_id = file_id.strip()
                logger.info(f"Resolved file_id '{file_id}' to path: {drawio_file_path}")
                
            except FileServiceError as e:
                return {
                    "success": False,
                    "png_file_id": None,
                    "png_file_path": None,
                    "base64_content": None,
                    "error": f"File not found or expired: {str(e)}",
                    "error_code": "FILE_NOT_FOUND",
                    "cli_available": False,
                    "fallback_message": None,
                    "alternatives": None,
                    "timestamp": timestamp
                }
        else:
            # Use provided file_path
            if not isinstance(file_path, str) or not file_path.strip():
                return {
                    "success": False,
                    "png_file_id": None,
                    "png_file_path": None,
                    "base64_content": None,
                    "error": "file_path must be a non-empty string",
                    "error_code": "INVALID_FILE_PATH",
                    "cli_available": False,
                    "fallback_message": None,
                    "alternatives": None,
                    "timestamp": timestamp
                }
            
            drawio_file_path = file_path.strip()
            logger.info(f"Using provided file path: {drawio_file_path}")
        
        # Validate that the file exists and is a .drawio file
        from pathlib import Path
        drawio_path = Path(drawio_file_path)
        
        if not drawio_path.exists():
            return {
                "success": False,
                "png_file_id": None,
                "png_file_path": None,
                "base64_content": None,
                "error": f"Draw.io file does not exist: {drawio_file_path}",
                "error_code": "FILE_NOT_FOUND",
                "cli_available": False,
                "fallback_message": None,
                "alternatives": None,
                "timestamp": timestamp
            }
        
        if not drawio_path.suffix.lower() == '.drawio':
            return {
                "success": False,
                "png_file_id": None,
                "png_file_path": None,
                "base64_content": None,
                "error": f"Invalid file type. Expected .drawio file, got: {drawio_path.suffix}",
                "error_code": "INVALID_FILE_TYPE",
                "cli_available": False,
                "fallback_message": None,
                "alternatives": None,
                "timestamp": timestamp
            }
        
        # Attempt PNG conversion using ImageService
        try:
            logger.info(f"Starting PNG conversion for: {drawio_file_path}")
            
            # Use the comprehensive PNG generation workflow
            conversion_result = await image_service.generate_png_with_fallback(
                drawio_file_path=drawio_file_path,
                output_dir=None,  # Use same directory as input
                include_base64=True,  # Include Base64 for convenience
                file_service=file_service  # For managed file saving
            )
            
            if conversion_result["success"]:
                # Successful conversion
                conv_data = conversion_result["conversion_result"]
                save_data = conversion_result.get("save_result", {})
                
                logger.info(f"Successfully converted {drawio_file_path} to PNG")
                
                return {
                    "success": True,
                    "png_file_id": save_data.get("file_id") or conv_data.get("image_file_id"),
                    "png_file_path": save_data.get("file_path") or conv_data.get("png_file_path"),
                    "base64_content": conv_data.get("base64_content"),
                    "error": None,
                    "error_code": None,
                    "cli_available": conv_data.get("cli_available", True),
                    "fallback_message": None,
                    "alternatives": None,
                    "timestamp": timestamp,
                    "metadata": {
                        "original_file_id": original_file_id,
                        "original_file_path": drawio_file_path,
                        "conversion_message": conversion_result.get("message"),
                        "file_size_bytes": save_data.get("size_bytes"),
                        "expires_at": save_data.get("expires_at")
                    }
                }
            else:
                # Conversion failed - return comprehensive error information
                logger.warning(f"PNG conversion failed for {drawio_file_path}: {conversion_result.get('error')}")
                
                return {
                    "success": False,
                    "png_file_id": None,
                    "png_file_path": None,
                    "base64_content": None,
                    "error": conversion_result.get("error", "PNG conversion failed"),
                    "error_code": "CONVERSION_FAILED",
                    "cli_available": conversion_result.get("cli_available", False),
                    "fallback_message": conversion_result.get("fallback_message"),
                    "alternatives": conversion_result.get("alternatives"),
                    "timestamp": timestamp,
                    "troubleshooting": conversion_result.get("troubleshooting"),
                    "metadata": {
                        "original_file_id": original_file_id,
                        "original_file_path": drawio_file_path
                    }
                }
                
        except ImageServiceError as e:
            logger.error(f"Image service error during PNG conversion: {str(e)}")
            
            # Get fallback information even when service fails
            try:
                fallback_message = await image_service.get_fallback_message()
                alternatives = await image_service._get_alternative_options()
            except:
                fallback_message = "Draw.io CLI is required for PNG conversion. Please install it with: npm install -g @drawio/drawio-desktop-cli"
                alternatives = {
                    "manual_export": "Open the .drawio file in Draw.io Desktop and export as PNG manually",
                    "web_version": "Use Draw.io web version at https://app.diagrams.net/"
                }
            
            return {
                "success": False,
                "png_file_id": None,
                "png_file_path": None,
                "base64_content": None,
                "error": f"Image service error: {str(e)}",
                "error_code": "IMAGE_SERVICE_ERROR",
                "cli_available": False,
                "fallback_message": fallback_message,
                "alternatives": alternatives,
                "timestamp": timestamp,
                "metadata": {
                    "original_file_id": original_file_id,
                    "original_file_path": drawio_file_path
                }
            }
    
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in convert_to_png: {str(e)}", exc_info=True)
        return {
            "success": False,
            "png_file_id": None,
            "png_file_path": None,
            "base64_content": None,
            "error": "An unexpected error occurred during PNG conversion. Please try again.",
            "error_code": "UNKNOWN_ERROR",
            "cli_available": False,
            "fallback_message": "Draw.io CLI is required for PNG conversion. Please install it with: npm install -g @drawio/drawio-desktop-cli",
            "alternatives": {
                "manual_export": "Open the .drawio file in Draw.io Desktop and export as PNG manually",
                "web_version": "Use Draw.io web version at https://app.diagrams.net/"
            },
            "timestamp": timestamp
        }


# Tool schema definitions are now handled in server.py using the official MCP SDK