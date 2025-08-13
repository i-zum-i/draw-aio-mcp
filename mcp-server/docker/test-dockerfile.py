#!/usr/bin/env python3
"""
Test Dockerfile syntax and optimization features without building.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any


class DockerfileAnalyzer:
    """Analyze Dockerfile for optimization and security features."""
    
    def __init__(self, dockerfile_path: str = "Dockerfile"):
        self.dockerfile_path = Path(dockerfile_path)
        self.content = ""
        self.lines = []
        
    def load_dockerfile(self) -> bool:
        """Load Dockerfile content."""
        try:
            if not self.dockerfile_path.exists():
                print(f"❌ Dockerfile not found: {self.dockerfile_path}")
                return False
                
            self.content = self.dockerfile_path.read_text()
            self.lines = [line.strip() for line in self.content.split('\n') if line.strip()]
            print(f"✅ Loaded Dockerfile: {len(self.lines)} lines")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load Dockerfile: {e}")
            return False
    
    def analyze_optimization(self) -> Dict[str, Any]:
        """Analyze optimization features."""
        print("\n📏 Analyzing optimization features...")
        
        features = {
            "multi_stage_build": False,
            "cache_cleanup": False,
            "package_cleanup": False,
            "layer_consolidation": False,
            "virtual_env_usage": False,
            "dockerignore_present": False,
        }
        
        # Check for multi-stage build
        from_count = len([line for line in self.lines if line.upper().startswith('FROM ')])
        features["multi_stage_build"] = from_count >= 2
        
        # Check for cache cleanup
        cache_patterns = [
            r'npm cache clean',
            r'pip cache purge',
            r'rm -rf.*cache',
            r'--no-cache',
        ]
        features["cache_cleanup"] = any(
            any(re.search(pattern, line, re.IGNORECASE) for pattern in cache_patterns)
            for line in self.lines
        )
        
        # Check for package cleanup
        cleanup_patterns = [
            r'apk del',
            r'rm -rf /var/cache',
            r'rm -rf /tmp',
            r'\.build-deps',
        ]
        features["package_cleanup"] = any(
            any(re.search(pattern, line, re.IGNORECASE) for pattern in cleanup_patterns)
            for line in self.lines
        )
        
        # Check for layer consolidation (RUN commands with &&)
        consolidated_runs = [line for line in self.lines if line.startswith('RUN ') and '&&' in line]
        features["layer_consolidation"] = len(consolidated_runs) > 0
        
        # Check for virtual environment usage
        features["virtual_env_usage"] = any('/opt/venv' in line for line in self.lines)
        
        # Check for .dockerignore
        dockerignore_path = self.dockerfile_path.parent / '.dockerignore'
        features["dockerignore_present"] = dockerignore_path.exists()
        
        # Print results
        for feature, present in features.items():
            status = "✅" if present else "❌"
            print(f"   {feature}: {status}")
        
        optimization_score = sum(features.values())
        print(f"\n   Optimization score: {optimization_score}/{len(features)}")
        
        return {
            "features": features,
            "score": optimization_score,
            "max_score": len(features)
        }
    
    def analyze_security(self) -> Dict[str, Any]:
        """Analyze security features."""
        print("\n🔒 Analyzing security features...")
        
        features = {
            "non_root_user": False,
            "user_creation": False,
            "proper_entrypoint": False,
            "non_privileged_port": False,
            "security_env_vars": False,
            "proper_permissions": False,
        }
        
        # Check for non-root user
        user_lines = [line for line in self.lines if line.upper().startswith('USER ')]
        features["non_root_user"] = any('root' not in line.lower() for line in user_lines)
        
        # Check for user creation
        features["user_creation"] = any('adduser' in line or 'useradd' in line for line in self.lines)
        
        # Check for proper entrypoint
        entrypoint_lines = [line for line in self.lines if line.upper().startswith('ENTRYPOINT')]
        features["proper_entrypoint"] = any(
            'tini' in line or 'dumb-init' in line for line in entrypoint_lines
        )
        
        # Check for non-privileged port
        expose_lines = [line for line in self.lines if line.upper().startswith('EXPOSE')]
        if expose_lines:
            ports = []
            for line in expose_lines:
                port_match = re.search(r'EXPOSE\s+(\d+)', line, re.IGNORECASE)
                if port_match:
                    ports.append(int(port_match.group(1)))
            features["non_privileged_port"] = all(port >= 1024 for port in ports)
        else:
            features["non_privileged_port"] = True  # No exposed ports is also secure
        
        # Check for security environment variables
        env_lines = [line for line in self.lines if line.upper().startswith('ENV')]
        security_env_patterns = [
            r'PYTHONSAFEPATH',
            r'PYTHONHASHSEED',
            r'PIP_NO_CACHE_DIR',
        ]
        features["security_env_vars"] = any(
            any(re.search(pattern, line, re.IGNORECASE) for pattern in security_env_patterns)
            for line in env_lines
        )
        
        # Check for proper permissions
        features["proper_permissions"] = any(
            'chmod' in line or 'chown' in line for line in self.lines
        )
        
        # Print results
        for feature, present in features.items():
            status = "✅" if present else "❌"
            print(f"   {feature}: {status}")
        
        security_score = sum(features.values())
        print(f"\n   Security score: {security_score}/{len(features)}")
        
        return {
            "features": features,
            "score": security_score,
            "max_score": len(features)
        }
    
    def analyze_health_check(self) -> Dict[str, Any]:
        """Analyze health check implementation."""
        print("\n🏥 Analyzing health check features...")
        
        features = {
            "healthcheck_present": False,
            "custom_script": False,
            "proper_intervals": False,
            "timeout_configured": False,
            "retries_configured": False,
        }
        
        # Check for HEALTHCHECK instruction
        healthcheck_lines = [line for line in self.lines if line.upper().startswith('HEALTHCHECK')]
        features["healthcheck_present"] = len(healthcheck_lines) > 0
        
        if healthcheck_lines:
            healthcheck_line = ' '.join(healthcheck_lines)
            
            # Check for custom script
            features["custom_script"] = 'healthcheck.py' in healthcheck_line
            
            # Check for proper intervals
            features["proper_intervals"] = '--interval=' in healthcheck_line
            
            # Check for timeout configuration
            features["timeout_configured"] = '--timeout=' in healthcheck_line
            
            # Check for retries configuration
            features["retries_configured"] = '--retries=' in healthcheck_line
        
        # Check if health check script exists
        healthcheck_script = self.dockerfile_path.parent / 'src' / 'healthcheck.py'
        if healthcheck_script.exists():
            features["custom_script"] = True
            print(f"   ✅ Health check script found: {healthcheck_script}")
        
        # Print results
        for feature, present in features.items():
            status = "✅" if present else "❌"
            print(f"   {feature}: {status}")
        
        health_score = sum(features.values())
        print(f"\n   Health check score: {health_score}/{len(features)}")
        
        return {
            "features": features,
            "score": health_score,
            "max_score": len(features)
        }
    
    def generate_report(self) -> bool:
        """Generate comprehensive analysis report."""
        print("🔍 DOCKERFILE ANALYSIS REPORT")
        print("=" * 50)
        
        if not self.load_dockerfile():
            return False
        
        # Run analyses
        optimization = self.analyze_optimization()
        security = self.analyze_security()
        health_check = self.analyze_health_check()
        
        # Calculate overall score
        total_score = optimization["score"] + security["score"] + health_check["score"]
        max_total = optimization["max_score"] + security["max_score"] + health_check["max_score"]
        
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        print(f"Optimization: {optimization['score']}/{optimization['max_score']}")
        print(f"Security: {security['score']}/{security['max_score']}")
        print(f"Health Check: {health_check['score']}/{health_check['max_score']}")
        print(f"Overall: {total_score}/{max_total} ({total_score/max_total*100:.1f}%)")
        
        # Determine pass/fail
        min_required_score = max_total * 0.8  # 80% threshold
        passed = total_score >= min_required_score
        
        print(f"\nStatus: {'✅ PASS' if passed else '❌ FAIL'}")
        if not passed:
            print(f"Required score: {min_required_score:.1f}, Actual: {total_score}")
        
        return passed


def main():
    """Main analysis function."""
    analyzer = DockerfileAnalyzer()
    success = analyzer.generate_report()
    
    if success:
        print("\n🎉 Dockerfile analysis completed successfully!")
    else:
        print("\n💥 Dockerfile analysis failed!")
    
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)