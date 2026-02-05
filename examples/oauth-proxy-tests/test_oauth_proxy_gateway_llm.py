#!/usr/bin/env python3
"""
OAuth Proxy Gateway Mode Test for LLM Proxy
Tests OAuth Proxy functionality with Gateway mode on an LLM proxy.

This script tests:
1. Dynamic Client Registration (DCR)
2. OAuth 2.1 Authorization Flow with PKCE
3. Token Exchange
4. Using OAuth tokens to access the proxy
5. API Key authentication (should still work when OAuth Proxy is enabled)
6. Making actual LLM requests through the proxy

Prerequisites:
- Gateway running on http://localhost:8080
- LLM Proxy configured with OAuth Proxy Gateway mode enabled
- OAuth Provider configured
- API Key generated (optional, for testing API key auth)

Usage:
    python3 test_oauth_proxy_gateway_llm.py --target <proxy_url> --proxy-id <id> [options]

    Required arguments:
        --target <url>      Target proxy URL (e.g., http://localhost:8093)
        --proxy-id <id>     Proxy ID for OAuth Proxy API endpoints

    Optional arguments:
        --gateway <url>     Gateway API URL (default: http://localhost:8080)
        --api-key <key>     Gateway API key for testing API key authentication
        -h, --help          Show this help message
"""

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any
from urllib.error import HTTPError

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def make_request(method: str, url: str, headers: Optional[Dict[str, str]] = None, 
                 data: Optional[bytes] = None) -> tuple[Dict[str, Any], int]:
    """Make HTTP request and return response as JSON and status code"""
    req = urllib.request.Request(url, data=data, headers=headers or {})
    req.get_method = lambda: method
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            try:
                return json.loads(body), status
            except json.JSONDecodeError:
                return {"raw": body}, status
    except HTTPError as e:
        status = e.code
        body = e.read().decode('utf-8')
        try:
            return json.loads(body), status
        except json.JSONDecodeError:
            return {"error": body}, status

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    received_code = None
    received_state = None
    
    def do_GET(self):
        """Handle GET request for OAuth callback"""
        # Parse query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Extract code and state
        code = query_params.get('code', [None])[0]
        state = query_params.get('state', [None])[0]
        error = query_params.get('error', [None])[0]
        
        if error:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>OAuth Error</h1>
                <p>Error: {error}</p>
                <p>Description: {query_params.get('error_description', [''])[0]}</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            CallbackHandler.received_code = None
            return
        
        if code:
            # Store the code
            CallbackHandler.received_code = code
            CallbackHandler.received_state = state
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>OAuth Success</title></head>
            <body>
                <h1>✅ Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>setTimeout(() => window.close(), 2000);</script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>❌ Authorization Failed</h1>
                <p>No authorization code received.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def start_callback_server(port: int = 8888) -> HTTPServer:
    """Start a local HTTP server to handle OAuth callback"""
    server = HTTPServer(('localhost', port), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def wait_for_callback(timeout: int = 300) -> Optional[tuple[str, str]]:
    """Wait for OAuth callback with timeout (default 5 minutes)"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if CallbackHandler.received_code:
            return CallbackHandler.received_code, CallbackHandler.received_state
        time.sleep(0.5)
    return None

def generate_pkce() -> tuple[str, str, str]:
    """Generate PKCE verifier, challenge, and method"""
    # Generate code verifier (43-128 characters, base64url)
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Generate code challenge (S256 method)
    challenge_bytes = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    
    return verifier, challenge, "S256"

def test_dcr(gateway_url: str, proxy_id: int, scope: str = "") -> Optional[Dict[str, Any]]:
    """Test 1: Dynamic Client Registration"""
    print_header("Test 1: Dynamic Client Registration (DCR)")
    
    redirect_uris = ["http://localhost:8888/callback", "cursor://oauth-callback"]
    
    payload = {
        "redirect_uris": redirect_uris,
        "client_name": "Test Client",
        "token_endpoint_auth_method": "client_secret_post",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"]
    }
    
    # Only include scope if provided
    if scope:
        payload["scope"] = scope
    
    url = f"{gateway_url.rstrip('/')}/api/v1/oauth-proxy/{proxy_id}/register"
    headers = {"Content-Type": "application/json"}
    
    print_info(f"Registering client with redirect URIs: {redirect_uris}")
    response, status = make_request("POST", url, headers, json.dumps(payload).encode())
    
    if status == 200 or status == 201:
        print_success(f"Client registered successfully")
        print_info(f"Client ID: {response.get('client_id', 'N/A')}")
        print_info(f"Client Secret: {response.get('client_secret', 'N/A')[:20]}...")
        return response
    else:
        print_error(f"Client registration failed: {status}")
        print_error(f"Response: {json.dumps(response, indent=2)}")
        return None

def test_authorization(gateway_url: str, proxy_id: int, client_id: str, code_challenge: str, code_challenge_method: str, scope: str = "") -> Optional[str]:
    """Test 2: Initiate Authorization Flow"""
    print_header("Test 2: OAuth Authorization Flow")
    
    redirect_uri = "http://localhost:8888/callback"
    state = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode('utf-8').rstrip('=')
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method
    }
    
    # Only include scope if provided
    if scope:
        params["scope"] = scope
    
    url = f"{gateway_url.rstrip('/')}/api/v1/oauth-proxy/{proxy_id}/authorize?" + urllib.parse.urlencode(params)
    
    print_info("Initiating authorization flow...")
    print_info(f"Authorization URL: {url}")
    print()
    
    # Start local callback server
    print_info("Starting local callback server on http://localhost:8080/callback...")
    try:
        server = start_callback_server(8888)
        print_success("Callback server started successfully")
    except Exception as e:
        print_error(f"Failed to start callback server: {e}")
        print_warning("Falling back to manual code entry")
        server = None
    
    # Reset callback handler state
    CallbackHandler.received_code = None
    CallbackHandler.received_state = None
    
    # Open browser automatically
    print_info("Opening authorization URL in your default browser...")
    try:
        webbrowser.open(url)
        print_success("Browser opened successfully")
        time.sleep(1)  # Give browser a moment to open
    except Exception as e:
        print_warning(f"Could not open browser automatically: {e}")
        print_info("Please manually open the URL above in your browser")
    
    print()
    
    if server:
        print_info("Waiting for OAuth callback (timeout: 5 minutes)...")
        print_info("Complete the authentication in your browser window.")
        print()
        
        result = wait_for_callback(timeout=300)
        
        # Shutdown server
        server.shutdown()
        
        if result:
            auth_code, received_state = result
            print_success(f"✅ Authorization code received automatically!")
            print_info(f"Code: {auth_code[:20]}...")
            print_info(f"State: {received_state[:20]}...")
            return auth_code
        else:
            print_warning("⏱️  Timeout waiting for callback. Falling back to manual entry.")
    
    # Manual fallback
    print()
    print_warning("=" * 70)
    print_warning("MANUAL CODE ENTRY:")
    print_warning("=" * 70)
    print_info("1. Complete the OAuth authentication in the browser window")
    print_info("2. After authentication, you'll be redirected to a callback URL")
    print_info("3. Look for the 'code=' parameter in the callback URL")
    print_info("4. Copy the authorization code value")
    print_info("5. Paste it below when prompted")
    print()
    print_info("Example callback URL format:")
    print_info("  http://localhost:8080/callback?code=AUTHORIZATION_CODE_HERE&state=...")
    print()
    print_warning("=" * 70)
    print()
    
    # Prompt user for authorization code
    print_info("Waiting for authorization code...")
    print()
    auth_code = input(f"{Colors.OKCYAN}Enter authorization code (or press Enter to skip): {Colors.ENDC}").strip()
    
    if not auth_code:
        print_warning("No authorization code provided. Skipping token exchange and proxy tests.")
        return None
    
    print_success(f"Authorization code received: {auth_code[:20]}...")
    return auth_code

def test_token_exchange(gateway_url: str, proxy_id: int, client_id: str, client_secret: str, auth_code: str, 
                       code_verifier: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    """Test 3: Exchange Authorization Code for Access Token"""
    print_header("Test 3: Token Exchange")
    
    url = f"{gateway_url.rstrip('/')}/api/v1/oauth-proxy/{proxy_id}/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": code_verifier
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    form_data = urllib.parse.urlencode(data).encode()
    
    print_info("Exchanging authorization code for access token...")
    response, status = make_request("POST", url, headers, form_data)
    
    if status == 200:
        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token")
        print_success("Token exchange successful")
        print_info(f"Access Token: {access_token[:50]}..." if access_token else "N/A")
        print_info(f"Token Type: {response.get('token_type', 'N/A')}")
        print_info(f"Expires In: {response.get('expires_in', 'N/A')} seconds")
        return response
    else:
        print_error(f"Token exchange failed: {status}")
        print_error(f"Response: {json.dumps(response, indent=2)}")
        return None

def test_proxy_with_oauth_token(access_token: str, proxy_target: str):
    """Test 4: Access Proxy with OAuth Token"""
    print_header("Test 4: Access LLM Proxy with OAuth Token")
    
    # Construct proxy URL from target
    proxy_url = f"{proxy_target.rstrip('/')}/v1/messages"
    
    # Test with Anthropic Claude API format
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Say hello in one word"}
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "anthropic-version": "2023-06-01"
    }
    
    print_info(f"Making request to proxy: {proxy_url}")
    print_info("Using OAuth access token for authentication")
    
    response, status = make_request("POST", proxy_url, headers, json.dumps(payload).encode())
    
    if status == 200:
        print_success("Proxy request successful with OAuth token")
        print_info(f"Response: {json.dumps(response, indent=2)[:500]}...")
        return True
    else:
        print_error(f"Proxy request failed: {status}")
        print_error(f"Response: {json.dumps(response, indent=2)}")
        return False

def test_proxy_with_api_key(api_key: str, proxy_target: str):
    """Test 5: Access Proxy with API Key (should still work)"""
    print_header("Test 5: Access LLM Proxy with API Key")
    
    if not api_key:
        print_warning("No API key provided (use --api-key argument)")
        print_info("Skipping API key test")
        return False
    
    # Construct proxy URL from target
    proxy_url = f"{proxy_target.rstrip('/')}/v1/messages"
    
    # Test with Anthropic Claude API format
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Say hello in one word"}
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "anthropic-version": "2023-06-01"
    }
    
    print_info(f"Making request to proxy: {proxy_url}")
    print_info("Using Gateway API key for authentication")
    print_info("API keys should still work even when OAuth Proxy is enabled")
    
    response, status = make_request("POST", proxy_url, headers, json.dumps(payload).encode())
    
    if status == 200:
        print_success("Proxy request successful with API key")
        print_info("✅ API key authentication works alongside OAuth Proxy")
        print_info(f"Response: {json.dumps(response, indent=2)[:500]}...")
        return True
    else:
        print_error(f"Proxy request failed: {status}")
        print_error(f"Response: {json.dumps(response, indent=2)}")
        print_warning("API key authentication may not be working with OAuth Proxy enabled")
        return False

def test_proxy_health(proxy_target: str):
    """Test 0: Check Proxy Health"""
    print_header("Test 0: Proxy Health Check")
    
    # Try to access the proxy directly
    health_url = f"{proxy_target.rstrip('/')}/health"
    
    print_info(f"Checking proxy health at: {health_url}")
    try:
        response, status = make_request("GET", health_url)
        if status == 200:
            print_success("Proxy is accessible")
            return True
        else:
            print_warning(f"Proxy health check returned status {status}, but continuing...")
            return True  # Continue anyway, might not have /health endpoint
    except Exception as e:
        print_warning(f"Could not check proxy health: {e}")
        print_info("Continuing with tests anyway...")
        return True  # Continue anyway

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Test OAuth Proxy Gateway Mode for LLM Proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with target proxy (uses provider default scopes or empty)
  python3 test_oauth_proxy_gateway_llm.py --target http://localhost:8093 --proxy-id 9

  # With custom scopes (e.g., for GitHub: read:user user:email)
  python3 test_oauth_proxy_gateway_llm.py --target http://localhost:8093 --proxy-id 9 --scope "read:user user:email"

  # With API key for testing hybrid auth
  python3 test_oauth_proxy_gateway_llm.py --target http://localhost:8093 --proxy-id 9 --api-key uag_...

  # Custom Gateway URL and scopes (e.g., for Google: openid profile email)
  python3 test_oauth_proxy_gateway_llm.py --target http://localhost:8093 --proxy-id 9 --gateway http://localhost:8080 --scope "openid profile email"
        """
    )
    
    parser.add_argument(
        "--target",
        required=True,
        help="Target proxy URL (e.g., http://localhost:8093)"
    )
    
    parser.add_argument(
        "--proxy-id",
        type=int,
        required=True,
        help="Proxy ID for OAuth Proxy API endpoints"
    )
    
    parser.add_argument(
        "--gateway",
        default="http://localhost:8080",
        help="Gateway API URL (default: http://localhost:8080)"
    )
    
    parser.add_argument(
        "--api-key",
        default="",
        help="Gateway API key for testing API key authentication (optional)"
    )
    
    parser.add_argument(
        "--scope",
        default="",
        help="OAuth scopes to request (e.g., 'openid profile email' or leave empty for provider defaults)"
    )
    
    return parser.parse_args()

