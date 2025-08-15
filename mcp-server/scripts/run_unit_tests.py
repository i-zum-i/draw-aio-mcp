#!/usr/bin/env python3
"""
Unit test runner for LLMService and FileService.
Provides comprehensive testing with coverage reporting.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        print(f"Exit code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run unit tests for LLMService and FileService")
    parser.add_argument("--service", choices=["llm", "file", "both"], default="both",
                       help="Which service to test (default: both)")
    parser.add_argument("--coverage", action="store_true", default=True,
                       help="Generate coverage report (default: True)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--fast", action="store_true",
                       help="Skip slow tests")
    parser.add_argument("--html-coverage", action="store_true",
                       help="Generate HTML coverage report")
    
    args = parser.parse_args()
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    if script_dir.name != "mcp-server":
        print("ERROR: This script must be run from the mcp-server directory")
        sys.exit(1)
    
    # Build base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add test paths based on service selection
    if args.service == "llm":
        pytest_cmd.append("tests/unit/test_llm_service.py")
    elif args.service == "file":
        pytest_cmd.append("tests/unit/test_file_service.py")
    else:  # both
        pytest_cmd.append("tests/unit/")
    
    # Add options
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])
    
    if args.coverage:
        pytest_cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
        
        if args.html_coverage:
            pytest_cmd.append("--cov-report=html")
    
    # Add other useful options
    pytest_cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--strict-markers",  # Strict marker checking
        "--strict-config"  # Strict config checking
    ])
    
    # Run the tests
    success = run_command(pytest_cmd, "Unit Tests")
    
    if success:
        print(f"\n{'='*60}")
        print("✅ ALL TESTS PASSED!")
        print(f"{'='*60}")
        
        if args.coverage:
            print("\n📊 Coverage report generated:")
            print("  - Terminal: Displayed above")
            print("  - XML: coverage.xml")
            if args.html_coverage:
                print("  - HTML: htmlcov/index.html")
        
        # Run mock strategy documentation tests
        mock_cmd = ["python", "-m", "pytest", "tests/unit/test_mock_strategies.py", "-v"]
        print(f"\n{'='*60}")
        print("Running mock strategy documentation tests...")
        print(f"{'='*60}")
        run_command(mock_cmd, "Mock Strategy Tests")
        
    else:
        print(f"\n{'='*60}")
        print("❌ TESTS FAILED!")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()