# Hac Hack Release Notes

This document contains the release notes for the Hac Hack project. It provides a comprehensive overview of changes, new features, and improvements in each version. The goal is to keep users informed about the evolution of the project and to document the history of changes.

## [0.1.0] - 2025-10-09

### Initial Release

We are excited to announce the first release of the Hac Hack project! This initial version provides a complete toolkit for interacting with SAP Hybris Commerce through a secure API interface and direct Python integration.

### What's Included

#### Core Components

1. **FastAPI Server Implementation (`hac_api.py`)**
   - RESTful API server built with FastAPI
   - mTLS authentication for secure communication
   - Comprehensive error handling and logging
   - Auto-generated API documentation

2. **HACClient Class (`hac_client.py`)**
   - Direct Python integration for SAP Hybris Commerce
   - Simplified interface for common operations
   - Built-in authentication handling
   - Support for both synchronous and asynchronous operations

3. **VPN Control Script (`tunnelblick.zsh`)**
   - Automated VPN control for Tunnelblick on macOS
   - Seamless integration with the Hac Hack workflow
   - Easy connection and disconnection commands

4. **Certificate Generation Script (`generate_certificates.zsh`)**
   - Automated SSL certificate generation
   - Setup for mTLS authentication
   - Easy configuration and deployment

#### API Endpoints

The complete API includes endpoints for:

- **Authentication**: Secure login and session management
- **Groovy Execution**: Run Groovy scripts on the Hybris Administration Console
- **ImpEx Operations**: Import and export ImpEx files
- **Health Checks**: Monitor system status and connectivity
- **VPN Management**: Control VPN connections through the API

#### Demo Scripts

Comprehensive demo scripts for both API and client-side usage:

1. **API Demos**:
   - `demos/api_login_test.py` - Authentication testing
   - `demos/api_run_groovy_script.py` - Groovy script execution
   - `demos/api_import_impex.py` - ImpEx import operations
   - `demos/api_import_impex_file.py` - File-based ImpEx import

2. **Client Demos**:
   - `demos/run_groovy_script.py` - Direct Groovy script execution
   - `demos/import_impex.py` - ImpEx import via client
   - `demos/import_impex_file.py` - File-based ImpEx import via client

#### Documentation

Complete documentation structure:

- `README.md` - Main project documentation
- `README-client.md` - Client usage guide
- `README-tunnelblick.md` - VPN setup and configuration

#### Sample Data

- `samples/test.impex` - Sample ImpEx file for testing

### Getting Started

To get started with Hac Hack v0.1.0:

1. Clone the repository: `git clone https://github.com/storizzi/hachack.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Generate certificates: `./generate_certificates.zsh`
4. Start the API server: `python hac_api.py`
5. Run the demo scripts to test functionality

### Known Issues

Please check the [issues page](https://github.com/storizzi/hachack/issues) for known issues and to report new ones.

### Future Plans

We are already working on the next version, which will include:
- Enhanced error handling
- Additional API endpoints
- Performance improvements
- Expanded documentation

---

## Project Links

- **GitHub Repository**: https://github.com/storizzi/hachack
- **Issues Page**: https://github.com/storizzi/hachack/issues
- **Documentation**: See README files in the repository root