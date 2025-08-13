# MCP Draw.io Server

A Model Context Protocol (MCP) server that generates Draw.io diagrams from natural language descriptions using Claude AI.

## Features

- Generate Draw.io XML diagrams from natural language prompts
- Save diagrams to temporary files with automatic cleanup
- Convert Draw.io files to PNG images using Draw.io CLI
- Lightweight containerized deployment
- Comprehensive error handling and logging

## Requirements

- Python 3.10 or higher
- Anthropic API key
- Draw.io CLI (for PNG conversion)

## Installation

### Development Setup

1. Clone the repository and navigate to the mcp-server directory:
```bash
cd mcp-server
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Copy the environment template and configure:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Production Setup

1. Install production dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

## Usage

### Running the Server

```bash
python -m src.server
```

### Available MCP Tools

1. **generate-drawio-xml**: Generate Draw.io XML from natural language
2. **save-drawio-file**: Save XML content to temporary files
3. **convert-to-png**: Convert Draw.io files to PNG images

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
isort src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Project Structure

```
mcp-server/
├── src/                    # Source code
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── services/          # Business logic services
│   └── models/            # Data models
├── tests/                 # Test files
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docker/               # Docker configuration
├── pyproject.toml        # Project configuration
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

## License

MIT License