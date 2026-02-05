# OAuth Proxy Tests

This directory contains test scripts for the OAuth Proxy functionality with Dynamic Client Registration (DCR).

## Test Scripts

### `test_oauth_proxy_gateway_llm.py`

Comprehensive Python test script for OAuth Proxy Gateway mode on LLM proxies.

**What it tests:**
- ✅ Dynamic Client Registration (DCR) - RFC 7591
- ✅ OAuth 2.1 Authorization Flow with PKCE - RFC 7636
- ✅ Token Exchange
- ✅ Accessing LLM proxy with OAuth access tokens
- ✅ API Key authentication (verifies it still works with OAuth Proxy enabled)

**Prerequisites:**
- Gateway running on `http://localhost:8080`
- LLM Proxy configured with OAuth Proxy Gateway mode enabled
- OAuth Provider configured
- Gateway API Key (optional, for testing API key auth)

**Usage:**
```bash
# Basic usage (required arguments)
python3 test_oauth_proxy_gateway_llm.py \
  --target http://localhost:8093 \
  --proxy-id 9

# With API key for testing hybrid authentication
python3 test_oauth_proxy_gateway_llm.py \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --api-key uag_your_api_key_here

# Custom Gateway URL
python3 test_oauth_proxy_gateway_llm.py \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --gateway http://localhost:8080

# With custom scopes (if your provider requires specific scopes)
python3 test_oauth_proxy_gateway_llm.py \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --scope "openid profile email"

# Show help
python3 test_oauth_proxy_gateway_llm.py --help
```

**Arguments:**
- `--target` (required): Target proxy URL (e.g., `http://localhost:8093`)
- `--proxy-id` (required): Proxy ID for OAuth Proxy API endpoints
- `--gateway` (optional): Gateway API URL (default: `http://localhost:8080`)
- `--api-key` (optional): Gateway API key for testing API key authentication
- `--scope` (optional): OAuth scopes to request (e.g., `"openid profile email"` or `"read:user user:email"`). If not provided, uses provider defaults or empty scopes.

**Note on Scopes:**
Different OAuth providers use different scopes. Common examples:
- **GitHub**: `"read:user user:email"`
- **Google**: `"openid profile email"`
- **Microsoft/Azure AD**: `"openid profile email"`
- **GitLab**: `"read_user email"`

If you get an `invalid_scope` error, check your OAuth provider configuration to see what scopes are available, then use the `--scope` argument with the correct scopes.

### `test_api_key_with_oauth_proxy.sh`

Quick bash script to verify API keys work when OAuth Proxy is enabled.

**What it tests:**
- ✅ Proxy accessibility
- ✅ API Key authentication with OAuth Proxy enabled
- ✅ Verifies hybrid authentication mode works

**Usage:**
```bash
# Basic usage (required)
./test_api_key_with_oauth_proxy.sh --target http://localhost:8093

# With API key
./test_api_key_with_oauth_proxy.sh \
  --target http://localhost:8093 \
  --api-key uag_your_api_key_here

# Custom Gateway URL
./test_api_key_with_oauth_proxy.sh \
  --target http://localhost:8093 \
  --api-key uag_your_api_key_here \
  --gateway http://localhost:8080

# Show help
./test_api_key_with_oauth_proxy.sh --help
```

**Arguments:**
- `--target` (required): Target proxy URL (e.g., `http://localhost:8093`)
- `--api-key` (optional): Gateway API key for testing
- `--gateway` (optional): Gateway API URL (default: `http://localhost:8080`)

**Interactive Flow:**
1. Script registers a client via DCR
2. Script generates PKCE parameters
3. Script provides authorization URL
4. **You manually**: Open URL in browser, complete OAuth flow
5. **You manually**: Extract authorization code from callback URL
6. Script exchanges code for access token
7. Script tests proxy access with OAuth token
8. Script tests proxy access with API key (if provided)

**Expected Output:**
```
✅ Dynamic Client Registration: PASSED
✅ OAuth Authorization: PASSED
✅ Token Exchange: PASSED
✅ Proxy Access with OAuth Token: PASSED
✅ Proxy Access with API Key: PASSED
✅ API keys work alongside OAuth Proxy (hybrid mode)
```

