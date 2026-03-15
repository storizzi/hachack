import os
import requests
import argparse
import logging
import asyncio
import time
from datetime import datetime
from typing import Literal, Dict, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Query, Request
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
from pydantic import BaseModel
from hac_client import HACClient

# --- State Management for VPN Operations ---
active_vpn_tasks: Dict[str, asyncio.Task] = {}
vpn_operations: Dict[str, dict] = {}  # Tracks in-progress VPN operations per connection
_op_counter = 0

# --- Configuration ---
load_dotenv()

# Debug configuration
def _get_bool_env(env_var, default=False):
    """Helper to get boolean value from environment variable."""
    value = os.getenv(env_var, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

DEBUG_INCOMING_REQUEST = _get_bool_env("DEBUG_INCOMING_REQUEST", False)
DEBUG_OUTGOING_REQUEST = _get_bool_env("DEBUG_OUTGOING_REQUEST", False)
DEBUG_INCOMING_DATA = _get_bool_env("DEBUG_INCOMING_DATA", False)
DEBUG_OUTGOING_DATA = _get_bool_env("DEBUG_OUTGOING_DATA", False)

DEFAULT_TIMEOUT = None
env_timeout = os.getenv("HAC_TIMEOUT")
if env_timeout is not None:
    try:
        DEFAULT_TIMEOUT = int(env_timeout)
    except ValueError:
        print(f"⚠️ Invalid HAC_TIMEOUT value: {env_timeout}, using default 30s")
        DEFAULT_TIMEOUT = None
else:
    DEFAULT_TIMEOUT = None

IMPEX_DIR = "impex"
os.makedirs(IMPEX_DIR, exist_ok=True)
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
VPN_SCRIPT_PATH = os.getenv("VPN_SCRIPT_PATH", "tunnelblick.zsh")
DEFAULT_HAC_URL = os.getenv("HAC_URL")
DEFAULT_USERNAME = os.getenv("HAC_USERNAME")
DEFAULT_PASSWORD = os.getenv("HAC_PASSWORD")
VPN_DEFAULT_TIMEOUT = int(os.getenv("VPN_TIMEOUT", "60"))
VPN_OFF_RETRY_STEPS = [int(x) for x in os.getenv("VPN_OFF_RETRY_STEPS", "10,30,60").split(",")]

# --- Logging Setup ---
log_file = os.path.join(LOG_DIR, "HAC_API.log")
log_handler = TimedRotatingFileHandler(log_file, when="W0", interval=1, backupCount=0, encoding="utf-8")
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])

app = FastAPI()

logging.info("🔹 HAC URL Loaded: %s", "Set" if DEFAULT_HAC_URL else "Not Set")
logging.info("🔹 HAC Username Loaded: %s", "Set" if DEFAULT_USERNAME else "Not Set")
logging.info("🔹 HAC Password Loaded: %s", "Set" if DEFAULT_PASSWORD else "Not Set")
logging.info("🔹 Debug - Incoming Request: %s", DEBUG_INCOMING_REQUEST)
logging.info("🔹 Debug - Outgoing Request: %s", DEBUG_OUTGOING_REQUEST)
logging.info("🔹 Debug - Incoming Data: %s", DEBUG_INCOMING_DATA)
logging.info("🔹 Debug - Outgoing Data: %s", DEBUG_OUTGOING_DATA)

# --- Debug logging functions ---
def log_incoming_request(message):
    """Log incoming API requests."""
    if DEBUG_INCOMING_REQUEST:
        logging.info(f"[INCOMING_REQUEST] {message}")

def log_outgoing_request(message):
    """Log outgoing requests to HAC."""
    if DEBUG_OUTGOING_REQUEST:
        logging.info(f"[OUTGOING_REQUEST] {message}")

def log_incoming_data(message):
    """Log incoming data/responses."""
    if DEBUG_INCOMING_DATA:
        logging.info(f"[INCOMING_DATA] {message}")

def log_outgoing_data(message):
    """Log outgoing data/payloads."""
    if DEBUG_OUTGOING_DATA:
        logging.info(f"[OUTGOING_DATA] {message}")

# --- Middleware for request logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log incoming requests and responses."""
    # Log incoming request
    log_incoming_request(f"{request.method} {request.url}")
    if DEBUG_INCOMING_REQUEST:
        client_host = request.client.host if request.client else "unknown"
        log_incoming_request(f"Client: {client_host}")
        log_incoming_request(f"Headers: {dict(request.headers)}")

    # Process request
    response = await call_next(request)

    # Log response
    log_incoming_request(f"Response status: {response.status_code}")

    return response

