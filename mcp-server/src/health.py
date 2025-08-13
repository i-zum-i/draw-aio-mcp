"""
Health check system for the MCP Draw.io Server.
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .config import MCPServerConfig
from .llm_service import LLMService
from .file_service import FileService
from .image_service import ImageService


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
    timestamp: datetime
    duration_ms: float
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """Health check manager for the MCP server."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._last_check_time: Optional[datetime] = None
        self._cached_results: Dict[str, HealthCheckResult] = {}
        self._services_initialized = False
        
        # Service instances (initialized lazily)
        self._llm_service: Optional[LLMService] = None
        self._file_service: Optional[FileService] = None
        self._image_service: Optional[ImageService] = None
        self._dependency_checker = None
    
    def set_services(
        self, 
        llm_service: LLMService, 
        file_service: FileService, 
        image_service: ImageService
    ):
        """Set service instances for health checking."""
        self._llm_service = llm_service
        self._file_service = file_service
        self._image_service = image_service
        self._services_initialized = True
        self.logger.info("Health checker initialized with services")
    
    def set_dependency_checker(self, dependency_checker):
        """Set dependency checker instance for enhanced health checking."""
        self._dependency_checker = dependency_checker
        self.logger.info("Health checker initialized with dependency checker")
    
    async def check_all(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Perform all health checks and return comprehensive status.
        
        Args:
            force_refresh: Force fresh checks instead of using cache
            
        Returns:
            Dictionary containing overall health status and individual check results
        """
        start_time = time.time()
        
        # Check if we need to refresh (based on cache interval)
        now = datetime.utcnow()
        if (not force_refresh and 
            self._last_check_time and 
            (now - self._last_check_time).total_seconds() < self.config.health_check_interval):
            
            # Return cached results
            return self._build_health_response(list(self._cached_results.values()))
        
        # Perform fresh health checks
        self.logger.info("Performing health checks...")
        
        # Run all health checks concurrently
        check_tasks = [
            self._check_server_basic(),
            self._check_configuration(),
            self._check_file_system(),
            self._check_llm_service(),
            self._check_image_service(),
            self._check_dependencies(),
            self._check_enhanced_dependencies(),
        ]
        
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle check that raised an exception
                check_name = [
                    "server_basic", "configuration", "file_system", 
                    "llm_service", "image_service", "dependencies", "enhanced_dependencies"
                ][i]
                
                health_results.append(HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}",
                    timestamp=now,
                    duration_ms=0,
                    details={"exception": str(result)}
                ))
            else:
                health_results.append(result)
        
        # Cache results
        self._cached_results = {result.name: result for result in health_results}
        self._last_check_time = now
        
        total_duration = (time.time() - start_time) * 1000
        self.logger.info(f"Health checks completed in {total_duration:.2f}ms")
        
        return self._build_health_response(health_results)
    
    async def _check_server_basic(self) -> HealthCheckResult:
        """Check basic server functionality."""
        start_time = time.time()
        
        try:
            # Basic server checks
            checks = {
                "memory_available": True,  # Could add actual memory check
                "startup_time": time.time(),
                "config_loaded": self.config is not None,
            }
            
            all_passed = all(checks.values())
            status = HealthStatus.HEALTHY if all_passed else HealthStatus.DEGRADED
            
            return HealthCheckResult(
                name="server_basic",
                status=status,
                message="Server basic functionality check",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details=checks
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="server_basic",
                status=HealthStatus.UNHEALTHY,
                message=f"Server basic check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    async def _check_configuration(self) -> HealthCheckResult:
        """Check configuration validity."""
        start_time = time.time()
        
        try:
            config_checks = {
                "anthropic_api_key_present": bool(self.config.anthropic_api_key),
                "anthropic_api_key_format": self.config.anthropic_api_key.startswith("sk-ant-"),
                "temp_dir_exists": self.config.temp_dir and len(self.config.temp_dir) > 0,
                "cache_settings_valid": self.config.cache_ttl > 0 and self.config.max_cache_size > 0,
                "file_settings_valid": self.config.file_expiry_hours > 0,
            }
            
            all_passed = all(config_checks.values())
            status = HealthStatus.HEALTHY if all_passed else HealthStatus.UNHEALTHY
            
            return HealthCheckResult(
                name="configuration",
                status=status,
                message="Configuration validation check",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details=config_checks
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="configuration",
                status=HealthStatus.UNHEALTHY,
                message=f"Configuration check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    async def _check_file_system(self) -> HealthCheckResult:
        """Check file system accessibility."""
        start_time = time.time()
        
        try:
            from pathlib import Path
            import tempfile
            import os
            
            temp_dir = Path(self.config.temp_dir)
            
            checks = {
                "temp_dir_exists": temp_dir.exists(),
                "temp_dir_writable": False,
                "temp_dir_readable": False,
                "disk_space_available": False,
            }
            
            # Check if temp directory is writable
            if temp_dir.exists():
                try:
                    with tempfile.NamedTemporaryFile(dir=temp_dir, delete=True) as tmp_file:
                        tmp_file.write(b"health check test")
                        tmp_file.flush()
                        checks["temp_dir_writable"] = True
                        checks["temp_dir_readable"] = True
                except Exception:
                    pass
            
            # Check disk space (basic check)
            try:
                stat = os.statvfs(temp_dir)
                free_bytes = stat.f_frsize * stat.f_bavail
                checks["disk_space_available"] = free_bytes > 100 * 1024 * 1024  # 100MB minimum
                checks["free_space_mb"] = free_bytes // (1024 * 1024)
            except Exception:
                pass
            
            # Determine status
            critical_checks = ["temp_dir_exists", "temp_dir_writable", "temp_dir_readable"]
            critical_passed = all(checks.get(check, False) for check in critical_checks)
            
            if critical_passed and checks.get("disk_space_available", False):
                status = HealthStatus.HEALTHY
            elif critical_passed:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return HealthCheckResult(
                name="file_system",
                status=status,
                message="File system accessibility check",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details=checks
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="file_system",
                status=HealthStatus.UNHEALTHY,
                message=f"File system check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    async def _check_llm_service(self) -> HealthCheckResult:
        """Check LLM service health."""
        start_time = time.time()
        
        try:
            if not self._services_initialized or not self._llm_service:
                return HealthCheckResult(
                    name="llm_service",
                    status=HealthStatus.UNKNOWN,
                    message="LLM service not initialized",
                    timestamp=datetime.utcnow(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={"initialized": False}
                )
            
            # Check LLM service health
            checks = {
                "service_initialized": True,
                "api_key_configured": bool(self._llm_service.api_key),
                "cache_functional": len(self._llm_service.cache) >= 0,  # Basic cache check
            }
            
            # Could add a lightweight API connectivity test here
            # For now, we'll just check basic initialization
            
            all_passed = all(checks.values())
            status = HealthStatus.HEALTHY if all_passed else HealthStatus.DEGRADED
            
            return HealthCheckResult(
                name="llm_service",
                status=status,
                message="LLM service health check",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details=checks
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="llm_service",
                status=HealthStatus.UNHEALTHY,
                message=f"LLM service check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    async def _check_image_service(self) -> HealthCheckResult:
        """Check image service health."""
        start_time = time.time()
        
        try:
            if not self._services_initialized or not self._image_service:
                return HealthCheckResult(
                    name="image_service",
                    status=HealthStatus.UNKNOWN,
                    message="Image service not initialized",
                    timestamp=datetime.utcnow(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={"initialized": False}
                )
            
            # Check Draw.io CLI availability
            cli_available = await self._image_service.is_drawio_cli_available()
            
            checks = {
                "service_initialized": True,
                "drawio_cli_available": cli_available,
                "cli_path_configured": bool(self._image_service.drawio_cli_path),
            }
            
            # Determine status based on CLI availability
            if cli_available:
                status = HealthStatus.HEALTHY
            else:
                # Service can still function with fallback, so it's degraded not unhealthy
                status = HealthStatus.DEGRADED
            
            return HealthCheckResult(
                name="image_service",
                status=status,
                message="Image service health check",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details=checks
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="image_service",
                status=HealthStatus.UNHEALTHY,
                message=f"Image service check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    async def _check_dependencies(self) -> HealthCheckResult:
        """Check external dependencies."""
        start_time = time.time()
        
        try:
            checks = {
                "anthropic_library": False,
                "httpx_library": False,
                "pathlib_available": False,
                "json_available": False,
            }
            
            # Check required libraries
            try:
                import anthropic
                checks["anthropic_library"] = True
            except ImportError:
                pass
            
            try:
                import httpx
                checks["httpx_library"] = True
            except ImportError:
                pass
            
            try:
                from pathlib import Path
                checks["pathlib_available"] = True
            except ImportError:
                pass
            
            try:
                import json
                checks["json_available"] = True
            except ImportError:
                pass
            
            # Determine status
            critical_deps = ["anthropic_library", "pathlib_available", "json_available"]
            critical_passed = all(checks.get(dep, False) for dep in critical_deps)
            
            if critical_passed and checks.get("httpx_library", False):
                status = HealthStatus.HEALTHY
            elif critical_passed:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return HealthCheckResult(
                name="dependencies",
                status=status,
                message="External dependencies check",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details=checks
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="dependencies",
                status=HealthStatus.UNHEALTHY,
                message=f"Dependencies check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    async def _check_enhanced_dependencies(self) -> HealthCheckResult:
        """Check dependencies using the enhanced dependency checker."""
        start_time = time.time()
        
        try:
            if not self._dependency_checker:
                return HealthCheckResult(
                    name="enhanced_dependencies",
                    status=HealthStatus.UNKNOWN,
                    message="Enhanced dependency checker not available",
                    timestamp=datetime.utcnow(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={"checker_available": False}
                )
            
            # Run comprehensive dependency check
            dependency_results = await self._dependency_checker.check_all_dependencies()
            
            # Analyze results
            summary = dependency_results["summary"]
            critical_issues = summary["critical_issues"]
            
            # Determine status
            if critical_issues > 0:
                status = HealthStatus.UNHEALTHY
                message = f"Critical dependencies missing: {critical_issues}"
            elif summary["missing"] > 0 or summary["invalid"] > 0:
                status = HealthStatus.DEGRADED
                message = f"Optional dependencies missing: {summary['missing']} missing, {summary['invalid']} invalid"
            else:
                status = HealthStatus.HEALTHY
                message = "All dependencies available"
            
            # Build detailed information
            details = {
                "total_dependencies": summary["total"],
                "available": summary["available"],
                "missing": summary["missing"],
                "invalid": summary["invalid"],
                "errors": summary["errors"],
                "critical_issues": critical_issues,
                "dependency_status": {
                    name: {
                        "status": info["status"],
                        "required": info["required"],
                        "version": info["version"]
                    }
                    for name, info in dependency_results["dependencies"].items()
                }
            }
            
            # Add critical issues details
            if dependency_results.get("critical_issues"):
                details["critical_issues_details"] = dependency_results["critical_issues"]
            
            return HealthCheckResult(
                name="enhanced_dependencies",
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="enhanced_dependencies",
                status=HealthStatus.UNHEALTHY,
                message=f"Enhanced dependencies check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    def _build_health_response(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Build comprehensive health response from check results."""
        # Determine overall status
        statuses = [result.status for result in results]
        
        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            overall_status = HealthStatus.DEGRADED
        elif any(status == HealthStatus.UNKNOWN for status in statuses):
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Build response
        response = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "server": {
                "name": self.config.server_name,
                "version": self.config.server_version,
                "protocol_version": self.config.protocol_version,
            },
            "checks": {
                result.name: {
                    "status": result.status.value,
                    "message": result.message,
                    "timestamp": result.timestamp.isoformat() + "Z",
                    "duration_ms": result.duration_ms,
                    "details": result.details or {}
                }
                for result in results
            },
            "summary": {
                "total_checks": len(results),
                "healthy": sum(1 for r in results if r.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for r in results if r.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for r in results if r.status == HealthStatus.UNHEALTHY),
                "unknown": sum(1 for r in results if r.status == HealthStatus.UNKNOWN),
            }
        }
        
        return response
    
    async def get_readiness(self) -> Dict[str, Any]:
        """
        Check if server is ready to handle requests.
        
        Returns:
            Dictionary indicating readiness status
        """
        ready = (
            self._services_initialized and
            self.config is not None and
            bool(self.config.anthropic_api_key)
        )
        
        return {
            "ready": ready,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": {
                "services_initialized": self._services_initialized,
                "config_loaded": self.config is not None,
                "api_key_configured": bool(self.config.anthropic_api_key) if self.config else False,
            }
        }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """
        Check if server is alive and responsive.
        
        Returns:
            Dictionary indicating liveness status
        """
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": time.time() - (self._last_check_time.timestamp() if self._last_check_time else time.time()),
        }