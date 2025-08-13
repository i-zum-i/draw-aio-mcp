# API Key Validation

This document describes the improved API key validation functionality implemented in the MCP Draw.io Server.

## Overview

The API key validation system provides comprehensive validation of Anthropic API keys including:

- **Format validation**: Ensures keys follow the correct `sk-ant-` format
- **Test key detection**: Identifies and handles test/fake keys appropriately
- **Production key validation**: Performs actual API calls to validate real keys
- **Policy-based decisions**: Allows test keys in development environments
- **Startup validation**: Validates keys during server initialization

## Key Features

### 1. API Key Classification

The system automatically classifies API keys into categories:

- **Invalid**: Keys with incorrect format or missing
- **Test**: Keys that appear to be for testing (contain patterns like "test", "fake", "12345")
- **Production**: Keys that appear to be real production keys

### 2. Environment-Aware Validation

The validation behavior adapts based on the environment:

- **Development Mode**: Test keys are allowed
- **Production Mode**: Only valid production keys are accepted
- **Testing Environment**: Test keys are allowed when `TESTING=true` or `pytest` is detected

### 3. Real API Validation

For production keys, the system performs actual API calls to validate:

- Makes minimal API calls to verify key validity
- Handles various error conditions (rate limits, quota issues, network problems)
- Provides detailed error messages for troubleshooting

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `DEVELOPMENT_MODE`: Set to `true` to allow test keys (default: `false`)
- `ALLOW_TEST_API_KEYS`: Explicitly allow test keys regardless of mode (default: `false`)
- `TESTING`: Indicates testing environment (default: `false`)

### Example Configurations

#### Development Environment
```bash
export ANTHROPIC_API_KEY=sk-ant-test-key-12345
export DEVELOPMENT_MODE=true
```

#### Production Environment
```bash
export ANTHROPIC_API_KEY=sk-ant-api03_your_real_key_here
export DEVELOPMENT_MODE=false
```

#### Testing Environment
```bash
export ANTHROPIC_API_KEY=sk-ant-test-key-for-testing
export TESTING=true
```

## API Key Types and Behavior

### Test Keys

Test keys are identified by patterns such as:
- `sk-ant-test-*`
- `sk-ant-*-test-*`
- `sk-ant-*-fake-*`
- `sk-ant-*-12345-*`
- `sk-ant-*-testing-*`

**Behavior:**
- ✅ Allowed in development mode
- ✅ Allowed when `ALLOW_TEST_API_KEYS=true`
- ✅ Allowed in testing environments
- ❌ Rejected in production mode
- ❌ Cannot be used for actual API calls

### Production Keys

Production keys follow the format `sk-ant-api03_*` or similar real formats.

**Behavior:**
- ✅ Always allowed if valid
- 🔍 Validated through actual API calls
- 📊 Account information retrieved when possible
- ⚠️ May fail due to rate limits or quota issues

### Invalid Keys

Keys that don't follow the `sk-ant-` format are always rejected.

## Error Handling

The validation system provides detailed error messages for different scenarios:

### Common Error Codes

- `INVALID_FORMAT`: Key doesn't start with `sk-ant-`
- `TEST_KEY_NOT_ALLOWED`: Test key used in production mode
- `UNAUTHORIZED`: Invalid or expired API key
- `RATE_LIMITED`: API key valid but rate limited
- `QUOTA_EXCEEDED`: API key valid but account has quota issues
- `CONNECTION_ERROR`: Network connectivity issues
- `TIMEOUT`: API validation timed out
- `UNKNOWN_ERROR`: Unexpected error occurred

### Example Error Messages

```
❌ API key format is invalid. Must start with 'sk-ant-'

⚠️ Test/fake API key detected. Please provide a valid production API key.

❌ API key is invalid or unauthorized. Please check your Anthropic API key.

⚠️ API key validation hit rate limit. Key appears valid but is currently rate limited.
```

## Server Integration

### Startup Validation

The server validates the API key during initialization:

1. **Configuration Loading**: API key loaded from environment
2. **Format Validation**: Basic format checks performed
3. **Policy Application**: Environment-based decisions made
4. **Real Validation**: Production keys validated via API calls
5. **Service Initialization**: Services initialized only if key is valid