# --- Helper to create HAC client ---
def get_hac_client(hac_url: str = None, username: str = None, password: str = None, timeout: int = None):
    hac_url = hac_url or DEFAULT_HAC_URL
    username = username or DEFAULT_USERNAME
    password = password or DEFAULT_PASSWORD
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    if not hac_url or not username or not password:
        raise HTTPException(status_code=400, detail="HAC credentials must be provided.")

    # Create HAC client with debug settings from environment
    debug_enabled = any([DEBUG_INCOMING_REQUEST, DEBUG_OUTGOING_REQUEST, DEBUG_INCOMING_DATA, DEBUG_OUTGOING_DATA])
    return HACClient(hac_url, username, password, timeout, debug=debug_enabled)

# --- VPN Utility Functions ---

async def _run_vpn_cmd(cmd: str, connection: str, timeout: Optional[int] = None) -> str:
    """Invoke Tunnelblick wrapper asynchronously, treating redundant operations as success."""
    args = [VPN_SCRIPT_PATH]
    if timeout is not None:
        args.extend(["-t", str(timeout)])
    args.extend([cmd, connection])

    try:
        log_outgoing_request(f"VPN command: {cmd} on connection: {connection}")
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"VPN script '{VPN_SCRIPT_PATH}' not found. Please set VPN_SCRIPT_PATH correctly.")

    stdout = stdout_bytes.decode().strip()
    stderr = stderr_bytes.decode().strip()
    returncode = proc.returncode

    logging.debug(f"VPN script '{cmd}' on '{connection}': returncode={returncode}, stdout='{stdout}', stderr='{stderr}'")

    if returncode != 0:
        error_msg = stderr if stderr else stdout
        if returncode == 3:
            raise HTTPException(status_code=503, detail=f"Tunnelblick is not running: {error_msg}")
        elif returncode == 2:
            raise HTTPException(status_code=404, detail=f"VPN connection not found: {error_msg}")
        elif returncode == 4:
            raise HTTPException(status_code=504, detail=f"VPN operation timed out: {error_msg}")
        else:
            raise HTTPException(status_code=500, detail=f"VPN script failed for '{cmd}' on '{connection}': {error_msg}")

    return stdout


async def _get_status(connection: str) -> Literal["on", "off", "error"]:
    """Always query the actual VPN status."""
    try:
        out = await _run_vpn_cmd("status", connection)
        logging.debug(f"VPN status output for '{connection}': {out}")
        if ":" in out:
            state_token = out.rsplit(":", 1)[1].strip()
        else:
            state_token = out.strip()
        if state_token == "CONNECTED":
            return "on"
        return "off"
    except HTTPException as e:
        logging.error(f"Failed to get VPN status for '{connection}': {e.detail}")
        return "error"


def _new_operation_id() -> str:
    """Generate a unique operation ID."""
    global _op_counter
    _op_counter += 1
    return f"vpn_op_{int(time.time())}_{_op_counter}"


def _get_operation_snapshot(connection: str) -> Optional[dict]:
    """Get a snapshot of the current operation for a connection, with elapsed times."""
    op = vpn_operations.get(connection)
    if not op:
        return None
    snap = dict(op)
    now = time.time()
    snap["total_elapsed"] = round(now - op["started_at"], 1)
    if op.get("step_started_at"):
        snap["step_elapsed"] = round(now - op["step_started_at"], 1)
    else:
        snap["step_elapsed"] = 0
    # Remove internal fields
    snap.pop("started_at", None)
    snap.pop("step_started_at", None)
    snap["started_at_iso"] = op.get("started_at_iso", "")
    return snap


