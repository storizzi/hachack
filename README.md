# Hac Hack v0.1.1 - API for Auto-running Hybris HAC Operations

A Python library and FastAPI-based HTTP API for automating SAP Commerce / Hybris HAC tasks.

**Repository:** [https://github.com/storizzi/hachack](https://github.com/storizzi/hachack)

## Table of Contents

- [Hac Hack - API for Auto-running Hybris HAC Operations](#hac-hack---api-for-auto-running-hybris-hac-operations)
  - [Table of Contents](#table-of-contents)
  - [Project Introduction](#project-introduction)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [mTLS Authentication](#mtls-authentication)
  - [Certificate Generation Script](#certificate-generation-script)
    - [Script Path](#script-path)
    - [Usage](#usage)
    - [Optional Parameters](#optional-parameters)
    - [Actions (choose at least one)](#actions-choose-at-least-one)
    - [What It Does](#what-it-does)
  - [Usage Approaches](#usage-approaches)
    - [API Approach](#api-approach)
    - [Client-Side Python Approach](#client-side-python-approach)
    - [VPN Tunnel Management](#vpn-tunnel-management)
  - [Documentation](#documentation)
    - [API Documentation](#api-documentation)
    - [Client-Side Usage](#client-side-usage)
    - [VPN Control](#vpn-control)
    - [Demo Scripts](#demo-scripts)
    - [Release Notes](#release-notes)
  - [License](#license)
  - [Issues and Feedback](#issues-and-feedback)

## Project Introduction

Hac Hack is a versatile toolkit designed to automate and streamline interactions with SAP Commerce / Hybris HAC (Hybris Administration Console). It provides three complementary approaches to suit different integration scenarios and technical requirements:

1. **API Approach**: A FastAPI-based REST API for language-agnostic integration
2. **Client-Side Python Approach**: Direct Python library integration for Python applications
3. **VPN Tunnel Management**: Tools for managing secure VPN connections to HAC instances

This toolkit is designed for developers, system administrators, and DevOps engineers who need to automate HAC operations as part of their CI/CD pipelines, deployment processes, or system administration tasks.

## Features

* **Multiple Integration Approaches**: Choose between API, or client-side Python, optionally using direct VPN control
* **Authentication**: Secure login to HAC with proper session management
* **Execute Groovy scripts**: Run arbitrary Groovy code on the HAC for system administration
* **Import ImpEx scripts**: Submit ImpEx payloads directly for data management
* **Upload & import ImpEx files**: Handle file-based batch data operations
* **Health monitoring**: Check system status and connectivity
* **VPN tunnel management**: Secure connectivity with status/connect/disconnect/revert operations
* **Mutual TLS Authentication**: Enterprise-grade security for all communications

## Prerequisites

* Python 3.9+
* `pip install -r [`requirements.txt`](requirements.txt)`
* [`generate_certificates.zsh`](generate_certificates.zsh) (for mTLS certs)
* Tunnel control script (e.g. [`tunnelblick.zsh`](tunnelblick.zsh)) if you want to control VPN establishment from the endpoint too

## Environment Variables

| Variable          | Description                                         | Default                            |
| ----------------- | --------------------------------------------------- | ---------------------------------- |
| `HAC_URL`         | Base URL of your Hybris HAC (e.g. `https://my-hac`) | —                                  |
| `HAC_USERNAME`    | Username for HAC authentication                     | —                                  |
| `HAC_PASSWORD`    | Password for HAC authentication                     | —                                  |
| `HAC_TIMEOUT`     | Default timeout for HAC calls (seconds)             | `30` (if unset)                    |
| `VPN_SCRIPT_PATH` | Path to your VPN control script                     | `/usr/local/bin/tunnel-control.sh` |
| `VPN_TIMEOUT`     | Default auto-revert timeout for VPN (seconds)       | `60`                               |

Load variables from a `.env` file by default.

## mTLS Authentication

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

Secure your CA directory separately for best practice.

## Certificate Generation Script

The [`generate_certificates.zsh`](generate_certificates.zsh) script automates creation of a private Certificate Authority (CA), plus server and client certificates for mutual TLS authentication.

### Script Path

```sh
./generate_certificates.zsh
```

### Usage

```sh
Usage: generate_certificates.zsh [<optional params>] [--ca | --server | --client | --all]
```

### Optional Parameters

* `--base-dir <path>`     : Base directory for all certificates (default: `certs`)
* `--ca-dir <path>`       : Directory to place CA key & cert (default: `certs/ca`)
* `--server-dir <path>`   : Directory for server key, CSR & cert (default: `certs/server`)
* `--client-dir <path>`   : Directory for client key, CSR & cert (default: `certs/client`)
* `--country <value>`     : Certificate country code (default: `GB`)
* `--state <value>`       : State or province (default: `England`)
* `--city <value>`        : Locality / city (default: `London`)
* `--org <value>`         : Organization name (default: `Example`)
* `--ou <value>`          : Organizational unit (default: `ExampleApp`)
* `--email <value>`       : Contact email (default: `simon@example.com`)

### Actions (choose at least one)

* `--ca`       : Generate a new Certificate Authority (CA key & self-signed cert)
* `--server`   : Generate server private key, CSR, and sign with the CA
* `--client`   : Generate client private key, CSR, and sign with the CA
* `--all`      : Perform all of the above in sequence

### What It Does

1. **Directory setup**: Ensures `ca`, `server`, and `client` directories exist under `--base-dir`.
2. **CA generation** (`--ca`):

   * Creates an RSA key pair for the CA.
   * Issues a self-signed CA certificate valid for 365 days.
3. **Server certificate** (`--server`):

   * Generates an RSA key for the server.
   * Creates a CSR (Common Signing Request) with `CN=localhost`.
   * Signs the CSR using the CA key and certificate, producing a server certificate.
4. **Client certificate** (`--client`):

   * Generates an RSA key for the client.
   * Creates a CSR with `CN=Example-Client`.
   * Signs the CSR with the CA, producing a client certificate.
5. **Output**:

   * CA: `ca/ca-key.pem`, `ca/ca-cert.pem`
   * Server: `server/server-key.pem`, `server/server-req.csr`, `server/server-cert.pem`
   * Client: `client/client-key.pem`, `client/client-req.csr`, `client/client-cert.pem`

## Usage Approaches

Hac Hack provides three distinct approaches for interacting with HAC, each designed for different use cases and integration scenarios:

### API Approach

The API approach uses a FastAPI-based REST API that provides a language-agnostic interface for HAC operations. This approach is ideal for:

- Multi-language environments and distributed systems
- Exposing HAC functionality to external systems
- Centralized authentication and session management
- Microservice style architecture (i.e. baby API but secured!)
- Scenarios where direct HAC access needs to be abstracted from client applications - e.g. occasional operational scripts that you don't want to turn into full-blown cronjobs - handy because you can log the responses rather than having them being run directly with no trace of them being run

**Getting Started:**
- Refer to [`README-api.md`](README-api.md) for comprehensive API documentation
- Includes detailed endpoint descriptions, request/response formats, and examples
- Covers authentication, error handling, and best practices
- Provides demo scripts for representative operations

**Key Commands:**
```bash
# Start the API server
uvicorn hac_api:app --reload --host 0.0.0.0 --port 8037

# Run API demo scripts
python demos/api_login_test.py
python demos/api_import_impex.py
python demos/api_import_impex_file.py
python demos/api_run_groovy_script.py
```

### Client-Side Python Approach

The client-side approach provides direct Python library integration for applications that prefer to interact with HAC without going through a REST API. This approach is ideal for:

- Python-native applications and scripts
- Direct integration with existing Python codebases
- Scenarios where REST API overhead is undesirable
- Applications that need fine-grained control over HAC interactions

**Getting Started:**
- Refer to [`README-client.md`](README-client.md) for comprehensive client documentation
- Covers direct HACClient class usage, session management, and CSRF token handling
- Includes client-side demo scripts and examples
- Provides best practices for client-side HAC operations

**Key Commands:**
```bash
# Run client demo scripts
python demos/login_test.py
python demos/import_impex.py
python demos/import_impex_file.py
python demos/run_groovy_script.py
```

### VPN Tunnel Management

The VPN tunnel management approach provides tools for controlling VPN connections to HAC instances, particularly useful for secure network environments. This approach is ideal for:

- Secure network environments requiring VPN access
- Automated VPN connection management
- Scenarios where HAC instances are behind VPNs

**Getting Started:**
- Refer to [`README-tunnelblick.md`](README-tunnelblick.md) for detailed VPN control documentation
- Covers Tunnelblick VPN control on macOS
- Includes installation, setup, and usage examples
- Provides automation examples and troubleshooting guidance

**Key Commands:**
```bash
# Control VPN connections
./tunnelblick.zsh status "MyVPN"
./tunnelblick.zsh connect "MyVPN"
./tunnelblick.zsh disconnect "MyVPN"
```

## Documentation

For more detailed information on specific aspects of the project, please refer to the following documentation:

### API Documentation

[`README-api.md`](README-api.md) - Comprehensive guide to the Hac Hack REST API.

This document covers:
- Complete API endpoint documentation with request/response formats
- Authentication setup and mutual TLS configuration
- Detailed usage examples and curl commands
- API demo scripts and integration patterns
- Error handling, troubleshooting, and best practices
- Server deployment and configuration options

### Client-Side Usage

[`README-client.md`](README-client.md) - Comprehensive guide for using the HACClient class directly in Python applications.

This document covers:
- Direct integration with Python applications without using the REST API
- Session management and CSRF token handling
- Client-side demo scripts and examples
- Best practices for client-side HAC operations
- Comparison between API and client-side approaches
- Troubleshooting common issues

### VPN Control

[`README-tunnelblick.md`](README-tunnelblick.md) - Detailed documentation for controlling Tunnelblick VPN connections on macOS.

This document covers:
- Command-line control of Tunnelblick VPN connections
- Installation and setup instructions
- Usage examples for various VPN operations
- Automation examples and exit codes
- Troubleshooting common VPN issues

### Demo Scripts

[`demos/README-demos.md`](demos/README-demos.md) - Collection of demo scripts showcasing various HAC operations.

This document contains:
- Complete demo scripts for both API and client-side approaches
- Examples of common HAC operations (login, ImpEx import, Groovy execution)
- Customizable templates for your own automation tasks
- Best practices and integration patterns

### Release Notes

[`RELEASES.md`](RELEASES.md) - Comprehensive release notes and version history for the Hac Hack project.

This document contains:
- Detailed changelog for each version release
- New features and improvements
- Bug fixes and security updates
- Breaking changes and migration instructions
- Version compatibility information

## License

MIT

## Issues and Feedback

If you encounter any issues or have suggestions for improvements, please report them at:
[https://github.com/storizzi/hachack/issues](https://github.com/storizzi/hachack/issues)
