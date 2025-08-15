#!/usr/bin/env python3
"""
Container Test Validation Script
Validates that container test files are properly structured and can be executed.
"""

import os
import sys
import subprocess
from pathlib import Path


def validate_test_files():
    """Validate that all test files exist and are properly structured."""
    project_root = Path(__file__).parent
    
    required_files = [
        "tests/container/test_docker_build.py",
        "tests/container/test_container_runtime.py", 
        "tests/container/run_container_tests.py",
        "run_container_tests.sh",
        "run_container_tests.ps1"
    ]
    
    print("Validating container test files...")
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_files:
        print(f"\n✗ Missing files: {missing_files}")
        return False
    
    print("\n✓ All container test files present")
    return True


def validate_python_syntax():
    """Validate Python test files have correct syntax."""
    project_root = Path(__file__).parent
    
    python_files = [
        "tests/container/test_docker_build.py",
        "tests/container/test_container_runtime.py",
        "tests/container/run_container_tests.py"
    ]
    
    print("\nValidating Python syntax...")
    
    for file_path in python_files:
        full_path = project_root / file_path
        try:
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(full_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ {file_path}")
            else:
                print(f"✗ {file_path}: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ {file_path}: {e}")
            return False
    
    print("\n✓ All Python files have valid syntax")
    return True


def validate_documentation():
    """Validate that documentation files exist."""
    project_root = Path(__file__).parent
    
    doc_files = [
        "docs/MCP_SERVER_USAGE_GUIDE.md",
        "docs/INSTALLATION_GUIDE.md",
        "docs/CLAUDE_CODE_INTEGRATION.md",
        "docs/README.md"
    ]
    
    print("\nValidating documentation files...")
    
    missing_docs = []
    for file_path in doc_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_docs.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_docs:
        print(f"\n✗ Missing documentation: {missing_docs}")
        return False
    
    print("\n✓ All documentation files present")
    return True


def validate_docker_files():
    """Validate Docker-related files."""
    project_root = Path(__file__).parent
    
    docker_files = [
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.dev.yml", 
        "docker-compose.prod.yml",
        ".dockerignore"
    ]
    
    print("\nValidating Docker files...")
    
    missing_docker = []
    for file_path in docker_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_docker.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_docker:
        print(f"\n✗ Missing Docker files: {missing_docker}")
        return False
    
    print("\n✓ All Docker files present")
    return True


def check_prerequisites():
    """Check if required tools are available."""
    print("\nChecking prerequisites...")
    
    tools = [
        ("python", ["python", "--version"]),
        ("docker", ["docker", "--version"])
    ]
    
    missing_tools = []
    for tool_name, command in tools:
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✓ {tool_name}: {version}")
            else:
                missing_tools.append(tool_name)
        except FileNotFoundError:
            missing_tools.append(tool_name)
    
    if missing_tools:
        print(f"\n⚠ Missing tools (tests may not run): {missing_tools}")
        return False
    
    print("\n✓ All prerequisites available")
    return True


def main():
    """Main validation function."""
    print("Container Test Validation")
    print("=" * 50)
    
    validations = [
        ("Test Files", validate_test_files),
        ("Python Syntax", validate_python_syntax),
        ("Documentation", validate_documentation),
        ("Docker Files", validate_docker_files),
        ("Prerequisites", check_prerequisites)
    ]
    
    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ {name} validation failed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"Validation Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All validations passed! Container tests are ready to run.")
        print("\nTo run container tests:")
        print("  Windows: .\\run_container_tests.ps1")
        print("  Linux/Mac: ./run_container_tests.sh")
        print("  Python: python tests/container/run_container_tests.py")
        return 0
    else:
        print("✗ Some validations failed! Please fix issues before running tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())