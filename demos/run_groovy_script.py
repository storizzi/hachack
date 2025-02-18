import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hac_client import HACClient

# Define HAC instance details
HAC_URL = "https://backgroundprocessing.c2fvm37cl7-wilkoreta1-s1-public.model-t.cc.commerce.ondemand.com/hac"
USERNAME = "admin"
PASSWORD = "nimda"

# Groovy script to execute
GROOVY_SCRIPT = """
configurationService = spring.getBean('configurationService')
storageConnectionString = configurationService.getConfiguration().getString("azure.hotfolder.storage.account.connection-string")
println "Azure Storage Explorer connection string: $storageConnectionString\\n"
return "$storageConnectionString\\n"
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
