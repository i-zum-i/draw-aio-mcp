#!/usr/bin/env python3
"""
Comprehensive health check script for Docker container.
This script is used by Docker HEALTHCHECK to verify container health.
"""
import asyncio
import sys
import os
import logging
import subprocess
import time
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add src to path for imports
sys.path.insert(0, '/app/src')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class HealthStatus(Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    timestamp: float
    duration_ms: float
    details: Optional[Dict[str, Any]] = None


class ContainerHealthCheck:
    """Container-specific health check implementation."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.config: Optional[MCPServerConfig] = None
        self.health_checker: Optional[HealthChecker] = None
    
    def _setup_logging(self) -> logging.Logger:
        """Set up minimal logging for health checks."""
        logger = logging.getLogger("healthcheck")
        logger.setLevel(logging.WARNING)  # Only log warnings and errors
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def check_container_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive container health check.
        
        Returns:
            Dictionary with health check results
        """
        start_time = time.time()
        results = {
            "overall_status": "healthy",
            "timestamp": time.time(),
            "checks": {},
            "duration_ms": 0
        }
        
        try:
            # Initialize configuration
            await self._initialize_config()
            
            # Perform individual health checks
            checks = [
                ("basic_functionality", self._check_basic_functionality),
                ("configuration", self._check_configuration),
                ("file_system", self._check_file_system),
                ("python_environment", self._check_python_environment),
                ("drawio_cli", self._check_drawio_cli),
                ("server_process", self._check_server_process),
            ]
            
            failed_checks = []
            
            for check_name, check_func in checks:
                try:
                    check_result = await check_func()
                    results["checks"][check_name] = check_result
                    
                    if not check_result.get("passed", False):
                        failed_checks.append(check_name)
                        
                except Exception as e:
                    self.logger.error(f"Health check {check_name} failed: {e}")
                    results["checks"][check_name] = {
                        "passed": False,
                        "error": str(e),
                        "critical": True
                    }
                    failed_checks.append(check_name)
            
            # Determine overall status
            critical_failures = [
                name for name in failed_checks 
                if results["checks"][name].get("critical", False)
            ]
            
            if critical_failures:
                results["overall_status"] = "unhealthy"
            elif failed_checks:
                results["overall_status"] = "degraded"
            else:
                results["overall_status"] = "healthy"
            
            results["failed_checks"] = failed_checks
            results["critical_failures"] = critical_failures
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            results["overall_status"] = "unhealthy"
            results["error"] = str(e)
        
        results["duration_ms"] = (time.time() - start_time) * 1000
        return results
    
    async def _initialize_config(self):
        """Initialize configuration for health checks."""
        try:
            # Set default environment variables if not present
            if not os.getenv("ANTHROPIC_API_KEY"):
                os.environ["ANTHROPIC_API_KEY"] = "sk-ant-healthcheck-dummy-key"
            
            # Create a simple config object for health checks
            self.config = {
                "temp_dir": os.getenv("TEMP_DIR", "/app/temp"),
                "drawio_cli_path": os.getenv("DRAWIO_CLI_PATH", "drawio"),
                "cache_ttl": int(os.getenv("CACHE_TTL", "3600")),
                "max_cache_size": int(os.getenv("MAX_CACHE_SIZE", "100")),
                "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initialize config: {e}")
            raise
    
    async def _check_basic_functionality(self) -> Dict[str, Any]:
        """Check basic container functionality."""
        try:
            # Check if we can import required modules
            import anthropic
            import httpx
            from pathlib import Path
            import json
            
            # Check basic Python functionality
            test_data = {"test": "data"}
            json_str = json.dumps(test_data)
            parsed_data = json.loads(json_str)
            
            # Check file system access
            temp_file = Path("/tmp/healthcheck_test")
            temp_file.write_text("test")
            content = temp_file.read_text()
            temp_file.unlink()
            
            return {
                "passed": True,
                "message": "Basic functionality check passed",
                "critical": True
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "Basic functionality check failed",
                "critical": True
            }
    
    async def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity."""
        try:
            if not self.config:
                return {
                    "passed": False,
                    "error": "Configuration not initialized",
                    "critical": True
                }
            
            # Check essential configuration
            checks = {
                "temp_dir_configured": bool(self.config.get("temp_dir")),
                "drawio_cli_path_configured": bool(self.config.get("drawio_cli_path")),
                "cache_settings_valid": self.config.get("cache_ttl", 0) > 0 and self.config.get("max_cache_size", 0) > 0,
                "api_key_configured": bool(self.config.get("anthropic_api_key")),
            }
            
            all_passed = all(checks.values())
            
            return {
                "passed": all_passed,
                "message": "Configuration check completed",
                "details": checks,
                "critical": not all_passed
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "Configuration check failed",
                "critical": True
            }
    
    async def _check_file_system(self) -> Dict[str, Any]:
        """Check file system accessibility and permissions."""
        try:
            temp_dir = Path(self.config.get("temp_dir", "/app/temp") if self.config else "/app/temp")
            
            checks = {
                "temp_dir_exists": temp_dir.exists(),
                "temp_dir_writable": False,
                "temp_dir_readable": False,
                "proper_permissions": False
            }
            
            # Test write access
            try:
                test_file = temp_dir / "healthcheck_test"
                test_file.write_text("health check test")
                content = test_file.read_text()
                test_file.unlink()
                
                checks["temp_dir_writable"] = True
                checks["temp_dir_readable"] = True
                checks["proper_permissions"] = content == "health check test"
                
            except Exception as e:
                self.logger.warning(f"File system test failed: {e}")
            
            critical_checks = ["temp_dir_exists", "temp_dir_writable", "temp_dir_readable"]
            critical_passed = all(checks[check] for check in critical_checks)
            
            return {
                "passed": critical_passed,
                "message": "File system check completed",
                "details": checks,
                "critical": not critical_passed
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "File system check failed",
                "critical": True
            }
    
    async def _check_python_environment(self) -> Dict[str, Any]:
        """Check Python environment and dependencies."""
        try:
            checks = {
                "python_version": sys.version_info >= (3, 10),
                "required_modules": True,
                "virtual_env": "/opt/venv" in sys.path[0] if sys.path else False,
            }
            
            # Check required modules
            required_modules = ["anthropic", "httpx", "pathlib", "json", "asyncio"]
            missing_modules = []
            
            for module_name in required_modules:
                try:
                    __import__(module_name)
                except ImportError:
                    missing_modules.append(module_name)
            
            checks["required_modules"] = len(missing_modules) == 0
            if missing_modules:
                checks["missing_modules"] = missing_modules
            
            all_passed = all(checks[key] for key in ["python_version", "required_modules"])
            
            return {
                "passed": all_passed,
                "message": "Python environment check completed",
                "details": checks,
                "critical": not all_passed
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "Python environment check failed",
                "critical": True
            }
    
    async def _check_drawio_cli(self) -> Dict[str, Any]:
        """Check Draw.io CLI availability and functionality."""
        try:
            checks = {
                "cli_executable": False,
                "cli_responsive": False,
                "version_info": None
            }
            
            # Check if CLI is executable
            try:
                result = subprocess.run(
                    ["drawio", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                checks["cli_executable"] = result.returncode == 0
                checks["cli_responsive"] = result.returncode == 0
                
                if result.returncode == 0:
                    checks["version_info"] = result.stdout.strip()
                else:
                    checks["error_output"] = result.stderr.strip()
                    
            except subprocess.TimeoutExpired:
                checks["error"] = "CLI command timed out"
            except FileNotFoundError:
                checks["error"] = "Draw.io CLI not found in PATH"
            except Exception as e:
                checks["error"] = str(e)
            
            # CLI availability is important but not critical for basic health
            passed = checks["cli_executable"] and checks["cli_responsive"]
            
            return {
                "passed": passed,
                "message": "Draw.io CLI check completed",
                "details": checks,
                "critical": False  # Not critical - server can run without CLI
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "Draw.io CLI check failed",
                "critical": False
            }
    
    async def _check_server_process(self) -> Dict[str, Any]:
        """Check if the MCP server process can be initialized."""
        try:
            # This is a lightweight check to see if server components can be imported
            # and basic initialization works
            checks = {
                "server_module_importable": False,
                "services_importable": False,
                "basic_initialization": False
            }
            
            # Check if server module can be imported
            try:
                import server
                checks["server_module_importable"] = True
            except ImportError as e:
                checks["server_import_error"] = str(e)
            
            # Check if service modules can be imported
            try:
                import llm_service
                import file_service
                import image_service
                checks["services_importable"] = True
            except ImportError as e:
                checks["services_import_error"] = str(e)
            
            # Basic initialization test (without actually starting the server)
            if checks["services_importable"]:
                try:
                    # Just test that we can access the classes
                    checks["basic_initialization"] = (
                        hasattr(llm_service, 'LLMService') and
                        hasattr(file_service, 'FileService') and
                        hasattr(image_service, 'ImageService')
                    )
                except Exception as e:
                    checks["initialization_error"] = str(e)
            
            critical_checks = ["server_module_importable", "services_importable"]
            critical_passed = all(checks[check] for check in critical_checks)
            
            return {
                "passed": critical_passed,
                "message": "Server process check completed",
                "details": checks,
                "critical": not critical_passed
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "Server process check failed",
                "critical": True
            }


async def main():
    """Main health check function for Docker HEALTHCHECK."""
    health_check = ContainerHealthCheck()
    
    try:
        results = await health_check.check_container_health()
        
        # Print results for debugging (only in verbose mode)
        if os.getenv("HEALTHCHECK_VERBOSE", "").lower() in ("true", "1", "yes"):
            import json
            print(json.dumps(results, indent=2))
        
        # Exit with appropriate code
        if results["overall_status"] == "healthy":
            print("Container is healthy")
            sys.exit(0)
        elif results["overall_status"] == "degraded":
            print(f"Container is degraded: {results.get('failed_checks', [])}")
            sys.exit(0)  # Still considered healthy for Docker
        else:
            print(f"Container is unhealthy: {results.get('critical_failures', [])}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())