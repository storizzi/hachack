import os
import requests
import subprocess
import argparse
import logging
import asyncio
import time
from datetime import datetime
from typing import Literal, Dict, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Query
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
from pydantic import BaseModel
from hac_client import HACClient

# --- State Management for Cancellable Tasks ---
active_vpn_tasks: Dict[str, asyncio.Task] = {}

# --- Configuration ---
load_dotenv()

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

# --- Logging Setup ---
log_file = os.path.join(LOG_DIR, "HAC_API.log")
log_handler = TimedRotatingFileHandler(log_file, when="W0", interval=1, backupCount=0, encoding="utf-8")
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])

app = FastAPI()

logging.info("🔹 HAC URL Loaded: %s", "Set" if DEFAULT_HAC_URL else "Not Set")
logging.info("🔹 HAC Username Loaded: %s", "Set" if DEFAULT_USERNAME else "Not Set")
logging.info("🔹 HAC Password Loaded: %s", "Set" if DEFAULT_PASSWORD else "Not Set")

# --- Helper to create HAC client ---
def get_hac_client(hac_url: str = None, username: str = None, password: str = None, timeout: int = None):
    hac_url = hac_url or DEFAULT_HAC_URL
    username = username or DEFAULT_USERNAME
    password = password or DEFAULT_PASSWORD
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    if not hac_url or not username or not password:
        raise HTTPException(status_code=400, detail="HAC credentials must be provided.")
    return HACClient(hac_url, username, password, timeout, debug=True)

# --- VPN Utility Functions ---

def _run_vpn_cmd(cmd: str, connection: str) -> str:
    """Invoke Tunnelblick wrapper, treating redundant operations as success."""
    try:
        proc = subprocess.run(
            [VPN_SCRIPT_PATH, cmd, connection],
            capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"VPN script '{VPN_SCRIPT_PATH}' not found. Please set VPN_SCRIPT_PATH correctly.")
    
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    
    # Log the actual output for debugging
    logging.debug(f"VPN script '{cmd}' on '{connection}': returncode={proc.returncode}, stdout='{stdout}', stderr='{stderr}'")
    
    # Your script returns exit code 0 for both success and idempotent operations
    # It only returns non-zero for actual errors
    if proc.returncode != 0:
        error_msg = stderr if stderr else stdout
        raise HTTPException(status_code=500, detail=f"VPN script failed for '{cmd}' on '{connection}': {error_msg}")
    
    # Exit code 0 means success (including idempotent operations)
    return stdout


def _get_status(connection: str) -> Literal["on", "off"]:
    """Always query the actual VPN status."""
    try:
        out = _run_vpn_cmd("status", connection)
        logging.debug(f"VPN status output for '{connection}': {out}")
        
        # Your script outputs: "Status of 'Wilko Grid VPN': CONNECTED" or "Status of 'Wilko Grid VPN': EXITING"
        # CONNECTED means on, anything else (EXITING, DISCONNECTED, etc.) means off
        if "CONNECTED" in out:
            return "on"
        return "off"
    except HTTPException as e:
        logging.error(f"Failed to get VPN status for '{connection}': {e.detail}")
        # If we can't get status, assume it's off for safety
        return "off"


def _ensure_state(connection: str, desired: Literal["on", "off"]) -> Literal["on", "off"]:
    """Ensure VPN ends in desired state, else raise."""
    current = _get_status(connection)
    if current != desired:
        cmd = "connect" if desired == "on" else "disconnect"
        _run_vpn_cmd(cmd, connection)
        final = _get_status(connection)
        if final != desired:
            raise HTTPException(status_code=500, detail=f"Failed to {cmd}. Expected '{desired}', got '{final}'")
        return final
    return current

# --- Scheduler for revert ---
async def _schedule_revert_async(connection: str, target_state: Literal["on", "off"], delay: int):
    """Revert VPN to target state after delay, always checking current state first."""
    try:
        logging.info(f"🕒 Scheduled revert for '{connection}' in {delay} seconds. Task: {asyncio.current_task().get_name()}")
        await asyncio.sleep(delay)
        
        # Always check current state before reverting
        current = _get_status(connection)
        logging.info(f"⏰ Timeout reached for '{connection}'. Performing emergency revert from '{current}' to '{target_state}'")
        
        if current != target_state:
            cmd = "connect" if target_state == "on" else "disconnect"
            _run_vpn_cmd(cmd, connection)
            final = _get_status(connection)
            logging.info(f"✅ Emergency revert for '{connection}' completed: '{current}' -> '{final}'")
            # Log successful revert in format expected by workflow script
            logging.info(f"🔄 VPN REVERT -> HTTP 200, status={final}")
        else:
            logging.info(f"✅ No revert needed for '{connection}' - already in target state '{target_state}'")
            # Log successful revert (no-op) in format expected by workflow script
            logging.info(f"🔄 VPN REVERT -> HTTP 200, status={current}")
    except asyncio.CancelledError:
        logging.info(f"✅ Revert for '{connection}' was cancelled by a manual call. Scheduled task is exiting.")
    except Exception as e:
        logging.error(f"❌ Emergency revert task for '{connection}' failed: {e}")
        # Log failed revert in format expected by workflow script
        logging.error(f"❌ VPN REVERT -> HTTP 500, status=None")
    finally:
        active_vpn_tasks.pop(connection, None)

