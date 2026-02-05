#!/usr/bin/env python3
"""
Complete OAuth + MCP Integration Example
=========================================

This script demonstrates how to:
1. Authenticate with OAuth (Google, etc.)
2. Get a session token
3. Use the token to call MCP tools

Usage:
    python3 mcp_oauth_example.py

Requirements:
    pip install requests
"""

import requests
import webbrowser
import json
import sys
from urllib.parse import urlparse, parse_qs

# Configuration
GATEWAY_URL = "http://localhost:8080"
MCP_PROXY_URL = "http://localhost:8040"
PROVIDER_ID = 2  # Change to your OAuth provider ID

def print_header(text):
    """Print a nice header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def get_oauth_token():
    """
    Step 1: Start OAuth flow and get session token

    Returns:
        str: Session token for authenticating MCP requests
    """
    print_header("🔐 Step 1: OAuth Authentication")

    print(f"\n📡 Starting OAuth flow with provider {PROVIDER_ID}...")

    try:
        # Start OAuth flow
        response = requests.post(
            f"{GATEWAY_URL}/api/v1/oauth/authorize/{PROVIDER_ID}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
            sys.exit(1)

        auth_url = data["data"]["authorization_url"]
        state = data["data"]["state"]

        print(f"✅ OAuth flow started successfully")
        print(f"📋 State: {state}")

        # Open browser for user to login
        print(f"\n🌐 Opening browser for OAuth login...")
        webbrowser.open(auth_url)

        print("\n" + "─" * 60)
        print("👤 Please complete the login in your browser")
        print("📋 After login, you'll see a JSON response")
        print("📋 Copy the 'session_token' value (the JWT)")
        print("─" * 60)
        print("\nThe response will look like:")
        print('{"success":true,"data":{"session_token":"eyJhbG...","user_email":"..."}}')
        print("\nCopy ONLY the session_token value (starts with 'eyJ')")

        session_token = input("\n🔑 Paste session token (JWT) here: ").strip()

        if not session_token:
            print("❌ No token provided")
            sys.exit(1)

        # Validate JWT format
        if not session_token.startswith('eyJ'):
            print("❌ Invalid JWT format (should start with 'eyJ')")
            sys.exit(1)

        print(f"\n🔄 Validating JWT token...")

        # Decode JWT to extract user information
        import base64
        try:
            # Split JWT into parts (header.payload.signature)
            parts = session_token.split('.')
            if len(parts) != 3:
                print("❌ Invalid JWT format (should have 3 parts)")
                sys.exit(1)

            # Decode payload (second part)
            payload = parts[1]
            # Add padding if needed for base64 decoding
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding

            # Decode base64 and parse JSON
            decoded = base64.b64decode(payload)
            user_data = json.loads(decoded)

            user_email = user_data.get('email') or user_data.get('sub', 'unknown')
            user_name = user_data.get('username') or user_email

            print(f"\n✅ OAuth authentication successful!")
            print(f"👤 Logged in as: {user_name} ({user_email})")
            print(f"🔑 Session token: {session_token[:30]}...")

            return session_token

        except (base64.binascii.Error, json.JSONDecodeError, IndexError) as e:
            print(f"❌ Failed to decode JWT: {e}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network error: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"\n❌ Unexpected response format: {e}")
        sys.exit(1)

def list_mcp_tools(session_token):
    """
    Step 2: List available MCP tools using the OAuth session token

    Args:
        session_token (str): OAuth session token

    Returns:
        list: List of MCP tools
    """
    print_header("🔧 Step 2: List MCP Tools")

    print(f"\n📡 Connecting to MCP proxy at {MCP_PROXY_URL}...")

    headers = {
        "Content-Type": "application/json",
        "X-Session-Token": session_token
    }

    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }

    try:
        response = requests.post(
            f"{MCP_PROXY_URL}/mcp/tools/list",
            headers=headers,
            json=mcp_request,
            timeout=10
        )

        if response.status_code == 401:
            print("❌ Authentication failed!")
            print("   Check that:")
            print("   1. Your session token is valid")
            print("   2. The proxy has OAuth enabled")
            print("   3. You're using the correct provider ID")
            return []

        response.raise_for_status()

        result = response.json()

        if "result" not in result:
            print(f"❌ Unexpected response: {result}")
            return []

        tools = result["result"]["tools"]

        print(f"\n✅ Found {len(tools)} MCP tools:\n")

        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool['name']}")
            print(f"     📝 {tool['description']}")
            if i < len(tools):
                print()

        return tools

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error calling MCP proxy: {e}")
        return []

def call_mcp_tool(session_token, tool_name, arguments=None):
    """
    Step 3: Call a specific MCP tool

    Args:
        session_token (str): OAuth session token
        tool_name (str): Name of the tool to call
        arguments (dict): Tool arguments
    """
    print_header(f"⚡ Step 3: Call MCP Tool '{tool_name}'")

    headers = {
        "Content-Type": "application/json",
        "X-Session-Token": session_token
    }

    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        },
        "id": 2
    }

    print(f"\n📡 Calling tool '{tool_name}'...")

    try:
        response = requests.post(
            f"{MCP_PROXY_URL}/mcp/tools/call",
            headers=headers,
            json=mcp_request,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        if "result" in result:
            print(f"\n✅ Tool executed successfully!")
            print(f"\n📊 Result:")
            print(json.dumps(result["result"], indent=2))
        elif "error" in result:
            print(f"\n⚠️  Tool returned error:")
            print(f"   {result['error'].get('message', 'Unknown error')}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error calling tool: {e}")

def save_token(session_token):
    """Save session token to file for reuse"""
    try:
        with open(".session_token", "w") as f:
            f.write(session_token)
        print(f"\n💾 Token saved to .session_token file")
        print(f"   Reuse it with: export SESSION_TOKEN=$(cat .session_token)")
    except IOError as e:
        print(f"\n⚠️  Could not save token: {e}")

def main():
    """Main execution flow"""
    print_header("🚀 MCP OAuth Integration Example")
    print("\nThis script will:")
    print("  1. Authenticate you via OAuth")
    print("  2. Get a session token")
    print("  3. List available MCP tools")
    print("  4. (Optional) Call a tool")

    input("\nPress Enter to start...")

    # Step 1: Get OAuth token
    try:
        session_token = get_oauth_token()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ OAuth failed: {e}")
        sys.exit(1)

    # Step 2: List MCP tools
    try:
        tools = list_mcp_tools(session_token)
    except Exception as e:
        print(f"\n❌ Failed to list tools: {e}")
        sys.exit(1)

    # Step 3: Optionally call a tool
    if tools:
        print("\n" + "─" * 60)
        choice = input("\n🔧 Want to call a tool? (y/N): ").strip().lower()

        if choice == 'y':
            tool_name = input("Enter tool name: ").strip()
            call_mcp_tool(session_token, tool_name)

    # Save token for reuse
    save_token(session_token)

    # Success summary
    print_header("✅ SUCCESS!")
    print("\n🎉 You've successfully:")
    print("   ✓ Authenticated with OAuth")
    print("   ✓ Retrieved a session token")
    print("   ✓ Called MCP tools with user attribution")
    print("\n📝 All your requests are logged with your identity!")
    print(f"   Check the audit logs at: {GATEWAY_URL}/audit-logs")

    print("\n💡 Next steps:")
    print("   • Save the token and reuse it in your scripts")
    print("   • Build your own MCP client with this pattern")
    print("   • Check token expiry and implement refresh logic")

    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
