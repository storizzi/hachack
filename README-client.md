# HAC Client Documentation

## Introduction

This documentation provides a comprehensive guide to using the SAP Hybris HAC (Hybris Administration Console) directly through the Python `HACClient` class. This client-side approach allows you to interact with HAC programmatically without relying on the REST API, giving you more flexibility and control over your HAC operations.

The client-side approach is ideal for:
- Direct integration with Python applications
- Custom automation workflows
- Complex scripting scenarios
- Development and testing environments

## Overview of HACClient Class

The [`HACClient`](hac_client.py:6) class is a Python client designed to interact with the SAP Hybris HAC. It maintains a session for executing multiple commands without re-authenticating, providing a seamless experience for programmatic HAC operations.

### Key Features

- **Session Management**: Maintains authentication state across multiple requests
- **CSRF Token Handling**: Automatically retrieves and refreshes CSRF tokens
- **Debug Mode**: Optional debug logging for troubleshooting
- **Error Handling**: Comprehensive error handling with detailed messages
- **Multiple Operations**: Supports ImpEx imports, Groovy script execution, and more

### Benefits of Using HACClient Directly

1. **Direct Control**: Full control over HAC operations without API limitations
2. **Stateful Operations**: Maintain session state across multiple requests
3. **Flexibility**: Easy to customize and extend for specific use cases
4. **Performance**: Reduced overhead compared to API calls
5. **Integration**: Seamless integration with Python applications

## Prerequisites

Before using the HACClient class, ensure you have the following:

### System Requirements

- Python 3.7 or higher
- Access to a SAP Hybris HAC instance
- Valid HAC credentials (username and password)

### Python Dependencies

Install the required packages using pip:

```bash
pip install -r requirements.txt
```

The key dependencies include:
- [`requests`](requirements.txt:6) - For HTTP communication
- [`beautifulsoup4`](requirements.txt:9) - For parsing HTML responses
- [`pyOpenSSL`](requirements.txt:12) - For SSL support

## Installation and Setup

### 1. Clone or Download the Project

If you haven't already, clone the repository or download the project files:

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Your Environment

Set up your HAC connection details. You can either:

- Hardcode them in your scripts (not recommended for production)
- Use environment variables
- Use a configuration file

Example environment variables:

```bash
export HAC_URL="https://your-hac-instance.com/hac"
export HAC_USERNAME="your-username"
export HAC_PASSWORD="your-password"
```

### 4. Verify Your Setup

Test your connection using a simple script:

```python
from hac_client import HACClient

# Create client instance
hac = HACClient("https://your-hac-instance.com/hac", "username", "password")

# Test login
result = hac.login()
if result.get("success"):
    print("✅ Connection successful!")
else:
    print(f"❌ Connection failed: {result.get('error')}")
```

## Client-Side Demo Scripts

The project includes several demo scripts that demonstrate how to use the HACClient class directly. Each script is located in the [`demos/`](demos/) directory.

### 1. demos/import_impex.py

This script demonstrates how to import ImpEx data directly using the HACClient class.

#### Purpose
- Shows how to execute ImpEx imports programmatically
- Demonstrates error handling and result processing
- Provides a template for custom ImpEx operations

#### Key Features
- Direct ImpEx script execution
- Configurable validation mode
- Detailed result reporting
- Debug mode support

#### Usage Example

```python
from hac_client import HACClient

# Define HAC instance details
HAC_URL = "http://localhost:9002/hac"
USERNAME = "admin"
PASSWORD = "nimda"

# Sample ImpEx script
IMPEX_SCRIPT = """
$catalog = myProductCatalog
$catalogVersion = catalogVersion(CatalogVersion.catalog(Catalog.id[default=$catalog]), CatalogVersion.version[default=Staged])[default=$catalog:Staged]
$lang = en

INSERT_UPDATE Product; code[unique=true]; name[$lang]; description[$lang]; $catalogVersion[unique=true]; ean[allownull=true]; brand
; 100001 ; Super Widget  ; The latest version of our premium widget. ; ; 1234567890123 ; Acme
; 100002 ; Budget Widget ; A basic widget at an affordable price.     ; ; 9876543210987 ; BestCo
"""

# Create HACClient instance with debug mode ON
hac = HACClient(HAC_URL, USERNAME, PASSWORD, debug=True)

# Login
if hac.login().get("success"):
    print("✅ Successfully logged in. Ready to execute commands.")
    
    # Execute ImpEx import
    result = hac.import_impex(IMPEX_SCRIPT)

    if result["success"]:
        print(f"\n✅ ImpEx Import Successful! Message: {result['impex_result']}")
    else:
        print(f"\n❌ ImpEx Import Failed. Message: {result['impex_result']}")
        print(f"\n📄 Error Details: {result['impex_details']}")
else:
    print("❌ Failed to log in. Cannot execute HAC commands.")
```