### Initialization Flow

```mermaid
graph TD
    A[Load Configuration] --> B[Create API Key Validator]
    B --> C[Classify API Key]
    C --> D{Key Type?}
    D -->|Invalid| E[❌ Reject - Invalid Format]
    D -->|Test| F{Development Mode?}
    D -->|Production| G[Validate via API Call]
    F -->|Yes| H[✅ Allow Test Key]
    F -->|No| I[❌ Reject Test Key]
    G --> J{API Response?}
    J -->|Success| K[✅ Allow Production Key]
    J -->|Error| L[❌ Reject - API Error]
    H --> M[Initialize Services]
    K --> M
    E --> N[Fail Initialization]
    I --> N
    L --> N
```

## Testing

### Running Tests

```bash
# Test API key validation functionality
python test_api_key_validation.py

# Test server integration
python test_server_api_key_integration.py

# Test with real API key (optional)
export REAL_ANTHROPIC_API_KEY=sk-ant-your-real-key
python test_real_api_key.py
```

### Test Coverage

The test suite covers:

- ✅ API key classification
- ✅ Format validation
- ✅ Policy-based decisions
- ✅ Production key validation (mocked)
- ✅ LLM service integration
- ✅ Configuration integration
- ✅ Environment detection
- ✅ Server initialization scenarios

## Migration Guide

### For Existing Deployments

1. **Development Environments**: Add `DEVELOPMENT_MODE=true` to continue using test keys
2. **Production Environments**: Ensure you have a valid production API key
3. **CI/CD Pipelines**: Set `TESTING=true` or `ALLOW_TEST_API_KEYS=true` for test environments

### Breaking Changes

- Test keys are now rejected in production mode by default
- Server initialization will fail with invalid API keys
- Real API validation may introduce startup delays for production keys

### Backward Compatibility

- Existing test keys continue to work in development mode
- Configuration format remains unchanged
- All existing functionality preserved

## Troubleshooting

### Common Issues

#### "Test/fake API key detected"
- **Cause**: Using a test key in production mode
- **Solution**: Set `DEVELOPMENT_MODE=true` or use a real API key

#### "API key validation timed out"
- **Cause**: Network connectivity issues or API service problems
- **Solution**: Check internet connection and try again

#### "API key is invalid or unauthorized"
- **Cause**: Invalid, expired, or revoked API key
- **Solution**: Check your Anthropic account and generate a new key

#### "API key validation hit rate limit"
- **Cause**: Too many validation requests
- **Solution**: Wait and try again (key is likely valid)

### Debug Information

Enable debug logging to see detailed validation information:

```bash
export LOG_LEVEL=DEBUG
```

This will show:
- API key classification results
- Validation steps and decisions
- Detailed error information
- Account information (when available)

## Security Considerations

### API Key Protection

- API keys are never logged in full (only prefixes shown)
- Test keys are clearly identified in logs
- Production keys are validated securely
- No API keys stored in configuration files

### Validation Security

- Minimal API calls used for validation
- Short timeouts prevent hanging
- Error messages don't expose sensitive information
- Rate limiting respected during validation

## Best Practices

### Development

1. Use `DEVELOPMENT_MODE=true` for local development
2. Use clearly identifiable test keys (e.g., `sk-ant-test-local-dev`)
3. Never commit real API keys to version control
4. Use environment-specific configuration

### Production

1. Always use real production API keys
2. Set `DEVELOPMENT_MODE=false` explicitly
3. Monitor API key usage and quotas
4. Implement proper key rotation procedures

### Testing

1. Use `TESTING=true` in CI/CD environments
2. Use consistent test key patterns
3. Mock API calls in unit tests
4. Test both success and failure scenarios

## Future Enhancements

Planned improvements include:

- **Key Rotation Support**: Automatic handling of key rotation
- **Multiple Key Support**: Fallback to secondary keys
- **Usage Monitoring**: Track API key usage and quotas
- **Health Checks**: Periodic validation of production keys
- **Metrics Integration**: Detailed validation metrics and alerts