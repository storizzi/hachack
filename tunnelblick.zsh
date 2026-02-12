#!/usr/bin/env zsh

# tunnelblick.zsh - Advanced Tunnelblick VPN control script
# Author: Simon Huggins
# Usage: ./tunnelblick.zsh [options] command [connection_name]

# Default configuration
typeset -A CONFIG
CONFIG[timeout]=30            # Timeout in seconds for operations
CONFIG[poll_interval]=1       # Status polling interval in seconds
CONFIG[verbose]=0             # Verbose output (0=off, 1=on)
CONFIG[quiet]=0               # Quiet mode (0=off, 1=on)

# Exit codes
SUCCESS=0
ERR_INVALID_ARGS=1
ERR_CONNECTION_NOT_FOUND=2
ERR_TUNNELBLICK_NOT_RUNNING=3
ERR_OPERATION_TIMEOUT=4
ERR_OPERATION_FAILED=5

# Function to print help message
function show_help() {
    cat << EOF
Usage: $0 [options] command [connection_name]

Commands:
  list                    List all available Tunnelblick connections
  status [connection]     Show status of all connections or a specific connection
  connect <connection>    Connect to the specified VPN
  disconnect [connection] Disconnect from the specified VPN or all active VPNs if none specified
  toggle <connection>     Toggle connection state
  monitor <connection>    Monitor connection status continuously

Options:
  -t, --timeout SEC       Set timeout for operations (default: ${CONFIG[timeout]}s)
  -p, --poll SEC          Set polling interval (default: ${CONFIG[poll_interval]}s)
  -v, --verbose           Enable verbose output
  -q, --quiet             Enable quiet mode (minimal output)
  -h, --help              Show this help message

Examples:
  $0 list
  $0 status "Work VPN"
  $0 -t 60 connect "Work VPN"
  $0 --verbose disconnect "Work VPN"
  $0 disconnect             # Disconnect all active VPNs
  $0 -q toggle "Personal VPN"
  $0 monitor "Work VPN"
EOF
}

# Function to log messages
function log() {
    local level=$1
    shift
    local message="$@"
    
    if [[ $level == "error" ]]; then
        echo "ERROR: $message" >&2
    elif [[ $level == "warning" ]]; then
        [[ ${CONFIG[quiet]} -eq 0 ]] && echo "WARNING: $message" >&2
    elif [[ $level == "info" ]]; then
        [[ ${CONFIG[quiet]} -eq 0 ]] && echo "$message"
    elif [[ $level == "debug" ]]; then
        [[ ${CONFIG[verbose]} -eq 1 && ${CONFIG[quiet]} -eq 0 ]] && echo "DEBUG: $message"
    fi
}

# Function to check if Tunnelblick is running
function ensure_tunnelblick_running() {
    log "debug" "Checking if Tunnelblick is running..."
    
    if ! pgrep -q Tunnelblick; then
        log "info" "Starting Tunnelblick..."
        open -a Tunnelblick
        
        # Wait for Tunnelblick to start
        local counter=0
        while ! pgrep -q Tunnelblick; do
            sleep 0.5
            counter=$((counter + 1))
            if [[ $counter -gt 10 ]]; then
                log "error" "Failed to start Tunnelblick"
                return $ERR_TUNNELBLICK_NOT_RUNNING
            fi
        done
        
        # Give it a moment to initialize
        sleep 2
        log "debug" "Tunnelblick is now running"
    else
        log "debug" "Tunnelblick is already running"
    fi
    
    return $SUCCESS
}

# Function to check if a connection exists
function connection_exists() {
    local connection_name="$1"
    log "debug" "Checking if connection '$connection_name' exists..."
    
    # Get all configuration names
    local all_configs=$(osascript -e 'tell application "Tunnelblick" to get name of configurations')
    
    # Check if the connection name is in the list
    if [[ $all_configs == *"$connection_name"* ]]; then
        log "debug" "Connection '$connection_name' exists"
        return $SUCCESS
    else
        log "debug" "Connection '$connection_name' does not exist"
        return $ERR_CONNECTION_NOT_FOUND
    fi
}

# Function to get connection status
function get_connection_state() {
    local connection_name="$1"
    osascript -e "tell application \"Tunnelblick\" to get state of first configuration where name is \"$connection_name\""
}

