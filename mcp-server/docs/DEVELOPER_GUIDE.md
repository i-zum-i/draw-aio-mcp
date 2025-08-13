# MCP Draw.io サーバー 開発者ガイド

## 概要

このガイドは、MCP Draw.io サーバーのコードベースに貢献、拡張、または理解したい開発者向けの包括的な情報を提供します。開発環境のセットアップ、テスト手順、コードアーキテクチャ、貢献ガイドラインをカバーしています。

## 目次

- [開発環境セットアップ](#開発環境セットアップ)
- [プロジェクト構造](#プロジェクト構造)
- [アーキテクチャ概要](#アーキテクチャ概要)
- [テストフレームワーク](#テストフレームワーク)
- [コード標準](#コード標準)
- [貢献ガイドライン](#貢献ガイドライン)
- [デバッグとトラブルシューティング](#デバッグとトラブルシューティング)
- [パフォーマンス最適化](#パフォーマンス最適化)
- [セキュリティ考慮事項](#セキュリティ考慮事項)
- [リリースプロセス](#リリースプロセス)

## Development Environment Setup

### Prerequisites

- **Python 3.10+** - Required for the MCP server
- **Node.js 18+** - Required for Draw.io CLI
- **Docker** - Required for containerized development and testing
- **Git** - For version control

### Quick Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd mcp-server
   ```

2. **Create Python Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Install Draw.io CLI**
   ```bash
   npm install -g @drawio/drawio-desktop-cli
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Anthropic API key
   ```

6. **Verify Setup**
   ```bash
   python run_unit_tests.py
   ```

### Development Dependencies

The project uses several development tools:

```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt
```

Key development packages:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `pre-commit` - Git hooks

### IDE Configuration

#### VS Code Setup

Recommended extensions:
- Python
- Pylance
- Python Docstring Generator
- GitLens
- Docker

Workspace settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".coverage": true,
    "htmlcov": true
  }
}
```

#### PyCharm Setup

1. Configure Python interpreter to use the virtual environment
2. Enable pytest as the test runner
3. Configure code style to use Black formatter
4. Enable type checking with mypy

## Project Structure

```
mcp-server/
├── src/                          # Source code
│   ├── __init__.py
│   ├── server.py                 # MCP server implementation
│   ├── tools.py                  # MCP tool definitions
│   ├── llm_service.py           # Claude API integration
│   ├── file_service.py          # File management
│   ├── image_service.py         # PNG conversion
│   ├── exceptions.py            # Custom exceptions
│   ├── config.py                # Configuration management
│   └── health.py                # Health check endpoints
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── container/               # Container tests
│   ├── fixtures/                # Test data and utilities
│   └── conftest.py              # Pytest configuration
├── docs/                         # Documentation
│   ├── API_DOCUMENTATION.md     # API reference
│   ├── DEVELOPER_GUIDE.md       # This file
│   ├── INSTALLATION_GUIDE.md    # Installation instructions
│   └── MCP_SERVER_USAGE_GUIDE.md # Usage guide
├── docker/                       # Docker configuration
│   ├── Dockerfile               # Multi-stage build
│   ├── build.sh                 # Build scripts
│   └── README.md                # Docker documentation
├── config/                       # Configuration files
│   └── fluent-bit.conf          # Logging configuration
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── pyproject.toml               # Project configuration
├── Makefile                     # Build automation
├── docker-compose.yml           # Development environment
├── docker-compose.prod.yml      # Production environment
└── README.md                    # Project overview
```

### Key Files and Directories

#### Source Code (`src/`)

- **`server.py`** - Main MCP server implementation using the MCP SDK
- **`tools.py`** - MCP tool definitions and implementations
- **`llm_service.py`** - Claude API integration with caching and error handling
- **`file_service.py`** - Temporary file management with automatic cleanup
- **`image_service.py`** - Draw.io CLI integration for PNG conversion
- **`exceptions.py`** - Custom exception classes with error codes
- **`config.py`** - Configuration management and validation
- **`health.py`** - Health check endpoints for monitoring

#### Tests (`tests/`)

- **`unit/`** - Unit tests for individual components
- **`integration/`** - Integration tests for component interactions
- **`container/`** - Docker container validation tests
- **`fixtures/`** - Shared test data and utilities
- **`conftest.py`** - Pytest configuration and fixtures

#### Documentation (`docs/`)

- **`API_DOCUMENTATION.md`** - Complete API reference
- **`DEVELOPER_GUIDE.md`** - Development and contribution guide
- **`INSTALLATION_GUIDE.md`** - Installation and setup instructions
- **`MCP_SERVER_USAGE_GUIDE.md`** - End-user usage guide

## Architecture Overview

### High-Level Architecture

The MCP Draw.io Server follows a layered architecture:

```
┌─────────────────────────────────────┐
│           MCP Client                │
│        (Claude Code, etc.)          │
└─────────────────┬───────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────┐
│           MCP Server                │
│         (server.py)                 │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│          MCP Tools                  │
│         (tools.py)                  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│        Service Layer                │
│  ┌─────────────────────────────────┐ │
│  │      LLMService                 │ │
│  │   (Claude API)                  │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │     FileService                 │ │
│  │  (File Management)              │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │    ImageService                 │ │
│  │  (PNG Conversion)               │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Component Responsibilities

#### MCP Server (`server.py`)
- Implements the MCP protocol
- Handles client connections and requests
- Routes tool calls to appropriate handlers
- Manages server lifecycle and health checks

#### MCP Tools (`tools.py`)
- Defines the three main tools: generate-drawio-xml, save-drawio-file, convert-to-png
- Handles input validation and sanitization
- Coordinates service layer calls
- Formats responses according to MCP standards

#### Service Layer
- **LLMService**: Claude API integration, caching, XML validation
- **FileService**: Temporary file management, cleanup, metadata tracking
- **ImageService**: Draw.io CLI integration, PNG conversion, fallback handling

### Design Patterns

#### Singleton Pattern
- **FileService** uses singleton pattern to ensure single instance
- Prevents multiple cleanup schedulers and ensures consistent state

#### Factory Pattern
- Service initialization uses factory methods
- Allows for easy testing with mock services

#### Strategy Pattern
- Error handling strategies for different error types
- Fallback strategies when Draw.io CLI is unavailable

#### Observer Pattern
- File cleanup scheduler observes file expiration
- Health checks observe service states

### Data Flow

#### XML Generation Flow
1. Client sends prompt to `generate-drawio-xml` tool
2. Tool validates and sanitizes input
3. LLMService checks cache for existing result
4. If not cached, LLMService calls Claude API
5. Response is validated as proper Draw.io XML
6. Result is cached and returned to client

#### File Save Flow
1. Client sends XML content to `save-drawio-file` tool
2. Tool validates XML structure
3. FileService generates unique file ID
4. XML is written to temporary file
5. File metadata is stored for tracking
6. File ID and metadata returned to client

#### PNG Conversion Flow
1. Client sends file ID to `convert-to-png` tool
2. Tool resolves file ID to file path
3. ImageService checks Draw.io CLI availability
4. If available, CLI converts .drawio to PNG
5. PNG file is registered with FileService
6. PNG file information returned to client

## Testing Framework

### Test Structure

The project uses pytest with a comprehensive test suite:

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_llm_service.py
│   ├── test_file_service.py
│   ├── test_image_service.py
│   └── test_mock_strategies.py
├── integration/             # Integration tests (slower, realistic)
│   ├── test_mcp_tools.py
│   └── test_end_to_end.py
├── container/               # Container tests (slowest, full environment)
│   ├── test_docker_build.py
│   └── test_container_runtime.py
├── fixtures/                # Shared test data
│   ├── sample_xml.py
│   └── sample_prompts.py
└── conftest.py             # Pytest configuration
```

### Running Tests

#### Unit Tests (Fast)
```bash
# Run all unit tests
python run_unit_tests.py

# Run specific service tests
python run_unit_tests.py --service llm
python run_unit_tests.py --service file

# Run with coverage
python run_unit_tests.py --coverage

# Generate HTML coverage report
python run_unit_tests.py --html-coverage
```

#### Integration Tests
```bash
# Run integration tests
python -m pytest tests/integration/ -v

# Run with API key (for full testing)
ANTHROPIC_API_KEY=your-key python -m pytest tests/integration/ -v
```

#### Container Tests
```bash
# Run container tests (requires Docker)
./run_container_tests.sh

# Windows
.\run_container_tests.ps1

# Python (cross-platform)
python tests/container/run_container_tests.py
```

#### All Tests
```bash
# Run complete test suite
make test

# Run with coverage
make test-coverage
```

### Test Categories

#### Unit Tests
- **Scope**: Individual functions and classes
- **Speed**: Very fast (< 1 second per test)
- **Dependencies**: Mocked external dependencies
- **Coverage**: 97% for LLMService, 82% for FileService

#### Integration Tests
- **Scope**: Component interactions
- **Speed**: Moderate (1-10 seconds per test)
- **Dependencies**: Real services with controlled inputs
- **Coverage**: End-to-end workflows

#### Container Tests
- **Scope**: Full containerized environment
- **Speed**: Slow (30+ seconds per test)
- **Dependencies**: Docker, full environment
- **Coverage**: Deployment and runtime validation

### Mock Strategies

#### Claude API Mocking
```python
@pytest.fixture
def mock_anthropic_client():
    with patch('anthropic.Anthropic') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        
        # Configure successful response
        mock_response = Mock()
        mock_response.content = [Mock(text="<mxfile>...</mxfile>")]
        mock_instance.messages.create.return_value = mock_response
        
        yield mock_instance
```

#### File System Mocking
```python
@pytest.fixture
def temp_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
```

#### Time Mocking
```python
@pytest.fixture
def mock_time():
    with patch('time.time') as mock_time:
        mock_time.return_value = 1640995200.0  # Fixed timestamp
        yield mock_time
```

### Writing Tests

#### Test Naming Convention
- Test files: `test_<component>.py`
- Test classes: `Test<Component><Functionality>`
- Test methods: `test_<specific_behavior>`

#### Example Unit Test
```python
class TestLLMServiceXMLGeneration:
    @pytest.mark.asyncio
    async def test_generate_drawio_xml_success(self, mock_anthropic_client):
        """Test successful XML generation with valid response."""
        # Arrange
        llm_service = LLMService(api_key="test-key")
        prompt = "Create a simple flowchart"
        expected_xml = "<mxfile>...</mxfile>"
        
        mock_anthropic_client.messages.create.return_value.content[0].text = expected_xml
        
        # Act
        result = await llm_service.generate_drawio_xml(prompt)
        
        # Assert
        assert result == expected_xml
        mock_anthropic_client.messages.create.assert_called_once()
```

#### Example Integration Test
```python
class TestMCPToolsIntegration:
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow: generate -> save -> convert."""
        # Generate XML
        xml_result = await generate_drawio_xml("Simple flowchart")
        assert xml_result["success"]
        
        # Save file
        save_result = await save_drawio_file(xml_result["xml_content"])
        assert save_result["success"]
        
        # Convert to PNG
        png_result = await convert_to_png(file_id=save_result["file_id"])
        # Note: May fail if CLI not available, but should handle gracefully
        assert "cli_available" in png_result
```

## Code Standards

### Python Style Guide

The project follows PEP 8 with some modifications:

#### Formatting
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes preferred
- **Imports**: Sorted with isort

#### Code Formatting Tools
```bash
# Format code with Black
black src/ tests/

# Sort imports
isort src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Type Hints

All functions should include type hints:

```python
from typing import Dict, List, Optional, Union, Any

async def generate_drawio_xml(prompt: str) -> Dict[str, Any]:
    """Generate Draw.io XML from prompt."""
    pass

def validate_xml(xml_content: str) -> None:
    """Validate XML content structure."""
    pass

class FileService:
    def __init__(self, temp_dir: Optional[str] = None) -> None:
        self.temp_dir = temp_dir or "./temp"
```

### Documentation Standards

#### Docstring Format
Use Google-style docstrings:

```python
def save_drawio_file(xml_content: str, filename: Optional[str] = None) -> str:
    """
    Save Draw.io XML content to a temporary file.
    
    Args:
        xml_content: Valid Draw.io XML content to save.
        filename: Optional custom filename without extension.
        
    Returns:
        Unique file identifier for the saved file.
        
    Raises:
        FileServiceError: If file saving fails.
        ValueError: If XML content is invalid.
        
    Example:
        >>> file_id = await save_drawio_file("<mxfile>...</mxfile>", "my-diagram")
        >>> print(f"Saved with ID: {file_id}")
    """
```

#### Code Comments
- Use comments sparingly for complex logic
- Prefer self-documenting code
- Comment the "why", not the "what"

```python
# Cache the result to avoid repeated API calls for identical prompts
cache_key = self._generate_cache_key(prompt)
if cached_result := self._get_from_cache(cache_key):
    return cached_result
```

### Error Handling

#### Exception Hierarchy
```python
# Use custom exception hierarchy
class MCPServerError(Exception):
    """Base exception for all MCP server errors."""
    pass

class LLMError(MCPServerError):
    """LLM service specific errors."""
    pass

class FileServiceError(MCPServerError):
    """File service specific errors."""
    pass
```

#### Error Response Format
```python
def create_error_response(error: Exception, error_code: str) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "success": False,
        "error": str(error),
        "error_code": error_code,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
```

### Logging Standards

#### Logger Configuration
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General information about program execution")
logger.warning("Something unexpected happened")
logger.error("A serious error occurred")
logger.critical("A very serious error occurred")
```

#### Structured Logging
```python
logger.info(
    "File saved successfully",
    extra={
        "file_id": file_id,
        "filename": filename,
        "size_bytes": len(xml_content),
        "expires_at": expires_at.isoformat()
    }
)
```

## Contribution Guidelines

### Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/mcp-drawio-server.git
   cd mcp-drawio-server
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements-dev.txt
   ```

4. **Make Changes**
   - Follow code standards
   - Add tests for new functionality
   - Update documentation

5. **Run Tests**
   ```bash
   python run_unit_tests.py
   python -m pytest tests/integration/
   ```

6. **Submit Pull Request**
   - Provide clear description
   - Reference related issues
   - Ensure CI passes

### Pull Request Process

#### Before Submitting
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] Commit messages are clear

#### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Code Review Guidelines

#### For Authors
- Keep PRs focused and small
- Provide clear descriptions
- Respond to feedback promptly
- Update based on review comments

#### For Reviewers
- Review for correctness, not style (automated)
- Check test coverage
- Verify documentation updates
- Consider security implications
- Be constructive in feedback

### Issue Reporting

#### Bug Reports
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python version: [e.g., 3.10.5]
- Docker version: [if applicable]

## Additional Context
Any other relevant information
```

#### Feature Requests
```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other approaches considered

## Additional Context
Any other relevant information
```

## Debugging and Troubleshooting

### Development Debugging

#### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
export ANTHROPIC_LOG_LEVEL=DEBUG
python -m src.server
```

#### Python Debugger
```python
import pdb; pdb.set_trace()  # Set breakpoint

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

#### VS Code Debugging
Launch configuration (`.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug MCP Server",
      "type": "python",
      "request": "launch",
      "module": "src.server",
      "console": "integratedTerminal",
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key",
        "LOG_LEVEL": "DEBUG"
      }
    }
  ]
}
```

### Common Issues

#### Import Errors
```bash
# Ensure PYTHONPATH includes src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or use -m flag
python -m src.server
```

#### API Key Issues
```bash
# Check environment variable
echo $ANTHROPIC_API_KEY

# Test API key validity
python -c "import anthropic; client = anthropic.Anthropic(); print('API key valid')"
```

#### Docker Issues
```bash
# Check Docker daemon
docker info

# Build with verbose output
docker build --progress=plain -t mcp-drawio-server .

# Check container logs
docker logs <container-id>
```

### Performance Profiling

#### Memory Profiling
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code here
    pass
```

#### CPU Profiling
```python
import cProfile
import pstats

# Profile a function
cProfile.run('your_function()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative').print_stats(10)
```

#### Async Profiling
```python
import asyncio
import time

async def profile_async_function():
    start_time = time.time()
    result = await your_async_function()
    end_time = time.time()
    print(f"Function took {end_time - start_time:.2f} seconds")
    return result
```

## Performance Optimization

### Caching Strategies

#### LLM Response Caching
```python
class LLMService:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.max_cache_size = 100
    
    def _generate_cache_key(self, prompt: str) -> str:
        """Generate cache key from prompt."""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get cached result if valid."""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.cache_ttl:
                return entry['result']
            else:
                del self.cache[key]
        return None
```

#### File Metadata Caching
```python
class FileService:
    def __init__(self):
        self.file_metadata = {}  # In-memory metadata cache
    
    async def get_file_info(self, file_id: str) -> TempFile:
        """Get file info with caching."""
        if file_id in self.file_metadata:
            return self.file_metadata[file_id]
        
        # Load from disk if not in cache
        file_info = await self._load_file_metadata(file_id)
        self.file_metadata[file_id] = file_info
        return file_info
```

### Async Optimization

#### Concurrent Operations
```python
async def process_multiple_prompts(prompts: List[str]) -> List[Dict]:
    """Process multiple prompts concurrently."""
    tasks = [generate_drawio_xml(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

#### Connection Pooling
```python
class LLMService:
    def __init__(self):
        # Use connection pooling for HTTP requests
        self.client = anthropic.Anthropic(
            max_retries=3,
            timeout=30.0
        )
```

### Memory Management

#### Cleanup Strategies
```python
class FileService:
    async def cleanup_expired_files(self):
        """Clean up expired files to free memory and disk space."""
        current_time = time.time()
        expired_files = []
        
        for file_id, file_info in self.file_metadata.items():
            if current_time > file_info.expires_at.timestamp():
                expired_files.append(file_id)
        
        for file_id in expired_files:
            await self._remove_file(file_id)
            del self.file_metadata[file_id]
```

#### Memory Monitoring
```python
import psutil
import logging

def log_memory_usage():
    """Log current memory usage."""
    process = psutil.Process()
    memory_info = process.memory_info()
    logging.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
```

## Security Considerations

### Input Validation

#### Prompt Sanitization
```python
def sanitize_prompt(prompt: str) -> str:
    """Sanitize user input prompt."""
    if not isinstance(prompt, str):
        raise ValueError("Prompt must be a string")
    
    # Remove control characters except newlines and tabs
    prompt = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', prompt)
    
    # Limit length
    if len(prompt) > 10000:
        raise ValueError("Prompt too long")
    
    return prompt.strip()
```

#### XML Validation
```python
def validate_drawio_xml(xml_content: str) -> None:
    """Validate Draw.io XML structure."""
    # Check for required elements
    required_elements = ['mxfile', 'mxGraphModel', 'root']
    for element in required_elements:
        if f'<{element}' not in xml_content:
            raise ValueError(f"Missing required element: {element}")
    
    # Basic XML parsing validation
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML structure: {e}")
```

### File Security

#### Path Traversal Prevention
```python
def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace('..', '')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename
```

#### Temporary File Security
```python
class FileService:
    def __init__(self, temp_dir: str = None):
        # Use secure temporary directory
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp(prefix='mcp_drawio_')
        
        self.temp_dir = Path(temp_dir)
        
        # Set restrictive permissions
        self.temp_dir.chmod(0o700)  # Owner read/write/execute only
```

### API Security

#### API Key Management
```python
class LLMService:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            raise LLMError("API key is required", LLMErrorCode.API_KEY_MISSING)
        
        # Never log the API key
        self.client = anthropic.Anthropic(api_key=api_key)
```

#### Request Validation
```python
def validate_mcp_request(request: Dict) -> None:
    """Validate MCP request structure."""
    required_fields = ['method', 'params']
    for field in required_fields:
        if field not in request:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate method name
    valid_methods = ['tools/call', 'tools/list']
    if request['method'] not in valid_methods:
        raise ValueError(f"Invalid method: {request['method']}")
```

## Release Process

### Version Management

#### Semantic Versioning
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

#### Version Update Process
1. Update version in `pyproject.toml`
2. Update version in `src/__init__.py`
3. Update CHANGELOG.md
4. Create git tag
5. Build and publish

### Build Process

#### Local Build
```bash
# Build Python package
python -m build

# Build Docker image
docker build -t mcp-drawio-server:latest .

# Test build
docker run --rm mcp-drawio-server:latest --version
```

#### Automated Build (CI/CD)
```yaml
# .github/workflows/build.yml
name: Build and Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements-dev.txt
      - run: python run_unit_tests.py
      - run: python -m pytest tests/integration/
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t mcp-drawio-server .
      - run: docker run --rm mcp-drawio-server --version
```

### Quality Gates

#### Pre-release Checklist
- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Documentation updated
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Docker image builds successfully
- [ ] Integration tests pass

#### Release Validation
```bash
# Run complete test suite
make test-all

# Security scan
bandit -r src/

# Performance benchmark
python benchmark/run_benchmarks.py

# Docker security scan
docker scan mcp-drawio-server:latest
```

### Deployment

#### Production Deployment
```bash
# Build production image
docker build -f Dockerfile.prod -t mcp-drawio-server:prod .

# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl http://localhost:8000/health
```

#### Rollback Process
```bash
# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
docker tag mcp-drawio-server:v1.0.0 mcp-drawio-server:latest
docker-compose -f docker-compose.prod.yml up -d
```

## Support and Resources

### Documentation
- [API Documentation](API_DOCUMENTATION.md)
- [Installation Guide](INSTALLATION_GUIDE.md)
- [Usage Guide](MCP_SERVER_USAGE_GUIDE.md)
- [Claude Code Integration](CLAUDE_CODE_INTEGRATION.md)

### Development Tools
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)

### Community
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and community support
- Code review process for contributions

### Troubleshooting
- Check the [troubleshooting section](MCP_SERVER_USAGE_GUIDE.md#troubleshooting) in the usage guide
- Review server logs for detailed error information
- Use the provided debugging tools and techniques
- Consult the test suite for usage examples

---

*This developer guide is maintained by the project contributors and updated with each release.*