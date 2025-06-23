import uvicorn
import argparse
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks, Query
from pydantic import BaseModel
from datetime import datetime
import subprocess
import time
from typing import Literal, Dict

from hac_client import HACClient

DEFAULT_TIMEOUT = None

# Load environment variables from .env file (if exists)
load_dotenv()

env_timeout = os.getenv("HAC_TIMEOUT")
if env_timeout is not None:
    try:
        DEFAULT_TIMEOUT = int(env_timeout)  # Convert string to int
    except ValueError:
        print(f"⚠️ Invalid HAC_TIMEOUT value: {env_timeout}, using default 30s")
        DEFAULT_TIMEOUT = None
else:
    DEFAULT_TIMEOUT = None  # Default to 30 if not set

IMPEX_DIR = "impex"
os.makedirs(IMPEX_DIR, exist_ok=True) 

# Set up Tunnelblick VPN script path and timeout

VPN_SCRIPT_PATH = os.getenv("VPN_SCRIPT_PATH", "tunnelblick.zsh")
VPN_DEFAULT_TIMEOUT = int(os.getenv("VPN_TIMEOUT", "60"))  # seconds

# Stores the original state before we last changed it
# e.g. { "WorkVPN": "on", "ClientVPN": "off" }
previous_vpn_states: Dict[str, Literal["on", "off"]] = {}

# Set up logging directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logging (rotates weekly)
log_file = os.path.join(LOG_DIR, "HAC_API.log")
log_handler = TimedRotatingFileHandler(log_file, when="W0", interval=1, backupCount=0, encoding="utf-8")
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])

app = FastAPI()

# Default HAC credentials (can be overridden per request)
DEFAULT_HAC_URL = os.getenv("HAC_URL", None)
DEFAULT_USERNAME = os.getenv("HAC_USERNAME", None)
DEFAULT_PASSWORD = os.getenv("HAC_PASSWORD", None)

# Log whether credentials have been set (without exposing values)
logging.info("🔹 HAC URL Loaded: %s", "Set" if DEFAULT_HAC_URL else "Not Set")
logging.info("🔹 HAC Username Loaded: %s", "Set" if DEFAULT_USERNAME else "Not Set")
logging.info("🔹 HAC Password Loaded: %s", "Set" if DEFAULT_PASSWORD else "Not Set")

# Secure endpoint - use defaults if not provided
def get_hac_client(hac_url: str = None, username: str = None, password: str = None, timeout: int = None ):
    global DEFAULT_TIMEOUT
    """Initialize HACClient dynamically per request, using default values if not provided."""
    hac_url = hac_url or DEFAULT_HAC_URL
    username = username or DEFAULT_USERNAME
    password = password or DEFAULT_PASSWORD
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUT 

    if not hac_url or not username or not password:
        raise HTTPException(status_code=400, detail="HAC credentials must be provided.")
    
    return HACClient(hac_url, username, password, timeout, debug=True)

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

    # Ensure authentication
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
    
    # Always create a fresh HAC client
    hac = get_hac_client(request.hac_url, request.username, request.password)
    # Explicitly log in before executing the import
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
    retain: bool = Form(False)  # ✅ Option to retain the file (defaults to False)
):
    """Upload and import an ImpEx file dynamically, ensuring authentication first."""

    # Always create a fresh HAC client
    hac = get_hac_client(hac_url, username, password)

    # Explicitly log in before executing the import
    if not hac.login().get("success"):  
        raise HTTPException(status_code=401, detail="Login failed before importing ImpEx file.")

    # Generate timestamp for unique file naming
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # ✅ Use _ instead of :
    original_filename, ext = os.path.splitext(file.filename)
    new_filename = f"{original_filename}_{timestamp}{ext}"  # ✅ Append timestamp before extension
    file_path = os.path.join(IMPEX_DIR, new_filename)

    # Save file to `impex/` directory
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Execute the import
    result = hac.import_impex_file(file_path)

    # Remove file unless retain flag is set
    if not retain:
        os.remove(file_path)
    else:
        logging.info(f"🗂️ Retained ImpEx file: {file_path}")

    # Return result
    if result and result.get("success"):
        logging.info(f"✅ ImpEx file '{new_filename}' imported successfully")
        return {"success": True, "impex_result": result["impex_result"], "file_path": file_path if retain else None}

    logging.warning(f"❌ ImpEx file '{new_filename}' import failed")
    return {"success": False, "impex_result": "Import failed", "impex_details": result.get("impex_details", "Unknown error")}

