#!/usr/bin/env python3
"""
Docker Image Optimization Validation Script
Task 27: Docker イメージ最適化

This script validates all three optimization sub-tasks:
1. MCP依存関係を含めたイメージサイズ再計算
2. セキュリティ脆弱性スキャン
3. マルチアーキテクチャ対応の確認
"""

import subprocess
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil
from datetime import datetime

class DockerOptimizationValidator:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_command(self, cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=self.base_dir
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)
    
    def check_docker_availability(self) -> bool:
        """Check if Docker is available and running"""
        print("🔍 Checking Docker availability...")
        
        # Check Docker command
        exit_code, stdout, stderr = self.run_command(["docker", "--version"])
        if exit_code != 0:
            print("❌ Docker command not found")
            return False
        
        print(f"✅ Docker version: {stdout.strip()}")
        
        # Check Docker daemon
        exit_code, stdout, stderr = self.run_command(["docker", "info"])
        if exit_code != 0:
            print("❌ Docker daemon not running")
            return False
        
        print("✅ Docker daemon is running")
        return True
    
    def check_buildx_availability(self) -> bool:
        """Check if Docker Buildx is available"""
        print("🔍 Checking Docker Buildx availability...")
        
        exit_code, stdout, stderr = self.run_command(["docker", "buildx", "version"])
        if exit_code != 0:
            print("❌ Docker Buildx not available")
            return False
        
        print(f"✅ Docker Buildx version: {stdout.strip()}")
        
        # Check supported platforms
        exit_code, stdout, stderr = self.run_command(["docker", "buildx", "ls"])
        if exit_code == 0:
            print("✅ Available builders:")
            for line in stdout.split('\n'):
                if line.strip():
                    print(f"   {line}")
        
        return True
    
    def validate_dockerfiles(self) -> Dict:
        """Validate Dockerfile configurations"""
        print("🔍 Validating Dockerfile configurations...")
        
        dockerfiles = {
            'original': self.base_dir / 'Dockerfile',
            'optimized': self.base_dir / 'Dockerfile.optimized'
        }
        
        results = {}
        
        for name, dockerfile_path in dockerfiles.items():
            if not dockerfile_path.exists():
                results[name] = {
                    'exists': False,
                    'error': f'Dockerfile not found: {dockerfile_path}'
                }
                continue
            
            with open(dockerfile_path, 'r') as f:
                content = f.read()
            
            # Analyze Dockerfile content
            analysis = {
                'exists': True,
                'multi_stage': 'FROM' in content and content.count('FROM') > 1,
                'non_root_user': 'USER' in content and 'USER root' not in content,
                'alpine_base': 'alpine' in content.lower(),
                'build_args': 'ARG' in content,
                'health_check': 'HEALTHCHECK' in content,
                'security_labels': 'LABEL' in content,
                'size_optimization': any(opt in content for opt in [
                    'rm -rf', 'cache clean', 'no-cache', 'purge'
                ]),
                'multi_arch_support': any(arch in content for arch in [
                    'BUILDPLATFORM', 'TARGETPLATFORM', 'TARGETARCH'
                ])
            }
            
            results[name] = analysis
            
            print(f"✅ {name.title()} Dockerfile analysis:")
            for key, value in analysis.items():
                if key != 'exists':
                    status = "✅" if value else "❌"
                    print(f"   {status} {key.replace('_', ' ').title()}: {value}")
        
        return results
    
    def build_and_analyze_images(self) -> Dict:
        """Build images and analyze their sizes"""
        print("🔍 Building and analyzing Docker images...")
        
        configurations = {
            'original': {
                'dockerfile': 'Dockerfile',
                'tag': f'mcp-drawio-server:original-{self.timestamp}'
            },
            'optimized': {
                'dockerfile': 'Dockerfile.optimized',
                'tag': f'mcp-drawio-server:optimized-{self.timestamp}'
            }
        }
        
        results = {}
        
        for config_name, config in configurations.items():
            dockerfile_path = self.base_dir / config['dockerfile']
            if not dockerfile_path.exists():
                print(f"⚠️  Skipping {config_name}: {dockerfile_path} not found")
                continue
            
            print(f"🔨 Building {config_name} image...")
            
            # Build the image
            build_cmd = [
                "docker", "build",
                "-f", str(dockerfile_path),
                "-t", config['tag'],
                "--build-arg", f"VERSION=1.0.0-{self.timestamp}",
                "--build-arg", f"BUILD_DATE={datetime.now().isoformat()}",
                str(self.base_dir)
            ]
            
            exit_code, stdout, stderr = self.run_command(build_cmd)
            
            if exit_code != 0:
                print(f"❌ Failed to build {config_name}: {stderr}")
                results[config_name] = {
                    'build_success': False,
                    'error': stderr
                }
                continue
            
            # Get image size
            exit_code, stdout, stderr = self.run_command([
                "docker", "images", config['tag'], "--format", "{{.Size}}"
            ])
            
            if exit_code == 0:
                size_str = stdout.strip()
                size_bytes = self._parse_size_to_bytes(size_str)
            else:
                size_str = "unknown"
                size_bytes = 0
            
            # Get layer count
            exit_code, stdout, stderr = self.run_command([
                "docker", "history", config['tag'], "--quiet"
            ])
            
            layer_count = len(stdout.strip().split('\n')) if exit_code == 0 else 0
            
            results[config_name] = {
                'build_success': True,
                'tag': config['tag'],
                'size_str': size_str,
                'size_bytes': size_bytes,
                'layer_count': layer_count
            }
            
            print(f"✅ {config_name.title()} image built: {size_str} ({layer_count} layers)")
        
        return results
    
    def _parse_size_to_bytes(self, size_str: str) -> int:
        """Parse Docker size string to bytes"""
        size_str = size_str.upper()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3
        }
        
        for unit, multiplier in multipliers.items():
            if size_str.endswith(unit):
                try:
                    number = float(size_str[:-len(unit)])
                    return int(number * multiplier)
                except ValueError:
                    return 0
        
        try:
            return int(float(size_str))
        except ValueError:
            return 0
    
    def run_security_scan(self, image_tag: str) -> Dict:
        """Run security vulnerability scan on an image"""
        print(f"🔍 Running security scan on {image_tag}...")
        
        results = {
            'image': image_tag,
            'tools_available': {},
            'scan_results': {}
        }
        
        # Check available security tools
        security_tools = {
            'trivy': ['trivy', '--version'],
            'docker_scout': ['docker', 'scout', 'version'],
            'snyk': ['snyk', '--version']
        }
        
        for tool_name, version_cmd in security_tools.items():
            exit_code, stdout, stderr = self.run_command(version_cmd)
            results['tools_available'][tool_name] = exit_code == 0
            
            if exit_code == 0:
                print(f"✅ {tool_name} available: {stdout.strip().split()[0] if stdout.strip() else 'installed'}")
            else:
                print(f"❌ {tool_name} not available")
        
        # Run Trivy scan if available
        if results['tools_available']['trivy']:
            print("🔍 Running Trivy vulnerability scan...")
            exit_code, stdout, stderr = self.run_command([
                'trivy', 'image', '--format', 'json', image_tag
            ])
            
            if exit_code == 0:
                try:
                    trivy_data = json.loads(stdout)
                    vulnerabilities = []
                    
                    for result in trivy_data.get('Results', []):
                        for vuln in result.get('Vulnerabilities', []):
                            vulnerabilities.append({
                                'id': vuln.get('VulnerabilityID'),
                                'severity': vuln.get('Severity'),
                                'package': vuln.get('PkgName'),
                                'version': vuln.get('InstalledVersion')
                            })
                    
                    # Count by severity
                    severity_counts = {}
                    for vuln in vulnerabilities:
                        severity = vuln['severity']
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    results['scan_results']['trivy'] = {
                        'success': True,
                        'total_vulnerabilities': len(vulnerabilities),
                        'severity_counts': severity_counts,
                        'vulnerabilities': vulnerabilities[:10]  # Top 10 for summary
                    }
                    
                    print(f"✅ Trivy scan completed: {len(vulnerabilities)} vulnerabilities found")
                    for severity, count in severity_counts.items():
                        print(f"   {severity}: {count}")
                        
                except json.JSONDecodeError:
                    results['scan_results']['trivy'] = {
                        'success': False,
                        'error': 'Failed to parse Trivy output'
                    }
            else:
                results['scan_results']['trivy'] = {
                    'success': False,
                    'error': stderr
                }
        
        return results
    
    def test_multiarch_support(self) -> Dict:
        """Test multi-architecture build support"""
        print("🔍 Testing multi-architecture build support...")
        
        results = {
            'buildx_available': False,
            'supported_platforms': [],
            'test_build_success': False
        }
        
        # Check if buildx is available
        exit_code, stdout, stderr = self.run_command(['docker', 'buildx', 'version'])
        results['buildx_available'] = exit_code == 0
        
        if not results['buildx_available']:
            print("❌ Docker Buildx not available")
            return results
        
        print("✅ Docker Buildx available")
        
        # Get supported platforms
        exit_code, stdout, stderr = self.run_command(['docker', 'buildx', 'ls'])
        if exit_code == 0:
            # Parse builder output to find supported platforms
            for line in stdout.split('\n'):
                if 'linux/' in line:
                    # Extract platforms from builder output
                    parts = line.split()
                    for part in parts:
                        if 'linux/' in part:
                            platforms = part.split(',')
                            results['supported_platforms'].extend(platforms)
                            break
        
        # Remove duplicates and clean up
        results['supported_platforms'] = list(set(results['supported_platforms']))
        results['supported_platforms'] = [p.strip() for p in results['supported_platforms'] if p.strip()]
        
        print(f"✅ Supported platforms: {', '.join(results['supported_platforms'])}")
        
        # Test multi-arch build (dry run)
        dockerfile_path = self.base_dir / 'Dockerfile.optimized'
        if dockerfile_path.exists():
            print("🔍 Testing multi-architecture build (dry run)...")
            
            test_platforms = "linux/amd64,linux/arm64"  # Common platforms
            test_tag = f"mcp-drawio-server:multiarch-test-{self.timestamp}"
            
            build_cmd = [
                'docker', 'buildx', 'build',
                '--platform', test_platforms,
                '-f', str(dockerfile_path),
                '-t', test_tag,
                '--dry-run',
                str(self.base_dir)
            ]
            
            exit_code, stdout, stderr = self.run_command(build_cmd)
            results['test_build_success'] = exit_code == 0
            
            if results['test_build_success']:
                print("✅ Multi-architecture build test successful")
            else:
                print(f"❌ Multi-architecture build test failed: {stderr}")
                results['test_build_error'] = stderr
        
        return results
    
    def generate_optimization_report(self) -> str:
        """Generate comprehensive optimization report"""
        print("📊 Generating optimization report...")
        
        # Run all validations
        docker_available = self.check_docker_availability()
        buildx_available = self.check_buildx_availability()
        dockerfile_analysis = self.validate_dockerfiles()
        
        report_lines = [
            "# Docker Image Optimization Validation Report",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Report ID:** {self.timestamp}",
            "",
            "## Task 27: Docker イメージ最適化",
            "",
            "### Sub-task 1: MCP依存関係を含めたイメージサイズ再計算",
            ""
        ]
        
        if docker_available:
            image_analysis = self.build_and_analyze_images()
            
            report_lines.extend([
                "#### Image Size Analysis",
                ""
            ])
            
            for config_name, config_data in image_analysis.items():
                if config_data.get('build_success'):
                    size_mb = config_data['size_bytes'] / (1024**2) if config_data['size_bytes'] else 0
                    status = "✅ PASS" if size_mb < 500 else "❌ FAIL"
                    
                    report_lines.extend([
                        f"- **{config_name.title()} Image:**",
                        f"  - Size: {config_data['size_str']} ({size_mb:.1f}MB)",
                        f"  - Layers: {config_data['layer_count']}",
                        f"  - 500MB Target: {status}",
                        ""
                    ])
            
            # Size comparison
            if 'original' in image_analysis and 'optimized' in image_analysis:
                orig_size = image_analysis['original'].get('size_bytes', 0)
                opt_size = image_analysis['optimized'].get('size_bytes', 0)
                
                if orig_size and opt_size:
                    savings = orig_size - opt_size
                    savings_percent = (savings / orig_size) * 100
                    
                    report_lines.extend([
                        "#### Optimization Results",
                        f"- **Size Reduction:** {savings / (1024**2):.1f}MB ({savings_percent:.1f}%)",
                        ""
                    ])
        else:
            report_lines.extend([
                "❌ Docker not available - cannot perform image size analysis",
                ""
            ])
        
        # Sub-task 2: Security scanning
        report_lines.extend([
            "### Sub-task 2: セキュリティ脆弱性スキャン",
            ""
        ])
        
        if docker_available and 'optimized' in image_analysis and image_analysis['optimized'].get('build_success'):
            security_results = self.run_security_scan(image_analysis['optimized']['tag'])
            
            report_lines.extend([
                "#### Security Tools Availability",
                ""
            ])
            
            for tool, available in security_results['tools_available'].items():
                status = "✅ Available" if available else "❌ Not Available"
                report_lines.append(f"- **{tool.title()}:** {status}")
            
            report_lines.append("")
            
            if 'trivy' in security_results['scan_results']:
                trivy_results = security_results['scan_results']['trivy']
                if trivy_results['success']:
                    report_lines.extend([
                        "#### Vulnerability Scan Results (Trivy)",
                        f"- **Total Vulnerabilities:** {trivy_results['total_vulnerabilities']}",
                        ""
                    ])
                    
                    for severity, count in trivy_results['severity_counts'].items():
                        report_lines.append(f"- **{severity}:** {count}")
                    
                    report_lines.append("")
        else:
            report_lines.extend([
                "❌ Cannot perform security scan - image build failed or Docker unavailable",
                ""
            ])
        
        # Sub-task 3: Multi-architecture support
        report_lines.extend([
            "### Sub-task 3: マルチアーキテクチャ対応の確認",
            ""
        ])
        
        if buildx_available:
            multiarch_results = self.test_multiarch_support()
            
            report_lines.extend([
                "#### Multi-Architecture Support",
                f"- **Docker Buildx:** {'✅ Available' if multiarch_results['buildx_available'] else '❌ Not Available'}",
                f"- **Supported Platforms:** {', '.join(multiarch_results['supported_platforms']) if multiarch_results['supported_platforms'] else 'None detected'}",
                f"- **Test Build:** {'✅ Success' if multiarch_results['test_build_success'] else '❌ Failed'}",
                ""
            ])
        else:
            report_lines.extend([
                "❌ Docker Buildx not available - cannot test multi-architecture support",
                ""
            ])
        
        # Dockerfile analysis
        report_lines.extend([
            "## Dockerfile Analysis",
            ""
        ])
        
        for dockerfile_name, analysis in dockerfile_analysis.items():
            if analysis['exists']:
                report_lines.extend([
                    f"### {dockerfile_name.title()} Dockerfile",
                    ""
                ])
                
                for feature, status in analysis.items():
                    if feature != 'exists':
                        icon = "✅" if status else "❌"
                        report_lines.append(f"- **{feature.replace('_', ' ').title()}:** {icon} {status}")
                
                report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "### Immediate Actions:",
            "1. Ensure all images meet the 500MB size target",
            "2. Address any critical security vulnerabilities",
            "3. Verify multi-architecture build compatibility",
            "4. Implement automated security scanning in CI/CD",
            "",
            "### Long-term Improvements:",
            "1. Consider distroless base images for further size reduction",
            "2. Implement regular dependency updates",
            "3. Add automated multi-architecture builds",
            "4. Monitor for new security vulnerabilities",
            ""
        ])
        
        return "\n".join(report_lines)
    
    def run_validation(self) -> None:
        """Run complete optimization validation"""
        print("🚀 Starting Docker Image Optimization Validation")
        print("=" * 60)
        
        # Generate comprehensive report
        report = self.generate_optimization_report()
        
        # Save report
        report_file = self.base_dir / "docker" / f"OPTIMIZATION_VALIDATION_{self.timestamp}.md"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📊 Validation complete. Report saved to: {report_file}")
        
        # Display summary
        print("\n" + "=" * 60)
        print("🎯 VALIDATION SUMMARY")
        print("=" * 60)
        
        # Check if Docker is available
        if self.check_docker_availability():
            print("✅ Docker: Available and running")
        else:
            print("❌ Docker: Not available or not running")
            return
        
        # Check if Buildx is available
        if self.check_buildx_availability():
            print("✅ Docker Buildx: Available for multi-arch builds")
        else:
            print("❌ Docker Buildx: Not available")
        
        print("\n📋 Next Steps:")
        print("1. Review the detailed report for specific recommendations")
        print("2. Address any failed validations")
        print("3. Run security scans on built images")
        print("4. Test multi-architecture builds if needed")
        print("5. Update CI/CD pipelines with optimization settings")

if __name__ == "__main__":
    validator = DockerOptimizationValidator()
    validator.run_validation()