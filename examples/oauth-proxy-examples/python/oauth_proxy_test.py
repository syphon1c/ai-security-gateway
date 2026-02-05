#!/usr/bin/env python3
"""
OAuth Proxy Testing Example - Python

This script demonstrates how to test OAuth Proxy functionality using the Gateway API.
It covers the complete OAuth 2.1 flow with Dynamic Client Registration (DCR) and PKCE.

Features:
- Dynamic Client Registration (DCR)
- PKCE code verifier and challenge generation
- OAuth authorization flow with automatic callback handling
- Token exchange (authorization code for access token)
- Using OAuth tokens to access protected resources
- Hybrid authentication (OAuth + API Keys)

Prerequisites:
- Gateway running on http://localhost:8080
- OAuth Proxy configured for a target proxy
- Python 3.7+ (no external dependencies required)

Usage:
    python3 oauth_proxy_test.py --target http://localhost:8093 --proxy-id 9

For complete examples and advanced usage, see:
    test/oauth-proxy-tests/test_oauth_proxy_gateway_llm.py
"""

import argparse
import base64
import hashlib
import json
import secrets
import sys
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional
from urllib.error import HTTPError


def make_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[bytes] = None
) -> tuple[Dict[str, Any], int]:
    """
    Make HTTP request and return response as JSON and status code.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        headers: Optional request headers
        data: Optional request body (bytes)
    
    Returns:
        Tuple of (response_json, status_code)
    """
    req = urllib.request.Request(url, data=data, headers=headers or {})
    req.get_method = lambda: method
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            return json.loads(body), status
    except HTTPError as e:
        status = e.code
        body = e.read().decode('utf-8')
        try:
            return json.loads(body), status
        except json.JSONDecodeError:
            return {"error": body}, status


def generate_pkce() -> tuple[str, str, str]:
    """
    Generate PKCE (Proof Key for Code Exchange) parameters.
    
    PKCE adds security to the OAuth flow by preventing authorization code interception.
    Uses SHA256 method as required by OAuth 2.1.
    
    Returns:
        Tuple of (code_verifier, code_challenge, code_challenge_method)
    
    Example:
        verifier, challenge, method = generate_pkce()
        # verifier: random 43-128 character string (base64url encoded)
        # challenge: SHA256 hash of verifier (base64url encoded)
        # method: "S256" (indicates SHA256 hashing)
    """
    # Generate code verifier: 43-128 characters, base64url encoded random bytes
    verifier_bytes = secrets.token_bytes(32)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).decode('utf-8').rstrip('=')
    
    # Generate code challenge: SHA256 hash of verifier
    challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge, "S256"


