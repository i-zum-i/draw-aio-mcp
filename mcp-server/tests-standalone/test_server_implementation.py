"""
Test the enhanced MCP server implementation.
"""
import asyncio
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from src.server import MCPServer
from src.config import MCPServerConfig
from src.exceptions import ConfigurationError, InitializationError


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = MCPServerConfig(
            anthropic_api_key="sk-ant-test-key-12345",
            temp_dir=temp_dir,
            file_expiry_hours=24,
            cleanup_interval_minutes=60,
            cache_ttl=3600,
            max_cache_size=100,
            drawio_cli_path="drawio",
            max_concurrent_requests=10,
            request_timeout=30,
            debug=True,
            development_mode=True
        )
        yield config


@pytest.fixture
def mock_server(mock_config):
    """Create a mock server instance."""
    return MCPServer(config=mock_config)


async def test_server_initialization(mock_server):
    """Test server initialization."""
    print("Testing server initialization...")
    
    # Server should not be initialized yet
    assert not mock_server._initialized
    
    # Mock the service initialization to avoid actual API calls
    with patch.object(mock_server, '_initialize_services') as mock_init_services, \
         patch.object(mock_server, '_start_background_tasks') as mock_start_tasks, \
         patch.object(mock_server.health_checker, 'check_all') as mock_health_check:
        
        mock_health_check.return_value = {"status": "healthy"}
        
        # Initialize server
        await mock_server.initialize()
        
        # Verify initialization
        assert mock_server._initialized
        mock_init_services.assert_called_once()
        mock_start_tasks.assert_called_once()
        mock_health_check.assert_called_once()
    
    print("✅ Server initialization test passed")


async def test_configuration_validation():
    """Test configuration validation."""
    print("Testing configuration validation...")
    
    # Test missing API key
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
        MCPServerConfig(anthropic_api_key="")
    
    # Test invalid API key format
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY must start with 'sk-ant-'"):
        MCPServerConfig(anthropic_api_key="invalid-key")
    
    # Test invalid cache settings
    with pytest.raises(ValueError, match="cache_ttl must be positive"):
        MCPServerConfig(
            anthropic_api_key="sk-ant-test-key",
            cache_ttl=0
        )
    
    print("✅ Configuration validation test passed")


async def test_request_handling(mock_server):
    """Test basic request handling."""
    print("Testing request handling...")
    
    # Mock initialization
    with patch.object(mock_server, 'initialize') as mock_init:
        mock_init.return_value = None
        mock_server._initialized = True
        
        # Test initialize request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        with patch.object(mock_server.health_checker, 'get_readiness') as mock_readiness:
            mock_readiness.return_value = {"ready": True}
            
            response = await mock_server.handle_request(request)
            
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "result" in response
            assert response["result"]["serverInfo"]["name"] == mock_server.config.server_name
    
    print("✅ Request handling test passed")


async def test_tools_list(mock_server):
    """Test tools list functionality."""
    print("Testing tools list...")
    
    # Mock initialization
    mock_server._initialized = True
    
    with patch.object(mock_server, '_check_tool_dependencies') as mock_deps:
        mock_deps.return_value = True
        
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = await mock_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) == 3  # Three tools
        
        # Check tool names
        tool_names = [tool["name"] for tool in response["result"]["tools"]]
        expected_tools = ["generate-drawio-xml", "save-drawio-file", "convert-to-png"]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    print("✅ Tools list test passed")


async def test_error_handling(mock_server):
    """Test error handling."""
    print("Testing error handling...")
    
    # Test invalid request
    invalid_request = {
        "jsonrpc": "2.0",
        "id": 3,
        # Missing method
    }
    
    response = await mock_server.handle_request(invalid_request)
    
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 3
    assert "error" in response
    assert response["error"]["code"] == -32600  # Invalid request
    
    # Test method not found
    not_found_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "nonexistent/method",
        "params": {}
    }
    
    response = await mock_server.handle_request(not_found_request)
    
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 4
    assert "error" in response
    assert response["error"]["code"] == -32601  # Method not found
    
    print("✅ Error handling test passed")