def main():
    """Main test execution"""
    args = parse_arguments()
    
    # Extract API key from args or environment
    api_key = args.api_key or os.getenv("GATEWAY_API_KEY", "")
    
    print_header("OAuth Proxy Gateway Mode Test for LLM Proxy")
    print_info(f"Gateway URL: {args.gateway}")
    print_info(f"Proxy ID: {args.proxy_id}")
    print_info(f"Proxy Target: {args.target}")
    if api_key:
        print_info(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    # Test 0: Health check
    if not test_proxy_health(args.target):
        print_warning("Proxy health check had issues, but continuing...")
    
    # Handle scope
    scope = args.scope.strip() if args.scope else ""
    if scope:
        print_info(f"Using custom scopes: {scope}")
    else:
        print_info("No scopes specified - using provider defaults (or empty)")
    
    # Test 1: DCR
    dcr_response = test_dcr(args.gateway, args.proxy_id, scope)
    if not dcr_response:
        print_error("DCR failed. Cannot continue.")
        sys.exit(1)
    
    client_id = dcr_response.get("client_id")
    client_secret = dcr_response.get("client_secret")
    redirect_uri = dcr_response.get("redirect_uris", [])[0] if dcr_response.get("redirect_uris") else "http://localhost:8888/callback"
    
    if not client_id or not client_secret:
        print_error("Missing client_id or client_secret from DCR response")
        sys.exit(1)
    
    # Generate PKCE
    code_verifier, code_challenge, code_challenge_method = generate_pkce()
    print_info(f"Generated PKCE verifier: {code_verifier[:20]}...")
    print_info(f"Generated PKCE challenge: {code_challenge[:20]}...")
    
    # Test 2: Authorization (interactive)
    # The test_authorization function will handle opening the browser and prompting for the code
    auth_code = test_authorization(args.gateway, args.proxy_id, client_id, code_challenge, code_challenge_method, scope)
    
    if not auth_code:
        print_warning("Authorization code not provided. Skipping token exchange and proxy tests.")
        print_info("To test manually:")
        print_info(f"  1. Open the authorization URL in a browser")
        print_info(f"  2. Complete OAuth flow")
        print_info(f"  3. Extract the code from the callback URL")
        print_info(f"  4. Run the script again with the code")
        sys.exit(0)
    
    # Test 3: Token Exchange
    token_response = test_token_exchange(args.gateway, args.proxy_id, client_id, client_secret, auth_code, 
                                        code_verifier, redirect_uri)
    if not token_response:
        print_error("Token exchange failed. Cannot test proxy access.")
        sys.exit(1)
    
    access_token = token_response.get("access_token")
    if not access_token:
        print_error("No access token in response")
        sys.exit(1)
    
    # Test 4: Proxy with OAuth Token
    oauth_success = test_proxy_with_oauth_token(access_token, args.target)
    
    # Test 5: Proxy with API Key
    api_key_success = test_proxy_with_api_key(api_key, args.target)
    
    # Summary
    print_header("Test Summary")
    print_success("✅ Dynamic Client Registration: PASSED")
    if auth_code:
        print_success("✅ OAuth Authorization: PASSED")
        print_success("✅ Token Exchange: PASSED")
        if oauth_success:
            print_success("✅ Proxy Access with OAuth Token: PASSED")
        else:
            print_error("❌ Proxy Access with OAuth Token: FAILED")
    
    if api_key:
        if api_key_success:
            print_success("✅ Proxy Access with API Key: PASSED")
            print_info("✅ API keys work alongside OAuth Proxy (hybrid mode)")
        else:
            print_error("❌ Proxy Access with API Key: FAILED")
    else:
        print_warning("⚠️  API Key test skipped (no API key provided)")
    
    print()
    print_info("Test completed!")

if __name__ == "__main__":
    main()

