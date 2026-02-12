# Hac Hack v0.1.1 - API for Auto-running Hybris HAC Operations

A Python library and FastAPI-based HTTP API for automating SAP Commerce / Hybris HAC tasks.

## Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [mTLS Authentication](#mtls-authentication)
- [Certificate Generation Script](#certificate-generation-script)
- [API Endpoints](#api-endpoints)
- [Sample curl Commands](#sample-curl-commands-https-self-signed-cert)
- [Running the Server](#running-the-server)
- [VPN Tunnel Management](#vpn-tunnel-management)
- [Version History](#version-history)
- [License](#license)

## Features

* **Authentication**: Login to HAC.
* **Execute Groovy scripts**: Run arbitrary Groovy code on the HAC.
* **Import ImpEx scripts**: Submit ImpEx payloads directly.
* **Upload & import ImpEx files**: POST files for batch data operations.
* **Health check**: Simple ping endpoint.
* **VPN tunnel management**: Wrap HAC calls with a VPN tunnel (status/connect/disconnect/revert) — see the [Tunnelblick control script documentation](READMe-tunnelblick.md) for details on the underlying shell script.

## Prerequisites

* Python 3.9+
* `pip install -r requirements.txt`
* `generate_certificates.zsh` (for mTLS certs)
* Tunnel control script (e.g. `tunnelblick.zsh`) if you want to control VPN establishment from the endpoint too

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

The `generate_certificates.zsh` script automates creation of a private Certificate Authority (CA), plus server and client certificates for mutual TLS authentication.

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

---

## API Endpoints

| Method | Path                 | Description                              | Parameters                                                                        |
| ------ | -------------------- | ---------------------------------------- | --------------------------------------------------------------------------------- |
| GET    | `/ping`              | Health check                             | —                                                                                 |
| POST   | `/login`             | Login to HAC                             | JSON body: `hac_url`, `username`, `password`                                      |
| POST   | `/execute_groovy`    | Execute a Groovy script                  | JSON body: `hac_url`, `username`, `password`, `script`                            |
| POST   | `/import_impex`      | Import an ImpEx script                   | JSON body: `hac_url`, `username`, `password`, `script`                            |
| POST   | `/import_impex_file` | Upload & import an ImpEx file            | Form-data: `hac_url`, `username`, `password`, `file`, `retain`                    |
| GET    | `/vpn-service`       | Get VPN tunnel status                    | Query: `connection`                                                               |
| PUT    | `/vpn-service`       | Connect / disconnect / revert VPN tunnel | Query: `connection`, `action` (`on`/`off`/`revert`), optional `timeout` (seconds) |

> All endpoints require mutual TLS and return JSON responses.

## Sample `curl` Commands (HTTPS, self-signed cert)

> Use `-k` to bypass certificate verification in development.

### 1. Health Check

```sh
curl -k https://localhost:8037/ping
```

### 2. Login

```sh
curl -k -X POST https://localhost:8037/login \
  -H 'Content-Type: application/json' \
  -d '{"hac_url":"https://my-hac","username":"user","password":"pass"}'
```

### 3. Execute Groovy Script

```sh
curl -k -X POST https://localhost:8037/execute_groovy \
  -H 'Content-Type: application/json' \
  -d '{"hac_url":"https://my-hac","username":"user","password":"pass","script":"println(\"Hello HAC\")"}'
```

### 4. Import ImpEx Script

```sh
curl -k -X POST https://localhost:8037/import_impex \
  -H 'Content-Type: application/json' \
  -d '{"hac_url":"https://my-hac","username":"user","password":"pass","script":"INSERT_UPDATE Catalog; code[unique = true]; name[lang = en];\n; testCatalog; Test Catalog"}'
```

### 5. Upload & Import ImpEx File

```sh
curl -k -X POST https://localhost:8037/import_impex_file \
  -F hac_url=https://my-hac \
  -F username=user \
  -F password=pass \
  -F file=@path/to/products.impex \
  -F retain=true
```

### 6. VPN Tunnel — Status

```sh
curl -k -G https://localhost:8037/vpn-service \
  --data-urlencode 'connection=MyVPN'
```

### 7. VPN Tunnel — Connect (default timeout)

```sh
curl -k -X PUT 'https://localhost:8037/vpn-service?connection=MyVPN&action=on'
```

### 8. VPN Tunnel — Disconnect (30s timeout)

```sh
curl -k -X PUT 'https://localhost:8037/vpn-service?connection=MyVPN&action=off&timeout=30'
```

### 9. VPN Tunnel — Revert to Previous State

```sh
curl -k -X PUT 'https://localhost:8037/vpn-service?connection=MyVPN&action=revert'
```

## Running the Server

### Development (HTTP only)

```sh
uvicorn hac_api:app --reload --host 0.0.0.0 --port 8037
```

### Testing with Built-in TLS

```sh
uvicorn hac_api:app --host 0.0.0.0 --port 8037 \
  --ssl-keyfile certs/server/server-key.pem \
  --ssl-certfile certs/server/server-cert.pem \
  --ssl-ca-certs certs/ca/ca-cert.pem
```

## VPN Tunnel Management

The VPN integration uses Tunnelblick on macOS. For full details on the underlying shell script (commands, options, exit codes, automation examples), see the [Tunnelblick Control Script documentation](READMe-tunnelblick.md).

Key behaviours of the API VPN endpoints:

* **Async non-blocking** — VPN operations run asynchronously and do not block the API event loop
* **Automatic retries** — connect/disconnect operations retry on failure (2 attempts with 3s backoff)
* **Scheduled reverts** — after a timeout, the VPN reverts to its previous state with aggressive retries (3 attempts, 5s/10s backoff)
* **Error propagation** — Tunnelblick not running returns HTTP 503, connection not found returns 404, operation timeout returns 504

## Version History

See [VERSIONS.md](VERSIONS.md) for the full release history.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG](CHANGELOG.md) for details.

-- Simon Huggins, Storizzi - 14 Nov 2025 to 12-Feb-2025
