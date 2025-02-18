import sys
import os
import requests
import urllib3

# Suppress SSL warnings (only for local testing)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def test_login():
    """Tests the login API."""
    url = f"{HAC_API_URL}/login"

    payload = {
        "hac_url": HAC_URL,
        "username": USERNAME,
        "password": PASSWORD
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"🔄 Attempting login to {HAC_API_URL}...")

    try:
        response = requests.post(url, json=payload, cert=(CLIENT_CERT, CLIENT_KEY), verify=False, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx

        data = response.json()
        print("✅ Successfully logged in to HAC API.")
        print("\n=== API Response ===")
        print(data)
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ Login failed: {response.status_code} {response.text}")
        sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_login()