## API Key Authentication with OAuth Proxy

**Important:** API keys continue to work even when OAuth Proxy is enabled!

The Gateway supports **hybrid authentication mode**:
- **OAuth Proxy tokens**: For clients that register via DCR and use OAuth flow
- **API Keys**: For scripts, CLI tools, and automated systems

Both authentication methods work simultaneously:
- Clients can use OAuth Proxy tokens (`Authorization: Bearer <oauth_token>`)
- Scripts can use API keys (`Authorization: Bearer <api_key>` or `X-API-Key: <api_key>`)

This allows you to:
- Use OAuth Proxy for interactive clients (Cursor IDE, browser integrations)
- Use API keys for automation, CI/CD, and scripts
- Gradually migrate from API keys to OAuth without breaking existing integrations

## Testing API Key Authentication

To test that API keys still work:

```bash
# Pass API key as argument
python3 test_oauth_proxy_gateway_llm.py \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --api-key uag_your_api_key_here

# Or set as environment variable (fallback)
export GATEWAY_API_KEY="uag_your_api_key_here"
python3 test_oauth_proxy_gateway_llm.py \
  --target http://localhost:8093 \
  --proxy-id 9
```

The script will automatically test API key authentication if `--api-key` is provided or `GATEWAY_API_KEY` is set.

## Manual Testing

### Test 1: DCR Registration
```bash
curl -X POST http://localhost:8080/api/v1/oauth-proxy/9/register \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uris": ["http://localhost:8080/callback", "cursor://oauth-callback"],
    "client_name": "Test Client"
  }'
```

### Test 2: Authorization Flow
```bash
# Generate PKCE
CODE_VERIFIER=$(openssl rand -base64 32 | tr -d '=' | tr '+/' '-_')
CODE_CHALLENGE=$(echo -n "$CODE_VERIFIER" | openssl dgst -binary -sha256 | openssl base64 | tr -d '=' | tr '+/' '-_')

# Initiate authorization
CLIENT_ID="gateway_..." # From Test 1
curl -L "http://localhost:8080/api/v1/oauth-proxy/9/authorize?client_id=$CLIENT_ID&redirect_uri=http://localhost:8080/callback&response_type=code&code_challenge=$CODE_CHALLENGE&code_challenge_method=S256"
```

### Test 3: Token Exchange
```bash
AUTH_CODE="..." # From callback
CLIENT_SECRET="..." # From Test 1

curl -X POST http://localhost:8080/api/v1/oauth-proxy/9/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=$AUTH_CODE&redirect_uri=http://localhost:8080/callback&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET&code_verifier=$CODE_VERIFIER"
```

### Test 4: Access Proxy with OAuth Token
```bash
# Replace with your actual proxy target URL
PROXY_TARGET="http://localhost:8093"
ACCESS_TOKEN="..." # From Test 3

curl -X POST "${PROXY_TARGET}/v1/messages" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-haiku-20240307",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Test 5: Access Proxy with API Key
```bash
# Replace with your actual proxy target URL
PROXY_TARGET="http://localhost:8093"
API_KEY="uag_your_api_key_here"

curl -X POST "${PROXY_TARGET}/v1/messages" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-haiku-20240307",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Troubleshooting

### Proxy not running
```bash
# Check proxy status
curl http://localhost:8080/api/v1/proxies/9/status

# Start proxy
curl -X POST http://localhost:8080/api/v1/proxies/9/start \
  -H "Authorization: Bearer YOUR_ADMIN_JWT"
```

### OAuth Provider not configured
Ensure you have an OAuth provider configured with ID matching `PROVIDER_ID`.

### Invalid redirect URI
Make sure your redirect URIs match the patterns configured in `oauth_proxy_allowed_redirects`:
- `http://localhost:*` - Any port on localhost
- `cursor://*` - Cursor IDE custom scheme
- `vscode://*` - VS Code custom scheme

## Related Documentation

- [OAuth Proxy Testing Guide](../../docs/testing/oauth-proxy-testing-guide.md)
- [OAuth Proxy Architecture](../../docs/technical/architecture/oauth-proxy.md)

