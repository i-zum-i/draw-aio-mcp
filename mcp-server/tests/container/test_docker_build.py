#!/usr/bin/env python3
"""
Docker Build Tests for MCP Draw.io Server
Tests Docker image building, size optimization, and dependency verification.
"""

import subprocess
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pytest
import docker
from docker.models.images import Image
from docker.models.containers import Container


class DockerBuildTester:
    """Test Docker build process and image characteristics."""
    
    def __init__(self):
        self.client = docker.from_env()
        self.project_root = Path(__file__).parent.parent.parent
        self.image_name = "mcp-drawio-server"
        self.test_tag = "test"
        self.built_images: List[str] = []
        
    def cleanup(self):
        """Clean up test images and containers."""
        for image_tag in self.built_images:
            try:
                self.client.images.remove(image_tag, force=True)
                print(f"Cleaned up image: {image_tag}")
            except Exception as e:
                print(f"Warning: Could not remove image {image_tag}: {e}")
    
    def build_image(self, tag: str = None, build_args: Dict[str, str] = None) -> Image:
        """Build Docker image with specified tag and build arguments."""
        if tag is None:
            tag = f"{self.image_name}:{self.test_tag}"
        
        print(f"Building Docker image: {tag}")
        print(f"Build context: {self.project_root}")
        
        try:
            image, build_logs = self.client.images.build(
                path=str(self.project_root),
                tag=tag,
                buildargs=build_args or {},
                rm=True,
                forcerm=True,
                pull=True
            )
            
            # Print build logs for debugging
            for log in build_logs:
                if 'stream' in log:
                    print(log['stream'].strip())
            
            self.built_images.append(tag)
            return image
            
        except Exception as e:
            print(f"Build failed: {e}")
            raise
    
    def get_image_info(self, image: Image) -> Dict:
        """Get detailed information about the built image."""
        attrs = image.attrs
        
        return {
            'id': image.id,
            'size': attrs.get('Size', 0),
            'size_mb': round(attrs.get('Size', 0) / (1024 * 1024), 2),
            'created': attrs.get('Created'),
            'architecture': attrs.get('Architecture'),
            'os': attrs.get('Os'),
            'config': attrs.get('Config', {}),
            'layers': len(attrs.get('RootFS', {}).get('Layers', [])),
            'labels': attrs.get('Config', {}).get('Labels', {}),
            'env': attrs.get('Config', {}).get('Env', []),
            'cmd': attrs.get('Config', {}).get('Cmd', []),
            'entrypoint': attrs.get('Config', {}).get('Entrypoint', []),
            'exposed_ports': list(attrs.get('Config', {}).get('ExposedPorts', {}).keys()),
            'working_dir': attrs.get('Config', {}).get('WorkingDir'),
            'user': attrs.get('Config', {}).get('User')
        }
    
    def test_build_success(self) -> bool:
        """Test that Docker image builds successfully."""
        print("\n=== Testing Docker Build Success ===")
        
        try:
            image = self.build_image()
            info = self.get_image_info(image)
            
            print(f"✓ Image built successfully")
            print(f"  - Image ID: {info['id'][:12]}")
            print(f"  - Size: {info['size_mb']} MB")
            print(f"  - Layers: {info['layers']}")
            print(f"  - Architecture: {info['architecture']}")
            print(f"  - OS: {info['os']}")
            
            return True
            
        except Exception as e:
            print(f"✗ Build failed: {e}")
            return False
    
    def test_image_size(self, max_size_mb: int = 500) -> bool:
        """Test that image size is within acceptable limits."""
        print(f"\n=== Testing Image Size (max: {max_size_mb} MB) ===")
        
        try:
            image = self.client.images.get(f"{self.image_name}:{self.test_tag}")
            info = self.get_image_info(image)
            
            size_mb = info['size_mb']
            
            if size_mb <= max_size_mb:
                print(f"✓ Image size acceptable: {size_mb} MB (limit: {max_size_mb} MB)")
                return True
            else:
                print(f"✗ Image size too large: {size_mb} MB (limit: {max_size_mb} MB)")
                return False
                
        except Exception as e:
            print(f"✗ Size check failed: {e}")
            return False
    
    def test_dependencies(self) -> bool:
        """Test that required dependencies are installed in the image."""
        print("\n=== Testing Dependencies ===")
        
        required_commands = [
            'python3',
            'pip',
            'drawio',
            'node',
            'npm'
        ]
        
        required_python_packages = [
            'mcp',
            'anthropic',
            'httpx',
            'pathlib'
        ]
        
        try:
            image = self.client.images.get(f"{self.image_name}:{self.test_tag}")
            
            # Test system commands
            for cmd in required_commands:
                try:
                    container = self.client.containers.run(
                        image,
                        command=f"which {cmd}",
                        remove=True,
                        detach=False
                    )
                    print(f"✓ Command available: {cmd}")
                except Exception:
                    print(f"✗ Command missing: {cmd}")
                    return False
            
            # Test Python packages
            for package in required_python_packages:
                try:
                    container = self.client.containers.run(
                        image,
                        command=f"python3 -c 'import {package}; print(f\"{package} imported successfully\")'",
                        remove=True,
                        detach=False
                    )
                    print(f"✓ Python package available: {package}")
                except Exception:
                    print(f"✗ Python package missing: {package}")
                    return False
            
            # Test Draw.io CLI specifically
            try:
                container = self.client.containers.run(
                    image,
                    command="drawio --help",
                    remove=True,
                    detach=False
                )
                print("✓ Draw.io CLI working")
            except Exception:
                print("✗ Draw.io CLI not working")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Dependency check failed: {e}")
            return False
    
    def test_security_configuration(self) -> bool:
        """Test security-related image configuration."""
        print("\n=== Testing Security Configuration ===")
        
        try:
            image = self.client.images.get(f"{self.image_name}:{self.test_tag}")
            info = self.get_image_info(image)
            
            # Check non-root user
            user = info.get('user', '')
            if user and user != 'root' and user != '0':
                print(f"✓ Non-root user configured: {user}")
            else:
                print(f"✗ Root user or no user specified: {user}")
                return False
            
            # Check entrypoint for security
            entrypoint = info.get('entrypoint', [])
            if 'dumb-init' in ' '.join(entrypoint):
                print("✓ dumb-init entrypoint configured")
            else:
                print("✗ dumb-init entrypoint not found")
                return False
            
            # Check labels
            labels = info.get('labels', {})
            required_labels = ['maintainer', 'version', 'description']
            for label in required_labels:
                if any(label in key.lower() for key in labels.keys()):
                    print(f"✓ Label present: {label}")
                else:
                    print(f"✗ Label missing: {label}")
            
            return True
            
        except Exception as e:
            print(f"✗ Security check failed: {e}")
            return False
    
    def test_multi_stage_optimization(self) -> bool:
        """Test that multi-stage build optimization is working."""
        print("\n=== Testing Multi-Stage Build Optimization ===")
        
        try:
            image = self.client.images.get(f"{self.image_name}:{self.test_tag}")
            
            # Check that build tools are not present in final image
            build_tools = ['gcc', 'make', 'build-base']
            
            for tool in build_tools:
                try:
                    container = self.client.containers.run(
                        image,
                        command=f"which {tool}",
                        remove=True,
                        detach=False
                    )
                    print(f"✗ Build tool found in final image: {tool}")
                    return False
                except Exception:
                    print(f"✓ Build tool properly removed: {tool}")
            
            # Check that Python virtual environment is properly copied
            try:
                container = self.client.containers.run(
                    image,
                    command="ls -la /opt/venv/bin/python",
                    remove=True,
                    detach=False
                )
                print("✓ Python virtual environment properly copied")
            except Exception:
                print("✗ Python virtual environment not found")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Multi-stage optimization check failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all Docker build tests."""
        print("Starting Docker Build Tests...")
        print("=" * 50)
        
        tests = [
            self.test_build_success,
            self.test_image_size,
            self.test_dependencies,
            self.test_security_configuration,
            self.test_multi_stage_optimization
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
        print(f"Docker Build Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("✓ All Docker build tests passed!")
            return True
        else:
            print("✗ Some Docker build tests failed!")
            return False


def main():
    """Main test execution."""
    tester = DockerBuildTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())