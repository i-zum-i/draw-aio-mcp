"""
Configuration management for the MCP Draw.io Server.
"""
import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(Enum):
    """Supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """Supported log formats."""
    TEXT = "text"
    JSON = "json"


@dataclass
class MCPServerConfig:
    """Configuration for the MCP Draw.io Server."""
    
    # Required settings
    anthropic_api_key: str
    
    # File and storage settings
    temp_dir: str = "./temp"
    file_expiry_hours: int = 24
    cleanup_interval_minutes: int = 60
    
    # LLM service settings
    cache_ttl: int = 3600  # 1 hour
    max_cache_size: int = 100
    
    # Image service settings
    drawio_cli_path: str = "drawio"
    
    # Server settings
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    
    # Logging settings
    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.TEXT
    
    # Development settings
    debug: bool = False
    development_mode: bool = False
    
    # Health check settings
    health_check_interval: int = 300  # 5 minutes
    
    # Additional metadata
    server_name: str = "mcp-drawio-server"
    server_version: str = "1.0.0"
    protocol_version: str = "2025-06-18"  # Updated to latest MCP protocol version
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
        self._ensure_directories()
    
    def _validate_config(self):
        """Validate configuration values."""
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        if not self.anthropic_api_key.startswith("sk-ant-"):
            raise ValueError("ANTHROPIC_API_KEY must start with 'sk-ant-'")
        
        if self.cache_ttl <= 0:
            raise ValueError("cache_ttl must be positive")
        
        if self.max_cache_size <= 0:
            raise ValueError("max_cache_size must be positive")
        
        if self.file_expiry_hours <= 0:
            raise ValueError("file_expiry_hours must be positive")
        
        if self.cleanup_interval_minutes <= 0:
            raise ValueError("cleanup_interval_minutes must be positive")
        
        if self.max_concurrent_requests <= 0:
            raise ValueError("max_concurrent_requests must be positive")
        
        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be positive")
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        temp_path = Path(self.temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> 'MCPServerConfig':
        """Create configuration from environment variables."""
        # Required settings
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        # Parse log level
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        try:
            log_level = LogLevel(log_level_str)
        except ValueError:
            log_level = LogLevel.INFO
        
        # Parse log format
        log_format_str = os.getenv("LOG_FORMAT", "text").lower()
        try:
            log_format = LogFormat(log_format_str)
        except ValueError:
            log_format = LogFormat.TEXT
        
        # Parse boolean values
        debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        development_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() in ("true", "1", "yes", "on")
        
        return cls(
            anthropic_api_key=anthropic_api_key,
            temp_dir=os.getenv("TEMP_DIR", "./temp"),
            file_expiry_hours=int(os.getenv("FILE_EXPIRY_HOURS", "24")),
            cleanup_interval_minutes=int(os.getenv("CLEANUP_INTERVAL_MINUTES", "60")),
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            max_cache_size=int(os.getenv("MAX_CACHE_SIZE", "100")),
            drawio_cli_path=os.getenv("DRAWIO_CLI_PATH", "drawio"),
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            log_level=log_level,
            log_format=log_format,
            debug=debug,
            development_mode=development_mode,
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "300")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "server_name": self.server_name,
            "server_version": self.server_version,
            "protocol_version": self.protocol_version,
            "temp_dir": self.temp_dir,
            "file_expiry_hours": self.file_expiry_hours,
            "cleanup_interval_minutes": self.cleanup_interval_minutes,
            "cache_ttl": self.cache_ttl,
            "max_cache_size": self.max_cache_size,
            "drawio_cli_path": self.drawio_cli_path,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            "log_level": self.log_level.value,
            "log_format": self.log_format.value,
            "debug": self.debug,
            "development_mode": self.development_mode,
            "health_check_interval": self.health_check_interval,
        }


def setup_logging(config: MCPServerConfig) -> logging.Logger:
    """
    Set up logging configuration based on server config.
    
    Args:
        config: Server configuration
        
    Returns:
        Configured logger instance
    """
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    log_level = getattr(logging, config.log_level.value)
    
    # Configure formatter based on format preference
    if config.log_format == LogFormat.JSON:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Create and return server-specific logger
    logger = logging.getLogger("mcp-drawio-server")
    logger.setLevel(log_level)
    
    return logger


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)