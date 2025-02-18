import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hac_client import HACClient

# Define HAC instance details
HAC_URL = "http://localhost:9002/hac"
USERNAME = "admin"
PASSWORD = "nimda"

# Groovy script to execute
GROOVY_SCRIPT = """
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
    
    # Execute Groovy script
    result = hac.execute_groovy_script(GROOVY_SCRIPT)

    # Display result
    if result:
        print("\n=== Execution Result ===")
        print(result.get("executionResult", "No result"))
        print("\n=== Output Text ===")
        print(result.get("outputText", "No output"))
        
        # If there's a stack trace, display it
        if result.get("stacktraceText"):
            print("\n=== Stack Trace ===")
            print(result["stacktraceText"])
else:
    print("❌ Failed to log in. Cannot execute HAC commands.")

# Turn off debug mode and try again
hac.set_debug(False)
