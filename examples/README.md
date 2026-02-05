# OAuth + MCP Integration Examples

Working code examples for developers to integrate OAuth authentication with MCP/LLM proxies.

## 📚 Available Examples

### 1. **OAuth Proxy Testing** (DCR + PKCE Flow)
Complete examples for testing OAuth Proxy with Dynamic Client Registration:

- **Python**: `python/oauth_proxy_test.py` - Self-contained, no dependencies
- **TypeScript**: `typescript/oauth-proxy-test.ts` - Node.js/Bun compatible

**See**: [`oauth-proxy-testing-README.md`](oauth-proxy-testing-README.md) for comprehensive guide

**Quick Start:**
```bash
# Python
python3 examples/python/oauth_proxy_test.py --target http://localhost:8093 --proxy-id 9

# TypeScript
npx ts-node examples/typescript/oauth-proxy-test.ts --target http://localhost:8093 --proxy-id 9
```

### 2. **MCP OAuth Integration** (Session-based Flow)
Examples for integrating OAuth authentication with MCP clients:

- **Python**: `python/mcp_oauth_example.py`
- **TypeScript**: `typescript/mcp-oauth-example.ts`

**Quick Start:**

```bash
cd examples/python
pip install requests
python3 mcp_oauth_example.py
```

### TypeScript Example

```bash
cd examples/typescript
npm install axios open readline
ts-node mcp-oauth-example.ts
```

## What These Examples Do

1. **Start OAuth Flow** → Opens browser for login
2. **Get Session Token** → Captures OAuth callback
3. **Call MCP Tools** → Uses token to make authenticated requests
4. **Show Results** → Displays tools and user attribution

## Output Example

```
============================================================
  🚀 MCP OAuth Integration Example
============================================================

This script will:
  1. Authenticate you via OAuth
  2. Get a session token
  3. List available MCP tools
  4. (Optional) Call a tool

Press Enter to start...

============================================================
  🔐 Step 1: OAuth Authentication
============================================================

📡 Starting OAuth flow with provider 2...
✅ OAuth flow started successfully
📋 State: abc123...

🌐 Opening browser for OAuth login...
[Browser opens with Google login]

🔗 Paste redirect URL here: http://localhost:8080/oauth/callback?code=...

🔄 Completing OAuth flow...

✅ OAuth authentication successful!
👤 Logged in as: Gareth Phillips (gareth@ai-gateway.localhost)
🔑 Session token: VKBRWGztPGiF-777Tub33frj...

============================================================
  🔧 Step 2: List MCP Tools
============================================================

📡 Connecting to MCP proxy at http://localhost:8040...

✅ Found 5 MCP tools:

  1. execute_command
     📝 Execute system commands (VULNERABLE)

  2. query_database
     📝 Query user database (VULNERABLE TO SQL INJECTION)

  [... more tools ...]

💾 Token saved to .session_token file

============================================================
  ✅ SUCCESS!
============================================================

🎉 You've successfully:
   ✓ Authenticated with OAuth
   ✓ Retrieved a session token
   ✓ Called MCP tools with user attribution

📝 All your requests are logged with your identity!
```

## Files

- **`python/mcp_oauth_example.py`** - Complete Python implementation
- **`typescript/mcp-oauth-example.ts`** - Complete TypeScript implementation

## Documentation

See **`/docs/developer-oauth-guide.md`** for detailed API reference and usage patterns.

## Key Concepts

### Session Token Format

```
X-Session-Token: VKBRWGztPGiF-777Tub33frjrJ0LR_D3ad7vmY30g0=
```

### MCP Request with OAuth

```python
headers = {
    "Content-Type": "application/json",
    "X-Session-Token": session_token
}

response = requests.post(
    "http://localhost:8040/mcp/tools/list",
    headers=headers,
    json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
)
```

### User Attribution

Every request is logged with your identity:
- **User**: gareth@ai-gateway.localhost
- **Timestamp**: 2025-12-24T22:53:35
- **Action**: tools/list
- **Proxy**: Test (ID: 3)

View logs at: http://localhost:8080/audit-logs

## Customization

Change these variables in the scripts:

```python
GATEWAY_URL = "http://localhost:8080"    # Your gateway URL
MCP_PROXY_URL = "http://localhost:8040"  # Your proxy URL
PROVIDER_ID = 2                           # Your OAuth provider ID
```

## Troubleshooting

**"OAuth authentication required"**
- Verify proxy has `oauth_enabled: true` and `oauth_required: true`
- Check you're using `X-Session-Token` header (not Authorization)

**"Failed to start OAuth flow"**
- Ensure gateway is running on port 8080
- Verify OAuth provider is configured (ID exists)

**"No tools returned"**
- Check upstream MCP server is running
- Verify proxy target URL is correct

## Next Steps

1. **Save Token** - Store in environment variable or config file
2. **Refresh Logic** - Handle token expiry (1 hour default)
3. **Error Handling** - Add retry logic for network errors
4. **Production** - Use secrets management for tokens

