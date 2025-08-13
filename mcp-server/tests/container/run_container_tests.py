#!/usr/bin/env python3
"""
Container Test Runner for MCP Draw.io Server
Orchestrates all container-related tests including build and runtime tests.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Add the tests directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from test_docker_build import DockerBuildTester
from test_container_runtime import ContainerRuntimeTester


class ContainerTestRunner:
    """Orchestrates all container tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.results: Dict[str, bool] = {}
        
    def run_docker_build_tests(self) -> bool:
        """Run Docker build tests."""
        print("\n" + "=" * 60)
        print("RUNNING DOCKER BUILD TESTS")
        print("=" * 60)
        
        tester = DockerBuildTester()
        try:
            result = tester.run_all_tests()
            self.results['docker_build'] = result
            return result
        finally:
            tester.cleanup()
    
    def run_container_runtime_tests(self) -> bool:
        """Run container runtime tests."""
        print("\n" + "=" * 60)
        print("RUNNING CONTAINER RUNTIME TESTS")
        print("=" * 60)
        
        tester = ContainerRuntimeTester()
        try:
            result = tester.run_all_tests()
            self.results['container_runtime'] = result
            return result
        finally:
            tester.cleanup()
    
    def check_prerequisites(self) -> bool:
        """Check that all prerequisites are available."""
        print("Checking prerequisites...")
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✓ Docker available: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ Docker not available")
            return False
        
        # Check Docker daemon
        try:
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True, check=True)
            print("✓ Docker daemon running")
        except subprocess.CalledProcessError:
            print("✗ Docker daemon not running")
            return False
        
        # Check Python packages
        required_packages = ['docker', 'pytest']
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ Python package available: {package}")
            except ImportError:
                print(f"✗ Python package missing: {package}")
                print(f"  Install with: pip install {package}")
                return False
        
        # Check project structure
        required_files = [
            'Dockerfile',
            'requirements.txt',
            'src/server.py',
            'src/tools.py'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"✓ Required file exists: {file_path}")
            else:
                print(f"✗ Required file missing: {file_path}")
                return False
        
        return True
    
    def create_test_directories(self):
        """Create necessary test directories."""
        test_dirs = [
            self.project_root / 'temp_test',
            self.project_root / 'logs_test',
            self.project_root / 'temp_dev',
            self.project_root / 'logs_dev',
            self.project_root / 'temp_prod',
            self.project_root / 'logs_prod'
        ]
        
        for dir_path in test_dirs:
            dir_path.mkdir(exist_ok=True)
            print(f"✓ Test directory ready: {dir_path.name}")
    
    def cleanup_test_directories(self):
        """Clean up test directories."""
        import shutil
        
        test_dirs = [
            self.project_root / 'temp_test',
            self.project_root / 'logs_test'
        ]
        
        for dir_path in test_dirs:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"✓ Cleaned up test directory: {dir_path.name}")
                except Exception as e:
                    print(f"⚠ Could not clean up {dir_path.name}: {e}")
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("=" * 60)
        report.append("CONTAINER TEST REPORT")
        report.append("=" * 60)
        report.append(f"Test execution time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Test results summary
        total_tests = len(self.results)
        passed_tests = sum(self.results.values())
        
        report.append(f"Overall Results: {passed_tests}/{total_tests} test suites passed")
        report.append("")
        
        # Individual test results
        for test_name, result in self.results.items():
            status = "PASSED" if result else "FAILED"
            report.append(f"  {test_name}: {status}")
        
        report.append("")
        
        # Recommendations
        if passed_tests == total_tests:
            report.append("✓ All container tests passed!")
            report.append("  The Docker image is ready for deployment.")
        else:
            report.append("✗ Some container tests failed!")
            report.append("  Please review the test output and fix issues before deployment.")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def run_all_tests(self) -> bool:
        """Run all container tests."""
        print("Starting Container Test Suite...")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("✗ Prerequisites not met. Aborting tests.")
            return False
        
        # Create test directories
        self.create_test_directories()
        
        try:
            # Run tests in order
            tests = [
                ('Docker Build Tests', self.run_docker_build_tests),
                ('Container Runtime Tests', self.run_container_runtime_tests)
            ]
            
            for test_name, test_func in tests:
                print(f"\nStarting {test_name}...")
                try:
                    result = test_func()
                    if result:
                        print(f"✓ {test_name} completed successfully")
                    else:
                        print(f"✗ {test_name} failed")
                except Exception as e:
                    print(f"✗ {test_name} failed with exception: {e}")
                    self.results[test_name.lower().replace(' ', '_')] = False
            
            # Generate and display report
            report = self.generate_test_report()
            print("\n" + report)
            
            # Save report to file
            report_file = self.project_root / 'tests' / 'container' / 'test_report.txt'
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\nTest report saved to: {report_file}")
            
            # Return overall success
            return all(self.results.values())
            
        finally:
            self.cleanup_test_directories()


def main():
    """Main test execution."""
    runner = ContainerTestRunner()
    success = runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())