async def _vpn_on_task(connection: str, op_id: str, revert_timeout: Optional[int]):
    """Background task to turn VPN on with retries."""
    op = vpn_operations.get(connection)
    if not op:
        return
    max_attempts = 3
    backoff = 5

    try:
        for attempt in range(1, max_attempts + 1):
            op["attempt"] = attempt
            op["max_attempts"] = max_attempts
            op["status"] = "in_progress"
            op["step_started_at"] = time.time()

            current = await _get_status(connection)
            op["current_state"] = current

            if current == "on":
                op["status"] = "completed"
                op["current_state"] = "on"
                logging.info(f"🔄 VPN ON -> completed, status=on (attempt {attempt})")
                break

            try:
                cmd = "connect"
                logging.info(f"VPN ON attempt {attempt}/{max_attempts}: {cmd} '{connection}'")
                await _run_vpn_cmd(cmd, connection)
                final = await _get_status(connection)
                op["current_state"] = final
                if final == "on":
                    op["status"] = "completed"
                    logging.info(f"🔄 VPN ON -> completed, status=on (attempt {attempt})")
                    break
            except Exception as e:
                op["error"] = str(e)
                logging.warning(f"VPN ON attempt {attempt}/{max_attempts} failed: {e}")

            if attempt < max_attempts:
                logging.info(f"VPN ON: waiting {backoff}s before retry...")
                await asyncio.sleep(backoff)

        if op["status"] != "completed":
            op["status"] = "failed"
            logging.error(f"❌ VPN ON -> failed after {max_attempts} attempts")

        # Schedule revert (safety net) if VPN is now on and timeout requested
        if op["status"] == "completed" and revert_timeout and revert_timeout > 0:
            existing = active_vpn_tasks.pop(connection, None)
            if existing:
                existing.cancel()
            revert_task = asyncio.create_task(
                _vpn_off_task(connection, _new_operation_id(), is_revert=True),
                name=f"revert-{connection}-{time.time()}"
            )
            # Store revert info but don't overwrite the current operation yet
            logging.info(f"🕒 Scheduled VPN OFF revert for '{connection}' in {revert_timeout}s")
            await asyncio.sleep(revert_timeout)
            # After timeout, launch the off task
            if connection in vpn_operations and vpn_operations[connection].get("operation_id") == op_id:
                # Only revert if no other operation has taken over
                vpn_operations[connection] = {
                    "operation_id": _new_operation_id(),
                    "connection": connection,
                    "action": "off",
                    "is_revert": True,
                    "target_state": "off",
                    "status": "pending",
                    "current_state": op.get("current_state", "unknown"),
                    "attempt": 0,
                    "max_attempts": len(VPN_OFF_RETRY_STEPS),
                    "retry_steps": VPN_OFF_RETRY_STEPS,
                    "current_step_timeout": VPN_OFF_RETRY_STEPS[0] if VPN_OFF_RETRY_STEPS else 0,
                    "started_at": time.time(),
                    "started_at_iso": datetime.now().isoformat(),
                    "step_started_at": time.time(),
                    "error": None,
                }
                await _vpn_off_task_inner(connection)

    except asyncio.CancelledError:
        op["status"] = "cancelled"
        logging.info(f"VPN ON operation cancelled for '{connection}'")
    except Exception as e:
        op["status"] = "failed"
        op["error"] = str(e)
        logging.error(f"VPN ON operation failed for '{connection}': {e}")


async def _vpn_off_task(connection: str, op_id: str, is_revert: bool = False):
    """Background task to turn VPN off with stepped retry backoff."""
    op = vpn_operations.get(connection)
    if not op:
        return
    await _vpn_off_task_inner(connection)


async def _vpn_off_task_inner(connection: str):
    """Inner implementation of VPN OFF with stepped retries."""
    op = vpn_operations.get(connection)
    if not op:
        return

    retry_steps = op.get("retry_steps", VPN_OFF_RETRY_STEPS)
    label = "VPN OFF (revert)" if op.get("is_revert") else "VPN OFF"

    try:
        for step_idx, step_timeout in enumerate(retry_steps):
            attempt = step_idx + 1
            op["attempt"] = attempt
            op["max_attempts"] = len(retry_steps)
            op["status"] = "in_progress"
            op["current_step_timeout"] = step_timeout
            op["step_started_at"] = time.time()

            # Check current state
            current = await _get_status(connection)
            op["current_state"] = current

            if current == "off":
                op["status"] = "completed"
                logging.info(f"🔄 {label} -> completed, status=off (step {attempt})")
                return

            # Try to disconnect
            try:
                logging.info(f"{label} step {attempt}/{len(retry_steps)}: disconnect '{connection}' (will wait {step_timeout}s)")
                await _run_vpn_cmd("disconnect", connection)
                final = await _get_status(connection)
                op["current_state"] = final
                if final == "off":
                    op["status"] = "completed"
                    logging.info(f"🔄 {label} -> completed, status=off (step {attempt})")
                    return
            except Exception as e:
                op["error"] = str(e)
                logging.warning(f"{label} step {attempt}/{len(retry_steps)} disconnect failed: {e}")

            # Wait for the step timeout before retrying
            logging.info(f"{label}: waiting {step_timeout}s before next attempt...")
            await asyncio.sleep(step_timeout)

            # Check again after waiting
            final = await _get_status(connection)
            op["current_state"] = final
            if final == "off":
                op["status"] = "completed"
                logging.info(f"🔄 {label} -> completed, status=off (after step {attempt} wait)")
                return

        # All steps exhausted
        op["status"] = "failed"
        logging.warning(f"⚠️ {label} -> gave up after {len(retry_steps)} steps, VPN may still be on")

    except asyncio.CancelledError:
        op["status"] = "cancelled"
        logging.info(f"{label} operation cancelled for '{connection}'")
    except Exception as e:
        op["status"] = "failed"
        op["error"] = str(e)
        logging.error(f"{label} operation failed for '{connection}': {e}")