# Function to list all available connections
function list_connections() {
    log "debug" "Listing all available connections..."
    
    ensure_tunnelblick_running || return $?
    
    log "info" "Available Tunnelblick connections:"
    local connections=$(osascript -e 'tell application "Tunnelblick" to get name of configurations')
    
    if [[ -z "$connections" ]]; then
        log "info" "No connections found"
        return $SUCCESS
    fi
    
    # Format and display connections with their status
    echo "$connections" | tr "," "\n" | while read -r conn; do
        # Remove leading/trailing spaces
        conn=$(echo "$conn" | sed 's/^ *//;s/ *$//')
        if [[ -n "$conn" ]]; then
            local conn_state=$(get_connection_state "$conn")
            log "info" "- $conn: $conn_state"
        fi
    done
    
    return $SUCCESS
}

# Function to show connection status
function show_status() {
    local connection_name="$1"
    
    ensure_tunnelblick_running || return $?
    
    if [[ -z "$connection_name" ]]; then
        # Show status of all connections
        log "info" "Status of all Tunnelblick connections:"
        list_connections
    else
        # Check if connection exists
        connection_exists "$connection_name" || {
            log "error" "Connection '$connection_name' not found"
            return $ERR_CONNECTION_NOT_FOUND
        }
        
        # Show status of specific connection
        local conn_state=$(get_connection_state "$connection_name")
        log "info" "Status of '$connection_name': $conn_state"
    fi
    
    return $SUCCESS
}

# Function to monitor a connection continuously
function monitor_connection() {
    local connection_name="$1"
    
    ensure_tunnelblick_running || return $?
    
    # Check if connection exists
    connection_exists "$connection_name" || {
        log "error" "Connection '$connection_name' not found"
        return $ERR_CONNECTION_NOT_FOUND
    }
    
    log "info" "Monitoring '$connection_name'. Press Ctrl+C to stop..."
    local last_state=""
    
    while true; do
        local current_state=$(get_connection_state "$connection_name")
        
        if [[ "$current_state" != "$last_state" ]]; then
            log "info" "$(date '+%Y-%m-%d %H:%M:%S') - '$connection_name': $current_state"
            last_state="$current_state"
        fi
        
        sleep ${CONFIG[poll_interval]}
    done
}

# Function to connect to a VPN with timeout
function connect_vpn() {
    local connection_name="$1"
    
    ensure_tunnelblick_running || return $?
    
    # Check if connection exists
    connection_exists "$connection_name" || {
        log "error" "Connection '$connection_name' not found"
        return $ERR_CONNECTION_NOT_FOUND
    }
    
    # Check current status
    local conn_state=$(get_connection_state "$connection_name")
    if [[ "$conn_state" == "CONNECTED" ]]; then
        log "info" "Connection '$connection_name' is already connected"
        return $SUCCESS
    fi

    log "info" "Connecting to '$connection_name'..."
    osascript -e "tell application \"Tunnelblick\" to connect \"$connection_name\""

    # Wait for connection to establish with timeout
    local timer=0
    while [[ $timer -lt ${CONFIG[timeout]} ]]; do
        conn_state=$(get_connection_state "$connection_name")
        log "debug" "State: $conn_state (waited ${timer}s)"

        if [[ "$conn_state" == "CONNECTED" ]]; then
            log "info" "Successfully connected to '$connection_name'"
            return $SUCCESS
        elif [[ "$conn_state" == "EXITING" || "$conn_state" == "FAILED" ]]; then
            log "error" "Connection failed with state: $conn_state"
            return $ERR_OPERATION_FAILED
        elif [[ "$conn_state" == "DISCONNECTED" ]]; then
            log "error" "Connection dropped to DISCONNECTED during connect attempt"
            return $ERR_OPERATION_FAILED
        elif [[ "$conn_state" == "SLEEP" || "$conn_state" == "RECONNECTING" ]]; then
            log "debug" "Intermediate state '$conn_state', continuing to wait..."
        fi

        sleep ${CONFIG[poll_interval]}
        timer=$((timer + ${CONFIG[poll_interval]}))
    done
    
    log "error" "Connection timed out after ${CONFIG[timeout]} seconds"
    return $ERR_OPERATION_TIMEOUT
}

