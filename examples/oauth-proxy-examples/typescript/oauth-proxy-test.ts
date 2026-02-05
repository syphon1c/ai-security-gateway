/**
 * OAuth Proxy Testing Example - TypeScript
 * 
 * This script demonstrates how to test OAuth Proxy functionality using the Gateway API.
 * It covers the complete OAuth 2.1 flow with Dynamic Client Registration (DCR) and PKCE.
 * 
 * Features:
 * - Dynamic Client Registration (DCR)
 * - PKCE code verifier and challenge generation
 * - OAuth authorization flow
 * - Token exchange (authorization code for access token)
 * - Using OAuth tokens to access protected resources
 * 
 * Prerequisites:
 * - Node.js 18+ or Bun runtime
 * - Gateway running on http://localhost:8080
 * - OAuth Proxy configured for a target proxy
 * 
 * Usage:
 *   # With Node.js
 *   npx ts-node oauth-proxy-test.ts --target http://localhost:8093 --proxy-id 9
 * 
 *   # With Bun
 *   bun run oauth-proxy-test.ts --target http://localhost:8093 --proxy-id 9
 */

import { randomBytes, createHash } from 'crypto';

/**
 * HTTP Response type
 */
interface HttpResponse<T = any> {
  data: T;
  status: number;
}

/**
 * DCR Response from OAuth Proxy
 */
interface DCRResponse {
  client_id: string;
  client_secret: string;
  redirect_uris: string[];
  authorization_url: string;
  token_url: string;
  introspection_url?: string;
  revocation_url?: string;
}

/**
 * OAuth Token Response
 */
interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope?: string;
}

/**
 * Make HTTP request
 */
async function makeRequest<T = any>(
  method: string,
  url: string,
  headers: Record<string, string> = {},
  body?: any
): Promise<HttpResponse<T>> {
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers
    }
  };

  if (body) {
    if (headers['Content-Type'] === 'application/x-www-form-urlencoded') {
      options.body = new URLSearchParams(body).toString();
    } else {
      options.body = JSON.stringify(body);
    }
  }

  const response = await fetch(url, options);
  const data = await response.json();
  
  return {
    data,
    status: response.status
  };
}

/**
 * Generate PKCE (Proof Key for Code Exchange) parameters
 * 
 * PKCE adds security to the OAuth flow by preventing authorization code interception.
 * Uses SHA256 method as required by OAuth 2.1.
 * 
 * @returns Object containing code_verifier, code_challenge, and code_challenge_method
 * 
 * @example
 * ```ts
 * const pkce = generatePKCE();
 * console.log(pkce.code_verifier);   // Random 43-128 character string
 * console.log(pkce.code_challenge);  // SHA256 hash of verifier
 * console.log(pkce.code_challenge_method); // "S256"
 * ```
 */
function generatePKCE(): {
  code_verifier: string;
  code_challenge: string;
  code_challenge_method: string;
} {
  // Generate code verifier: 43-128 characters, base64url encoded random bytes
  const verifierBytes = randomBytes(32);
  const code_verifier = verifierBytes
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');

  // Generate code challenge: SHA256 hash of verifier
  const challengeBytes = createHash('sha256')
    .update(code_verifier)
    .digest();
  const code_challenge = challengeBytes
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');

  return {
    code_verifier,
    code_challenge,
    code_challenge_method: 'S256'
  };
}

/**
 * Register a new OAuth client via Dynamic Client Registration (DCR)
 * 
 * @param gatewayUrl - Gateway API base URL (e.g., http://localhost:8080)
 * @param proxyId - ID of the OAuth Proxy-enabled proxy
 * @param redirectUris - List of allowed redirect URIs
 * @param clientName - Human-readable client name
 * @param scopes - OAuth scopes to request (optional, provider-specific)
 * @returns DCR response containing client_id, client_secret, and endpoint URLs
 * 
 * @example
 * ```ts
 * const client = await registerClient(
 *   'http://localhost:8080',
 *   9,
 *   ['http://localhost:8888/callback'],
 *   'My OAuth Client',
 *   'read:user user:email'
 * );
 * 
 * if (client) {
 *   console.log(`Client ID: ${client.client_id}`);
 *   console.log(`Client Secret: ${client.client_secret}`);
 *   console.log(`Authorization URL: ${client.authorization_url}`);
 * }
 * ```
 */