#### Running the Script

```bash
python demos/import_impex.py
```

#### Customization Options

You can customize the script by:
- Modifying the `IMPEX_SCRIPT` variable with your own ImpEx content
- Changing the validation mode (default: "IMPORT_STRICT")
- Adjusting thread count and encoding parameters
- Enabling/disabling debug mode

### 2. demos/import_impex_file.py

This script demonstrates how to import ImpEx data from a file using the HACClient class.

#### Purpose
- Shows how to upload and import ImpEx files
- Demonstrates file handling and error processing
- Provides a template for batch operations

#### Key Features
- File-based ImpEx import
- Automatic file validation
- Progress reporting
- Error handling for file operations

#### Usage Example

```python
from hac_client import HACClient
import os

# Define HAC instance details
HAC_URL = "http://localhost:9002/hac"
USERNAME = "admin"
PASSWORD = "nimda"

# Path to the ImpEx file
IMPEX_FILE_PATH = "samples/test.impex"

# Create HACClient instance
hac = HACClient(HAC_URL, USERNAME, PASSWORD, debug=True)

# Login
if hac.login().get("success"):
    print("✅ Successfully logged in. Ready to execute commands.")
    
    # Execute ImpEx file import
    result = hac.import_impex_file(IMPEX_FILE_PATH)

    if result["success"]:
        print(f"\n✅ ImpEx File Import Successful! Message: {result['impex_result']}")
    else:
        print(f"\n❌ ImpEx File Import Failed. Message: {result['impex_result']}")
        print(f"\n📄 Error Details: {result['impex_details']}")
else:
    print("❌ Failed to log in. Cannot execute HAC commands.")
```

#### Running the Script

```bash
python demos/import_impex_file.py
```

#### Sample ImpEx File

The script uses the [`samples/test.impex`](samples/test.impex:1) file as an example:

```impex
# Define variables for catalog, catalogVersion, and brand
$catalog = myProductCatalog
$catalogVersion = catalogVersion(CatalogVersion.catalog(Catalog.id[default=$catalog]), CatalogVersion.version[default=Staged])[default=$catalog:Staged]
$lang = en

INSERT_UPDATE Product; code[unique=true]; name[$lang]; description[$lang]; $catalogVersion[unique=true]; ean[allownull=true]; brand
; 100001 ; Super Widget  ; The latest version of our premium widget. ; ; 1234567890123 ; Acme
; 100002 ; Budget Widget ; A basic widget at an affordable price.     ; ; 9876543210987 ; BestCo
```

### 3. demos/run_groovy_script.py

This script demonstrates how to execute Groovy scripts using the HACClient class.

#### Purpose
- Shows how to run Groovy scripts programmatically
- Demonstrates script execution and result handling
- Provides a template for custom Groovy operations

#### Key Features
- Direct Groovy script execution
- Configurable commit mode
- Detailed output and error reporting
- Stack trace handling

#### Usage Example

```python
from hac_client import HACClient

# Define HAC instance details
HAC_URL = "http://localhost:9002/hac"
USERNAME = "admin"
PASSWORD = "nimda"

# Groovy script to execute
GROOVY_SCRIPT = """
import de.hybris.platform.core.Registry
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery
import de.hybris.platform.servicelayer.search.FlexibleSearchService

def flexibleSearchService = Registry.getApplicationContext().getBean("flexibleSearchService")
def query = new FlexibleSearchQuery("SELECT {pk} FROM {Product}")
def result = flexibleSearchService.search(query)

println "Found ${result.getCount()} products"
result.getResult().each { product ->
    println "- ${product.code}: ${product.name}"
}

return "Product count: ${result.getCount()}"
"""

# Create HACClient instance with debug mode ON
hac = HACClient(HAC_URL, USERNAME, PASSWORD, debug=True)

# Login
if hac.login().get("success"):
    print("✅ Successfully logged in. Ready to execute commands.")
    
    # Execute Groovy script
    result = hac.execute_groovy_script(GROOVY_SCRIPT)

    # Display result
    if result:
        print("\n=== Execution Result ===")
        print(result.get("executionResult", "No result"))
        print("\n=== Output Text ===")
        print(result.get("outputText", "No output"))
        
        # If there's a stack trace, display it
        if result.get("stacktraceText"):
            print("\n=== Stack Trace ===")
            print(result["stacktraceText"])
else:
    print("❌ Failed to log in. Cannot execute HAC commands.")
```