async def test_health_checks(mock_server):
    """Test health check functionality."""
    print("Testing health checks...")
    
    mock_server._initialized = True
    
    # Mock health checker
    with patch.object(mock_server.health_checker, 'check_all') as mock_health, \
         patch.object(mock_server.health_checker, 'get_readiness') as mock_readiness, \
         patch.object(mock_server.health_checker, 'get_liveness') as mock_liveness:
        
        mock_health.return_value = {"status": "healthy", "checks": {}}
        mock_readiness.return_value = {"ready": True}
        mock_liveness.return_value = {"alive": True}
        
        # Test health check
        health_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "health",
            "params": {}
        }
        
        response = await mock_server.handle_request(health_request)
        assert response["result"]["status"] == "healthy"
        
        # Test readiness check
        readiness_request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "health/readiness",
            "params": {}
        }
        
        response = await mock_server.handle_request(readiness_request)
        assert response["result"]["ready"] is True
        
        # Test liveness check
        liveness_request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "health/liveness",
            "params": {}
        }
        
        response = await mock_server.handle_request(liveness_request)
        assert response["result"]["alive"] is True
    
    print("✅ Health checks test passed")


async def test_configuration_from_env():
    """Test configuration loading from environment variables."""
    print("Testing configuration from environment...")
    
    # Set environment variables
    env_vars = {
        "ANTHROPIC_API_KEY": "sk-ant-test-env-key",
        "TEMP_DIR": "./test_temp",
        "CACHE_TTL": "7200",
        "MAX_CACHE_SIZE": "200",
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true"
    }
    
    with patch.dict(os.environ, env_vars):
        config = MCPServerConfig.from_env()
        
        assert config.anthropic_api_key == "sk-ant-test-env-key"
        assert config.temp_dir == "./test_temp"
        assert config.cache_ttl == 7200
        assert config.max_cache_size == 200
        assert config.debug is True
    
    print("✅ Configuration from environment test passed")


def test_configuration_error_handling():
    """Test configuration error handling."""
    print("Testing configuration error handling...")
    
    # Test server creation with missing API key
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError):
            MCPServer()
    
    print("✅ Configuration error handling test passed")


async def test_server_lifecycle(mock_config):
    """Test server lifecycle management."""
    print("Testing server lifecycle...")
    
    server = MCPServer(config=mock_config)
    
    # Mock services to avoid actual initialization
    with patch.object(server, '_initialize_services') as mock_init_services, \
         patch.object(server, '_start_background_tasks') as mock_start_tasks, \
         patch.object(server.health_checker, 'check_all') as mock_health_check:
        
        mock_health_check.return_value = {"status": "healthy"}
        
        # Test initialization
        await server.initialize()
        assert server._initialized
        
        # Test shutdown
        await server.shutdown()
        assert server._shutdown_requested
    
    print("✅ Server lifecycle test passed")


if __name__ == "__main__":
    async def run_tests():
        """Run all tests."""
        print("🧪 Running MCP Server Implementation Tests\n")
        
        # Create mock config for tests that need it
        with tempfile.TemporaryDirectory() as temp_dir:
            config = MCPServerConfig(
                anthropic_api_key="sk-ant-test-key-12345",
                temp_dir=temp_dir,
                debug=True
            )
            server = MCPServer(config=config)
            
            # Run tests
            await test_server_initialization(server)
            await test_configuration_validation()
            await test_request_handling(server)
            await test_tools_list(server)
            await test_error_handling(server)
            await test_health_checks(server)
            await test_configuration_from_env()
            test_configuration_error_handling()
            await test_server_lifecycle(config)
        
        print("\n✅ All tests passed! MCP Server implementation is working correctly.")
    
    asyncio.run(run_tests())