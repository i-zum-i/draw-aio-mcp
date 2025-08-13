"""
Exception classes for the MCP server.
"""
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class LLMErrorCode(Enum):
    """Error codes for LLM service operations."""
    API_KEY_MISSING = "API_KEY_MISSING"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    INVALID_XML = "INVALID_XML"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class FileServiceErrorCode(Enum):
    """Error codes for file service operations."""
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_EXPIRED = "FILE_EXPIRED"
    INVALID_FILE_ID = "INVALID_FILE_ID"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    DISK_FULL = "DISK_FULL"
    INVALID_FILENAME = "INVALID_FILENAME"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    CLEANUP_ERROR = "CLEANUP_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ImageServiceErrorCode(Enum):
    """Error codes for image service operations."""
    CLI_NOT_AVAILABLE = "CLI_NOT_AVAILABLE"
    CLI_EXECUTION_ERROR = "CLI_EXECUTION_ERROR"
    INVALID_INPUT_FILE = "INVALID_INPUT_FILE"
    OUTPUT_FILE_ERROR = "OUTPUT_FILE_ERROR"
    CONVERSION_TIMEOUT = "CONVERSION_TIMEOUT"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class MCPServerErrorCode(Enum):
    """Error codes for MCP server operations."""
    INVALID_REQUEST = "INVALID_REQUEST"
    METHOD_NOT_FOUND = "METHOD_NOT_FOUND"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    INITIALIZATION_ERROR = "INITIALIZATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class MCPServerError(Exception):
    """Base exception class for MCP server errors."""
    
    def __init__(
        self,
        message: str,
        code: str,
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.original_error = original_error
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        self.name = self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": self.message,
            "error_code": self.code,
            "timestamp": self.timestamp.isoformat() + "Z",
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None
        }
    
    def log_error(self, logger: logging.Logger, level: int = logging.ERROR):
        """Log the error with appropriate context."""
        extra_fields = {
            "error_code": self.code,
            "error_details": self.details,
            "original_error": str(self.original_error) if self.original_error else None
        }
        
        # Add extra fields to log record
        logger.log(
            level,
            f"{self.name}: {self.message}",
            exc_info=self.original_error,
            extra={"extra_fields": extra_fields}
        )


class LLMError(MCPServerError):
    """Exception raised by LLM service operations."""
    
    def __init__(
        self, 
        message: str, 
        code: LLMErrorCode, 
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code.value, original_error, details)
        self.code = code


class FileServiceError(MCPServerError):
    """Exception raised by file service operations."""
    
    def __init__(
        self, 
        message: str, 
        code: FileServiceErrorCode, 
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code.value, original_error, details)
        self.code = code


class ImageServiceError(MCPServerError):
    """Exception raised by image service operations."""
    
    def __init__(
        self, 
        message: str, 
        code: ImageServiceErrorCode, 
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code.value, original_error, details)
        self.code = code


class ConfigurationError(MCPServerError):
    """Exception raised for configuration-related errors."""
    
    def __init__(
        self, 
        message: str, 
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, MCPServerErrorCode.CONFIGURATION_ERROR.value, original_error, details)


class InitializationError(MCPServerError):
    """Exception raised during server initialization."""
    
    def __init__(
        self, 
        message: str, 
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, MCPServerErrorCode.INITIALIZATION_ERROR.value, original_error, details)


def handle_exception(
    logger: logging.Logger,
    exception: Exception,
    context: str = "Unknown context",
    reraise: bool = True
) -> Optional[MCPServerError]:
    """
    Centralized exception handling utility.
    
    Args:
        logger: Logger instance to use for logging
        exception: The exception to handle
        context: Context description for logging
        reraise: Whether to reraise the exception after handling
        
    Returns:
        MCPServerError instance if not reraising, None otherwise
        
    Raises:
        The original exception if reraise is True
    """
    # Log the exception with context
    logger.error(f"Exception in {context}: {str(exception)}", exc_info=True)
    
    # Convert to appropriate MCPServerError if needed
    if isinstance(exception, MCPServerError):
        mcp_error = exception
    elif isinstance(exception, (ValueError, TypeError)):
        mcp_error = MCPServerError(
            message=f"Invalid input in {context}: {str(exception)}",
            code=MCPServerErrorCode.INVALID_PARAMETERS.value,
            original_error=exception
        )
    elif isinstance(exception, FileNotFoundError):
        mcp_error = FileServiceError(
            message=f"File not found in {context}: {str(exception)}",
            code=FileServiceErrorCode.FILE_NOT_FOUND,
            original_error=exception
        )
    elif isinstance(exception, PermissionError):
        mcp_error = FileServiceError(
            message=f"Permission denied in {context}: {str(exception)}",
            code=FileServiceErrorCode.PERMISSION_DENIED,
            original_error=exception
        )
    else:
        mcp_error = MCPServerError(
            message=f"Unexpected error in {context}: {str(exception)}",
            code=MCPServerErrorCode.UNKNOWN_ERROR.value,
            original_error=exception
        )
    
    # Log the converted error
    mcp_error.log_error(logger)
    
    if reraise:
        raise mcp_error
    else:
        return mcp_error