async function registerClient(
  gatewayUrl: string,
  proxyId: number,
  redirectUris: string[],
  clientName: string = 'Test OAuth Client',
  scopes: string = ''
): Promise<DCRResponse | null> {
  const url = `${gatewayUrl.replace(/\/$/, '')}/api/v1/oauth-proxy/${proxyId}/register`;
  
  const payload: any = {
    redirect_uris: redirectUris,
    client_name: clientName,
    token_endpoint_auth_method: 'client_secret_post',
    grant_types: ['authorization_code', 'refresh_token'],
    response_types: ['code']
  };

  if (scopes) {
    payload.scope = scopes;
  }

  try {
    const response = await makeRequest<DCRResponse>('POST', url, {}, payload);
    
    if (response.status === 200 || response.status === 201) {
      console.log(`✅ Client registered: ${response.data.client_id}`);
      return response.data;
    } else {
      console.error(`❌ Registration failed (${response.status}):`, response.data);
      return null;
    }
  } catch (error) {
    console.error('❌ Registration error:', error);
    return null;
  }
}

/**
 * Build OAuth authorization URL with PKCE parameters
 * 
 * @param authorizationEndpoint - OAuth authorization endpoint URL
 * @param clientId - OAuth client ID from DCR
 * @param redirectUri - Callback URI (must match registered URI)
 * @param codeChallenge - PKCE code challenge
 * @param codeChallengeMethod - PKCE method (always "S256" for OAuth 2.1)
 * @param state - Optional state parameter for CSRF protection
 * @param scopes - OAuth scopes to request
 * @returns Complete authorization URL to redirect user to
 * 
 * @example
 * ```ts
 * const pkce = generatePKCE();
 * const authUrl = buildAuthorizationUrl(
 *   'http://localhost:8093/oauth/authorize',
 *   'client_abc123',
 *   'http://localhost:8888/callback',
 *   pkce.code_challenge,
 *   pkce.code_challenge_method,
 *   undefined,
 *   'openid profile email'
 * );
 * 
 * // Direct user to authUrl in browser
 * console.log(`Visit: ${authUrl}`);
 * ```
 */
function buildAuthorizationUrl(
  authorizationEndpoint: string,
  clientId: string,
  redirectUri: string,
  codeChallenge: string,
  codeChallengeMethod: string = 'S256',
  state?: string,
  scopes: string = ''
): string {
  if (!state) {
    state = randomBytes(16)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }

  const params: Record<string, string> = {
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: 'code',
    state,
    code_challenge: codeChallenge,
    code_challenge_method: codeChallengeMethod
  };

  if (scopes) {
    params.scope = scopes;
  }

  const queryString = new URLSearchParams(params).toString();
  return `${authorizationEndpoint}?${queryString}`;
}

/**
 * Exchange authorization code for access token
 * 
 * @param tokenEndpoint - OAuth token endpoint URL
 * @param clientId - OAuth client ID
 * @param clientSecret - OAuth client secret
 * @param authorizationCode - Authorization code from callback
 * @param redirectUri - Redirect URI (must match original request)
 * @param codeVerifier - PKCE code verifier (proves you initiated the flow)
 * @returns Token response containing access_token, token_type, expires_in, etc.
 * 
 * @example
 * ```ts
 * const token = await exchangeCodeForToken(
 *   'http://localhost:8080/api/v1/oauth-proxy/9/token',
 *   clientId,
 *   clientSecret,
 *   'auth_code_abc123',
 *   'http://localhost:8888/callback',
 *   pkce.code_verifier
 * );
 * 
 * if (token) {
 *   const accessToken = token.access_token;
 *   // Use accessToken in Authorization header for API requests
 * }
 * ```
 */
async function exchangeCodeForToken(
  tokenEndpoint: string,
  clientId: string,
  clientSecret: string,
  authorizationCode: string,
  redirectUri: string,
  codeVerifier: string
): Promise<TokenResponse | null> {
  const data = {
    grant_type: 'authorization_code',
    code: authorizationCode,
    redirect_uri: redirectUri,
    client_id: clientId,
    client_secret: clientSecret,
    code_verifier: codeVerifier
  };

  const headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  };

  try {
    const response = await makeRequest<TokenResponse>(
      'POST',
      tokenEndpoint,
      headers,
      data
    );

    if (response.status === 200) {
      console.log('✅ Token exchange successful');
      console.log(`   Access Token: ${response.data.access_token.substring(0, 50)}...`);
      return response.data;
    } else {
      console.error(`❌ Token exchange failed (${response.status}):`, response.data);
      return null;
    }
  } catch (error) {
    console.error('❌ Token exchange error:', error);
    return null;
  }
}