# --- VPN Endpoints ---

@app.get("/vpn")
async def vpn_status(connection: str = Query(..., description="VPN connection name")):
    """Get VPN status including any in-progress operation."""
    connection = connection.strip("'").strip('"')
    status = await _get_status(connection)
    if status == "error":
        raise HTTPException(status_code=503, detail=f"Cannot determine VPN status for '{connection}'")

    result = {"connection": connection, "status": status}

    # Include operation info if one is active
    op_snap = _get_operation_snapshot(connection)
    if op_snap and op_snap["status"] in ("pending", "in_progress"):
        result["operation"] = op_snap

    return result


@app.put("/vpn")
async def vpn_control(
    connection: str = Query(..., description="VPN connection name"),
    action: Literal["on", "off", "revert"] = Query(..., description="Desired action"),
    timeout: Optional[int] = Query(None, description="Auto-revert timeout in seconds (for 'on' action)")
):
    """
    Request a VPN state change. Returns immediately (202 Accepted).
    Poll GET /vpn?connection=... to track progress.
    """
    connection = connection.strip("'").strip('"')
    logging.info(f"VPN control request: connection='{connection}', action='{action}', timeout={timeout}")

    # Get current state
    current = await _get_status(connection)
    if current == "error":
        logging.error(f"❌ VPN {action.upper()} -> cannot determine status")
        raise HTTPException(status_code=503, detail=f"Cannot determine VPN status for '{connection}'")

    # Handle revert: cancel any active operation/task
    if action == "revert":
        task = active_vpn_tasks.pop(connection, None)
        if task:
            task.cancel()
        vpn_operations.pop(connection, None)
        logging.info(f"🔄 VPN REVERT -> cancelled operations, status={current}")
        return {"connection": connection, "status": current, "action": "revert_cancelled"}

    desired_state = "on" if action == "on" else "off"

    # Already in desired state
    if current == desired_state:
        logging.info(f"VPN '{connection}' already '{desired_state}' - no action needed")
        action_log = action.upper()
        logging.info(f"🔄 VPN {action_log} -> HTTP 200, status={current}")
        # Clear any stale operation
        vpn_operations.pop(connection, None)
        # For ON with timeout, still schedule the safety revert
        if action == "on" and timeout and timeout > 0:
            op_id = _new_operation_id()
            vpn_operations[connection] = {
                "operation_id": op_id,
                "connection": connection,
                "action": "on",
                "target_state": "on",
                "status": "completed",
                "current_state": "on",
                "attempt": 0,
                "max_attempts": 0,
                "retry_steps": [],
                "current_step_timeout": 0,
                "started_at": time.time(),
                "started_at_iso": datetime.now().isoformat(),
                "step_started_at": None,
                "error": None,
            }
            # Schedule revert in background
            existing = active_vpn_tasks.pop(connection, None)
            if existing:
                existing.cancel()
            task = asyncio.create_task(
                _schedule_revert_via_off(connection, op_id, timeout),
                name=f"revert-{connection}-{time.time()}"
            )
            active_vpn_tasks[connection] = task
        return {"connection": connection, "status": current, "action": "noop", "accepted": True}

    # Cancel any existing background task for this connection
    existing_task = active_vpn_tasks.pop(connection, None)
    if existing_task:
        existing_task.cancel()

    # Create the operation
    op_id = _new_operation_id()
    now = time.time()
    op = {
        "operation_id": op_id,
        "connection": connection,
        "action": action,
        "target_state": desired_state,
        "status": "pending",
        "current_state": current,
        "attempt": 0,
        "max_attempts": len(VPN_OFF_RETRY_STEPS) if action == "off" else 3,
        "retry_steps": VPN_OFF_RETRY_STEPS if action == "off" else [],
        "current_step_timeout": VPN_OFF_RETRY_STEPS[0] if action == "off" and VPN_OFF_RETRY_STEPS else 0,
        "started_at": now,
        "started_at_iso": datetime.now().isoformat(),
        "step_started_at": now,
        "error": None,
    }
    vpn_operations[connection] = op

    # Launch background task
    if action == "on":
        revert_timeout = timeout if timeout is not None else VPN_DEFAULT_TIMEOUT
        task = asyncio.create_task(
            _vpn_on_task(connection, op_id, revert_timeout),
            name=f"vpn-on-{connection}-{time.time()}"
        )
    else:
        task = asyncio.create_task(
            _vpn_off_task(connection, op_id),
            name=f"vpn-off-{connection}-{time.time()}"
        )
    active_vpn_tasks[connection] = task

    logging.info(f"VPN {action.upper()} operation accepted: {op_id}")
    return {
        "connection": connection,
        "status": current,
        "action": action,
        "operation_id": op_id,
        "accepted": True,
    }


