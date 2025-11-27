# Hac Hack Demo Scripts

This directory contains a collection of demo scripts that showcase various HAC operations using both the API and client-side approaches. These scripts serve as practical examples and templates for your own automation tasks.

## Table of Contents

- [Hac Hack Demo Scripts](#hac-hack-demo-scripts)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [API Demo Scripts](#api-demo-scripts)
    - [api\_login\_test.py](#api_login_testpy)
    - [api\_import\_impex.py](#api_import_impexpy)
    - [api\_import\_impex\_file.py](#api_import_impex_filepy)
    - [api\_run\_groovy\_script.py](#api_run_groovy_scriptpy)
  - [Client-Side Demo Scripts](#client-side-demo-scripts)
    - [login\_test.py](#login_testpy)
    - [import\_impex.py](#import_impexpy)
    - [import\_impex\_file.py](#import_impex_filepy)
    - [run\_groovy\_script.py](#run_groovy_scriptpy)
  - [Customizing Demo Scripts](#customizing-demo-scripts)
    - [Environment Variables](#environment-variables)
    - [Configuration Files](#configuration-files)
    - [Error Handling](#error-handling)
  - [Best Practices](#best-practices)
    - [Security](#security)
    - [Password Management](#password-management)
      - [Using Password Vaults with Environment Variables](#using-password-vaults-with-environment-variables)
      - [Best Practices for Password Management](#best-practices-for-password-management)
    - [Performance](#performance)
    - [Reliability](#reliability)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
      - [Authentication Failures](#authentication-failures)
      - [Connection Timeouts](#connection-timeouts)
      - [Script Execution Errors](#script-execution-errors)
    - [Debug Mode](#debug-mode)
    - [Getting Help](#getting-help)

## Overview

The demo scripts are organized into two categories:

1. **API Demo Scripts**: Demonstrate how to interact with HAC through the REST API
2. **Client-Side Demo Scripts**: Show direct usage of the HACClient Python library

Each script is designed to be self-contained and focuses on a specific HAC operation. They include proper error handling, configuration management, and logging to serve as robust templates for your own automation needs.

## API Demo Scripts

### api_login_test.py

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

**Configuration:**
- Edit the script to set your HAC URL, username, and password
- Configure the API endpoint URL if different from default

### api_import_impex.py

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

**Configuration:**
- Modify the ImpEx content in the script to match your data model
- Adjust HAC connection parameters as needed

### api_import_impex_file.py

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

**Configuration:**
- Update the file path to point to your ImpEx file
- Configure the retain parameter based on your requirements

### api_run_groovy_script.py

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

**Configuration:**
- Modify the Groovy script content to perform your desired operations
- Adjust timeout values for long-running scripts

## Client-Side Demo Scripts

### login_test.py

This script demonstrates how to test the login functionality using the client-side approach.

**Purpose:**
- Shows how to authenticate with HAC using the HACClient class
- Demonstrates session management and CSRF token handling
- Provides a template for validating HAC connectivity

**Key Features:**
- Direct HAC authentication
- Session management
- CSRF token handling

**Usage:**
```bash
python demos/login_test.py
```

**Configuration:**
- Edit the script to set your HAC URL, username, and password
- Configure timeout values as needed

### import_impex.py

This script demonstrates how to import ImpEx scripts using the client-side approach.

**Purpose:**
- Shows how to submit ImpEx content directly to HAC
- Demonstrates proper session management for ImpEx operations
- Provides a template for automated ImpEx imports

**Key Features:**
- Direct ImpEx script submission
- Session-based authentication
- Result processing

**Usage:**
```bash
python demos/import_impex.py
```

**Configuration:**
- Modify the ImpEx content to match your data model
- Adjust HAC connection parameters as needed

### import_impex_file.py

This script demonstrates how to upload and import ImpEx files using the client-side approach.

**Purpose:**
- Shows how to handle file uploads directly to HAC
- Demonstrates file processing and session management
- Provides a template for batch file operations

**Key Features:**
- File-based ImpEx import
- Direct HAC file upload
- Session management

**Usage:**
```bash
python demos/import_impex_file.py
```

**Configuration:**
- Update the file path to point to your ImpEx file
- Configure file processing options as needed

### run_groovy_script.py

This script demonstrates how to execute Groovy scripts using the client-side approach.

**Purpose:**
- Shows how to run Groovy code directly on HAC
- Demonstrates script execution and result handling
- Provides a template for automated Groovy operations

**Key Features:**
- Direct Groovy script execution
- Session-based authentication
- Output and error processing

**Usage:**
```bash
python demos/run_groovy_script.py
```

**Configuration:**
- Modify the Groovy script content to perform your desired operations
- Adjust timeout values for long-running scripts

## Customizing Demo Scripts

### Environment Variables

All demo scripts can be configured using environment variables:

```bash
export HAC_URL="https://your-hac-instance"
export HAC_USERNAME="your-username"
export HAC_PASSWORD="your-password"
export HAC_TIMEOUT="60"
export API_URL="https://your-api-server"
```

### Configuration Files

For more complex configurations, consider creating a configuration file - but only for test environments where the credentials are well-known and you are trying things out - DO NOT COMMIT CREDENTIALS!!!:

```python
# config.py
HAC_CONFIG = {
    "url": "https://your-hac-instance",
    "username": "your-username",
    "password": "your-password",
    "timeout": 60
}

API_CONFIG = {
    "url": "https://your-api-server",
    "cert_path": "certs/client/client-cert.pem",
    "key_path": "certs/client/client-key.pem"
}
```

### Error Handling

All demo scripts include basic error handling. For production use, consider enhancing them with:

- Retry logic for transient failures
- Detailed logging for debugging
- Alerting for critical failures
- Graceful degradation for non-critical errors

## Best Practices

### Security

1. **Never commit credentials** to version control
2. **Use environment variables** or secure configuration management
3. **Implement proper certificate management** for API access
4. **Validate all inputs** to prevent injection attacks
5. **Use HTTPS** in all production environments

### Password Management

**WARNING:** Passwords should never be stored directly on your system or in plain text files. Storing credentials in plain text poses significant security risks and makes your system vulnerable to unauthorized access.

Instead of hardcoding passwords in scripts or configuration files, we strongly recommend integrating with password vaults that provide secure credential management. For personal use, there are command-line integrated approaches such as 1Password that can securely inject credentials into your environment when needed.

#### Using Password Vaults with Environment Variables

Password vaults can seamlessly integrate with your demo scripts through environment variables. Here's how you can use 1Password CLI to securely manage your credentials:

1. Install the 1Password CLI following the official documentation
2. Configure 1Password to access your vault
3. Use the 1Password CLI to inject secrets as environment variables:

```bash
# Using 1Password CLI to load secrets as environment variables
eval $(op signin)
export HAC_USERNAME=$(op read "op://Private/HAC-username/username")
export HAC_PASSWORD=$(op read "op://Private/HAC-password/password")
export API_URL=$(op read "op://Private/API-url/url")

# Now run your demo script with the securely loaded credentials
python demos/api_login_test.py
```

For more detailed information on using 1Password CLI with environment variables, see the official documentation: [1Password CLI Secrets Environment Variables](https://developer.1password.com/docs/cli/secrets-environment-variables/)

#### Best Practices for Password Management

- Always use a reputable password vault with strong encryption
- Regularly rotate your passwords and update them in your vault
- Enable multi-factor authentication on your password vault
- Limit access to credentials based on the principle of least privilege
- Audit your credential usage periodically
- Consider using temporary credentials that expire after a set time

By following these practices, you ensure that your demo scripts remain secure while still being convenient to use for development and testing purposes.

### Performance

1. **Reuse sessions** when performing multiple operations
2. **Implement appropriate timeouts** for network operations
3. **Handle large files** efficiently with streaming
4. **Monitor resource usage** for long-running operations
5. **Implement proper cleanup** for temporary files

### Reliability

1. **Implement retry logic** for transient failures
2. **Add comprehensive logging** for debugging
3. **Handle edge cases** gracefully
4. **Provide meaningful error messages**
5. **Test thoroughly** in your environment

## Troubleshooting

### Common Issues

#### Authentication Failures

**Symptoms:** Scripts fail with authentication errors

**Solutions:**
1. Verify HAC credentials are correct
2. Check HAC URL is accessible
3. Ensure user has proper permissions
4. Verify certificate validity for API access

#### Connection Timeouts

**Symptoms:** Scripts timeout during execution

**Solutions:**
1. Increase timeout values in configuration
2. Check network connectivity to HAC
3. Verify HAC instance is responsive
4. Consider VPN connectivity issues

#### Script Execution Errors

**Symptoms:** Groovy scripts or ImpEx imports fail

**Solutions:**
1. Validate script syntax before execution
2. Check HAC logs for detailed error information
3. Verify data model compatibility for ImpEx
4. Test scripts manually in HAC interface

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG=true
python demos/your_script.py
```

### Getting Help

If you encounter issues not covered here:

1. Check the main project documentation: [README.md](../README.md)
2. Review API documentation: [README-api.md](../README-api.md)
3. Consult client-side documentation: [README-client.md](../README-client.md)
4. Search existing issues: [GitHub Issues](https://github.com/storizzi/hachack/issues)
5. Create a new issue with detailed information about your problem

When reporting issues, please include:
- Script name and approach (API or client-side)
- Complete error messages and stack traces
- Configuration details (without sensitive information)
- Steps to reproduce the issue
- Expected vs. actual behavior