def _run_vpn_cmd(cmd: str, connection: str) -> str:
    """
    Invoke the tunnelblick.zsh script. 
    cmd: one of "connect", "disconnect", "status".
    Returns stdout on success; raises HTTPException on failure.
    """
    proc = subprocess.run(
        [VPN_SCRIPT_PATH, cmd, connection],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        # include stderr for diagnostics
        raise HTTPException(
            status_code=500,
            detail=f"VPN `{cmd}` failed for '{connection}': {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _get_status(connection: str) -> Literal["on", "off"]:
    """Return 'on' or 'off' by parsing the status output."""
    out = _run_vpn_cmd("status", connection).lower()
    # adjust parsing to your script’s actual output...
    if "connected" in out:
        return "on"
    return "off"


def _schedule_revert(connection: str, original: Literal["on","off"], after: int):
    """
    Sleeps for `after` seconds, then, if the connection is not in the
    original state, issues the opposite command to revert.
    Finally, cleans up the stored state.
    """
    time.sleep(after)
    try:
        current = _get_status(connection)
        if current != original:
            cmd = "disconnect" if original == "off" else "connect"
            _run_vpn_cmd(cmd, connection)
    finally:
        previous_vpn_states.pop(connection, None)

@app.get("/vpn")
async def vpn_status(
    connection: str = Query(..., description="Tunnelblick connection name")
):
    """
    Get current VPN status for the given connection.
    """
    status = _get_status(connection)
    return {"connection": connection, "status": status}


@app.put("/vpn")
async def vpn_control(
    background_tasks: BackgroundTasks,
    connection: str = Query(..., description="Tunnelblick connection name"),
    action: Literal["on", "off", "revert"] = Query(
        ..., description="Desired action: on, off, or revert"
    ),
    timeout: int = Query(
        None, description="Timeout in seconds after which to auto-revert"
    ),
):
    """
    Change VPN state. Supported actions:
      - on      : connect if not already connected
      - off     : disconnect if not already disconnected
      - revert  : return to the state before our last change

    If action is on/off and timeout is set (or defaults), schedules an
    automatic revert after that many seconds.
    """
    current = _get_status(connection)

    if action == "revert":
        # No previous state ⇒ invalid
        if connection not in previous_vpn_states:
            raise HTTPException(
                status_code=409,
                detail=f"No stored state for '{connection}'; cannot revert"
            )
        original = previous_vpn_states.pop(connection)
        if current != original:
            cmd = "disconnect" if original == "off" else "connect"
            _run_vpn_cmd(cmd, connection)
        return {"connection": connection, "status": original, "action": "reverted"}

    # for on/off, map to script commands
    desired_cmd = "connect" if action == "on" else "disconnect"
    desired_state = "on" if action == "on" else "off"

    # store previous only if state will actually change
    if current != desired_state:
        previous_vpn_states[connection] = current
        _run_vpn_cmd(desired_cmd, connection)
    else:
        # no-op if already in desired state
        return {"connection": connection, "status": current, "action": "noop"}

    # schedule auto-revert if requested
    after = timeout if timeout is not None else VPN_DEFAULT_TIMEOUT
    if after:
        background_tasks.add_task(_schedule_revert, connection, current, after)

    return {
        "connection": connection,
        "status": desired_state,
        "action": action,
        "will_revert_in": after
    }

@app.get("/")
async def root():
    """Test endpoint to verify authentication."""
    return {"message": "Hello, authenticated client!"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start FastAPI with optional port parameter.")
    parser.add_argument("--port", type=int, default=8037, help="Port number to run the server on (default: 8037)")
    parser.add_argument("--timeout", type=int, help="Request timeout in seconds (default: 30s or environment variable)")

    args = parser.parse_args()
    
    if args.timeout is not None:
        globals()["DEFAULT_TIMEOUT"] = args.timeout  # ✅ Now it updates correctly!

    logging.info("✅ Starting HAC API on port %d with timeout: %s seconds", args.port, DEFAULT_TIMEOUT or "Client Default")

    # Check if certificates exist before starting
    cert_file = "certs/server/server-cert.pem"
    key_file = "certs/server/server-key.pem"
    ca_cert = "certs/ca/ca-cert.pem"

    if not os.path.exists(cert_file) or not os.path.exists(key_file) or not os.path.exists(ca_cert):
        logging.error("❌ Missing SSL certificates! Please run `generate_certificates.zsh`.")
        exit(1)

    logging.info("🔹 SSL Certificate: %s (Loaded Successfully)", cert_file)
    logging.info("🔹 SSL Key: %s (Loaded Successfully)", key_file)
    logging.info("🔹 SSL CA Certificate: %s (Loaded Successfully)", ca_cert)

    uvicorn.run(
        "hac_api:app",
        host="0.0.0.0",
        port=args.port,
        ssl_certfile=cert_file,
        ssl_keyfile=key_file,
        ssl_ca_certs=ca_cert,
        reload=True
    )
