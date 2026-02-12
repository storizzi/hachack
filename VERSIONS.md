# Version History

## v0.1.1 - 2025-02-12

### VPN Reliability Fixes

**Shell script (`tunnelblick.zsh`):**

- Fixed `$status` variable typo in `disconnect_vpn()` — was referencing an undefined variable instead of `$conn_status`, causing the DISCONNECTED check to never match
- Restructured disconnect polling to wait for actual DISCONNECTED state instead of returning on transitional EXITING state; added final-check fallback on timeout
- Replaced all glob/substring state matching (`*"CONNECTED"*`) with exact matches (`"CONNECTED"`) to prevent false positives (e.g. DISCONNECTED matching as CONNECTED)
- Added explicit handling for intermediate states (SLEEP, RECONNECTING, DISCONNECTED) during connect polling

**Python API (`hac_api.py`):**

- Fixed critical CONNECTED/DISCONNECTED substring match bug in status parsing — now extracts the state token and uses exact equality
- Converted blocking `subprocess.run()` to async `asyncio.create_subprocess_exec()` so VPN operations no longer block the event loop
- Added timeout propagation — shell script now receives `-t <seconds>` flag from the API
- Mapped shell exit codes to specific HTTP status codes (503 for Tunnelblick not running, 404 for connection not found, 504 for timeout)
- Added retry logic to `_ensure_state()` (2 attempts, 3s backoff)
- Added aggressive retry logic to scheduled reverts (3 attempts, 5s/10s backoff) — the safety net for auto-revert
- Noop+timeout now schedules a revert even when VPN is already in the desired state, ensuring cancelled reverts are replaced
- Status errors now return `"error"` and raise HTTP 503 instead of silently defaulting to `"off"`

### Documentation

- Added table of contents to README.md
- Added VPN Tunnel Management section to README.md describing async, retry, and error propagation behaviours
- Added links from README.md to Tunnelblick docs, VERSIONS.md, and LICENSE
- Updated Tunnelblick README with new reliability features (exact state matching, disconnect wait behaviour, intermediate state handling)
- Added back-link from Tunnelblick README to main README
- Created VERSIONS.md for release history tracking

## v0.1.0 - 2025-11-14

### Initial Public Release

- HAC authentication, Groovy script execution, ImpEx import (script and file upload)
- VPN tunnel management via Tunnelblick (status, connect, disconnect, toggle, revert with auto-timeout)
- mTLS certificate generation script
- FastAPI-based HTTPS API with mutual TLS authentication
