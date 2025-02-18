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
HAC_URL = os.getenv("HAC_URL", "https://backgroundprocessing.c2fvm37cl7-wilkoreta1-s1-public.model-t.cc.commerce.ondemand.com/hac")
USERNAME = os.getenv("HAC_USERNAME", "admin")
PASSWORD = os.getenv("HAC_PASSWORD", "nimda")

# Sample ImpEx script
IMPEX_SCRIPT = """
# Define variables for catalog, catalogVersion, and brand
$catalog = wilkoProductCatalog
$catalogVersion = catalogVersion(CatalogVersion.catalog(Catalog.id[default = $catalog]), CatalogVersion.version[default = Staged])[default = $catalog:Staged]
$brand = brand(uid)[default = homebase]

# Define language variable
$lang = en

# Insert ProductBrandOverride data with defaults for $catalogVersion and $brand
INSERT_UPDATE ProductBrandOverride ; $catalogVersion[unique = true] ; $brand ; product(code, $catalogVersion)[unique = true] ; desc[lang = $lang]
; ; ; P0697357 ; "<p>This Posture Corrector provides gentle back and clavicle support for improved posture and reduced strain. Designed for a comfortable fit under clothing, it&#x27;s perfect for everyday wear at work, home, or on the go. Easily adjustable to your needs, it helps you develop better posture habits and alleviate pain and discomfort. Suitable for both men and women.</p>"
; ; ; P0697358 ; "<p>Enjoy all-day comfort and improved posture with this generously sized posture corrector. Its design provides excellent clavicle and back support for a secure, comfortable fit, making it ideal for discreet wear under clothing. Perfect for reducing tension and promoting better alignment, whether you&#x27;re sitting at your desk or on the go, this corrector helps you move with greater ease and confidence.</p>"
; ; ; P0697380 ; "<p>The Instant VersaZone Dual Air Fryer is a kitchen essential, perfect for families. Its 8.5L capacity and two independent cooking zones mean you can prepare delicious, crispy meals for everyone, quickly and efficiently. Enjoy healthier cooking with less oil, while saving time and energy thanks to fast, even heat distribution. Easy to use and clean, it&#x27;s a true kitchen MVP.</p>"
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
