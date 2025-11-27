# Hac Hack API Documentation

## Introduction

This documentation provides a comprehensive guide to using the Hac Hack REST API for automating SAP Commerce / Hybris HAC tasks. The API approach offers a centralized, language-agnostic way to interact with HAC functionality through HTTP endpoints.

The API approach is ideal for:
- Multi-language environments and distributed systems
- Exposing HAC functionality to external systems
- Centralized authentication and session management
- Microservice architectures
- Scenarios where direct HAC access needs to be abstracted from client applications

## API Overview

The Hac Hack API is built using FastAPI and provides a RESTful interface for common HAC operations. It serves as a middleware layer between client applications and the SAP Hybris HAC, handling authentication, session management, and request processing.

### Key Features

- **RESTful Architecture**: Clean HTTP-based API with standard methods (GET, POST, PUT)
- **Mutual TLS Authentication**: Secure mTLS authentication for all endpoints
- **JSON Responses**: Structured JSON responses for easy integration
- **VPN Integration**: Built-in VPN tunnel management for secure connections
- **File Upload Support**: Multipart form data for file operations
- **Health Monitoring**: Ping endpoint for service availability checks

### Benefits of Using the API

1. **Language Agnostic**: Any programming language with HTTP client support can use the API
2. **Centralized Management**: Single point of authentication and session management
3. **Scalability**: Easy to scale and deploy as a microservice
4. **Security**: Mutual TLS encryption for all communications
5. **Abstraction**: Clients don't need to handle HAC-specific details like CSRF tokens
6. **Monitoring**: Built-in health checks and status endpoints

## Prerequisites

Before using the Hac Hack API, ensure you have the following:

### System Requirements

- Python 3.9 or higher
- Access to a SAP Hybris HAC instance
- Valid HAC credentials (username and password)
- Network connectivity to both the API server and HAC instance

### Python Dependencies

Install the required packages using pip:

```bash
pip install -r requirements.txt
```

The key dependencies include:
- [`fastapi`](requirements.txt:3) - For the REST API framework
- [`uvicorn`](requirements.txt:6) - For the ASGI server
- [`requests`](requirements.txt:9) - For HTTP communication with HAC
- [`beautifulsoup4`](requirements.txt:12) - For parsing HTML responses
- [`pyOpenSSL`](requirements.txt:15) - For SSL support

### Certificate Requirements

- Generate CA, server, and client certificates using the [`generate_certificates.zsh`](generate_certificates.zsh) script
- Server certificates for the API endpoint
- Client certificates for API authentication

## Authentication

The Hac Hack API uses mutual TLS (mTLS) authentication to secure all endpoints. This ensures that both the client and server verify each other's identities before establishing a connection.

### mTLS Setup

Use the provided script to generate CA, server, and client certificates:

```sh
# List options:
./generate_certificates.zsh

# Generate all certs with defaults:
./generate_certificates.zsh --all

# Override paths and metadata:
./generate_certificates.zsh --all \
  --base-dir "certs" \
  --ca-dir "certs/ca" \
  --server-dir "certs/server" \
  --client-dir "certs/client" \
  --country "US" --state "NY" --city "NYC" \
  --org "MyOrg" --ou "MyDept" --email "you@example.com"
```

