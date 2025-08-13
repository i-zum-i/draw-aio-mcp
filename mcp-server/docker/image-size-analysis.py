#!/usr/bin/env python3
"""
Docker Image Size Analysis Tool
Task 27.1: MCP依存関係を含めたイメージサイズ再計算

This script analyzes Docker image sizes with MCP dependencies
and provides optimization recommendations.
"""

import subprocess
import json
import sys
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import re

class DockerImageAnalyzer:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.results = {}
        
    def get_image_size(self, image_name: str) -> Optional[int]:
        """Get image size in bytes"""
        try:
            result = subprocess.run(
                ["docker", "images", "--format", "json", image_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                image_data = json.loads(result.stdout.strip())
                size_str = image_data.get("Size", "0B")
                return self._parse_size(size_str)
            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            return None
    
    def _parse_size(self, size_str: str) -> int:
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
                number = float(size_str[:-len(unit)])
                return int(number * multiplier)
        
        # If no unit, assume bytes
        try:
            return int(float(size_str))
        except ValueError:
            return 0
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def analyze_layer_sizes(self, image_name: str) -> List[Dict]:
        """Analyze individual layer sizes"""
        try:
            result = subprocess.run(
                ["docker", "history", "--format", "json", image_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            layers = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    layer_data = json.loads(line)
                    layers.append({
                        'created_by': layer_data.get('CreatedBy', ''),
                        'size': self._parse_size(layer_data.get('Size', '0B')),
                        'size_formatted': layer_data.get('Size', '0B')
                    })
            
            return layers
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
    
    def build_and_analyze_images(self) -> Dict:
        """Build and analyze different Docker configurations"""
        configurations = {
            'original': {
                'dockerfile': 'Dockerfile',
                'description': 'Original Dockerfile'
            },
            'optimized': {
                'dockerfile': 'Dockerfile.optimized',
                'description': 'Optimized Dockerfile'
            }
        }
        
        results = {}
        
        for config_name, config in configurations.items():
            dockerfile_path = self.base_dir / config['dockerfile']
            if not dockerfile_path.exists():
                print(f"Warning: {dockerfile_path} not found, skipping {config_name}")
                continue
            
            image_name = f"mcp-drawio-server:{config_name}"
            
            print(f"Building {config['description']} ({image_name})...")
            
            # Build the image
            build_result = subprocess.run([
                "docker", "build",
                "-f", str(dockerfile_path),
                "-t", image_name,
                str(self.base_dir)
            ], capture_output=True, text=True)
            
            if build_result.returncode != 0:
                print(f"Failed to build {image_name}: {build_result.stderr}")
                continue
            
            # Analyze the built image
            size = self.get_image_size(image_name)
            layers = self.analyze_layer_sizes(image_name)
            
            results[config_name] = {
                'image_name': image_name,
                'description': config['description'],
                'size_bytes': size,
                'size_formatted': self._format_size(size) if size else 'Unknown',
                'layers': layers,
                'layer_count': len(layers)
            }
            
            print(f"✓ {config['description']}: {results[config_name]['size_formatted']}")
        
        return results
    
    def analyze_mcp_dependencies(self) -> Dict:
        """Analyze MCP-specific dependencies and their sizes"""
        requirements_file = self.base_dir / "requirements.txt"
        
        if not requirements_file.exists():
            return {"error": "requirements.txt not found"}
        
        with open(requirements_file, 'r') as f:
            requirements = f.read()
        
        # Extract MCP-related packages
        mcp_packages = []
        for line in requirements.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if 'mcp' in line.lower() or 'anthropic' in line.lower():
                    mcp_packages.append(line)
        
        return {
            'mcp_packages': mcp_packages,
            'total_packages': len([l for l in requirements.split('\n') if l.strip() and not l.startswith('#')])
        }
    
    def generate_optimization_report(self, analysis_results: Dict) -> str:
        """Generate optimization recommendations report"""
        report = []
        report.append("# Docker Image Size Analysis Report")
        report.append(f"Generated: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}")
        report.append("")
        
        # Image size comparison
        report.append("## Image Size Comparison")
        report.append("")
        
        if 'original' in analysis_results and 'optimized' in analysis_results:
            original_size = analysis_results['original']['size_bytes']
            optimized_size = analysis_results['optimized']['size_bytes']
            
            if original_size and optimized_size:
                savings = original_size - optimized_size
                savings_percent = (savings / original_size) * 100
                
                report.append(f"- **Original Image**: {analysis_results['original']['size_formatted']}")
                report.append(f"- **Optimized Image**: {analysis_results['optimized']['size_formatted']}")
                report.append(f"- **Size Reduction**: {self._format_size(savings)} ({savings_percent:.1f}%)")
                report.append("")
        
        # Layer analysis
        report.append("## Layer Analysis")
        report.append("")
        
        for config_name, config_data in analysis_results.items():
            if 'layers' in config_data:
                report.append(f"### {config_data['description']}")
                report.append(f"- Total layers: {config_data['layer_count']}")
                
                # Find largest layers
                largest_layers = sorted(config_data['layers'], key=lambda x: x['size'], reverse=True)[:5]
                report.append("- Largest layers:")
                
                for layer in largest_layers:
                    size_formatted = self._format_size(layer['size'])
                    command = layer['created_by'][:80] + "..." if len(layer['created_by']) > 80 else layer['created_by']
                    report.append(f"  - {size_formatted}: {command}")
                
                report.append("")
        
        # MCP dependencies analysis
        mcp_analysis = self.analyze_mcp_dependencies()
        report.append("## MCP Dependencies Analysis")
        report.append("")
        
        if 'mcp_packages' in mcp_analysis:
            report.append("### MCP-related packages:")
            for package in mcp_analysis['mcp_packages']:
                report.append(f"- {package}")
            report.append("")
            report.append(f"Total packages: {mcp_analysis['total_packages']}")
            report.append("")
        
        # Optimization recommendations
        report.append("## Optimization Recommendations")
        report.append("")
        report.append("### Immediate Actions:")
        report.append("1. **Multi-stage builds**: Use separate build and runtime stages")
        report.append("2. **Alpine base images**: Use minimal Alpine Linux base images")
        report.append("3. **Dependency cleanup**: Remove build dependencies after installation")
        report.append("4. **Layer optimization**: Combine RUN commands to reduce layers")
        report.append("5. **Cache cleanup**: Remove package manager caches")
        report.append("")
        
        report.append("### Advanced Optimizations:")
        report.append("1. **Distroless images**: Consider Google's distroless images for runtime")
        report.append("2. **Static linking**: Use static binaries where possible")
        report.append("3. **Dependency analysis**: Remove unused dependencies")
        report.append("4. **Binary stripping**: Strip debug symbols from binaries")
        report.append("")
        
        # Target size goals
        report.append("## Size Targets")
        report.append("")
        report.append("- **Current target**: < 500MB (as per requirements)")
        report.append("- **Optimized target**: < 300MB")
        report.append("- **Stretch goal**: < 200MB")
        report.append("")
        
        return "\n".join(report)
    
    def run_analysis(self) -> None:
        """Run complete image size analysis"""
        print("Starting Docker image size analysis...")
        print("=" * 50)
        
        # Build and analyze images
        analysis_results = self.build_and_analyze_images()
        
        if not analysis_results:
            print("No images could be analyzed. Please check Docker setup.")
            sys.exit(1)
        
        # Generate report
        report = self.generate_optimization_report(analysis_results)
        
        # Save report
        report_file = self.base_dir / "docker" / "IMAGE_SIZE_ANALYSIS.md"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n✓ Analysis complete. Report saved to: {report_file}")
        print("\nSummary:")
        
        for config_name, config_data in analysis_results.items():
            print(f"- {config_data['description']}: {config_data['size_formatted']}")
        
        # Check if we meet the size target
        for config_name, config_data in analysis_results.items():
            if config_data['size_bytes']:
                size_mb = config_data['size_bytes'] / (1024**2)
                if size_mb > 500:
                    print(f"\n⚠️  Warning: {config_data['description']} exceeds 500MB target ({size_mb:.1f}MB)")
                else:
                    print(f"\n✓ {config_data['description']} meets 500MB target ({size_mb:.1f}MB)")

if __name__ == "__main__":
    analyzer = DockerImageAnalyzer()
    analyzer.run_analysis()