# Function to disconnect from a VPN with timeout
function disconnect_vpn() {
    local connection_name="$1"
    
    ensure_tunnelblick_running || return $?
    
    # Check if connection exists
    connection_exists "$connection_name" || {
        log "error" "Connection '$connection_name' not found"
        return $ERR_CONNECTION_NOT_FOUND
    }
    
    # Check current status
    local conn_status=$(get_connection_state "$connection_name")
    if [[ "$conn_status" != "CONNECTED" && "$conn_status" != "EXITING" ]]; then
        log "info" "Connection '$connection_name' is already disconnected"
        return $SUCCESS
    fi

    log "info" "Disconnecting from '$connection_name'..."
    osascript -e "tell application \"Tunnelblick\" to disconnect \"$connection_name\""

    # Wait for disconnection with timeout
    local timer=0
    while [[ $timer -lt ${CONFIG[timeout]} ]]; do
        conn_status=$(get_connection_state "$connection_name")
        log "debug" "Status: $conn_status (waited ${timer}s)"

        if [[ "$conn_status" == "EXITING" ]]; then
            log "debug" "Transitional state EXITING, continuing to wait..."
        elif [[ "$conn_status" != "CONNECTED" ]]; then
            # Any state that is not CONNECTED or EXITING means disconnect succeeded
            log "info" "Successfully disconnected from '$connection_name' (state: $conn_status)"
            return $SUCCESS
        fi

        sleep ${CONFIG[poll_interval]}
        timer=$((timer + ${CONFIG[poll_interval]}))
    done

    # Final-check fallback: if timeout expired but state is not CONNECTED, treat as success
    conn_status=$(get_connection_state "$connection_name")
    if [[ "$conn_status" != "CONNECTED" ]]; then
        log "info" "Disconnect completed after timeout (final state: $conn_status)"
        return $SUCCESS
    fi

    log "error" "Disconnection timed out after ${CONFIG[timeout]} seconds"
    return $ERR_OPERATION_TIMEOUT
}

# Function to toggle connection state
function toggle_vpn() {
    local connection_name="$1"
    
    ensure_tunnelblick_running || return $?
    
    # Check if connection exists
    connection_exists "$connection_name" || {
        log "error" "Connection '$connection_name' not found"
        return $ERR_CONNECTION_NOT_FOUND
    }
    
    # Check current status
    local conn_state=$(get_connection_state "$connection_name")
    
    if [[ "$conn_state" == "CONNECTED" ]]; then
        log "info" "Connection '$connection_name' is connected, disconnecting..."
        disconnect_vpn "$connection_name"
        return $?
    else
        log "info" "Connection '$connection_name' is not connected, connecting..."
        connect_vpn "$connection_name"
        return $?
    fi
}

# Parse command line options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--timeout)
            if [[ $2 =~ ^[0-9]+$ ]]; then
                CONFIG[timeout]=$2
                shift 2
            else
                log "error" "Timeout must be a number"
                exit $ERR_INVALID_ARGS
            fi
            ;;
        -p|--poll)
            if [[ $2 =~ ^[0-9]+$ ]]; then
                CONFIG[poll_interval]=$2
                shift 2
            else
                log "error" "Poll interval must be a number"
                exit $ERR_INVALID_ARGS
            fi
            ;;
        -v|--verbose)
            CONFIG[verbose]=1
            shift
            ;;
        -q|--quiet)
            CONFIG[quiet]=1
            shift
            ;;
        -h|--help)
            show_help
            exit $SUCCESS
            ;;
        -*)
            log "error" "Unknown option: $1"
            show_help
            exit $ERR_INVALID_ARGS
            ;;
        *)
            break
            ;;
    esac
done

# Check for command
if [[ $# -lt 1 ]]; then
    log "error" "Command required"
    show_help
    exit $ERR_INVALID_ARGS
fi

# Process command
command="$1"
shift

case "$command" in
    list)
        list_connections
        exit $?
        ;;
    status)
        show_status "$1"
        exit $?
        ;;
    connect)
        if [[ -z "$1" ]]; then
            log "error" "Connection name required for 'connect' command"
            exit $ERR_INVALID_ARGS
        fi
        connect_vpn "$1"
        exit $?
        ;;
    disconnect)
        disconnect_vpn "$1"
        exit $?
        ;;
    toggle)
        if [[ -z "$1" ]]; then
            log "error" "Connection name required for 'toggle' command"
            exit $ERR_INVALID_ARGS
        fi
        toggle_vpn "$1"
        exit $?
        ;;
    monitor)
        if [[ -z "$1" ]]; then
            log "error" "Connection name required for 'monitor' command"
            exit $ERR_INVALID_ARGS
        fi
        monitor_connection "$1"
        exit $?
        ;;
    *)
        log "error" "Unknown command: $command"
        show_help
        exit $ERR_INVALID_ARGS
        ;;
esac