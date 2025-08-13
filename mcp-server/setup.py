#!/usr/bin/env python3
"""
Setup script for MCP Draw.io Server development environment.
This script helps set up the Python virtual environment and install dependencies.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command: str, cwd: Path = None) -> bool:
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(
            command.split(),
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Set up the development environment."""
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    
    print("Setting up MCP Draw.io Server development environment...")
    print(f"Project root: {project_root}")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("Error: Python 3.10 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create virtual environment
    if not venv_path.exists():
        print("Creating virtual environment...")
        if not run_command(f"python -m venv {venv_path}", project_root):
            print("Failed to create virtual environment")
            sys.exit(1)
    else:
        print("✓ Virtual environment already exists")
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate"
        pip_path = venv_path / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    # Install dependencies
    print("Installing dependencies...")
    if not run_command(f"{pip_path} install --upgrade pip", project_root):
        print("Failed to upgrade pip")
        sys.exit(1)
    
    if not run_command(f"{pip_path} install -r requirements-dev.txt", project_root):
        print("Failed to install dependencies")
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✓ .env file created - please edit it to add your ANTHROPIC_API_KEY")
    
    print("\n" + "="*50)
    print("Setup complete! 🎉")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':
        print(f"   {activate_script}")
    else:
        print(f"   source {activate_script}")
    print("2. Edit .env file and add your ANTHROPIC_API_KEY")
    print("3. Run tests: pytest")
    print("4. Start development!")


if __name__ == "__main__":
    main()