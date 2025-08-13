"""
Pytest configuration and shared fixtures.
"""
import asyncio
import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import pytest

# Import these only when needed to avoid import errors
# from src.llm_service import LLMService
# from src.file_service import FileService
from tests.fixtures.sample_xml import VALID_DRAWIO_XML, MINIMAL_VALID_XML
from tests.fixtures.sample_prompts import SIMPLE_FLOWCHART_PROMPT


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_anthropic_response():
    """Create a mock Anthropic API response."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.type = "text"
    mock_content.text = f'''```xml
{MINIMAL_VALID_XML}
```'''
    mock_response.content = [mock_content]
    return mock_response


@pytest.fixture
def mock_anthropic_response_direct_xml():
    """Create a mock Anthropic API response with direct XML (no code blocks)."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.type = "text"
    mock_content.text = MINIMAL_VALID_XML
    mock_response.content = [mock_content]
    return mock_response


@pytest.fixture
def mock_anthropic_response_complex():
    """Create a mock Anthropic API response with complex XML."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.type = "text"
    mock_content.text = f'''```xml
{VALID_DRAWIO_XML}
```'''
    mock_response.content = [mock_content]
    return mock_response


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    mock_client = Mock()
    mock_messages = Mock()
    mock_client.messages = mock_messages
    return mock_client


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def llm_service_with_mock():
    """Create LLMService with mocked Anthropic client."""
    from src.llm_service import LLMService
    
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        service = LLMService(api_key="sk-ant-test-key")
        service.client = mock_client
        
        yield service, mock_client


@pytest.fixture
def file_service_isolated():
    """Create an isolated FileService instance for testing."""
    from src.file_service import FileService
    
    # Reset singleton state
    FileService._instance = None
    FileService._initialized = False
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('src.file_service.FileService._start_cleanup_scheduler'):
            service = FileService(temp_dir=temp_dir, file_expiry_hours=24)
            yield service


@pytest.fixture
def file_service_with_cleanup():
    """Create FileService with real cleanup scheduler for testing."""
    from src.file_service import FileService
    
    # Reset singleton state
    FileService._instance = None
    FileService._initialized = False
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FileService(
            temp_dir=temp_dir, 
            file_expiry_hours=24,
            cleanup_interval_minutes=1  # Short interval for testing
        )
        yield service
        # Clean up
        service.stop_cleanup_scheduler()


@pytest.fixture
def sample_xml_content():
    """Provide sample XML content for testing."""
    return MINIMAL_VALID_XML


@pytest.fixture
def sample_complex_xml_content():
    """Provide complex sample XML content for testing."""
    return VALID_DRAWIO_XML


@pytest.fixture
def sample_prompt():
    """Provide sample prompt for testing."""
    return SIMPLE_FLOWCHART_PROMPT


@pytest.fixture
def mock_time():
    """Mock time functions for testing time-dependent functionality."""
    with patch('time.time') as mock_time_func:
        # Start with a fixed timestamp
        base_time = 1640995200.0  # 2022-01-01 00:00:00 UTC
        mock_time_func.return_value = base_time
        yield mock_time_func


@pytest.fixture
def mock_datetime():
    """Mock datetime for testing time-dependent functionality."""
    with patch('src.file_service.datetime') as mock_dt:
        # Fixed datetime for consistent testing
        fixed_datetime = datetime(2022, 1, 1, 0, 0, 0)
        mock_dt.now.return_value = fixed_datetime
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock_dt


@pytest.fixture
def create_temp_file():
    """Factory fixture to create temporary files for testing."""
    created_files = []
    
    def _create_temp_file(content: str, suffix: str = ".txt") -> str:
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = f.name
        created_files.append(temp_path)
        return temp_path
    
    yield _create_temp_file
    
    # Cleanup
    for file_path in created_files:
        try:
            Path(file_path).unlink()
        except FileNotFoundError:
            pass


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing logging functionality."""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    try:
        from src.file_service import FileService
        # Reset FileService singleton
        FileService._instance = None
        FileService._initialized = False
        
        yield
        
        # Clean up any remaining instances
        if FileService._instance:
            try:
                FileService._instance.stop_cleanup_scheduler()
            except:
                pass
            FileService._instance = None
            FileService._initialized = False
    except ImportError:
        # If imports fail, just yield
        yield


@pytest.fixture
def mock_threading():
    """Mock threading for testing scheduler functionality."""
    with patch('threading.Thread') as mock_thread_class:
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        mock_thread_class.return_value = mock_thread
        yield mock_thread_class, mock_thread


@pytest.fixture
def mock_os_chmod():
    """Mock os.chmod for testing file permissions."""
    with patch('os.chmod') as mock_chmod:
        yield mock_chmod


@pytest.fixture
def mock_pathlib_operations():
    """Mock pathlib operations for testing file system interactions."""
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.unlink') as mock_unlink, \
         patch('pathlib.Path.stat') as mock_stat:
        
        # Default behaviors
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1024)
        
        yield {
            'mkdir': mock_mkdir,
            'exists': mock_exists,
            'unlink': mock_unlink,
            'stat': mock_stat
        }


class AsyncContextManager:
    """Helper class for testing async context managers."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context_manager():
    """Factory for creating async context managers in tests."""
    return AsyncContextManager


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark tests that use real file operations as slow
        if any(fixture in item.fixturenames for fixture in ['file_service_with_cleanup']):
            item.add_marker(pytest.mark.slow)