async def _schedule_revert_via_off(connection: str, original_op_id: str, delay: int):
    """Schedule a VPN OFF after a delay (safety revert for ON operations)."""
    try:
        logging.info(f"🕒 Scheduled VPN OFF revert for '{connection}' in {delay}s")
        await asyncio.sleep(delay)

        # Only proceed if no other operation has taken over
        current_op = vpn_operations.get(connection)
        if current_op and current_op.get("operation_id") != original_op_id:
            logging.info(f"Revert cancelled — another operation is active for '{connection}'")
            return

        current = await _get_status(connection)
        if current == "off":
            logging.info(f"Revert not needed — '{connection}' already off")
            return

        logging.info(f"⏰ Revert triggered: turning off '{connection}'")
        op_id = _new_operation_id()
        vpn_operations[connection] = {
            "operation_id": op_id,
            "connection": connection,
            "action": "off",
            "is_revert": True,
            "target_state": "off",
            "status": "pending",
            "current_state": current,
            "attempt": 0,
            "max_attempts": len(VPN_OFF_RETRY_STEPS),
            "retry_steps": VPN_OFF_RETRY_STEPS,
            "current_step_timeout": VPN_OFF_RETRY_STEPS[0] if VPN_OFF_RETRY_STEPS else 0,
            "started_at": time.time(),
            "started_at_iso": datetime.now().isoformat(),
            "step_started_at": time.time(),
            "error": None,
        }
        await _vpn_off_task_inner(connection)

    except asyncio.CancelledError:
        logging.info(f"Revert task cancelled for '{connection}'")
    except Exception as e:
        logging.error(f"Revert task failed for '{connection}': {e}")

# --- Original HAC Endpoints ---

class LoginRequest(BaseModel):
    hac_url: str
    username: str
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    """Login to HAC dynamically with credentials in the JSON body."""
    log_incoming_request(f"Login request for HAC URL: {request.hac_url}")
    if DEBUG_INCOMING_DATA:
        log_incoming_data(f"Login request payload: {{'hac_url': '{request.hac_url}', 'username': '{request.username}', 'password': '[REDACTED]'}}")

    hac = get_hac_client(request.hac_url, request.username, request.password)
    result = hac.login()

    if result.get("success"):
        logging.info("✅ Successful HAC login")
        return {"success": True, "message": "Logged in successfully"}
    
    logging.warning("❌ Failed HAC login attempt")
    raise HTTPException(status_code=401, detail="Login failed")

class GroovyRequest(BaseModel):
    hac_url: str
    username: str
    password: str
    script: str

@app.post("/execute_groovy")
async def execute_groovy(request: GroovyRequest):
    """Execute a Groovy script with all parameters in the JSON body."""
    log_incoming_request(f"Groovy execution request for HAC URL: {request.hac_url}")
    if DEBUG_INCOMING_DATA:
        log_incoming_data(f"Groovy request payload: {{'hac_url': '{request.hac_url}', 'username': '{request.username}', 'password': '[REDACTED]', 'script': '[SCRIPT_CONTENT]'}}")

    hac = get_hac_client(request.hac_url, request.username, request.password)
    if not hac.is_authenticated():
        if not hac.login().get("success"):
            raise HTTPException(status_code=401, detail="Login failed before executing Groovy script.")
    result = hac.execute_groovy_script(request.script)
    if result:
        if DEBUG_OUTGOING_DATA:
            log_outgoing_data(f"Groovy execution result: {result}")
        return result
    raise HTTPException(status_code=500, detail="Groovy script execution failed")

