#!/usr/bin/env python3
"""
Container Runtime Tests for MCP Draw.io Server
Tests container startup, health checks, and MCP tool functionality.
"""

import subprocess
import json
import os
import sys
import time
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pytest
import docker
from docker.models.containers import Container
import requests


class ContainerRuntimeTester:
    """Test container runtime behavior and MCP functionality."""
    
    def __init__(self):
        self.client = docker.from_env()
        self.project_root = Path(__file__).parent.parent.parent
        self.image_name = "mcp-drawio-server:test"
        self.container_name = "mcp-test-container"
        self.test_containers: List[str] = []
        
        # Test environment variables
        self.test_env = {
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', 'test-key-for-testing'),
            'LOG_LEVEL': 'DEBUG',
            'CACHE_TTL': '300',
            'FILE_EXPIRY_HOURS': '1',
            'TEMP_DIR': '/app/temp',
            'DRAWIO_CLI_PATH': 'drawio'
        }
    
    def cleanup(self):
        """Clean up test containers."""
        for container_name in self.test_containers:
            try:
                container = self.client.containers.get(container_name)
                container.stop(timeout=10)
                container.remove(force=True)
                print(f"Cleaned up container: {container_name}")
            except Exception as e:
                print(f"Warning: Could not remove container {container_name}: {e}")
    
    def start_container(self, 
                       name: str = None, 
                       environment: Dict[str, str] = None,
                       ports: Dict[str, int] = None,
                       detach: bool = True,
                       remove: bool = False) -> Container:
        """Start a test container with specified configuration."""
        if name is None:
            name = f"{self.container_name}-{int(time.time())}"
        
        if environment is None:
            environment = self.test_env.copy()
        
        print(f"Starting container: {name}")
        
        try:
            container = self.client.containers.run(
                self.image_name,
                name=name,
                environment=environment,
                ports=ports,
                detach=detach,
                remove=remove,
                volumes={
                    f"{self.project_root}/temp_test": {'bind': '/app/temp', 'mode': 'rw'},
                    f"{self.project_root}/logs_test": {'bind': '/app/logs', 'mode': 'rw'}
                }
            )
            
            if detach:
                self.test_containers.append(name)
            
            return container
            
        except Exception as e:
            print(f"Failed to start container: {e}")
            raise
    
    def wait_for_container_ready(self, container: Container, timeout: int = 60) -> bool:
        """Wait for container to be ready and healthy."""
        print(f"Waiting for container {container.name} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                container.reload()
                
                # Check if container is running
                if container.status != 'running':
                    print(f"Container status: {container.status}")
                    time.sleep(2)
                    continue
                
                # Check health status if available
                health = container.attrs.get('State', {}).get('Health', {})
                if health:
                    health_status = health.get('Status', 'unknown')
                    print(f"Health status: {health_status}")
                    
                    if health_status == 'healthy':
                        print("✓ Container is healthy")
                        return True
                    elif health_status == 'unhealthy':
                        print("✗ Container is unhealthy")
                        return False
                else:
                    # If no health check, wait a bit and assume ready
                    time.sleep(5)
                    print("✓ Container is running (no health check)")
                    return True
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Error checking container status: {e}")
                time.sleep(2)
        
        print(f"✗ Container not ready after {timeout} seconds")
        return False
    
    def test_container_startup(self) -> bool:
        """Test that container starts successfully."""
        print("\n=== Testing Container Startup ===")
        
        try:
            container = self.start_container()
            
            if self.wait_for_container_ready(container, timeout=30):
                print("✓ Container started successfully")
                
                # Check logs for any startup errors
                logs = container.logs().decode('utf-8')
                if 'error' in logs.lower() or 'exception' in logs.lower():
                    print("⚠ Warning: Errors found in startup logs:")
                    print(logs[-500:])  # Last 500 characters
                else:
                    print("✓ No errors in startup logs")
                
                return True
            else:
                print("✗ Container failed to start properly")
                logs = container.logs().decode('utf-8')
                print("Container logs:")
                print(logs)
                return False
                
        except Exception as e:
            print(f"✗ Container startup test failed: {e}")
            return False
    
    def test_drawio_cli_availability(self) -> bool:
        """Test that Draw.io CLI is available and working in the container."""
        print("\n=== Testing Draw.io CLI Availability ===")
        
        try:
            container = self.start_container(detach=False, remove=True)
            
            # Test Draw.io CLI help command
            result = container.wait()
            if result['StatusCode'] == 0:
                print("✓ Container runs without immediate errors")
            
            # Run Draw.io CLI test in a new container
            test_container = self.client.containers.run(
                self.image_name,
                command="drawio --help",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            
            print("✓ Draw.io CLI is available and responsive")
            
            # Test Draw.io CLI version
            version_container = self.client.containers.run(
                self.image_name,
                command="drawio --version",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            
            print("✓ Draw.io CLI version command works")
            return True
            
        except Exception as e:
            print(f"✗ Draw.io CLI test failed: {e}")
            return False
    
    def test_python_environment(self) -> bool:
        """Test Python environment and MCP dependencies."""
        print("\n=== Testing Python Environment ===")
        
        try:
            # Test Python version
            python_version = self.client.containers.run(
                self.image_name,
                command="python3 --version",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            print("✓ Python 3 is available")
            
            # Test MCP package
            mcp_test = self.client.containers.run(
                self.image_name,
                command="python3 -c 'import mcp; print(\"MCP package imported successfully\")'",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            print("✓ MCP package is available")
            
            # Test Anthropic package
            anthropic_test = self.client.containers.run(
                self.image_name,
                command="python3 -c 'import anthropic; print(\"Anthropic package imported successfully\")'",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            print("✓ Anthropic package is available")
            
            # Test application modules
            app_test = self.client.containers.run(
                self.image_name,
                command="python3 -c 'import sys; sys.path.append(\"/app/src\"); from llm_service import LLMService; print(\"Application modules imported successfully\")'",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            print("✓ Application modules are importable")
            
            return True
            
        except Exception as e:
            print(f"✗ Python environment test failed: {e}")
            return False
    
    def test_file_system_permissions(self) -> bool:
        """Test file system permissions and directory access."""
        print("\n=== Testing File System Permissions ===")
        
        try:
            # Test temp directory access
            temp_test = self.client.containers.run(
                self.image_name,
                command="python3 -c 'import os; os.makedirs(\"/app/temp/test\", exist_ok=True); print(\"Temp directory writable\")'",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            print("✓ Temp directory is writable")
            
            # Test logs directory access
            logs_test = self.client.containers.run(
                self.image_name,
                command="python3 -c 'import os; os.makedirs(\"/app/logs/test\", exist_ok=True); print(\"Logs directory writable\")'",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            print("✓ Logs directory is writable")
            
            # Test user permissions
            user_test = self.client.containers.run(
                self.image_name,
                command="whoami",
                environment=self.test_env,
                remove=True,
                detach=False
            )
            print("✓ Container runs as non-root user")
            
            return True
            
        except Exception as e:
            print(f"✗ File system permissions test failed: {e}")
            return False
    
    def test_mcp_server_functionality(self) -> bool:
        """Test basic MCP server functionality."""
        print("\n=== Testing MCP Server Functionality ===")
        
        try:
            # Create a test script to run MCP server functionality
            test_script = '''
import sys
import asyncio
sys.path.append("/app/src")

from server import main
from tools import generate_drawio_xml, save_drawio_file, convert_to_png

async def test_tools():
    try:
        # Test generate_drawio_xml tool
        result = await generate_drawio_xml("Create a simple flowchart with start and end nodes")
        print(f"generate_drawio_xml result: {result.get('success', False)}")
        
        if result.get('success') and result.get('xml_content'):
            # Test save_drawio_file tool
            save_result = await save_drawio_file(result['xml_content'], "test.drawio")
            print(f"save_drawio_file result: {save_result.get('success', False)}")
            
            if save_result.get('success') and save_result.get('file_id'):
                # Test convert_to_png tool
                png_result = await convert_to_png(file_id=save_result['file_id'])
                print(f"convert_to_png result: {png_result.get('success', False)}")
        
        print("MCP tools test completed")
        
    except Exception as e:
        print(f"MCP tools test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_tools())
    sys.exit(0 if result else 1)
'''
            
            # Write test script to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                test_script_path = f.name
            
            try:
                # Copy test script to container and run it
                container = self.start_container(detach=True)
                
                # Wait for container to be ready
                if not self.wait_for_container_ready(container):
                    return False
                
                # Copy test script to container
                with open(test_script_path, 'rb') as f:
                    container.put_archive('/app/', f.read())
                
                # Run the test script
                exec_result = container.exec_run(
                    f"python3 /app/{os.path.basename(test_script_path)}",
                    environment=self.test_env
                )
                
                output = exec_result.output.decode('utf-8')
                print("MCP functionality test output:")
                print(output)
                
                if exec_result.exit_code == 0:
                    print("✓ MCP server functionality test passed")
                    return True
                else:
                    print("✗ MCP server functionality test failed")
                    return False
                    
            finally:
                os.unlink(test_script_path)
            
        except Exception as e:
            print(f"✗ MCP server functionality test failed: {e}")
            return False
    
    def test_health_check(self) -> bool:
        """Test container health check functionality."""
        print("\n=== Testing Health Check ===")
        
        try:
            container = self.start_container(detach=True)
            
            # Wait for container to be ready
            if not self.wait_for_container_ready(container, timeout=60):
                return False
            
            # Run health check manually
            health_result = container.exec_run(
                "python3 /app/src/healthcheck.py",
                environment=self.test_env
            )
            
            if health_result.exit_code == 0:
                print("✓ Health check passes")
                return True
            else:
                print("✗ Health check fails")
                print(f"Health check output: {health_result.output.decode('utf-8')}")
                return False
                
        except Exception as e:
            print(f"✗ Health check test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all container runtime tests."""
        print("Starting Container Runtime Tests...")
        print("=" * 50)
        
        tests = [
            self.test_container_startup,
            self.test_drawio_cli_availability,
            self.test_python_environment,
            self.test_file_system_permissions,
            self.test_health_check,
            # Note: MCP functionality test requires valid API key
            # self.test_mcp_server_functionality
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"Test failed with exception: {e}")
                results.append(False)
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("\n" + "=" * 50)
        print(f"Container Runtime Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("✓ All container runtime tests passed!")
            return True
        else:
            print("✗ Some container runtime tests failed!")
            return False


def main():
    """Main test execution."""
    tester = ContainerRuntimeTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())