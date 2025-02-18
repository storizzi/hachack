import sys
import os
import requests
import urllib3
import argparse

# Suppress SSL warnings (only for local testing)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure the parent directory is in Python's path (for `hac_client.py`)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# HAC API Base URL
HAC_API_URL = "https://localhost:8037"  # Update if using a different port

# Paths to client certificates (mTLS authentication)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Gets the "demos" directory
CLIENT_CERT = os.path.join(BASE_DIR, "../certs/client/client-cert.pem")
CLIENT_KEY = os.path.join(BASE_DIR, "../certs/client/client-key.pem")

# HAC Credentials (Loaded from environment variables or default values)
HAC_URL = os.getenv("HAC_URL", "https://localhost:9002/hac")
USERNAME = os.getenv("HAC_USERNAME", "admin")
PASSWORD = os.getenv("HAC_PASSWORD", "nimda")

# Ensure the `samples/` directory exists
SAMPLES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../samples"))
os.makedirs(SAMPLES_DIR, exist_ok=True)  # Ensure directory exists

# Path to the ImpEx file (absolute path, based on script location)
IMPEX_FILE_PATH = os.path.join(SAMPLES_DIR, "test.impex")

def import_impex_file(retain=False):
    """Tests the import_impex_file API."""
    url = f"{HAC_API_URL}/import_impex_file"

    # Ensure the file exists
    if not os.path.exists(IMPEX_FILE_PATH):
        print(f"❌ File not found: {IMPEX_FILE_PATH}")
        sys.exit(1)

    # Authentication data as form fields (not JSON)
 
    auth_payload = {
        "hac_url": HAC_URL,
        "username": USERNAME,
        "password": PASSWORD,
        "retain": str(retain).lower()  # ✅ Send retain flag as "true" or "false"
    }

    headers = {
        "Accept": "application/json"
    }

    print(f"🚀 Uploading ImpEx file: {IMPEX_FILE_PATH} via API... (retain={retain})")

    try:
        with open(IMPEX_FILE_PATH, "rb") as file:
            files = {
                "file": (os.path.basename(IMPEX_FILE_PATH), file, "application/octet-stream")
            }
            response = requests.post(
                url, files=files, data=auth_payload, cert=(CLIENT_CERT, CLIENT_KEY), verify=False, headers=headers
            )
            response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx

            data = response.json()
            print("\n✅ ImpEx File Import Successful!")
            print(f"📋 Message: {data['impex_result']}")

            if data.get("file_path"):
                print(f"🗂️ Retained file: {data['file_path']}")

    except requests.exceptions.HTTPError as e:
        print(f"❌ ImpEx File Import Failed: {response.status_code} {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ ImpEx File Import Request Failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload an ImpEx file to HAC API")
    parser.add_argument("--retain", action="store_true", help="Retain the ImpEx file on the server")
    args = parser.parse_args()

    import_impex_file(retain=args.retain)
