"""
Dependency checker for the MCP Draw.io Server.

This module provides comprehensive dependency checking functionality including:
- Startup-time dependency validation
- Clear error messages for missing dependencies
- Automatic setup guidance
- Troubleshooting information
"""
import asyncio
import logging
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import importlib.util


class DependencyType(Enum):
    """Types of dependencies to check."""
    PYTHON_LIBRARY = "python_library"
    SYSTEM_COMMAND = "system_command"
    ENVIRONMENT_VAR = "environment_var"
    FILE_PATH = "file_path"
    DIRECTORY = "directory"


class DependencyStatus(Enum):
    """Status of dependency check."""
    AVAILABLE = "available"
    MISSING = "missing"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class DependencyRequirement:
    """Definition of a dependency requirement."""
    name: str
    type: DependencyType
    required: bool
    description: str
    check_command: Optional[str] = None
    install_command: Optional[str] = None
    install_url: Optional[str] = None
    version_command: Optional[str] = None
    minimum_version: Optional[str] = None
    install_guidance: Optional[str] = None


@dataclass
class DependencyCheckResult:
    """Result of a dependency check."""
    requirement: DependencyRequirement
    status: DependencyStatus
    version: Optional[str] = None
    error_message: Optional[str] = None
    install_guidance: Optional[str] = None
    troubleshooting: Optional[Dict[str, str]] = None