> For detailed certificate generation instructions, refer to the main [README.md](README.md#mtls-authentication) documentation.

### Using Certificates with curl

When making API requests with curl, include the client certificate and key:

```sh
curl -k --cert certs/client/client-cert.pem \
     --key certs/client/client-key.pem \
     https://localhost:8037/ping
```

## API Endpoints

The API provides the following endpoints for HAC operations:

| Method | Path                 | Description                              | Parameters                                                                        |
| ------ | -------------------- | ---------------------------------------- | --------------------------------------------------------------------------------- |
| GET    | `/ping`              | Health check                             | —                                                                                 |
| POST   | `/login`             | Login to HAC                             | JSON body: `hac_url`, `username`, `password`                                      |
| POST   | `/execute_groovy`    | Execute a Groovy script                  | JSON body: `hac_url`, `username`, `password`, `script`                            |
| POST   | `/import_impex`      | Import an ImpEx script                   | JSON body: `hac_url`, `username`, `password`, `script`                            |
| POST   | `/import_impex_file` | Upload & import an ImpEx file            | Form-data: `hac_url`, `username`, `password`, `file`, `retain`                    |
| GET    | `/vpn-service`       | Get VPN tunnel status                    | Query: `connection`                                                               |
| PUT    | `/vpn-service`       | Connect / disconnect / revert VPN tunnel | Query: `connection`, `action` (`on`/`off`/`revert`), optional `timeout` (seconds) |

> 🔒 All endpoints require mutual TLS and return JSON responses.

## Usage Examples

The following examples demonstrate how to use the API endpoints with curl commands. Use `-k` to bypass certificate verification in development.

### 1. Health Check

```sh
curl -k --cert certs/client/client-cert.pem \
     --key certs/client/client-key.pem \
     https://localhost:8037/ping
```

This endpoint checks if the API server is running and accessible. It returns a simple JSON response indicating the service status.

**Response:**
```json
{
  "status": "ok",
  "message": "Hac Hack API is running"
}
```

### 2. Login

```sh
curl -k -X POST https://localhost:8037/login \
  --cert certs/client/client-cert.pem \
  --key certs/client/client-key.pem \
  -H 'Content-Type: application/json' \
  -d '{"hac_url":"https://my-hac","username":"user","password":"pass"}'
```

This endpoint authenticates with the HAC instance using the provided credentials. It's useful for testing connectivity and validating credentials.

**Response:**
```json
{
  "success": true,
  "message": "Login successful"
}
```

### 3. Execute Groovy Script

```sh
curl -k -X POST https://localhost:8037/execute_groovy \
  --cert certs/client/client-cert.pem \
  --key certs/client/client-key.pem \
  -H 'Content-Type: application/json' \
  -d '{"hac_url":"https://my-hac","username":"user","password":"pass","script":"println(\"Hello HAC\")"}'
```

This endpoint executes arbitrary Groovy code on the HAC instance. The script parameter contains the Groovy code to be executed.

**Response:**
```json
{
  "success": true,
  "executionResult": "Hello HAC",
  "outputText": "Hello HAC\n"
}
```

### 4. Import ImpEx Script

```sh
curl -k -X POST https://localhost:8037/import_impex \
  --cert certs/client/client-cert.pem \
  --key certs/client/client-key.pem \
  -H 'Content-Type: application/json' \
  -d '{"hac_url":"https://my-hac","username":"user","password":"pass","script":"INSERT_UPDATE Catalog; code[unique = true]; name[lang = en];\n; testCatalog; Test Catalog"}'
```

This endpoint imports ImpEx data directly from the provided script content. The script parameter contains the ImpEx statements to be executed.

**Response:**
```json
{
  "success": true,
  "impex_result": "Import successful",
  "impex_details": "2 rows processed"
}
```

### 5. Upload & Import ImpEx File

```sh
curl -k -X POST https://localhost:8037/import_impex_file \
  --cert certs/client/client-cert.pem \
  --key certs/client/client-key.pem \
  -F hac_url=https://my-hac \
  -F username=user \
  -F password=pass \
  -F file=@path/to/products.impex \
  -F retain=true
```

This endpoint uploads an ImpEx file and imports its contents. The file parameter specifies the file to upload, and the retain parameter determines whether to retain the file after import.

**Response:**
```json
{
  "success": true,
  "impex_result": "File import successful",
  "impex_details": "5 rows processed from products.impex"
}
```

### 6. VPN Tunnel — Status

```sh
curl -k -G https://localhost:8037/vpn-service \
  --cert certs/client/client-cert.pem \
  --key certs/client/client-key.pem \
  --data-urlencode 'connection=MyVPN'
```

This endpoint retrieves the current status of a VPN tunnel. The connection parameter specifies the VPN connection name.

**Response:**
```json
{
  "connection": "MyVPN",
  "status": "connected",
  "message": "VPN connection is active"
}
```

### 7. VPN Tunnel — Connect (default timeout)

```sh
curl -k -X PUT 'https://localhost:8037/vpn-service?connection=MyVPN&action=on' \
  --cert certs/client/client-cert.pem \
  --key certs/client/client-key.pem
```

This endpoint connects to a VPN tunnel using the default timeout. The connection parameter specifies the VPN connection name, and the action parameter is set to "on".

**Response:**
```json
{
  "success": true,
  "connection": "MyVPN",
  "action": "connect",
  "message": "VPN connection established"
}
```

### 8. VPN Tunnel — Disconnect (30s timeout)

```sh
curl -k -X PUT 'https://localhost:8037/vpn-service?connection=MyVPN&action=off&timeout=30' \
  --cert certs/client/client-cert.pem \
  --key certs/client/client-key.pem
```

This endpoint disconnects from a VPN tunnel with a 30-second timeout. The connection parameter specifies the VPN connection name, the action parameter is set to "off", and the timeout parameter specifies the timeout in seconds.

**Response:**
```json
{
  "success": true,
  "connection": "MyVPN",
  "action": "disconnect",
  "message": "VPN connection disconnected"
}
```

### 9. VPN Tunnel — Revert to Previous State

```sh
curl -k -X PUT 'https://localhost:8037/vpn-service?connection=MyVPN&action=revert' \
  --cert certs/client/client-cert.pem \
  --key certs/client/client-key.pem
```

This endpoint reverts the VPN tunnel to its previous state. The connection parameter specifies the VPN connection name, and the action parameter is set to "revert".

**Response:**
```json
{
  "success": true,
  "connection": "MyVPN",
  "action": "revert",
  "message": "VPN connection reverted to previous state"
}
```

## API Demo Scripts

The project includes several demo scripts that demonstrate how to use the API endpoints programmatically. These scripts are located in the [`demos/`](demos/) directory and provide examples for interacting with the API.

### 1. [`demos/api_login_test.py`](demos/api_login_test.py)

This script demonstrates how to test the login functionality through the API.

**Purpose:**
- Shows how to authenticate with the HAC system via the API
- Demonstrates proper error handling for authentication failures
- Provides a template for validating API connectivity

**Key Features:**
- Simple authentication test
- Response validation
- Error reporting

**Usage:**
```bash
python demos/api_login_test.py
```

**Code Overview:**
The script sends a POST request to the `/login` endpoint with HAC credentials and validates the response to ensure successful authentication.

### 2. [`demos/api_import_impex.py`](demos/api_import_impex.py)

This script demonstrates how to import ImpEx scripts using the API.

**Purpose:**
- Shows how to submit ImpEx payloads through the API
- Demonstrates proper JSON formatting for API requests
- Provides a template for automated ImpEx imports

**Key Features:**
- Direct ImpEx script submission
- Configurable HAC connection parameters
- Result processing and error handling

**Usage:**
```bash
python demos/api_import_impex.py
```

**Code Overview:**
The script constructs a JSON payload with ImpEx content and sends it to the `/import_impex` endpoint, then processes the response to determine success or failure.

### 3. [`demos/api_import_impex_file.py`](demos/api_import_impex_file.py)

This script demonstrates how to upload and import ImpEx files using the API.

**Purpose:**
- Shows how to handle file uploads through the API
- Demonstrates multipart form data usage
- Provides a template for batch file operations

**Key Features:**
- File-based ImpEx import
- Multipart form data handling
- Upload progress monitoring

**Usage:**
```bash
python demos/api_import_impex_file.py
```

**Code Overview:**
The script reads an ImpEx file and sends it as multipart form data to the `/import_impex_file` endpoint, handling the file upload and processing the import result.

### 4. [`demos/api_run_groovy_script.py`](demos/api_run_groovy_script.py)

This script demonstrates how to execute Groovy scripts using the API.

**Purpose:**
- Shows how to run arbitrary Groovy code through the API
- Demonstrates script execution and result handling
- Provides a template for automated Groovy operations

**Key Features:**
- Direct Groovy script execution
- Configurable execution parameters
- Output and error processing

**Usage:**
```bash
python demos/api_run_groovy_script.py
```

**Code Overview:**
The script sends a Groovy script to the `/execute_groovy` endpoint and processes the execution results, including output text and any stack traces.

## Running the API Server

### Development (HTTP only)

For development purposes, you can run the API server without TLS encryption:

```sh
uvicorn hac_api:app --reload --host 0.0.0.0 --port 8037
```

This command starts the server with:
- Auto-reload enabled for code changes
- HTTP only (no encryption)
- Listening on all interfaces (0.0.0.0)
- Port 8037

### Testing with Built-in TLS

For production or testing with TLS encryption:

```sh
uvicorn hac_api:app --host 0.0.0.0 --port 8037 \
  --ssl-keyfile certs/server/server-key.pem \
  --ssl-certfile certs/server/server-cert.pem \
  --ssl-ca-certs certs/ca/ca-cert.pem
```

This command starts the server with:
- TLS encryption enabled
- Server certificate and key
- CA certificate for client verification
- Mutual TLS authentication

### Environment Variables

The API server respects the following environment variables:

| Variable          | Description                                         | Default                            |
| ----------------- | --------------------------------------------------- | ---------------------------------- |
| `HAC_URL`         | Base URL of your Hybris HAC (e.g. `https://my-hac`) | —                                  |
| `HAC_USERNAME`    | Username for HAC authentication                     | —                                  |
| `HAC_PASSWORD`    | Password for HAC authentication                     | —                                  |
| `HAC_TIMEOUT`     | Default timeout for HAC calls (seconds)             | `30` (if unset)                    |
| `VPN_SCRIPT_PATH` | Path to your VPN control script                     | `/usr/local/bin/tunnel-control.sh` |
| `VPN_TIMEOUT`     | Default auto-revert timeout for VPN (seconds)       | `60`                               |

Load variables from a `.env` file by default.

## Error Handling

The API returns structured JSON responses for all requests, including error conditions. Understanding the response format is crucial for proper integration.

### Success Response Format

```json
{
  "success": true,
  "result": "Operation completed successfully",
  "details": "Additional information about the result"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": "Error type or description",
  "message": "Detailed error message",
  "details": "Additional error context or stack trace"
}
```

### Common Error Codes

| HTTP Status | Error Type               | Description                                  |
| ----------- | ------------------------ | -------------------------------------------- |
| 400         | Bad Request              | Invalid request parameters or format         |
| 401         | Unauthorized             | Authentication failed or invalid certificate |
| 403         | Forbidden               | Insufficient permissions                     |
| 404         | Not Found               | Endpoint not found                           |
| 422         | Validation Error        | Request validation failed                    |
| 500         | Internal Server Error   | Server-side error occurred                   |
| 503         | Service Unavailable     | HAC instance unavailable or timeout          |

### Handling Specific Errors

#### Authentication Errors
```json
{
  "success": false,
  "error": "AuthenticationError",
  "message": "Invalid HAC credentials",
  "details": "The provided username and password were rejected by the HAC instance"
}
```

#### Certificate Errors
```json
{
  "success": false,
  "error": "CertificateError",
  "message": "Invalid client certificate",
  "details": "The client certificate could not be verified"
}
```

#### HAC Connection Errors
```json
{
  "success": false,
  "error": "HACConnectionError",
  "message": "Unable to connect to HAC instance",
  "details": "Connection timeout or network error"
}
```

## Best Practices

### Security Considerations

1. **Certificate Management**
   - Store certificates securely with appropriate file permissions
   - Regularly rotate certificates and keys
   - Use strong encryption for certificate generation
   - Revoke compromised certificates immediately

2. **API Security**
   - Always use HTTPS in production environments
   - Implement proper certificate validation
   - Use strong, unique credentials for HAC authentication
   - Limit API access to trusted networks only

3. **Data Protection**
   - Never log sensitive information like passwords or tokens
   - Use secure connections for all API calls
   - Validate all input parameters to prevent injection attacks
   - Implement proper error handling to avoid information leakage

### Performance Optimization

1. **Connection Management**
   - Reuse HTTP connections when possible
   - Implement connection pooling for high-volume usage
   - Set appropriate timeouts for network operations
   - Monitor connection health and handle disconnects gracefully

2. **Request Optimization**
   - Batch related operations when possible
   - Use appropriate HTTP methods for different operations
   - Minimize payload sizes for better performance
   - Implement caching for frequently accessed data

3. **Resource Management**
   - Monitor memory usage for large file uploads
   - Implement proper cleanup for temporary files
   - Use streaming for large data transfers
   - Set reasonable limits on request sizes

### Integration Patterns

1. **Error Handling**
   - Implement retry logic for transient failures
   - Use exponential backoff for retry attempts
   - Log errors with sufficient context for debugging
   - Provide meaningful error messages to end users

2. **Monitoring**
   - Implement health checks for API availability
   - Monitor response times and error rates
   - Set up alerts for critical failures
   - Track usage patterns for capacity planning

3. **Versioning**
   - Use API versioning for backward compatibility
   - Document breaking changes in advance
   - Provide migration guides for major updates
   - Support multiple versions during transition periods

## Troubleshooting

### Common API Issues

#### Certificate Verification Problems

**Problem**: API requests fail with certificate verification errors

**Symptoms**:
- SSL handshake failures
- Certificate verification error messages
- Connection refused or timeout

**Solutions**:
1. Verify certificates are properly generated:
   ```sh
   openssl verify -CAfile certs/ca/ca-cert.pem certs/server/server-cert.pem
   openssl verify -CAfile certs/ca/ca-cert.pem certs/client/client-cert.pem
   ```

2. Check certificate expiration dates:
   ```sh
   openssl x509 -in certs/client/client-cert.pem -noout -dates
   openssl x509 -in certs/server/server-cert.pem -noout -dates
   ```

3. Ensure the server certificate includes the correct hostname (localhost for development)

4. For development only, use `-k` flag with curl to bypass verification (not recommended for production)

#### Authentication Failures

**Problem**: API returns authentication errors despite valid certificates

**Symptoms**:
- 401 Unauthorized responses
- "Invalid client certificate" errors
- Connection drops during handshake

**Solutions**:
1. Verify client certificate is being sent:
   ```sh
   curl -v --cert certs/client/client-cert.pem \
        --key certs/client/client-key.pem \
        https://localhost:8037/ping
   ```

2. Check certificate chain is complete:
   ```sh
   openssl s_client -connect localhost:8037 -cert certs/client/client-cert.pem \
                   -key certs/client/client-key.pem \
                   -CAfile certs/ca/ca-cert.pem
   ```

3. Ensure the CA certificate is trusted by the server

4. Verify certificate permissions allow reading by the server process

#### HAC Connection Issues

**Problem**: API server cannot connect to HAC instance

**Symptoms**:
- 503 Service Unavailable responses
- "Unable to connect to HAC instance" errors
- Timeout errors on HAC operations

**Solutions**:
1. Test direct HAC connectivity:
   ```sh
   curl -k https://your-hac-instance/hac
   ```

2. Verify HAC credentials are correct:
   ```sh
   curl -k -u username:password https://your-hac-instance/hac
   ```

3. Check network connectivity between API server and HAC instance

4. Verify HAC instance is running and accessible

5. Adjust timeout values for slow networks:
   ```sh
   export HAC_TIMEOUT=60
   ```

#### VPN Control Problems

**Problem**: VPN service endpoints fail to control VPN connections

**Symptoms**:
- VPN status returns incorrect information
- VPN connect/disconnect operations fail
- Timeout errors on VPN operations

**Solutions**:
1. Verify VPN control script exists and is executable:
   ```sh
   ls -la /usr/local/bin/tunnel-control.sh
   chmod +x /usr/local/bin/tunnel-control.sh
   ```

2. Test VPN script directly:
   ```sh
   /usr/local/bin/tunnel-control.sh status "MyVPN"
   ```

3. Check VPN connection names match exactly:
   ```sh
   /usr/local/bin/tunnel-control.sh list
   ```

4. Adjust VPN timeout values for slow connections:
   ```sh
   export VPN_TIMEOUT=120
   ```

### Debug Mode

Enable debug mode for detailed logging:

```sh
export DEBUG=true
uvicorn hac_api:app --reload --host 0.0.0.0 --port 8037
```

Debug mode provides:
- Detailed request/response logging
- Certificate verification details
- HAC operation traces
- Error stack traces

### Log Analysis

Check server logs for detailed error information:

```sh
tail -f /var/log/hac_api.log
```

Look for:
- Certificate validation errors
- HAC connection failures
- Timeout issues
- Memory or resource errors

### Performance Issues

**Problem**: API responses are slow or time out

**Solutions**:
1. Monitor resource usage:
   ```sh
   top -p $(pgrep -f uvicorn)
   ```

2. Check network latency:
   ```sh
   ping your-hac-instance
   ping localhost
   ```

3. Adjust timeout values:
   ```sh
   export HAC_TIMEOUT=60
   export VPN_TIMEOUT=120
   ```

4. Consider scaling options for high-volume usage

### Getting Help

If you encounter issues not covered here:

1. Check the main project documentation: [README.md](README.md)
2. Review client-side documentation: [README-client.md](README-client.md)
3. Consult VPN control documentation: [README-tunnelblick.md](README-tunnelblick.md)
4. Search existing issues: [GitHub Issues](https://github.com/storizzi/hachack/issues)
5. Create a new issue with detailed information about your problem

When reporting issues, please include:
- API server version
- Operating system and Python version
- Complete error messages and stack traces
- Steps to reproduce the issue
- Expected vs. actual behavior

## Related Documentation

For additional resources and documentation, please refer to:

- [Demo Scripts](demos/README-demos.md) - Collection of demo scripts showcasing various HAC operations using the API approach