/**
 * Main example demonstrating OAuth Proxy testing flow
 */
async function main() {
  const args = process.argv.slice(2);
  const targetIndex = args.indexOf('--target');
  const proxyIdIndex = args.indexOf('--proxy-id');
  const gatewayIndex = args.indexOf('--gateway');
  const scopeIndex = args.indexOf('--scope');

  if (targetIndex === -1 || proxyIdIndex === -1) {
    console.error('Usage: oauth-proxy-test.ts --target <url> --proxy-id <id> [--gateway <url>] [--scope <scopes>]');
    process.exit(1);
  }

  const targetUrl = args[targetIndex + 1];
  const proxyId = parseInt(args[proxyIdIndex + 1]);
  const gatewayUrl = gatewayIndex !== -1 ? args[gatewayIndex + 1] : 'http://localhost:8080';
  const scopes = scopeIndex !== -1 ? args[scopeIndex + 1] : '';

  console.log('='.repeat(70));
  console.log('OAuth Proxy Testing Example - TypeScript');
  console.log('='.repeat(70));
  console.log();

  // Step 1: Register OAuth client
  console.log('Step 1: Dynamic Client Registration (DCR)');
  console.log('-'.repeat(70));
  const client = await registerClient(
    gatewayUrl,
    proxyId,
    ['http://localhost:8888/callback'],
    'Example OAuth Client',
    scopes
  );

  if (!client) {
    console.log('\n❌ Failed to register client');
    process.exit(1);
  }

  const { client_id, client_secret, authorization_url, token_url } = client;
  console.log();

  // Step 2: Generate PKCE parameters
  console.log('Step 2: Generate PKCE Parameters');
  console.log('-'.repeat(70));
  const pkce = generatePKCE();
  console.log(`✅ Code Verifier: ${pkce.code_verifier.substring(0, 40)}...`);
  console.log(`✅ Code Challenge: ${pkce.code_challenge.substring(0, 40)}...`);
  console.log(`✅ Challenge Method: ${pkce.code_challenge_method}`);
  console.log();

  // Step 3: Build authorization URL
  console.log('Step 3: Build Authorization URL');
  console.log('-'.repeat(70));
  const authUrl = buildAuthorizationUrl(
    authorization_url,
    client_id,
    'http://localhost:8888/callback',
    pkce.code_challenge,
    pkce.code_challenge_method,
    undefined,
    scopes
  );
  console.log('✅ Authorization URL generated');
  console.log();
  console.log('🔗 Open this URL in your browser:');
  console.log(`   ${authUrl}`);
  console.log();

  // Step 4: Manual code entry (for simplicity)
  console.log('Step 4: Authorization & Token Exchange');
  console.log('-'.repeat(70));
  console.log('After authenticating in the browser, you\'ll receive an authorization code.');
  console.log('For automated callback handling, see: test/oauth-proxy-tests/test_oauth_proxy_gateway_llm.py');
  console.log();
  console.log('⚠️  Manual code entry not implemented in this example.');
  console.log();
  console.log('To complete the flow:');
  console.log('  1. Visit the authorization URL above');
  console.log('  2. Complete OAuth authentication');
  console.log('  3. Extract \'code\' parameter from callback URL');
  console.log('  4. Use exchangeCodeForToken() function with the code:');
  console.log();
  console.log('  const token = await exchangeCodeForToken(');
  console.log(`    '${token_url}',`);
  console.log(`    '${client_id}',`);
  console.log(`    '${client_secret}',`);
  console.log(`    'AUTHORIZATION_CODE_HERE',`);
  console.log(`    'http://localhost:8888/callback',`);
  console.log(`    '${pkce.code_verifier}'`);
  console.log('  );');
  console.log();
  console.log('  if (token) {');
  console.log('    console.log(`Access Token: ${token.access_token}`);');
  console.log('    // Use token.access_token in Authorization header');
  console.log('  }');
}

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}

// Export functions for use as library
export {
  generatePKCE,
  registerClient,
  buildAuthorizationUrl,
  exchangeCodeForToken,
  type DCRResponse,
  type TokenResponse
};
