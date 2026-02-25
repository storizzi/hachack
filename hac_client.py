import os
import requests
from bs4 import BeautifulSoup
import re
import json

class DebugConfig:
    """Granular debug configuration for HAC operations."""
    
    def __init__(self, debug=False):
        # Backward compatibility: if debug=True, enable all debug flags
        if debug:
            self.debug_incoming_request = True
            self.debug_outgoing_request = True
            self.debug_incoming_data = True
            self.debug_outgoing_data = True
        else:
            # Read from environment variables, defaulting to False
            self.debug_incoming_request = self._get_bool_env("DEBUG_INCOMING_REQUEST", False)
            self.debug_outgoing_request = self._get_bool_env("DEBUG_OUTGOING_REQUEST", False)
            self.debug_incoming_data = self._get_bool_env("DEBUG_INCOMING_DATA", False)
            self.debug_outgoing_data = self._get_bool_env("DEBUG_OUTGOING_DATA", False)
    
    def _get_bool_env(self, env_var, default=False):
        """Helper to get boolean value from environment variable."""
        value = os.getenv(env_var, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def set_debug(self, debug):
        """Enable or disable all debug settings (backward compatibility)."""
        if debug:
            self.debug_incoming_request = True
            self.debug_outgoing_request = True
            self.debug_incoming_data = True
            self.debug_outgoing_data = True
        else:
            self.debug_incoming_request = False
            self.debug_outgoing_request = False
            self.debug_incoming_data = False
            self.debug_outgoing_data = False
    
    def log_incoming_request(self, message):
        """Log incoming API requests."""
        if self.debug_incoming_request:
            print(f"[INCOMING_REQUEST] {message}")
    
    def log_outgoing_request(self, message):
        """Log outgoing requests to HAC."""
        if self.debug_outgoing_request:
            print(f"[OUTGOING_REQUEST] {message}")
    
    def log_incoming_data(self, message):
        """Log incoming data/responses."""
        if self.debug_incoming_data:
            print(f"[INCOMING_DATA] {message}")
    
    def log_outgoing_data(self, message):
        """Log outgoing data/payloads."""
        if self.debug_outgoing_data:
            print(f"[OUTGOING_DATA] {message}")

class HACClient:
    """
    A client for interacting with the SAP Hybris HAC (Hybris Administration Console).
    Maintains a session for executing multiple commands without re-authenticating.
    """

    def __init__(self, hac_url, username, password, timeout=60, debug=False):
        self.hac_url = hac_url.rstrip("/")  # Ensure no trailing slash
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        self.jsessionid = None
        self.authenticated = False  # Track login status
        self.timeout = timeout  # Request timeout in seconds
        self.debug_config = DebugConfig(debug)  # Granular debug configuration

    def set_debug(self, debug):
        """Enable or disable debug mode (backward compatibility)."""
        self.debug_config.set_debug(debug)

    def _log(self, message):
        """Prints a debug message if debugging is enabled (backward compatibility)."""
        # For backward compatibility, log to all categories if any debug is enabled
        if any([self.debug_config.debug_incoming_request, 
                self.debug_config.debug_outgoing_request,
                self.debug_config.debug_incoming_data, 
                self.debug_config.debug_outgoing_data]):
            print(f"[DEBUG] {message}")

    def login(self):
        """Logs in to HAC and retrieves session cookies & CSRF token. Always returns a dictionary."""
        try:
            self._log("🔄 Attempting to log in to HAC...")
            self.debug_config.log_outgoing_request(f"GET {self.hac_url}/login")

            # Step 1: Get initial CSRF token
            login_page_url = f"{self.hac_url}/login"
            response = self.session.get(login_page_url, timeout=self.timeout)
            
            self.debug_config.log_incoming_request(f"Response status: {response.status_code}")
            self.debug_config.log_incoming_data(f"Response headers: {dict(response.headers)}")

            # ✅ Check for 403 Forbidden (VPN/Downtime Issue)
            if response.status_code == 403:
                soup = BeautifulSoup(response.text, "html.parser")
                headline = soup.find("h1", class_="headline")  # Find the error message

                error_message = re.sub(r"\s+", " ", headline.get_text(separator=" ").strip()) if headline else "403 Forbidden: Access Denied"
                self._log(f"❌ Access Denied: {error_message}")
                return {"success": False, "error": error_message}

            # ✅ If no maintenance issue, proceed with login
            soup = BeautifulSoup(response.text, "html.parser")
            csrf_token_input = soup.find("meta", {"name": "_csrf"})
            if not csrf_token_input:
                self._log("❌ Failed to retrieve CSRF token from login page.")
                return {"success": False, "error": "CSRF token not found"}

            self.csrf_token = csrf_token_input["content"]
            self._log(f"🔑 CSRF Token retrieved before login: {self.csrf_token}")

            # Step 2: Perform login
            login_payload = {
                "j_username": self.username,
                "j_password": self.password,
                "_csrf": self.csrf_token
            }
            self.debug_config.log_outgoing_data(f"Login payload: {{'j_username': '{self.username}', 'j_password': '[REDACTED]', '_csrf': '{self.csrf_token}'}}")
            
            login_url = f"{self.hac_url}/j_spring_security_check"
            self.debug_config.log_outgoing_request(f"POST {login_url}")
            response = self.session.post(login_url, data=login_payload, timeout=self.timeout)
            
            self.debug_config.log_incoming_request(f"Response status: {response.status_code}")
            self.debug_config.log_incoming_data(f"Response headers: {dict(response.headers)}")

            # Validate login success
            if "Login failed" in response.text or response.status_code not in [200, 302]:
                self._log("❌ Login failed. Check credentials.")
                self.authenticated = False
                return {"success": False, "error": "Invalid credentials"}

            self.jsessionid = self.session.cookies.get("JSESSIONID")
            self.authenticated = True  # Mark as logged in
            self._log(f"✅ Login successful. JSESSIONID: {self.jsessionid}")

            # Step 3: Get new CSRF token for authenticated actions
            self.refresh_csrf_token()

            return {"success": True, "message": "Login successful", "JSESSIONID": self.jsessionid}

        except Exception as e:
            self._log(f"❌ Error during login: {e}")
            self.authenticated = False
            return {"success": False, "error": str(e)}


    def is_authenticated(self):
        """Returns True if the client is logged in, False otherwise."""
        return self.authenticated

    def refresh_csrf_token(self):
        """Retrieves a fresh CSRF token after login for executing commands."""
        try:
            scripting_url = f"{self.hac_url}/console/scripting"
            self.debug_config.log_outgoing_request(f"GET {scripting_url}")
            response = self.session.get(scripting_url, timeout=self.timeout)
            
            self.debug_config.log_incoming_request(f"Response status: {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")
            csrf_token_input = soup.find("meta", {"name": "_csrf"})
            if not csrf_token_input:
                self._log("❌ Failed to retrieve CSRF token from scripting page.")
                return False

            self.csrf_token = csrf_token_input["content"]
            self._log(f"🔑 New CSRF Token retrieved after login: {self.csrf_token}")
            return True
        except Exception as e:
            self._log(f"❌ Error retrieving CSRF token: {e}")
            return False

    def execute_groovy_script(self, script, commit=False):
        """Executes a Groovy script in HAC and returns the output."""
        if not self.is_authenticated():
            print("❌ Cannot execute script. User is not authenticated. Call login() first.")
            return None

        try:
            self._log("🛠️ Sending Groovy script for execution...")

            groovy_headers = {
                "X-CSRF-TOKEN": self.csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.hac_url}/console/scripting",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "application/json"
            }

            groovy_payload = {
                "script": script,
                "scriptType": "groovy",
                "commit": str(commit).lower(),  # Ensures commit is "true" or "false"
                "_csrf": self.csrf_token
            }

            groovy_execute_url = f"{self.hac_url}/console/scripting/execute"
            self.debug_config.log_outgoing_request(f"POST {groovy_execute_url}")
            self.debug_config.log_outgoing_data(f"Groovy payload: {{'script': '[SCRIPT_CONTENT]', 'scriptType': 'groovy', 'commit': '{commit}', '_csrf': '{self.csrf_token}'}}")
            response = self.session.post(groovy_execute_url, data=groovy_payload, headers=groovy_headers, timeout=self.timeout)
            
            self.debug_config.log_incoming_request(f"Response status: {response.status_code}")
            self.debug_config.log_incoming_data(f"Response headers: {dict(response.headers)}")

            # Parse JSON response
            json_response = response.json()
            if json_response.get("stacktraceText"):
                self._log("❌ Groovy script execution failed with errors!")
                return {
                    "executionResult": None,
                    "outputText": None,
                    "stacktraceText": json_response["stacktraceText"]
                }
            else:
                self._log("✅ Groovy script executed successfully!")
                self.debug_config.log_incoming_data(f"Execution result: {json_response.get('executionResult', 'No result')}")
                return {
                    "executionResult": json_response.get("executionResult", "No result"),
                    "outputText": json_response.get("outputText", "No output"),
                    "stacktraceText": ""
                }
        except json.JSONDecodeError:
            self._log("❌ Failed to parse response. Raw output:")
            self._log(response.text)
            return None
        except Exception as e:
            self._log(f"❌ Error executing Groovy script: {e}")
            return None

    def _process_impex_response(self, response_text):
        """Parses the HAC response and extracts import result messages."""
        soup = BeautifulSoup(response_text, "html.parser")

        # Extract main import result
        impex_result_tag = soup.find("span", {"id": "impexResult"})
        impex_result = impex_result_tag.get("data-result", "Unknown result") if impex_result_tag else "Unknown result"
        impex_level = impex_result_tag.get("data-level", "notice") if impex_result_tag else "unknown"

        # Extract detailed error message if available
        impex_details = ""
        error_box = soup.find("div", class_="box impexResult quiet")
        if error_box:
            pre_tag = error_box.find("pre")
            if pre_tag:
                impex_details = pre_tag.get_text(strip=True)

        self._log(f"📋 ImpEx Result: {impex_result}")
        self._log(f"📄 ImpEx Details: {impex_details}")

        return {
            "success": impex_level.lower() != "error",
            "impex_result": impex_result,
            "impex_details": impex_details
        }

    def import_impex(self, impex_script, validation="IMPORT_STRICT", max_threads=16, encoding="UTF-8"):
        """Imports an ImpEx script via HAC and extracts the import result message & details."""
        if not self.is_authenticated():
            print("❌ Cannot import ImpEx. User is not authenticated. Call login() first.")
            return None

        try:
            self._log("🛠️ Sending ImpEx script for import...")

            impex_headers = {
                "X-CSRF-TOKEN": self.csrf_token,
                "Referer": f"{self.hac_url}/console/impex/import",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }

            impex_payload = {
                "scriptContent": impex_script,
                "validationEnum": validation,
                "maxThreads": str(max_threads),
                "encoding": encoding,
                "_csrf": self.csrf_token
            }

            impex_url = f"{self.hac_url}/console/impex/import"
            self.debug_config.log_outgoing_request(f"POST {impex_url}")
            self.debug_config.log_outgoing_data(f"ImpEx payload: {{'scriptContent': '[IMPEX_SCRIPT]', 'validationEnum': '{validation}', 'maxThreads': '{max_threads}', 'encoding': '{encoding}', '_csrf': '{self.csrf_token}'}}")
            response = self.session.post(impex_url, data=impex_payload, headers=impex_headers, timeout=self.timeout)
            
            self.debug_config.log_incoming_request(f"Response status: {response.status_code}")
            self.debug_config.log_incoming_data(f"Response headers: {dict(response.headers)}")

            return self._process_impex_response(response.text)

        except Exception as e:
            self._log(f"❌ Error executing ImpEx import: {e}")
            return {"success": False, "impex_result": "Import failed due to an error.", "impex_details": str(e)}

    def import_impex_file(self, file_path, validation="IMPORT_STRICT", max_threads=16, encoding="UTF-8"):
        """Uploads and imports an ImpEx file via HAC, returning the import status and details."""
 
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        if not self.is_authenticated():
            print("❌ Cannot import ImpEx file. User is not authenticated. Call login() first.")
            return None

        try:
            self._log(f"📤 Uploading ImpEx file: {file_path}")

            impex_headers = {
                "X-CSRF-TOKEN": self.csrf_token,
                "Referer": f"{self.hac_url}/console/impex/import"
            }

            with open(file_path, "rb") as impex_file:
                impex_payload = {
                    "file": (os.path.basename(file_path), impex_file, "application/octet-stream"),
                    "encoding": (None, encoding),
                    "maxThreads": (None, str(max_threads)),
                    "validationEnum": (None, validation),
                    "_csrf": (None, self.csrf_token),
                }

                impex_url = f"{self.hac_url}/console/impex/import/upload"
                self.debug_config.log_outgoing_request(f"POST {impex_url}")
                self.debug_config.log_outgoing_data(f"ImpEx file payload: {{'file': '{os.path.basename(file_path)}', 'encoding': '{encoding}', 'maxThreads': '{max_threads}', 'validationEnum': '{validation}', '_csrf': '{self.csrf_token}'}}")
                response = self.session.post(impex_url, files=impex_payload, headers=impex_headers, timeout=self.timeout)
                
                self.debug_config.log_incoming_request(f"Response status: {response.status_code}")
                self.debug_config.log_incoming_data(f"Response headers: {dict(response.headers)}")

            return self._process_impex_response(response.text)

        except Exception as e:
            self._log(f"❌ Error executing ImpEx file upload: {e}")
            return {"success": False, "impex_result": "Import failed due to an error.", "impex_details": str(e)}

if __name__ == "__main__":
    # Example usage test when running the script directly
    hac_url = input("Enter HAC URL: ")
    username = input("Enter Username: ")
    password = input("Enter Password: ")

    hac = HACClient(hac_url, username, password, debug=True)

    if hac.login().get("success"):
        print("✅ Successfully logged into HAC!")
    else:
        print("❌ Login failed. Please check your credentials.")