class DependencyChecker:
    """Comprehensive dependency checker for the MCP server."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the dependency checker.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._check_cache: Dict[str, DependencyCheckResult] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_check_time: Optional[float] = None
        
        # Define all dependency requirements
        self.requirements = self._define_requirements()
    
    def _define_requirements(self) -> List[DependencyRequirement]:
        """Define all dependency requirements for the MCP server."""
        return [
            # Python libraries - Critical
            DependencyRequirement(
                name="anthropic",
                type=DependencyType.PYTHON_LIBRARY,
                required=True,
                description="Anthropic Claude API client library",
                install_command="pip install anthropic",
                minimum_version="0.3.0"
            ),
            DependencyRequirement(
                name="mcp",
                type=DependencyType.PYTHON_LIBRARY,
                required=True,
                description="Model Context Protocol SDK",
                install_command="pip install mcp",
                minimum_version="1.0.0"
            ),
            
            # Python libraries - Optional but recommended
            DependencyRequirement(
                name="httpx",
                type=DependencyType.PYTHON_LIBRARY,
                required=False,
                description="HTTP client library for async requests",
                install_command="pip install httpx"
            ),
            
            # System commands - Optional
            DependencyRequirement(
                name="drawio",
                type=DependencyType.SYSTEM_COMMAND,
                required=False,
                description="Draw.io CLI for PNG conversion",
                check_command="drawio --version",
                install_command="npm install -g @drawio/drawio-desktop-cli",
                install_url="https://www.npmjs.com/package/@drawio/drawio-desktop-cli"
            ),
            DependencyRequirement(
                name="node",
                type=DependencyType.SYSTEM_COMMAND,
                required=False,
                description="Node.js runtime (required for Draw.io CLI)",
                check_command="node --version",
                install_url="https://nodejs.org/",
                minimum_version="14.0.0"
            ),
            DependencyRequirement(
                name="npm",
                type=DependencyType.SYSTEM_COMMAND,
                required=False,
                description="Node Package Manager (required for Draw.io CLI)",
                check_command="npm --version",
                install_url="https://nodejs.org/"
            ),
            
            # Environment variables - Critical
            DependencyRequirement(
                name="ANTHROPIC_API_KEY",
                type=DependencyType.ENVIRONMENT_VAR,
                required=True,
                description="Anthropic Claude API key",
                install_guidance="Set your Anthropic API key: export ANTHROPIC_API_KEY=sk-ant-..."
            ),
        ]
    
    async def check_all_dependencies(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Check all dependencies and return comprehensive results.
        
        Args:
            force_refresh: Force fresh checks instead of using cache
            
        Returns:
            Dictionary with dependency check results and summary
        """
        start_time = time.time()
        
        # Check cache validity
        if not force_refresh and self._is_cache_valid():
            self.logger.debug("Using cached dependency check results")
            return self._build_summary_response()
        
        self.logger.info("🔍 Starting comprehensive dependency check...")
        
        # Run all dependency checks
        results = []
        for requirement in self.requirements:
            try:
                result = await self._check_single_dependency(requirement)
                results.append(result)
                self._check_cache[requirement.name] = result
                
                # Log individual results
                status_emoji = "✅" if result.status == DependencyStatus.AVAILABLE else "❌"
                self.logger.debug(f"{status_emoji} {requirement.name}: {result.status.value}")
                
            except Exception as e:
                self.logger.error(f"Error checking dependency {requirement.name}: {str(e)}")
                error_result = DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.ERROR,
                    error_message=str(e)
                )
                results.append(error_result)
                self._check_cache[requirement.name] = error_result
        
        self._last_check_time = time.time()
        
        # Build comprehensive response
        response = self._build_detailed_response(results)
        
        duration = (time.time() - start_time) * 1000
        self.logger.info(f"✅ Dependency check completed in {duration:.2f}ms")
        
        return response
    
    async def check_startup_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Check critical dependencies required for server startup.
        
        Returns:
            Tuple of (all_critical_available, error_messages)
        """
        self.logger.info("🚀 Checking startup dependencies...")
        
        critical_errors = []
        all_critical_available = True
        
        # Check only critical dependencies
        critical_requirements = [req for req in self.requirements if req.required]
        
        for requirement in critical_requirements:
            try:
                result = await self._check_single_dependency(requirement)
                
                if result.status != DependencyStatus.AVAILABLE:
                    all_critical_available = False
                    error_msg = self._format_startup_error(result)
                    critical_errors.append(error_msg)
                    
            except Exception as e:
                all_critical_available = False
                error_msg = f"❌ {requirement.name}: Failed to check - {str(e)}"
                critical_errors.append(error_msg)
        
        if all_critical_available:
            self.logger.info("✅ All critical dependencies are available")
        else:
            self.logger.error(f"❌ {len(critical_errors)} critical dependencies missing")
        
        return all_critical_available, critical_errors
    
    async def get_setup_guidance(self, missing_only: bool = True) -> str:
        """
        Generate comprehensive setup guidance.
        
        Args:
            missing_only: Only include guidance for missing dependencies
            
        Returns:
            Formatted setup guidance string
        """
        results = await self.check_all_dependencies()
        
        guidance_parts = [
            "📋 MCP Draw.io Server - Dependency Setup Guide",
            "=" * 50,
            ""
        ]
        
        # Critical dependencies section
        critical_issues = []
        optional_issues = []
        
        for dep_name, result_data in results["dependencies"].items():
            result = self._check_cache.get(dep_name)
            if not result:
                continue
                
            if result.status != DependencyStatus.AVAILABLE:
                if result.requirement.required:
                    critical_issues.append(result)
                else:
                    optional_issues.append(result)
        
        # Critical dependencies
        if critical_issues:
            guidance_parts.extend([
                "🚨 CRITICAL DEPENDENCIES (Required for server startup)",
                "-" * 50,
                ""
            ])
            
            for result in critical_issues:
                guidance_parts.extend(self._format_dependency_guidance(result))
                guidance_parts.append("")
        
        # Optional dependencies
        if optional_issues and not missing_only:
            guidance_parts.extend([
                "⚠️ OPTIONAL DEPENDENCIES (Enhanced functionality)",
                "-" * 50,
                ""
            ])
            
            for result in optional_issues:
                guidance_parts.extend(self._format_dependency_guidance(result))
                guidance_parts.append("")
        
        # General setup instructions
        if critical_issues or (optional_issues and not missing_only):
            guidance_parts.extend([
                "🔧 GENERAL SETUP STEPS",
                "-" * 50,
                "",
                "1. Install Python dependencies:",
                "   pip install -r requirements.txt",
                "",
                "2. Set up environment variables:",
                "   export ANTHROPIC_API_KEY=sk-ant-your-key-here",
                "",
                "3. (Optional) Install Draw.io CLI for PNG conversion:",
                "   npm install -g @drawio/drawio-desktop-cli",
                "",
                "4. Verify installation:",
                "   python -m src.server --check-dependencies",
                "",
                "5. Start the server:",
                "   python -m src.server",
                ""
            ])
        else:
            guidance_parts.extend([
                "✅ All dependencies are properly configured!",
                "",
                "You can start the server with:",
                "   python -m src.server",
                ""
            ])
        
        return "\n".join(guidance_parts)
    
    async def _check_single_dependency(self, requirement: DependencyRequirement) -> DependencyCheckResult:
        """Check a single dependency requirement."""
        try:
            if requirement.type == DependencyType.PYTHON_LIBRARY:
                return await self._check_python_library(requirement)
            elif requirement.type == DependencyType.SYSTEM_COMMAND:
                return await self._check_system_command(requirement)
            elif requirement.type == DependencyType.ENVIRONMENT_VAR:
                return await self._check_environment_variable(requirement)
            elif requirement.type == DependencyType.FILE_PATH:
                return await self._check_file_path(requirement)
            elif requirement.type == DependencyType.DIRECTORY:
                return await self._check_directory(requirement)
            else:
                return DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.ERROR,
                    error_message=f"Unknown dependency type: {requirement.type}"
                )
                
        except Exception as e:
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.ERROR,
                error_message=str(e)
            )
    
    async def _check_python_library(self, requirement: DependencyRequirement) -> DependencyCheckResult:
        """Check if a Python library is available."""
        try:
            # Try to import the library
            spec = importlib.util.find_spec(requirement.name)
            if spec is None:
                return DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.MISSING,
                    error_message=f"Python library '{requirement.name}' not found",
                    install_guidance=f"Install with: {requirement.install_command}" if requirement.install_command else None
                )
            
            # Try to get version if possible
            version = None
            try:
                module = importlib.import_module(requirement.name)
                if hasattr(module, '__version__'):
                    version = module.__version__
                elif hasattr(module, 'version'):
                    version = module.version
                elif hasattr(module, 'VERSION'):
                    version = module.VERSION
            except Exception:
                pass  # Version detection failed, but library exists
            
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.AVAILABLE,
                version=version
            )
            
        except Exception as e:
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.ERROR,
                error_message=str(e)
            )
    
    async def _check_system_command(self, requirement: DependencyRequirement) -> DependencyCheckResult:
        """Check if a system command is available."""
        try:
            # Check if command exists in PATH
            command_path = shutil.which(requirement.name)
            if not command_path:
                return DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.MISSING,
                    error_message=f"Command '{requirement.name}' not found in PATH",
                    install_guidance=self._get_install_guidance(requirement)
                )
            
            # Try to get version if version command is specified
            version = None
            if requirement.version_command or requirement.check_command:
                version_cmd = requirement.version_command or requirement.check_command
                try:
                    process = await asyncio.create_subprocess_shell(
                        version_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
                    
                    if process.returncode == 0:
                        version = stdout.decode().strip()
                    else:
                        # Command exists but version check failed
                        error_output = stderr.decode().strip()
                        return DependencyCheckResult(
                            requirement=requirement,
                            status=DependencyStatus.INVALID,
                            error_message=f"Command '{requirement.name}' exists but version check failed: {error_output}",
                            troubleshooting={"reinstall": f"Try reinstalling: {requirement.install_command}"}
                        )
                        
                except asyncio.TimeoutError:
                    return DependencyCheckResult(
                        requirement=requirement,
                        status=DependencyStatus.INVALID,
                        error_message=f"Command '{requirement.name}' exists but is not responding",
                        troubleshooting={"check_installation": f"Command may be corrupted, try reinstalling"}
                    )
            
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.AVAILABLE,
                version=version
            )
            
        except Exception as e:
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.ERROR,
                error_message=str(e)
            )
    
    async def _check_environment_variable(self, requirement: DependencyRequirement) -> DependencyCheckResult:
        """Check if an environment variable is set."""
        import os
        
        try:
            value = os.getenv(requirement.name)
            if not value:
                return DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.MISSING,
                    error_message=f"Environment variable '{requirement.name}' is not set",
                    install_guidance=requirement.install_guidance
                )
            
            # Special validation for API keys
            if requirement.name == "ANTHROPIC_API_KEY":
                if not value.startswith("sk-ant-"):
                    return DependencyCheckResult(
                        requirement=requirement,
                        status=DependencyStatus.INVALID,
                        error_message="ANTHROPIC_API_KEY must start with 'sk-ant-'",
                        install_guidance="Get your API key from https://console.anthropic.com/"
                    )
            
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.AVAILABLE,
                version=f"Set (length: {len(value)})"
            )
            
        except Exception as e:
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.ERROR,
                error_message=str(e)
            )
    
    async def _check_file_path(self, requirement: DependencyRequirement) -> DependencyCheckResult:
        """Check if a file path exists."""
        try:
            file_path = Path(requirement.name)
            if not file_path.exists():
                return DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.MISSING,
                    error_message=f"File not found: {requirement.name}"
                )
            
            if not file_path.is_file():
                return DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.INVALID,
                    error_message=f"Path exists but is not a file: {requirement.name}"
                )
            
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.AVAILABLE,
                version=f"Size: {file_path.stat().st_size} bytes"
            )
            
        except Exception as e:
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.ERROR,
                error_message=str(e)
            )
    
    async def _check_directory(self, requirement: DependencyRequirement) -> DependencyCheckResult:
        """Check if a directory exists."""
        try:
            dir_path = Path(requirement.name)
            if not dir_path.exists():
                return DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.MISSING,
                    error_message=f"Directory not found: {requirement.name}"
                )
            
            if not dir_path.is_dir():
                return DependencyCheckResult(
                    requirement=requirement,
                    status=DependencyStatus.INVALID,
                    error_message=f"Path exists but is not a directory: {requirement.name}"
                )
            
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.AVAILABLE,
                version="Directory exists"
            )
            
        except Exception as e:
            return DependencyCheckResult(
                requirement=requirement,
                status=DependencyStatus.ERROR,
                error_message=str(e)
            )
    
    def _get_install_guidance(self, requirement: DependencyRequirement) -> str:
        """Get installation guidance for a requirement."""
        guidance_parts = []
        
        if requirement.install_command:
            guidance_parts.append(f"Install with: {requirement.install_command}")
        
        if requirement.install_url:
            guidance_parts.append(f"Download from: {requirement.install_url}")
        
        return " | ".join(guidance_parts) if guidance_parts else "No installation guidance available"
    
    def _format_startup_error(self, result: DependencyCheckResult) -> str:
        """Format a startup error message."""
        req = result.requirement
        error_parts = [f"❌ {req.name}: {result.error_message or 'Not available'}"]
        
        if result.install_guidance:
            error_parts.append(f"   💡 {result.install_guidance}")
        elif req.install_command:
            error_parts.append(f"   💡 Install with: {req.install_command}")
        
        return "\n".join(error_parts)
    
    def _format_dependency_guidance(self, result: DependencyCheckResult) -> List[str]:
        """Format detailed guidance for a dependency."""
        req = result.requirement
        guidance = [
            f"❌ {req.name} - {req.description}",
            f"   Status: {result.status.value}",
            f"   Issue: {result.error_message or 'Not available'}"
        ]
        
        if result.install_guidance:
            guidance.append(f"   Solution: {result.install_guidance}")
        elif req.install_command:
            guidance.append(f"   Install: {req.install_command}")
        
        if req.install_url:
            guidance.append(f"   URL: {req.install_url}")
        
        if result.troubleshooting:
            guidance.append("   Troubleshooting:")
            for key, value in result.troubleshooting.items():
                guidance.append(f"     • {key}: {value}")
        
        return guidance
    
    def _is_cache_valid(self) -> bool:
        """Check if dependency check cache is still valid."""
        if not self._last_check_time:
            return False
        return (time.time() - self._last_check_time) < self._cache_ttl
    
    def _build_summary_response(self) -> Dict[str, Any]:
        """Build summary response from cached results."""
        if not self._check_cache:
            return {"error": "No cached results available"}
        
        return self._build_detailed_response(list(self._check_cache.values()))
    
    def _build_detailed_response(self, results: List[DependencyCheckResult]) -> Dict[str, Any]:
        """Build detailed response from check results."""
        # Categorize results
        available = [r for r in results if r.status == DependencyStatus.AVAILABLE]
        missing = [r for r in results if r.status == DependencyStatus.MISSING]
        invalid = [r for r in results if r.status == DependencyStatus.INVALID]
        errors = [r for r in results if r.status == DependencyStatus.ERROR]
        
        # Separate critical and optional
        critical_missing = [r for r in missing if r.requirement.required]
        critical_invalid = [r for r in invalid if r.requirement.required]
        critical_errors = [r for r in errors if r.requirement.required]
        
        # Determine overall status
        if critical_missing or critical_invalid or critical_errors:
            overall_status = "critical_issues"
        elif missing or invalid or errors:
            overall_status = "optional_issues"
        else:
            overall_status = "all_good"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "summary": {
                "total": len(results),
                "available": len(available),
                "missing": len(missing),
                "invalid": len(invalid),
                "errors": len(errors),
                "critical_issues": len(critical_missing) + len(critical_invalid) + len(critical_errors)
            },
            "dependencies": {
                result.requirement.name: {
                    "status": result.status.value,
                    "required": result.requirement.required,
                    "description": result.requirement.description,
                    "version": result.version,
                    "error": result.error_message,
                    "install_guidance": result.install_guidance,
                    "troubleshooting": result.troubleshooting
                }
                for result in results
            },
            "critical_issues": [
                {
                    "name": result.requirement.name,
                    "error": result.error_message,
                    "guidance": result.install_guidance or result.requirement.install_command
                }
                for result in critical_missing + critical_invalid + critical_errors
            ]
        }
    
    def clear_cache(self) -> None:
        """Clear the dependency check cache."""
        self._check_cache.clear()
        self._last_check_time = None
        self.logger.debug("Dependency check cache cleared")