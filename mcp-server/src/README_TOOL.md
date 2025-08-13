# generate-drawio-xml MCP Tool

This document describes the `generate-drawio-xml` MCP tool implementation.

## Overview

The `generate-drawio-xml` tool converts natural language descriptions into valid Draw.io XML format that can be opened in diagrams.net. It supports various diagram types including flowcharts, system diagrams, AWS architecture diagrams, and more.

## Implementation Details

### Tool Function

```python
async def generate_drawio_xml(prompt: str) -> Dict[str, Any]
```

### Input Parameters

- **prompt** (string, required): Natural language description of the diagram to generate
  - Minimum length: 5 characters
  - Maximum length: 10,000 characters
  - Must be a non-empty string

### Return Format

```python
{
    "success": bool,           # Whether the generation was successful
    "xml_content": str,        # Valid Draw.io XML content (if successful)
    "error": str,              # Error message (if failed)
    "error_code": str,         # Specific error code for programmatic handling (if failed)
    "timestamp": str           # ISO timestamp of the generation
}
```

### Error Codes

- `INVALID_INPUT`: Input validation failed (empty, too short, too long, etc.)
- `API_KEY_MISSING`: Anthropic API key not configured
- `CONNECTION_ERROR`: Network connection issues
- `RATE_LIMIT_ERROR`: API rate limit exceeded
- `QUOTA_EXCEEDED`: API usage quota exceeded
- `INVALID_RESPONSE`: Invalid response from Claude API
- `INVALID_XML`: Generated XML failed validation
- `TIMEOUT_ERROR`: API request timed out
- `UNKNOWN_ERROR`: Unexpected error occurred

### Input Validation and Sanitization

The tool includes comprehensive input validation:

1. **Type checking**: Ensures input is a string
2. **Length validation**: Enforces minimum (5) and maximum (10,000) character limits
3. **Content sanitization**: Removes control characters while preserving natural language
4. **Empty string detection**: Rejects empty or whitespace-only inputs

### MCP Tool Schema

```json
{
    "name": "generate-drawio-xml",
    "description": "Generate Draw.io XML diagram from natural language prompt",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Natural language description of the diagram to generate",
                "minLength": 5,
                "maxLength": 10000
            }
        },
        "required": ["prompt"]
    }
}
```

## Usage Examples

### Basic Usage

```python
result = await generate_drawio_xml("Create a simple flowchart showing user login process")

if result["success"]:
    print("Generated XML:", result["xml_content"])
else:
    print("Error:", result["error"])
    print("Error Code:", result["error_code"])
```

### AWS Architecture Diagram

```python
result = await generate_drawio_xml("""
Create an AWS architecture diagram showing:
- VPC with public and private subnets
- Application Load Balancer in public subnet
- EC2 instances in private subnet
- RDS database in private subnet
- NAT Gateway for outbound traffic
""")
```

### System Architecture

```python
result = await generate_drawio_xml("""
Create a microservices architecture diagram with:
- API Gateway
- User Service
- Order Service
- Payment Service
- Database for each service
- Message queue between services
""")
```

## Error Handling

The tool implements comprehensive error handling:

1. **Input validation errors** are caught and returned with `INVALID_INPUT` code
2. **LLM service errors** are categorized and returned with appropriate error codes
3. **Unexpected errors** are caught and returned with `UNKNOWN_ERROR` code
4. **All errors include timestamps** for debugging purposes

## Integration with LLMService

The tool integrates with the `LLMService` class which provides:

- **Caching**: Identical prompts return cached results for better performance
- **XML validation**: Generated XML is validated for Draw.io compatibility
- **Error categorization**: API errors are properly categorized and handled
- **AWS diagram rules**: Special handling for AWS architecture diagrams

## Testing

The implementation includes comprehensive tests:

- **Structure tests**: Verify tool schema and function signatures
- **Input validation tests**: Test all validation scenarios
- **MCP server tests**: Test server request handling
- **Integration tests**: Test with actual API calls (requires API key)

Run tests with:

```bash
python test_structure.py    # Structure and validation tests
python test_mcp_server.py   # MCP server functionality tests
python test_tool.py         # Full integration tests (requires API key)
```

## Requirements Compliance

This implementation satisfies the following requirements:

- **Requirement 1.1**: Generates valid Draw.io XML from natural language prompts
- **Requirement 1.2**: Returns file ID for future reference (via timestamp and success tracking)
- **Requirement 1.3**: Validates XML structure for required elements
- **Requirement 1.4**: Applies AWS-specific diagram rules when generating AWS diagrams

## Dependencies

- `anthropic`: Claude API integration
- `python-dotenv`: Environment variable management (optional)
- Standard library modules: `asyncio`, `logging`, `datetime`, `typing`, `re`