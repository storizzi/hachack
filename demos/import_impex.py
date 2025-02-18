import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hac_client import HACClient

# Define HAC instance details
HAC_URL = "https://backgroundprocessing.c2fvm37cl7-wilkoreta1-s1-public.model-t.cc.commerce.ondemand.com/hac"
USERNAME = "admin"
PASSWORD = "nimda"

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

# Define catalog and version variables
$catalog = wilkoProductCatalog
$catalogVersion = catalogVersion(CatalogVersion.catalog(Catalog.id[default = $catalog]), CatalogVersion.version[default = Staged])[default = $catalog:Staged]
# Insert ProductToAutoSync data
INSERT_UPDATE ProductToAutoSync ; product(code, $catalogVersion)[unique = true] ; state(code)[default = CREATED]
; P0697357
; P0697358
; P0697380
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