#### Running the Script

```bash
python demos/run_groovy_script.py
```

#### Customization Options

You can customize the script by:
- Modifying the `GROOVY_SCRIPT` variable with your own Groovy code
- Setting the commit parameter (default: false)
- Enabling/disabling debug mode
- Processing the results differently based on your needs

## Code Examples

### Basic Usage

```python
from hac_client import HACClient

# Initialize the client
hac = HACClient(
    hac_url="https://your-hac-instance.com/hac",
    username="your-username",
    password="your-password",
    debug=True
)

# Login
login_result = hac.login()
if not login_result.get("success"):
    print(f"Login failed: {login_result.get('error')}")
    exit(1)

print("✅ Successfully logged in!")
```

### ImpEx Import

```python
# Import ImpEx script
impex_script = """
INSERT_UPDATE Title; code[unique=true]; name
; mr ; Mr.
; mrs ; Mrs.
; ms ; Ms.
"""

result = hac.import_impex(impex_script)
if result["success"]:
    print(f"✅ Import successful: {result['impex_result']}")
else:
    print(f"❌ Import failed: {result['impex_result']}")
    print(f"Details: {result['impex_details']}")
```

### File-based ImpEx Import

```python
# Import ImpEx from file
file_path = "path/to/your/file.impex"
result = hac.import_impex_file(file_path)

if result["success"]:
    print(f"✅ File import successful: {result['impex_result']}")
else:
    print(f"❌ File import failed: {result['impex_result']}")
    print(f"Details: {result['impex_details']}")
```

### Groovy Script Execution

```python
# Execute Groovy script
groovy_script = """
println "Hello from Groovy!"
return "Script executed successfully"
"""

result = hac.execute_groovy_script(groovy_script)
if result:
    print("=== Execution Result ===")
    print(result.get("executionResult", "No result"))
    print("\n=== Output ===")
    print(result.get("outputText", "No output"))
    
    if result.get("stacktraceText"):
        print("\n=== Stack Trace ===")
        print(result["stacktraceText"])
```

### Advanced Usage with Error Handling

```python
from hac_client import HACClient

def execute_with_retry(hac_client, operation, max_retries=3):
    """Execute an operation with retry logic."""
    for attempt in range(max_retries):
        try:
            result = operation()
            if result and result.get("success"):
                return result
            
            # Check if we need to re-authenticate
            if not hac_client.is_authenticated():
                print("Session expired, re-authenticating...")
                login_result = hac_client.login()
                if not login_result.get("success"):
                    print(f"Re-authentication failed: {login_result.get('error')}")
                    return None
                continue
            
            print(f"Operation failed, attempt {attempt + 1}/{max_retries}")
            
        except Exception as e:
            print(f"Error during operation: {e}")
        
        if attempt < max_retries - 1:
            import time
            time.sleep(2)  # Wait before retrying
    
    return None

# Usage
hac = HACClient("https://your-hac-instance.com/hac", "username", "password")
hac.login()

# Execute with retry
result = execute_with_retry(hac, lambda: hac.import_impex("INSERT_UPDATE Title; code[unique=true]; name\n; test ; Test"))
if result:
    print("Operation succeeded after retries!")
else:
    print("Operation failed after all retries")
```

## API vs Client-Side Approaches

### API Approach

The API approach involves using the REST API server (hac_api.py) to interact with HAC.

**Advantages:**
- Centralized authentication and session management
- Language-agnostic (any HTTP client can be used)
- Easier to scale and deploy as a microservice
- Better for distributed systems

**Disadvantages:**
- Additional layer of complexity
- Network overhead
- Limited to the API's functionality
- Requires maintaining the API server

**Use Cases:**
- Multi-language environments
- Distributed systems
- When you need to expose HAC functionality to external systems
- When you want to abstract HAC details from client applications

### Client-Side Approach

The client-side approach involves using the HACClient class directly in your Python applications.

**Advantages:**
- Direct control over HAC operations
- No additional network overhead
- Full access to HAC functionality
- Easier debugging and troubleshooting
- Better performance for batch operations

**Disadvantages:**
- Python-only
- Each client needs to manage its own session
- More complex error handling
- Direct dependency on HAC structure

**Use Cases:**
- Python-only applications
- Development and testing scripts
- Batch processing
- When you need fine-grained control over HAC operations
- When performance is critical

### Comparison Table

