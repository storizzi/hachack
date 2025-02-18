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
HAC_URL = os.getenv("HAC_URL", "http://localhost:9002/hac")
USERNAME = os.getenv("HAC_USERNAME", "admin")
PASSWORD = os.getenv("HAC_PASSWORD", "nimda")

# Sample ImpEx script
IMPEX_SCRIPT = """
$catalog = myProductCatalog
$catalogVersion = catalogVersion(CatalogVersion.catalog(Catalog.id[default=$catalog]), CatalogVersion.version[default=Staged])[default=$catalog:Staged]
$lang = en

INSERT_UPDATE Product; code[unique=true]; name[$lang]; description[$lang]; $catalogVersion[unique=true]; ean[allownull=true]; brand
; 100001 ; Super Widget  ; The latest version of our premium widget. ; ; 1234567890123 ; Acme
; 100002 ; Budget Widget ; A basic widget at an affordable price.     ; ; 9876543210987 ; BestCo
"""

def import_impex():
    """Tests the import_impex API."""
    url = f"{HAC_API_URL}/import_impex"

    payload = {
        "hac_url": HAC_URL,
        "username": USERNAME,
        "password": PASSWORD,
        "script": IMPEX_SCRIPT
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🚀 Importing ImpEx script via API...")

    try:
        response = requests.post(url, json=payload, cert=(CLIENT_CERT, CLIENT_KEY), verify=False, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx

        data = response.json()
        print("\n✅ ImpEx Import Successful!")
        print(f"📋 Message: {data['impex_result']}")
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ ImpEx Import Failed: {response.status_code} {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ ImpEx Import Request Failed: {e}")

if __name__ == "__main__":
    import_impex()
