# Tunnelblick Control Script

A powerful zsh script for controlling Tunnelblick VPN connections on macOS from the command line. The main script is [`tunnelblick.zsh`](tunnelblick.zsh).

## Features

- List all available VPN connections with their status
- Connect to VPN connections with status monitoring
- Disconnect from individual or all active VPN connections
- Toggle connection state (connect if disconnected, disconnect if connected)
- Monitor connection status in real-time
- Configurable timeouts and polling intervals
- Verbose and quiet output modes
- Proper exit codes for use in automation
- Exact state matching to prevent false positives (e.g. DISCONNECTED no longer matches as CONNECTED)
- Disconnect waits for full DISCONNECTED state rather than returning on transitional EXITING
- Explicit handling of intermediate states (SLEEP, RECONNECTING) during connect operations

## Requirements

- macOS with Tunnelblick installed
- zsh shell (default on modern macOS)

## Installation

1. Download the script:
   ```
   curl -O https://raw.githubusercontent.com/yourusername/tunnelblick-control/main/tunnelblick.zsh
   ```

2. Make it executable:
   ```
   chmod +x tunnelblick.zsh
   ```

3. Optionally, move it to a directory in your PATH for easier access:
   ```
   mv tunnelblick.zsh /usr/local/bin/tunnelblick
   ```

## Usage

```
./tunnelblick.zsh [options] command [connection_name]
```

### Commands

- `list` - List all available connections with status
- `status [connection]` - Show status of all or a specific connection
- `connect <connection>` - Connect to a VPN with status polling
- `disconnect [connection]` - Disconnect from a VPN (waits for full DISCONNECTED state) or all active VPNs if none specified
- `toggle <connection>` - Toggle connection state
- `monitor <connection>` - Continuously monitor connection status

### Options

- `-t, --timeout SEC` - Set timeout for operations (default: 30s)
- `-p, --poll SEC` - Set polling interval (default: 1s)
- `-v, --verbose` - Enable verbose output for debugging
- `-q, --quiet` - Enable quiet mode with minimal output
- `-h, --help` - Show help message

## Examples

```bash
# List all available connections
./tunnelblick.zsh list

# Show status of a specific connection
./tunnelblick.zsh status "Work VPN"

# Connect to a VPN with 60 second timeout
./tunnelblick.zsh -t 60 connect "Work VPN"

# Disconnect from a VPN with verbose logging
./tunnelblick.zsh --verbose disconnect "Work VPN"

# Disconnect all active connections
./tunnelblick.zsh disconnect

# Toggle a connection with minimal output
./tunnelblick.zsh -q toggle "Personal VPN"

# Monitor a connection's status continuously
./tunnelblick.zsh monitor "Work VPN"
```

## Exit Codes

The script uses these exit codes for proper error handling in automation:

- `0`: Success
- `1`: Invalid arguments
- `2`: Connection not found
- `3`: Tunnelblick not running
- `4`: Operation timeout
- `5`: Operation failed

## Automation Examples

### Connect to VPN and execute commands only if connected

```bash
#!/bin/zsh
if ./tunnelblick.zsh -q connect "Work VPN"; then
  echo "Connected to VPN, executing secure operations..."
  # Run commands that require VPN
  # ...
  # Disconnect when done
  ./tunnelblick.zsh disconnect "Work VPN"
else
  echo "Failed to connect to VPN"
  exit 1
fi
```

### SSH with automatic VPN

```bash
#!/bin/zsh
HOST="internal-server.company.local"

# Try to connect directly first
if ssh -o ConnectTimeout=5 $HOST echo "Connection test"; then
  # Direct connection works, proceed
  ssh $HOST
else
  # Direct connection failed, try via VPN
  echo "Direct connection failed, connecting via VPN..."
  
  if ./tunnelblick.zsh -q connect "Work VPN"; then
    echo "VPN connected, trying SSH again..."
    ssh $HOST
    
    echo "Disconnecting VPN..."
    ./tunnelblick.zsh disconnect "Work VPN"
  else
    echo "Failed to connect to VPN"
    exit 1
  fi
fi
```

## Troubleshooting

### Common Issues

- **Error: Connection not found**: Verify the exact connection name in Tunnelblick by running the `list` command
- **Operation timed out**: Increase timeout with `-t` option if your connections take longer to establish
- **Tunnelblick not running**: The script will try to launch Tunnelblick automatically, but make sure it's installed correctly

### Debugging

Run the script with the `-v` (verbose) flag to see detailed output:

```bash
./tunnelblick.zsh -v connect "Work VPN"
```

## License

MIT License

## Acknowledgments

- This script uses AppleScript to control Tunnelblick
- Inspired by the need for better command-line control of VPN connections on macOS

## Related Documentation

For additional resources and documentation, please refer to:

- [Main Project Documentation](README.md) - General project context and setup information for the Hac Hack project