def register_client(
    gateway_url: str,
    proxy_id: int,
    redirect_uris: list[str],
    client_name: str = "Test OAuth Client",
    scopes: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Register a new OAuth client via Dynamic Client Registration (DCR).
    
    Args:
        gateway_url: Gateway API base URL (e.g., http://localhost:8080)
        proxy_id: ID of the OAuth Proxy-enabled proxy
        redirect_uris: List of allowed redirect URIs
        client_name: Human-readable client name
        scopes: OAuth scopes to request (optional, provider-specific)
    
    Returns:
        DCR response containing client_id, client_secret, and endpoint URLs
    
    Example:
        client = register_client(
            "http://localhost:8080",
            9,
            ["http://localhost:8888/callback"],
            "My OAuth Client",
            "read:user user:email"
        )
        
        if client:
            print(f"Client ID: {client['client_id']}")
            print(f"Client Secret: {client['client_secret']}")
            print(f"Authorization URL: {client['authorization_url']}")
    """
    url = f"{gateway_url.rstrip('/')}/api/v1/oauth-proxy/{proxy_id}/register"
    
    payload = {
        "redirect_uris": redirect_uris,
        "client_name": client_name,
        "token_endpoint_auth_method": "client_secret_post",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"]
    }
    
    if scopes:
        payload["scope"] = scopes
    
    headers = {"Content-Type": "application/json"}
    response, status = make_request("POST", url, headers, json.dumps(payload).encode())
    
    if status in (200, 201):
        print(f"✅ Client registered: {response.get('client_id')}")
        return response
    else:
        print(f"❌ Registration failed ({status}): {response}")
        return None


def build_authorization_url(
    authorization_endpoint: str,
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
    state: Optional[str] = None,
    scopes: str = ""
) -> str:
    """
    Build OAuth authorization URL with PKCE parameters.
    
    Args:
        authorization_endpoint: OAuth authorization endpoint URL
        client_id: OAuth client ID from DCR
        redirect_uri: Callback URI (must match registered URI)
        code_challenge: PKCE code challenge
        code_challenge_method: PKCE method (always "S256" for OAuth 2.1)
        state: Optional state parameter for CSRF protection
        scopes: OAuth scopes to request
    
    Returns:
        Complete authorization URL to redirect user to
    
    Example:
        verifier, challenge, method = generate_pkce()
        auth_url = build_authorization_url(
            "http://localhost:8093/oauth/authorize",
            "client_abc123",
            "http://localhost:8888/callback",
            challenge,
            method,
            scopes="openid profile email"
        )
        
        # Direct user to auth_url in browser
        print(f"Visit: {auth_url}")
    """
    if not state:
        state = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode('utf-8').rstrip('=')
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method
    }
    
    if scopes:
        params["scope"] = scopes
    
    return f"{authorization_endpoint}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(
    token_endpoint: str,
    client_id: str,
    client_secret: str,
    authorization_code: str,
    redirect_uri: str,
    code_verifier: str
) -> Optional[Dict[str, Any]]:
    """
    Exchange authorization code for access token.
    
    Args:
        token_endpoint: OAuth token endpoint URL
        client_id: OAuth client ID
        client_secret: OAuth client secret
        authorization_code: Authorization code from callback
        redirect_uri: Redirect URI (must match original request)
        code_verifier: PKCE code verifier (proves you initiated the flow)
    
    Returns:
        Token response containing access_token, token_type, expires_in, etc.
    
    Example:
        token = exchange_code_for_token(
            "http://localhost:8080/api/v1/oauth-proxy/9/token",
            client_id,
            client_secret,
            "auth_code_abc123",
            "http://localhost:8888/callback",
            verifier
        )
        
        if token:
            access_token = token['access_token']
            # Use access_token in Authorization header for API requests
    """
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": code_verifier
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    form_data = urllib.parse.urlencode(data).encode()
    
    response, status = make_request("POST", token_endpoint, headers, form_data)
    
    if status == 200:
        print(f"✅ Token exchange successful")
        print(f"   Access Token: {response.get('access_token', '')[:50]}...")
        return response
    else:
        print(f"❌ Token exchange failed ({status}): {response}")
        return None


def main():
    """Main example demonstrating OAuth Proxy testing flow"""
    parser = argparse.ArgumentParser(description="Test OAuth Proxy with DCR and PKCE")
    parser.add_argument("--target", required=True, help="Target proxy URL (e.g., http://localhost:8093)")
    parser.add_argument("--proxy-id", type=int, required=True, help="Proxy ID for OAuth Proxy")
    parser.add_argument("--gateway", default="http://localhost:8080", help="Gateway URL")
    parser.add_argument("--scope", default="", help="OAuth scopes (space-separated)")
    args = parser.parse_args()
    
    print("=" * 70)
    print("OAuth Proxy Testing Example")
    print("=" * 70)
    print()
    
    # Step 1: Register OAuth client
    print("Step 1: Dynamic Client Registration (DCR)")
    print("-" * 70)
    client = register_client(
        args.gateway,
        args.proxy_id,
        ["http://localhost:8888/callback"],
        "Example OAuth Client",
        args.scope
    )
    
    if not client:
        print("\n❌ Failed to register client")
        sys.exit(1)
    
    client_id = client.get("client_id")
    client_secret = client.get("client_secret")
    auth_endpoint = client.get("authorization_url")
    token_endpoint = client.get("token_url")
    
    print()
    
    # Step 2: Generate PKCE parameters
    print("Step 2: Generate PKCE Parameters")
    print("-" * 70)
    verifier, challenge, method = generate_pkce()
    print(f"✅ Code Verifier: {verifier[:40]}...")
    print(f"✅ Code Challenge: {challenge[:40]}...")
    print(f"✅ Challenge Method: {method}")
    print()
    
    # Step 3: Build authorization URL
    print("Step 3: Build Authorization URL")
    print("-" * 70)
    auth_url = build_authorization_url(
        auth_endpoint,
        client_id,
        "http://localhost:8888/callback",
        challenge,
        method,
        scopes=args.scope
    )
    print(f"✅ Authorization URL generated")
    print()
    print(f"🔗 Open this URL in your browser:")
    print(f"   {auth_url}")
    print()
    
    # Step 4: Manual code entry
    print("Step 4: Authorization & Token Exchange")
    print("-" * 70)
    print("After authenticating in the browser, you'll receive an authorization code.")
    print("For automated callback handling, see: test/oauth-proxy-tests/test_oauth_proxy_gateway_llm.py")
    print()
    auth_code = input("Enter authorization code (or press Enter to skip): ").strip()
    
    if not auth_code:
        print("\n⚠️  Skipping token exchange")
        print("\nTo complete the flow:")
        print("  1. Visit the authorization URL above")
        print("  2. Complete OAuth authentication")
        print("  3. Extract 'code' parameter from callback URL")
        print("  4. Use exchange_code_for_token() function")
        return
    
    print()
    
    # Exchange code for token
    token = exchange_code_for_token(
        token_endpoint,
        client_id,
        client_secret,
        auth_code,
        "http://localhost:8888/callback",
        verifier
    )
    
    if token:
        print()
        print("=" * 70)
        print("✅ OAuth Flow Complete!")
        print("=" * 70)
        print(f"Access Token: {token.get('access_token', '')[:50]}...")
        print(f"Token Type: {token.get('token_type')}")
        print(f"Expires In: {token.get('expires_in')} seconds")
        print()
        print("Use the access token in Authorization header:")
        print(f"  Authorization: Bearer {token.get('access_token')}")


if __name__ == "__main__":
    main()
