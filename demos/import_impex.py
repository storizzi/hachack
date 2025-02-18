import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hac_client import HACClient

# Define HAC instance details
HAC_URL = "http://localhost:9002/hac"
USERNAME = "admin"
PASSWORD = "nimda"

# Sample ImpEx script
IMPEX_SCRIPT = """
$catalog = myProductCatalog
$catalogVersion = catalogVersion(CatalogVersion.catalog(Catalog.id[default=$catalog]), CatalogVersion.version[default=Staged])[default=$catalog:Staged]
$lang = en

INSERT_UPDATE Product; code[unique=true]; name[$lang]; description[$lang]; $catalogVersion[unique=true]; ean[allownull=true]; brand
; 100001 ; Super Widget  ; The latest version of our premium widget. ; ; 1234567890123 ; Acme
; 100002 ; Budget Widget ; A basic widget at an affordable price.     ; ; 9876543210987 ; BestCo
"""

# Create HACClient instance with debug mode ON
hac = HACClient(HAC_URL, USERNAME, PASSWORD, debug=True)

# Login
if hac.login().get("success"):
    print("✅ Successfully logged in. Ready to execute commands.")
    
    # Execute ImpEx import
    result = hac.import_impex(IMPEX_SCRIPT)

    if result["success"]:
        print(f"\n✅ ImpEx Import Successful! Message: {result['impex_result']}")
    else:
        print(f"\n❌ ImpEx Import Failed. Message: {result['impex_result']}")
        print(f"\n📄 Error Details: {result['impex_details']}")

else:
    print("❌ Failed to log in. Cannot execute HAC commands.")

# Turn off debug mode
hac.set_debug(False)
