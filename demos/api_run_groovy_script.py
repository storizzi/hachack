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

# Groovy script to execute
GROOVY_SCRIPT = """
configurationService = spring.getBean('configurationService')
storageConnectionString = configurationService.getConfiguration().getString("example.config.key")
println "Azure Storage Explorer connection string: $storageConnectionString\\n"
return "$storageConnectionString\\n"
"""

def execute_groovy():
    """Executes a Groovy script via the HAC API."""
    url = f"{HAC_API_URL}/execute_groovy"
    
    # Send all parameters in the JSON body
    payload = {
        "hac_url": HAC_URL,
        "username": USERNAME,
        "password": PASSWORD,
        "script": GROOVY_SCRIPT
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🚀 Executing Groovy script via API...")

    try:
        response = requests.post(url, json=payload, cert=(CLIENT_CERT, CLIENT_KEY), verify=False, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
        
        data = response.json()
        print("\n=== Execution Result ===")
        print(data.get("executionResult", "No result"))
        print("\n=== Output Text ===")
        print(data.get("outputText", "No output"))

        if data.get("stacktraceText"):
            print("\n=== Stack Trace ===")
            print(data["stacktraceText"])

    except requests.exceptions.RequestException as e:
        print(f"❌ Groovy script execution failed: {e}")

if __name__ == "__main__":
    execute_groovy()
