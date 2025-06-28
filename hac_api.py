import uvicorn
import argparse
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Query
from pydantic import BaseModel
from datetime import datetime
import subprocess
import asyncio
import time
from typing import Literal, Dict, Optional

from hac_client import HACClient

# --- State Management for Cancellable Tasks ---
# Stores the original state before the last state-changing command
previous_vpn_states: Dict[str, Literal["on", "off"]] = {}
# Stores a reference to the active, cancellable asyncio revert task
active_vpn_tasks: Dict[str, asyncio.Task] = {}


# --- Boilerplate and other functions (no changes) ---

DEFAULT_TIMEOUT = None
load_dotenv()
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

VPN_SCRIPT_PATH = os.getenv("VPN_SCRIPT_PATH", "tunnelblick.zsh")
VPN_DEFAULT_TIMEOUT = int(os.getenv("VPN_TIMEOUT", "60"))

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "HAC_API.log")
log_handler = TimedRotatingFileHandler(log_file, when="W0", interval=1, backupCount=0, encoding="utf-8")
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])

app = FastAPI()

DEFAULT_HAC_URL = os.getenv("HAC_URL", None)
DEFAULT_USERNAME = os.getenv("HAC_USERNAME", None)
DEFAULT_PASSWORD = os.getenv("HAC_PASSWORD", None)

logging.info("🔹 HAC URL Loaded: %s", "Set" if DEFAULT_HAC_URL else "Not Set")
logging.info("🔹 HAC Username Loaded: %s", "Set" if DEFAULT_USERNAME else "Not Set")
logging.info("🔹 HAC Password Loaded: %s", "Set" if DEFAULT_PASSWORD else "Not Set")

def get_hac_client(hac_url: str = None, username: str = None, password: str = None, timeout: int = None ):
    global DEFAULT_TIMEOUT
    hac_url = hac_url or DEFAULT_HAC_URL
    username = username or DEFAULT_USERNAME
    password = password or DEFAULT_PASSWORD
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUT 
    if not hac_url or not username or not password:
        raise HTTPException(status_code=400, detail="HAC credentials must be provided.")
    return HACClient(hac_url, username, password, timeout, debug=True)

# --- All Original Endpoints Preserved ---

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

def _run_vpn_cmd(cmd: str, connection: str) -> str:
    """Invokes the tunnelblick.zsh script. Raises HTTPException on failure."""
    try:
        proc = subprocess.run(
            [VPN_SCRIPT_PATH, cmd, connection],
            capture_output=True, text=True, check=False
        )
        if proc.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"VPN script failed for action '{cmd}' on '{connection}': {proc.stderr.strip()}"
            )
        return proc.stdout.strip()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"VPN script '{VPN_SCRIPT_PATH}' not found. Ensure VPN_SCRIPT_PATH is an absolute path or in the server's PATH."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while running the VPN script: {e}"
        )

def _get_status(connection: str) -> Literal["on", "off"]:
    """Return 'on' or 'off' by parsing the status output."""
    out = _run_vpn_cmd("status", connection).lower()
    return "on" if "connected" in out else "off"

# --- MODIFIED: Replaced _schedule_revert with a cancellable asyncio version ---
async def _schedule_revert_async(connection: str, original: Literal["on", "off"], after: int):
    """Asynchronously waits for `after` seconds, then performs a revert if not cancelled."""
    try:
        logging.info(f"🕒 Scheduled revert for '{connection}' in {after} seconds. Task: {asyncio.current_task().get_name()}")
        await asyncio.sleep(after)

        # If we wake up and weren't cancelled, it means the client crashed/disconnected.
        logging.warning(f"⏰ Timeout reached for '{connection}'. Performing emergency revert.")
        current = _get_status(connection)
        if current != original:
            cmd = "disconnect" if original == "off" else "connect"
            _run_vpn_cmd(cmd, connection)
            logging.info(f"✅ Emergency revert for '{connection}' completed.")

    except asyncio.CancelledError:
        # This is the desired outcome for a clean shutdown by a manual revert call.
        logging.info(f"✅ Revert for '{connection}' was cancelled by a manual call. Scheduled task is exiting.")
    
    except Exception as e:
        logging.error(f"❌ Emergency revert task for '{connection}' failed: {e}")
    
    finally:
        # Clean up the task and state dictionaries regardless of outcome
        active_vpn_tasks.pop(connection, None)
        previous_vpn_states.pop(connection, None)

