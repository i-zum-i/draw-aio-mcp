# MCP Draw.io サーバー API ドキュメント

## 概要

MCP Draw.io サーバーは、Draw.io 図表の生成、保存、変換を行う3つのModel Context Protocol（MCP）ツールを提供します。このドキュメントでは、各ツールの包括的なAPI仕様、パラメータの詳細、戻り値、エラーコードを説明します。

## 目次

- [ツール概要](#ツール概要)
- [generate-drawio-xml](#generate-drawio-xml)
- [save-drawio-file](#save-drawio-file)
- [convert-to-png](#convert-to-png)
- [エラーコードリファレンス](#エラーコードリファレンス)
- [共通レスポンスパターン](#共通レスポンスパターン)
- [使用例](#使用例)

## ツール概要

| ツール名 | 目的 | 入力 | 出力 |
|-----------|---------|-------|--------|
| `generate-drawio-xml` | 自然言語からDraw.io XMLを生成 | テキストプロンプト | Draw.io XMLコンテンツ |
| `save-drawio-file` | XMLコンテンツを一時ファイルに保存 | XMLコンテンツ + オプションのファイル名 | ファイルIDとメタデータ |
| `convert-to-png` | Draw.ioファイルをPNG画像に変換 | ファイルIDまたはパス | PNGファイル情報 |

## generate-drawio-xml

Generates Draw.io XML diagram content from natural language descriptions using Claude AI.

### Tool Schema

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

### Parameters

#### `prompt` (required)
- **Type**: `string`
- **Description**: Natural language description of the diagram to generate
- **Constraints**: 
  - Minimum length: 5 characters
  - Maximum length: 10,000 characters
  - Must be non-empty after trimming whitespace
- **Examples**:
  - `"Create a flowchart showing user login process"`
  - `"Generate an AWS architecture diagram with EC2, RDS, and S3"`
  - `"Draw a simple organizational chart with CEO, managers, and employees"`

### Response Format

```json
{
  "success": boolean,
  "xml_content": string | null,
  "error": string | null,
  "error_code": string | null,
  "timestamp": string
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the generation was successful |
| `xml_content` | `string \| null` | Valid Draw.io XML content (if successful) |
| `error` | `string \| null` | Human-readable error message (if failed) |
| `error_code` | `string \| null` | Machine-readable error code (if failed) |
| `timestamp` | `string` | ISO 8601 timestamp of the operation |

### Success Response Example

```json
{
  "success": true,
  "xml_content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<mxfile host=\"app.diagrams.net\" modified=\"2024-01-01T00:00:00.000Z\" agent=\"Claude\" version=\"22.1.11\">\n  <diagram name=\"Page-1\" id=\"abc123\">\n    <mxGraphModel dx=\"1422\" dy=\"794\" grid=\"1\" gridSize=\"10\" guides=\"1\" tooltips=\"1\" connect=\"1\" arrows=\"1\" fold=\"1\" page=\"1\" pageScale=\"1\" pageWidth=\"827\" pageHeight=\"1169\" math=\"0\" shadow=\"0\">\n      <root>\n        <mxCell id=\"0\" />\n        <mxCell id=\"1\" parent=\"0\" />\n        <!-- Diagram content -->\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>",
  "error": null,
  "error_code": null,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Error Response Example

```json
{
  "success": false,
  "xml_content": null,
  "error": "Invalid input: Prompt is too short (minimum 5 characters)",
  "error_code": "INVALID_INPUT",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Possible Error Codes

- `INVALID_INPUT` - Input validation failed
- `API_KEY_MISSING` - Anthropic API key not configured
- `CONNECTION_ERROR` - Network connection failed
- `RATE_LIMIT_ERROR` - API rate limit exceeded
- `QUOTA_EXCEEDED` - API quota exceeded
- `INVALID_RESPONSE` - Invalid response from Claude API
- `INVALID_XML` - Generated XML failed validation
- `TIMEOUT_ERROR` - Request timed out
- `UNKNOWN_ERROR` - Unexpected error occurred

## save-drawio-file

Saves Draw.io XML content to a temporary file and returns a file ID for future reference.

### Tool Schema

```json
{
  "name": "save-drawio-file",
  "description": "Save Draw.io XML content to a temporary file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "xml_content": {
        "type": "string",
        "description": "Valid Draw.io XML content to save",
        "minLength": 10
      },
      "filename": {
        "type": "string",
        "description": "Optional custom filename (without extension)",
        "maxLength": 100
      }
    },
    "required": ["xml_content"]
  }
}
```

### Parameters

#### `xml_content` (required)
- **Type**: `string`
- **Description**: Valid Draw.io XML content to save
- **Constraints**:
  - Minimum length: 10 characters
  - Must contain required Draw.io elements: `mxfile`, `mxGraphModel`, `root`
  - Must be valid XML structure
- **Validation**: Automatically validated for Draw.io XML structure

#### `filename` (optional)
- **Type**: `string`
- **Description**: Custom filename without extension (.drawio will be added automatically)
- **Constraints**:
  - Maximum length: 100 characters
  - Will be sanitized to remove invalid characters
  - If not provided, UUID-based filename will be generated
- **Examples**: `"my-diagram"`, `"user-flow-v2"`, `"aws-architecture"`

### Response Format

```json
{
  "success": boolean,
  "file_id": string | null,
  "file_path": string | null,
  "filename": string | null,
  "expires_at": string | null,
  "error": string | null,
  "error_code": string | null,
  "timestamp": string
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the save operation was successful |
| `file_id` | `string \| null` | Unique identifier for the saved file |
| `file_path` | `string \| null` | Absolute path to the saved file |
| `filename` | `string \| null` | Final filename used (including .drawio extension) |
| `expires_at` | `string \| null` | ISO 8601 timestamp when file will expire |
| `error` | `string \| null` | Human-readable error message (if failed) |
| `error_code` | `string \| null` | Machine-readable error code (if failed) |
| `timestamp` | `string` | ISO 8601 timestamp of the operation |

### Success Response Example

```json
{
  "success": true,
  "file_id": "abc123-def456-ghi789",
  "file_path": "/app/temp/my-diagram_abc123.drawio",
  "filename": "my-diagram_abc123.drawio",
  "expires_at": "2024-01-02T12:00:00.000Z",
  "error": null,
  "error_code": null,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Error Response Example

```json
{
  "success": false,
  "file_id": null,
  "file_path": null,
  "filename": null,
  "expires_at": null,
  "error": "Invalid XML content: missing required element 'mxfile'",
  "error_code": "INVALID_XML",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Possible Error Codes

- `INVALID_XML` - XML content validation failed
- `INVALID_FILENAME` - Filename validation failed
- `SERVICE_ERROR` - File service initialization failed
- `FILE_SERVICE_ERROR` - File operation failed
- `PERMISSION_DENIED` - Insufficient permissions
- `DISK_FULL` - Insufficient disk space
- `UNKNOWN_ERROR` - Unexpected error occurred

## convert-to-png

Converts a Draw.io file to PNG format using the Draw.io CLI. Supports both file ID (from save-drawio-file) and direct file path input.

### Tool Schema

```json
{
  "name": "convert-to-png",
  "description": "Convert Draw.io file to PNG image using Draw.io CLI",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_id": {
        "type": "string",
        "description": "File ID returned from save-drawio-file tool (recommended)"
      },
      "file_path": {
        "type": "string",
        "description": "Direct path to .drawio file (alternative to file_id)"
      }
    },
    "oneOf": [
      {"required": ["file_id"]},
      {"required": ["file_path"]}
    ]
  }
}
```

### Parameters

You must provide exactly one of the following parameters:

#### `file_id` (conditional)
- **Type**: `string`
- **Description**: File ID returned from the save-drawio-file tool
- **Recommended**: This is the preferred method as it ensures file validity
- **Example**: `"abc123-def456-ghi789"`

#### `file_path` (conditional)
- **Type**: `string`
- **Description**: Direct path to a .drawio file
- **Constraints**: Must be a valid path to an existing .drawio file
- **Example**: `"/path/to/diagram.drawio"`

### Response Format

```json
{
  "success": boolean,
  "png_file_id": string | null,
  "png_file_path": string | null,
  "base64_content": string | null,
  "error": string | null,
  "error_code": string | null,
  "cli_available": boolean,
  "fallback_message": string | null,
  "alternatives": object | null,
  "timestamp": string,
  "troubleshooting": object | null,
  "metadata": object | null
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the conversion was successful |
| `png_file_id` | `string \| null` | Unique identifier for the PNG file |
| `png_file_path` | `string \| null` | Absolute path to the PNG file |
| `base64_content` | `string \| null` | Base64 encoded PNG content (optional) |
| `error` | `string \| null` | Human-readable error message (if failed) |
| `error_code` | `string \| null` | Machine-readable error code (if failed) |
| `cli_available` | `boolean` | Whether Draw.io CLI is available |
| `fallback_message` | `string \| null` | Detailed fallback instructions (if CLI unavailable) |
| `alternatives` | `object \| null` | Alternative options when CLI is unavailable |
| `timestamp` | `string` | ISO 8601 timestamp of the operation |
| `troubleshooting` | `object \| null` | Troubleshooting information (if failed) |
| `metadata` | `object \| null` | Additional metadata about the operation |

### Success Response Example

```json
{
  "success": true,
  "png_file_id": "xyz789-abc123-def456",
  "png_file_path": "/app/temp/my-diagram_abc123.png",
  "base64_content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "error": null,
  "error_code": null,
  "cli_available": true,
  "fallback_message": null,
  "alternatives": null,
  "timestamp": "2024-01-01T12:00:00.000Z",
  "troubleshooting": null,
  "metadata": {
    "original_file_id": "abc123-def456-ghi789",
    "original_file_path": "/app/temp/my-diagram_abc123.drawio",
    "conversion_message": "Successfully converted using Draw.io CLI",
    "file_size_bytes": 1024,
    "expires_at": "2024-01-02T12:00:00.000Z"
  }
}
```

### Error Response Example (CLI Not Available)

```json
{
  "success": false,
  "png_file_id": null,
  "png_file_path": null,
  "base64_content": null,
  "error": "Draw.io CLI is not available for PNG conversion",
  "error_code": "CLI_NOT_AVAILABLE",
  "cli_available": false,
  "fallback_message": "Draw.io CLI is required for PNG conversion. Install it with: npm install -g @drawio/drawio-desktop-cli",
  "alternatives": {
    "manual_export": "Open the .drawio file in Draw.io Desktop and export as PNG manually",
    "web_version": "Use Draw.io web version at https://app.diagrams.net/ to open and export the file",
    "docker_solution": "Use the Docker container which includes Draw.io CLI pre-installed"
  },
  "timestamp": "2024-01-01T12:00:00.000Z",
  "troubleshooting": {
    "check_installation": "Run 'drawio --version' to check if CLI is installed",
    "install_command": "npm install -g @drawio/drawio-desktop-cli",
    "docker_alternative": "Use the provided Docker container for guaranteed CLI availability"
  },
  "metadata": {
    "original_file_id": "abc123-def456-ghi789",
    "original_file_path": "/app/temp/my-diagram_abc123.drawio"
  }
}
```

### Possible Error Codes

- `MISSING_PARAMETER` - Neither file_id nor file_path provided
- `CONFLICTING_PARAMETERS` - Both file_id and file_path provided
- `INVALID_FILE_ID` - File ID format is invalid
- `INVALID_FILE_PATH` - File path format is invalid
- `FILE_NOT_FOUND` - File does not exist or has expired
- `INVALID_FILE_TYPE` - File is not a .drawio file
- `CLI_NOT_AVAILABLE` - Draw.io CLI is not installed
- `CONVERSION_FAILED` - PNG conversion failed
- `IMAGE_SERVICE_ERROR` - Image service error
- `SERVICE_INITIALIZATION_ERROR` - Service initialization failed
- `UNKNOWN_ERROR` - Unexpected error occurred

## Error Codes Reference

### LLM Service Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| `API_KEY_MISSING` | Anthropic API key not configured | Missing ANTHROPIC_API_KEY environment variable | Set the API key in environment variables |
| `CONNECTION_ERROR` | Network connection failed | Network issues, firewall, DNS problems | Check network connectivity |
| `RATE_LIMIT_ERROR` | API rate limit exceeded | Too many requests in short time | Wait and retry, implement backoff |
| `QUOTA_EXCEEDED` | API quota exceeded | Monthly/daily quota reached | Check Anthropic account limits |
| `INVALID_RESPONSE` | Invalid response from Claude API | API returned unexpected format | Retry request, check API status |
| `INVALID_XML` | Generated XML failed validation | Claude generated invalid Draw.io XML | Retry with different prompt |
| `TIMEOUT_ERROR` | Request timed out | Long-running request exceeded timeout | Retry with shorter prompt |
| `UNKNOWN_ERROR` | Unexpected LLM service error | Various internal errors | Check logs, retry request |

### File Service Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| `FILE_NOT_FOUND` | File does not exist | Invalid file ID, file expired | Check file ID, regenerate if expired |
| `FILE_EXPIRED` | File has expired | File older than retention period | Regenerate and save new file |
| `INVALID_FILE_ID` | File ID format is invalid | Malformed file ID string | Use valid file ID from save operation |
| `PERMISSION_DENIED` | Insufficient file permissions | File system permission issues | Check container/process permissions |
| `DISK_FULL` | Insufficient disk space | Storage volume full | Free up disk space |
| `INVALID_FILENAME` | Filename validation failed | Invalid characters in filename | Use alphanumeric characters only |
| `FILE_TOO_LARGE` | File exceeds size limits | XML content too large | Reduce diagram complexity |
| `CLEANUP_ERROR` | File cleanup operation failed | Permission or lock issues | Check file system status |
| `UNKNOWN_ERROR` | Unexpected file service error | Various internal errors | Check logs, retry operation |

### Image Service Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| `CLI_NOT_AVAILABLE` | Draw.io CLI not installed | Missing Draw.io CLI installation | Install CLI or use Docker container |
| `CLI_EXECUTION_ERROR` | CLI execution failed | CLI crashed or returned error | Check CLI installation, file validity |
| `INVALID_INPUT_FILE` | Input file is invalid | Corrupted or invalid .drawio file | Regenerate the Draw.io file |
| `OUTPUT_FILE_ERROR` | Output file creation failed | Permission or disk space issues | Check permissions and disk space |
| `CONVERSION_TIMEOUT` | Conversion process timed out | Complex diagram or system load | Simplify diagram or retry |
| `UNSUPPORTED_FORMAT` | File format not supported | Non-.drawio file provided | Ensure file has .drawio extension |
| `UNKNOWN_ERROR` | Unexpected image service error | Various internal errors | Check logs, retry operation |

### General MCP Server Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| `INVALID_REQUEST` | Request format is invalid | Malformed MCP request | Check request format |
| `METHOD_NOT_FOUND` | MCP method not found | Invalid tool name | Use valid tool names |
| `INVALID_PARAMETERS` | Parameter validation failed | Missing or invalid parameters | Check parameter requirements |
| `TOOL_NOT_FOUND` | Requested tool not found | Invalid tool name in request | Use valid tool names |
| `TOOL_EXECUTION_ERROR` | Tool execution failed | Various tool-specific errors | Check tool-specific error details |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | System overload or maintenance | Retry after delay |
| `CONFIGURATION_ERROR` | Server configuration error | Invalid environment variables | Check server configuration |
| `INITIALIZATION_ERROR` | Server initialization failed | Startup configuration issues | Check server logs and config |
| `UNKNOWN_ERROR` | Unexpected server error | Various internal errors | Check server logs |

## Common Response Patterns

### Success Response Pattern

All successful tool responses follow this pattern:

```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00.000Z",
  // Tool-specific success fields
  "error": null,
  "error_code": null
}
```

### Error Response Pattern

All error responses follow this pattern:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2024-01-01T12:00:00.000Z",
  // Tool-specific null fields
}
```

### Timestamp Format

All timestamps use ISO 8601 format with UTC timezone:
- Format: `YYYY-MM-DDTHH:mm:ss.sssZ`
- Example: `2024-01-01T12:00:00.000Z`

## Usage Examples

### Complete Workflow Example

```javascript
// 1. Generate Draw.io XML
const generateResult = await mcpClient.callTool("generate-drawio-xml", {
  prompt: "Create a simple user login flowchart with start, login form, validation, success, and error states"
});

if (generateResult.success) {
  console.log("Generated XML successfully");
  
  // 2. Save the XML to a file
  const saveResult = await mcpClient.callTool("save-drawio-file", {
    xml_content: generateResult.xml_content,
    filename: "user-login-flow"
  });
  
  if (saveResult.success) {
    console.log(`File saved with ID: ${saveResult.file_id}`);
    
    // 3. Convert to PNG
    const convertResult = await mcpClient.callTool("convert-to-png", {
      file_id: saveResult.file_id
    });
    
    if (convertResult.success) {
      console.log(`PNG created: ${convertResult.png_file_path}`);
      console.log(`Base64 content available: ${convertResult.base64_content ? 'Yes' : 'No'}`);
    } else {
      console.error(`PNG conversion failed: ${convertResult.error}`);
      if (!convertResult.cli_available) {
        console.log(`Fallback: ${convertResult.fallback_message}`);
      }
    }
  } else {
    console.error(`File save failed: ${saveResult.error}`);
  }
} else {
  console.error(`XML generation failed: ${generateResult.error}`);
}
```

### Error Handling Example

```javascript
async function handleToolCall(toolName, params) {
  try {
    const result = await mcpClient.callTool(toolName, params);
    
    if (result.success) {
      return result;
    } else {
      // Handle specific error codes
      switch (result.error_code) {
        case 'API_KEY_MISSING':
          throw new Error('Please configure your Anthropic API key');
        case 'RATE_LIMIT_ERROR':
          console.log('Rate limited, waiting 60 seconds...');
          await new Promise(resolve => setTimeout(resolve, 60000));
          return handleToolCall(toolName, params); // Retry
        case 'CLI_NOT_AVAILABLE':
          console.log('Draw.io CLI not available, alternatives:');
          console.log(result.alternatives);
          throw new Error(result.fallback_message);
        default:
          throw new Error(`Tool failed: ${result.error} (${result.error_code})`);
      }
    }
  } catch (error) {
    console.error(`Tool call failed: ${error.message}`);
    throw error;
  }
}
```

### Batch Processing Example

```javascript
async function processDiagramBatch(prompts) {
  const results = [];
  
  for (const [index, prompt] of prompts.entries()) {
    try {
      console.log(`Processing diagram ${index + 1}/${prompts.length}`);
      
      // Generate XML
      const xmlResult = await mcpClient.callTool("generate-drawio-xml", { prompt });
      if (!xmlResult.success) {
        results.push({ index, error: xmlResult.error, step: 'generate' });
        continue;
      }
      
      // Save file
      const saveResult = await mcpClient.callTool("save-drawio-file", {
        xml_content: xmlResult.xml_content,
        filename: `diagram-${index + 1}`
      });
      if (!saveResult.success) {
        results.push({ index, error: saveResult.error, step: 'save' });
        continue;
      }
      
      // Convert to PNG
      const pngResult = await mcpClient.callTool("convert-to-png", {
        file_id: saveResult.file_id
      });
      
      results.push({
        index,
        success: pngResult.success,
        file_id: saveResult.file_id,
        png_file_id: pngResult.png_file_id,
        error: pngResult.success ? null : pngResult.error
      });
      
    } catch (error) {
      results.push({ index, error: error.message, step: 'exception' });
    }
  }
  
  return results;
}
```

## Performance Considerations

### Caching

The `generate-drawio-xml` tool includes intelligent caching:
- Identical prompts return cached results
- Cache TTL: 1 hour (configurable)
- Cache size limit: 100 entries (configurable)
- Automatic cleanup of expired entries

### File Expiration

Temporary files have automatic expiration:
- Default expiration: 24 hours
- Automatic cleanup runs every hour
- Files are cleaned up when expired or on server restart

### Rate Limiting

Be aware of Anthropic API rate limits:
- Implement exponential backoff for rate limit errors
- Monitor your API usage and quotas
- Consider caching for repeated requests

### Resource Usage

- Memory: ~256MB minimum, 512MB recommended
- Disk: Temporary files require storage space
- CPU: PNG conversion is CPU-intensive
- Network: Outbound HTTPS for Claude API

## Security Considerations

### Input Validation

All tools perform comprehensive input validation:
- Prompt sanitization removes control characters
- XML validation ensures proper structure
- Filename sanitization prevents path traversal
- File type validation ensures .drawio files only

### File Security

- Files are stored in isolated temporary directories
- Automatic cleanup prevents disk space exhaustion
- Non-root container execution
- No persistent storage of sensitive data

### API Security

- API keys are never logged or exposed
- All external API calls use HTTPS
- Error messages don't expose internal details
- Request/response logging excludes sensitive data

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure `ANTHROPIC_API_KEY` environment variable is set
   - Verify API key is valid and has sufficient quota

2. **Draw.io CLI Issues**
   - Install CLI: `npm install -g @drawio/drawio-desktop-cli`
   - Verify installation: `drawio --version`
   - Use Docker container for guaranteed CLI availability

3. **File Not Found Errors**
   - Check if file has expired (24-hour default)
   - Verify file ID is correct and complete
   - Regenerate file if necessary

4. **Permission Errors**
   - Ensure container has write permissions to temp directory
   - Check disk space availability
   - Verify non-root user has appropriate permissions

### Debug Information

Enable debug logging by setting environment variables:
```bash
LOG_LEVEL=DEBUG
ANTHROPIC_LOG_LEVEL=DEBUG
```

### Support Resources

- Check server logs for detailed error information
- Use the validation tools provided in the test suite
- Refer to the troubleshooting sections in individual tool responses
- Review the installation and configuration guides

---

*This API documentation is automatically generated from the source code and is kept up-to-date with each release.*