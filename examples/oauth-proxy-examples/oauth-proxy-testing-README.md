# OAuth Proxy Testing Examples

This directory contains language-specific examples for testing OAuth Proxy functionality with the Unify AI Gateway.

## Overview

The examples demonstrate:
- **Dynamic Client Registration (DCR)** - Programmatically register OAuth clients
- **PKCE Implementation** - Generate code verifier and challenge for OAuth 2.1 security
- **Authorization Flow** - Build authorization URLs and handle callbacks
- **Token Exchange** - Exchange authorization codes for access tokens
- **Protected Resource Access** - Use OAuth tokens to access proxies

## Available Examples

### Python (`oauth-proxy-examples/python/oauth_proxy_test.py`)

Simple, self-contained example using only Python standard library (no dependencies).

**Usage:**
```bash
python3 examples/oauth-proxy-examples/python/oauth_proxy_test.py \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --scope "read:user user:email"
```

**Features:**
- ✅ No external dependencies (uses `urllib`, `hashlib`, `secrets`)
- ✅ Educational code with detailed comments
- ✅ Manual authorization code entry
- ✅ PKCE code generation and validation

**For Production:** See `examples/oauth-proxy-tests/test_oauth_proxy_gateway_llm.py` for a complete implementation with:
- Automatic callback server
- Browser automation
- LLM proxy testing
- Hybrid authentication (OAuth + API Keys)

### TypeScript (`oauth-proxy-examples/typescript/oauth-proxy-test.ts`)

Modern TypeScript example compatible with Node.js 18+ or Bun runtime.

**Usage:**
```bash
# With Node.js
npx ts-node examples/oauth-proxy-examples/typescript/oauth-proxy-test.ts \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --scope "openid profile email"

# With Bun
bun run examples/oauth-proxy-examples/typescript/oauth-proxy-test.ts \
  --target http://localhost:8093 \
  --proxy-id 9
```

**Features:**
- ✅ TypeScript with full type definitions
- ✅ Native `fetch` API (no axios dependency)
- ✅ Crypto module for PKCE generation
- ✅ Exportable functions for use as library
- ✅ Works with Node.js 18+ and Bun

**Installation (Node.js):**
```bash
npm install -D typescript ts-node @types/node
```

**Installation (Bun):**
```bash
# No installation needed - Bun has built-in TypeScript support
```

## Quick Start

### 1. Prerequisites

- **Gateway running** on `http://localhost:8080`
- **OAuth Proxy configured** for a target proxy
- **OAuth Provider** set up (GitHub, Google, Azure AD, etc.)

### 2. Configure OAuth Proxy

Using the Gateway UI:
1. Navigate to **OAuth Proxy** page
2. Click **Configure OAuth Proxy**
3. Select an MCP proxy
4. Configure:
   - **Mode**: `upstream` (forward to external provider)
   - **Provider**: Select your OAuth provider (GitHub, Google, etc.)
   - **Allowed Redirects**: `http://localhost:8888/callback`, `cursor://oauth-callback`
   - **PKCE Forwarding**: Enable (recommended)
5. **Save** and **Start** the proxy

### 3. Run Example

**Python:**
```bash
# Basic usage
python3 examples/oauth-proxy-examples/python/oauth_proxy_test.py --target http://localhost:8093 --proxy-id 9

# With custom scopes (GitHub)
python3 examples/oauth-proxy-examples/python/oauth_proxy_test.py \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --scope "read:user user:email"

# With custom scopes (Google)
python3 examples/oauth-proxy-examples/python/oauth_proxy_test.py \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --scope "openid profile email"
```

**TypeScript:**
```bash
# With Node.js
npx ts-node examples/oauth-proxy-examples/typescript/oauth-proxy-test.ts --target http://localhost:8093 --proxy-id 9

# With Bun
bun run examples/oauth-proxy-examples/typescript/oauth-proxy-test.ts --target http://localhost:8093 --proxy-id 9
```

### 4. Complete Authorization Flow

The examples will:
1. ✅ Register a new OAuth client (DCR)
2. ✅ Generate PKCE parameters
3. ✅ Build authorization URL
4. 📋 Display URL for you to open in browser
5. ⏳ Wait for you to complete OAuth authentication
6. 📋 Prompt you to enter the authorization code
7. ✅ Exchange code for access token
8. ✅ Display access token for use in API requests

**Manual Steps:**
1. Copy the authorization URL from terminal
2. Open URL in browser
3. Complete OAuth authentication (login, consent, etc.)
4. After redirect, copy the `code` parameter from callback URL:
   ```
   http://localhost:8888/callback?code=AUTHORIZATION_CODE&state=...
   ```