# --- Endpoints ---
@app.get("/vpn")
async def vpn_status(connection: str = Query(..., description="VPN connection name")):
    # Strip any extra quotes that might have been added by URL encoding or client
    connection = connection.strip("'").strip('"')
    status = _get_status(connection)
    return {"connection": connection, "status": status}

@app.put("/vpn")
async def vpn_control(
    connection: str = Query(..., description="VPN connection name"),
    action: Literal["on", "off", "revert"] = Query(..., description="Desired action"),
    timeout: Optional[int] = Query(None, description="Timeout for auto-revert in seconds")
):
    # Strip any extra quotes that might have been added by URL encoding or client
    connection = connection.strip("'").strip('"')
    
    logging.info(f"VPN control request: connection='{connection}', action='{action}', timeout={timeout}")
    
    # Always get current actual state
    try:
        current = _get_status(connection)
        logging.info(f"Current VPN status for '{connection}': {current}")
    except Exception as e:
        logging.error(f"Failed to get current VPN status: {e}")
        action_log = action.upper()
        logging.error(f"❌ VPN {action_log} -> HTTP 500, status=None")
        raise HTTPException(status_code=500, detail=f"Failed to get VPN status: {str(e)}")
    
    # Handle revert: cancel any scheduled revert
    if action == "revert":
        task = active_vpn_tasks.pop(connection, None)
        if task:
            task.cancel()
            logging.info(f"Cancelled scheduled revert for '{connection}'")
        # Log revert result in format expected by workflow script
        logging.info(f"🔄 VPN REVERT -> HTTP 200, status={current}")
        return {"connection": connection, "status": current, "action": "revert_cancelled"}

    # Handle on/off actions
    desired_state = "on" if action == "on" else "off"
    
    # Cancel any existing revert task for this connection
    existing_task = active_vpn_tasks.pop(connection, None)
    if existing_task:
        existing_task.cancel()
        logging.info(f"Cancelled existing revert task for '{connection}'")
    
    # Check if we need to change state
    if current == desired_state:
        logging.info(f"VPN '{connection}' already in desired state '{desired_state}' - no action needed")
        # Log success in format expected by workflow script
        action_log = "ON" if action == "on" else "OFF"
        logging.info(f"🔄 VPN {action_log} -> HTTP 200, status={current}")
        return {"connection": connection, "status": current, "action": "noop"}
    
    # Store the current state as the revert target BEFORE making any changes
    revert_target = current
    logging.info(f"Need to change VPN '{connection}' from '{current}' to '{desired_state}' (will revert to '{revert_target}')")
    
    # Perform the state change
    try:
        _ensure_state(connection, desired_state)
        new_state = _get_status(connection)  # Verify the change
        logging.info(f"Successfully changed VPN '{connection}' from '{current}' to '{new_state}'")
        
        # Log success in format expected by workflow script
        action_log = "ON" if action == "on" else "OFF"
        logging.info(f"🔄 VPN {action_log} -> HTTP 200, status={new_state}")
        
    except HTTPException as http_ex:
        # Log error in format expected by workflow script
        action_log = "ON" if action == "on" else "OFF"
        logging.error(f"❌ VPN {action_log} -> HTTP {http_ex.status_code}, status=None")
        logging.error(f"HTTPException details: {http_ex.detail}")
        raise
    except Exception as e:
        # Log generic error in format expected by workflow script
        action_log = "ON" if action == "on" else "OFF"
        logging.error(f"❌ VPN {action_log} -> HTTP 500, status=None")
        logging.error(f"Exception details: Failed to change VPN '{connection}' to '{desired_state}': {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Schedule revert if requested
    delay = timeout if timeout is not None else VPN_DEFAULT_TIMEOUT
    if delay and delay > 0:
        revert_task = asyncio.create_task(
            _schedule_revert_async(connection, revert_target, delay), 
            name=f"revert-{connection}-{time.time()}"
        )
        active_vpn_tasks[connection] = revert_task
        return {
            "connection": connection, 
            "status": new_state, 
            "action": action, 
            "will_revert_to": revert_target,
            "will_revert_in": delay
        }
    
    return {"connection": connection, "status": new_state, "action": action, "will_revert_in": None}

# --- Original HAC Endpoints ---

class LoginRequest(BaseModel):
    hac_url: str
    username: str
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    """Login to HAC dynamically with credentials in the JSON body."""
    hac = get_hac_client(request.hac_url, request.username, request.password)
    if hac.login().get("success"):
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
    hac = get_hac_client(request.hac_url, request.username, request.password)
    if not hac.is_authenticated():
        if not hac.login().get("success"):
            raise HTTPException(status_code=401, detail="Login failed before executing Groovy script.")
    result = hac.execute_groovy_script(request.script)
    if result:
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
    hac = get_hac_client(request.hac_url, request.username, request.password)
    if not hac.login().get("success"):  
        raise HTTPException(status_code=401, detail="Login failed before importing ImpEx.")
    result = hac.import_impex(request.script)
    if result and result.get("success"):
        logging.info("✅ ImpEx import completed successfully")
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