| Feature | API Approach | Client-Side Approach |
|---------|-------------|---------------------|
| Language Support | Any (HTTP client) | Python only |
| Performance | Good (network overhead) | Excellent (direct connection) |
| Scalability | High (microservice) | Medium (per-client sessions) |
| Complexity | Medium (API + client) | Low (direct client) |
| Flexibility | Limited by API | Full HAC access |
| Authentication | Centralized | Per-client |
| Error Handling | Simplified | More complex |
| Maintenance | API + client | Client only |

## Best Practices

### Security

1. **Never hardcode credentials**: Use environment variables or secure configuration files
2. **Use HTTPS**: Always connect to HAC using HTTPS
3. **Validate inputs**: Validate all inputs before sending to HAC
4. **Handle errors properly**: Implement proper error handling to avoid exposing sensitive information

### Performance

1. **Reuse sessions**: Create a single HACClient instance and reuse it for multiple operations
2. **Batch operations**: Group related operations together
3. **Use appropriate timeouts**: Set reasonable timeouts based on your operations
4. **Monitor resource usage**: Be mindful of memory and CPU usage for large operations

### Error Handling

1. **Check authentication status**: Always verify authentication before executing operations
2. **Handle session expiration**: Implement logic to re-authenticate when sessions expire
3. **Log errors appropriately**: Use debug mode for development but disable in production
4. **Validate results**: Always check the success status of operations

### Code Organization

1. **Modularize your code**: Create reusable functions for common operations
2. **Use configuration files**: Store HAC connection details in configuration files
3. **Implement retry logic**: Add retry logic for transient failures
4. **Document your code**: Provide clear documentation for custom scripts

## Troubleshooting

### Common Issues

#### Authentication Failures

**Problem**: Login fails with "Invalid credentials" error

**Solution**:
1. Verify your HAC URL is correct
2. Check your username and password
3. Ensure your account has the necessary permissions
4. Verify HAC is accessible from your network

#### CSRF Token Issues

**Problem**: Operations fail with CSRF-related errors

**Solution**:
1. Enable debug mode to see CSRF token details
2. Ensure you're calling `login()` before other operations
3. Check if HAC has been updated and changed CSRF handling

#### SSL Certificate Issues

**Problem**: SSL certificate verification fails

**Solution**:
1. Ensure you're using the correct certificates
2. Verify the certificate chain is complete
3. For development only, you can disable SSL verification (not recommended for production)

#### Session Timeouts

**Problem**: Operations fail after some time with authentication errors

**Solution**:
1. Implement retry logic with re-authentication
2. Check HAC session timeout settings
3. Consider refreshing the session periodically

### Debug Mode

Enable debug mode to get detailed information about operations:

```python
hac = HACClient(hac_url, username, password, debug=True)
```

Debug mode provides:
- Detailed request/response information
- CSRF token values
- Error details
- Execution flow information

## Links to Scripts and Resources

### Core Files

- [`hac_client.py`](hac_client.py:1) - Main HACClient class implementation
- [`requirements.txt`](requirements.txt:1) - Python dependencies

### Demo Scripts

- [`demos/import_impex.py`](demos/import_impex.py:1) - ImpEx import demo
- [`demos/import_impex_file.py`](demos/import_impex_file.py:1) - File-based ImpEx import demo
- [`demos/run_groovy_script.py`](demos/run_groovy_script.py:1) - Groovy script execution demo

### Sample Files

- [`samples/test.impex`](samples/test.impex:1) - Sample ImpEx file for testing

### API Scripts (for comparison)

- [`demos/api_import_impex.py`](demos/api_import_impex.py:1) - API-based ImpEx import
- [`demos/api_import_impex_file.py`](demos/api_import_impex_file.py:1) - API-based file import
- [`demos/api_run_groovy_script.py`](demos/api_run_groovy_script.py:1) - API-based Groovy script execution
- [`demos/api_login_test.py`](demos/api_login_test.py:1) - API login test

### Documentation

- [`README.md`](README.md) - Main project documentation
- [`README-tunnelblick.md`](README-tunnelblick.md) - Tunnelblick setup guide

## Conclusion

The client-side approach using the HACClient class provides a powerful and flexible way to interact with SAP Hybris HAC directly from Python applications. It offers full control over HAC operations, better performance for batch processing, and seamless integration with Python-based workflows.

By following the examples and best practices in this documentation, you can effectively leverage the HACClient class for your automation, testing, and integration needs. The demo scripts provide a solid foundation that you can customize and extend for your specific requirements.

For questions or issues, please refer to the main project documentation or create an issue in the project repository.

## Related Documentation

For additional resources and documentation, please refer to:

- [Demo Scripts](demos/README-demos.md) - Collection of demo scripts showcasing various HAC operations using the client-side approach