@app.get("/vpn")
async def vpn_status(connection: str = Query(..., description="Tunnelblick connection name")):
    """Get current VPN status for the given connection."""
    status = _get_status(connection)
    return {"connection": connection, "status": status}

# --- MODIFIED: Final, correct vpn_control endpoint using asyncio ---
@app.put("/vpn")
async def vpn_control(
    connection: str = Query(..., description="Tunnelblick connection name"),
    action: Literal["on", "off", "revert"] = Query(..., description="Desired action"),
    timeout: Optional[int] = Query(None, description="Timeout in seconds for auto-revert"),
):
    """
    Change VPN state. `revert` cancels any pending auto-revert timer.
    `on`/`off` with a timeout will schedule a new cancellable auto-revert timer.
    """
    current = _get_status(connection)
    
    # --- Revert Logic: Cancel any pending task first ---
    if action == "revert":
        pending_task = active_vpn_tasks.pop(connection, None)
        if pending_task:
            pending_task.cancel()
            logging.info(f"Cancelling pending revert task for '{connection}'.")

        original = previous_vpn_states.pop(connection, None)
        if original is None:
            return {"connection": connection, "status": current, "action": "revert_noop", "detail": "No prior state to revert to."}
        
        if current != original:
            cmd = "disconnect" if original == "off" else "connect"
            _run_vpn_cmd(cmd, connection)
        
        return {"connection": connection, "status": original, "action": "reverted"}

    # --- On/Off Logic: Create cancellable tasks ---
    desired_cmd = "connect" if action == "on" else "disconnect"
    desired_state = "on" if action == "on" else "off"

    if current != desired_state:
        # If another task is already running, cancel it before starting a new one.
        pending_task = active_vpn_tasks.pop(connection, None)
        if pending_task:
            logging.warning(f"Cancelling a pre-existing revert task for '{connection}' before starting a new one.")
            pending_task.cancel()
            
        previous_vpn_states[connection] = current
        _run_vpn_cmd(desired_cmd, connection)

        after = timeout if timeout is not None else VPN_DEFAULT_TIMEOUT
        if after and after > 0:
            # Create and store the new cancellable asyncio task
            revert_task = asyncio.create_task(
                _schedule_revert_async(connection, current, after),
                name=f"revert-{connection}-{time.time()}"
            )
            active_vpn_tasks[connection] = revert_task
            return {"connection": connection, "status": desired_state, "action": action, "will_revert_in": after}
        
        return {"connection": connection, "status": desired_state, "action": action, "will_revert_in": None}
    else:
        # If already in the desired state, it's a no-op.
        return {"connection": connection, "status": current, "action": "noop"}

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
    cert_file, key_file, ca_cert = "certs/server/server-cert.pem", "certs/server/server-key.pem", "certs/ca/ca-cert.pem"
    if not all(os.path.exists(p) for p in [cert_file, key_file, ca_cert]):
        logging.error("❌ Missing SSL certificates! Please run `generate_certificates.zsh`.")
        exit(1)
    logging.info("🔹 SSL Certificate: %s (Loaded Successfully)", cert_file)
    logging.info("🔹 SSL Key: %s (Loaded Successfully)", key_file)
    logging.info("🔹 SSL CA Certificate: %s (Loaded Successfully)", ca_cert)
    uvicorn.run("hac_api:app", host="0.0.0.0", port=args.port, ssl_certfile=cert_file, ssl_keyfile=key_file, ssl_ca_certs=ca_cert, reload=True)