5. Paste authorization code into terminal when prompted

## OAuth Scopes by Provider

Different OAuth providers require different scopes:

| Provider | Example Scopes | Purpose |
|----------|---------------|---------|
| **GitHub** | `read:user user:email` | Read user profile and email |
| **Google** | `openid profile email` | OpenID Connect + profile |
| **Azure AD** | `openid profile email` | OpenID Connect + profile |
| **Okta** | `openid profile email` | OpenID Connect + profile |
| **Custom** | Provider-specific | Check provider documentation |

**Finding Provider Scopes:**
1. Navigate to **OAuth** > **Providers** in Gateway UI
2. View your configured provider
3. Check **Available Scopes** section
4. Use scopes in `--scope` argument

## Advanced Testing

For production-ready testing with automated callback handling:

**Complete Test Suite:**
```bash
cd examples/oauth-proxy-tests/
python3 test_oauth_proxy_gateway_llm.py \
  --target http://localhost:8093 \
  --proxy-id 9 \
  --scope "read:user user:email"
```

**Features:**
- ✅ Automatic callback server (port 8888)
- ✅ Browser automation (opens auth URL automatically)
- ✅ Automatic authorization code capture
- ✅ LLM proxy request testing
- ✅ Hybrid authentication testing (OAuth + API Keys)
- ✅ Token refresh flow
- ✅ Comprehensive error handling

## Using as a Library

Both examples export reusable functions:

**Python:**
```python
from examples.python.oauth_proxy_test import (
    generate_pkce,
    register_client,
    build_authorization_url,
    exchange_code_for_token
)

# Generate PKCE
verifier, challenge, method = generate_pkce()

# Register client
client = register_client(
    "http://localhost:8080",
    proxy_id=9,
    redirect_uris=["http://localhost:8888/callback"],
    scopes="read:user user:email"
)

# Build auth URL
auth_url = build_authorization_url(
    client["authorization_url"],
    client["client_id"],
    "http://localhost:8888/callback",
    challenge,
    method,
    scopes="read:user user:email"
)

# Exchange code for token
token = exchange_code_for_token(
    client["token_url"],
    client["client_id"],
    client["client_secret"],
    authorization_code,
    "http://localhost:8888/callback",
    verifier
)
```

**TypeScript:**
```typescript
import {
  generatePKCE,
  registerClient,
  buildAuthorizationUrl,
  exchangeCodeForToken
} from './examples/oauth-proxy-examples/typescript/oauth-proxy-test';

// Generate PKCE
const pkce = generatePKCE();

// Register client
const client = await registerClient(
  'http://localhost:8080',
  9,
  ['http://localhost:8888/callback'],
  'My OAuth Client',
  'read:user user:email'
);

// Build auth URL
const authUrl = buildAuthorizationUrl(
  client.authorization_url,
  client.client_id,
  'http://localhost:8888/callback',
  pkce.code_challenge,
  pkce.code_challenge_method,
  undefined,
  'read:user user:email'
);

// Exchange code for token
const token = await exchangeCodeForToken(
  client.token_url,
  client.client_id,
  client.client_secret,
  authorizationCode,
  'http://localhost:8888/callback',
  pkce.code_verifier
);
```

## Troubleshooting

### "Client registration failed"
- ✅ Verify Gateway is running (`http://localhost:8080`)
- ✅ Verify OAuth Proxy is configured for the target proxy
- ✅ Check `--proxy-id` matches your OAuth Proxy-enabled proxy
- ✅ Check logs: `docker logs unified-admin` or terminal output

### "Authorization failed"
- ✅ Verify OAuth Provider is configured correctly
- ✅ Check redirect URIs match (case-sensitive)
- ✅ Verify scopes are valid for your provider
- ✅ Check provider credentials (Client ID, Client Secret)

### "Token exchange failed"
- ✅ Verify authorization code is correct (copy entire value)
- ✅ Verify code hasn't expired (use within 60 seconds)
- ✅ Check PKCE verifier matches original challenge
- ✅ Verify redirect URI matches original request exactly

### "Invalid redirect_uri"
- ✅ Add `http://localhost:8888/callback` to allowed redirects
- ✅ Check for trailing slashes (must match exactly)
- ✅ Verify protocol (http vs https)

## Next Steps

- **Production Integration**: See `examples/oauth-proxy-tests/` for complete examples

## Support

For questions or issues:
- 📖 Documentation site
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