class ImpExRequest(BaseModel):
    hac_url: str
    username: str
    password: str
    script: str

@app.post("/import_impex")
async def import_impex(request: ImpExRequest):
    """Import an ImpEx script dynamically, ensuring authentication first."""
    log_incoming_request(f"ImpEx import request for HAC URL: {request.hac_url}")
    if DEBUG_INCOMING_DATA:
        log_incoming_data(f"ImpEx request payload: {{'hac_url': '{request.hac_url}', 'username': '{request.username}', 'password': '[REDACTED]', 'script': '[IMPEX_SCRIPT]'}}")

    hac = get_hac_client(request.hac_url, request.username, request.password)
    if not hac.login().get("success"):  
        raise HTTPException(status_code=401, detail="Login failed before importing ImpEx.")
    result = hac.import_impex(request.script)
    if result and result.get("success"):
        logging.info("✅ ImpEx import completed successfully")
        if DEBUG_OUTGOING_DATA:
            log_outgoing_data(f"ImpEx import result: {result}")
        return result
    logging.warning("❌ ImpEx import failed")
    return {"success": False, "impex_result": "Import failed", "impex_details": result.get("impex_details", "Unknown error")}

@app.post("/import_impex_file")
async def import_impex_file(
    hac_url: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
    retain: bool = Form(False)
):
    """Upload and import an ImpEx file dynamically, ensuring authentication first."""
    log_incoming_request(f"ImpEx file import request for HAC URL: {hac_url}")
    log_incoming_request(f"File: {file.filename}, Retain: {retain}")

    hac = get_hac_client(hac_url, username, password)
    if not hac.login().get("success"):  
        raise HTTPException(status_code=401, detail="Login failed before importing ImpEx file.")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    original_filename, ext = os.path.splitext(file.filename)
    new_filename = f"{original_filename}_{timestamp}{ext}"
    file_path = os.path.join(IMPEX_DIR, new_filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    result = hac.import_impex_file(file_path)
    if not retain:
        os.remove(file_path)
    else:
        logging.info(f"🗂️ Retained ImpEx file: {file_path}")
    if result and result.get("success"):
        logging.info(f"✅ ImpEx file '{new_filename}' imported successfully")
        if DEBUG_OUTGOING_DATA:
            log_outgoing_data(f"ImpEx file import result: {result}")
        return {"success": True, "impex_result": result["impex_result"], "file_path": file_path if retain else None}
    logging.warning(f"❌ ImpEx file '{new_filename}' import failed")
    return {"success": False, "impex_result": "Import failed", "impex_details": result.get("impex_details", "Unknown error")}

@app.get("/")
async def root():
    """Test endpoint to verify authentication."""
    return {"message": "Hello, authenticated client!"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start FastAPI with optional port parameter.")
    parser.add_argument("--port", type=int, default=8037, help="Port number to run the server on")
    parser.add_argument("--timeout", type=int, help="Request timeout in seconds")
    args = parser.parse_args()
    
    if args.timeout is not None:
        globals()["DEFAULT_TIMEOUT"] = args.timeout

    logging.info("✅ Starting HAC API on port %d with timeout: %s seconds", args.port, DEFAULT_TIMEOUT or "Client Default")
    
    # SSL Configuration
    cert_file, key_file, ca_cert = "certs/server/server-cert.pem", "certs/server/server-key.pem", "certs/ca/ca-cert.pem"
    if not all(os.path.exists(p) for p in [cert_file, key_file, ca_cert]):
        logging.error("❌ Missing SSL certificates! Please run `generate_certificates.zsh`.")
        exit(1)
    logging.info("🔹 SSL Certificate: %s (Loaded Successfully)", cert_file)
    logging.info("🔹 SSL Key: %s (Loaded Successfully)", key_file)
    logging.info("🔹 SSL CA Certificate: %s (Loaded Successfully)", ca_cert)
    
    import uvicorn
    uvicorn.run("hac_api:app", host="0.0.0.0", port=args.port, ssl_certfile=cert_file, ssl_keyfile=key_file, ssl_ca_certs=ca_cert, reload=True)