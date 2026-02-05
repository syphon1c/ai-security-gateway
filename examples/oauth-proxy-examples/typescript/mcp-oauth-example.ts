#!/usr/bin/env ts-node
/**
 * Complete OAuth + MCP Integration Example (TypeScript)
 * ======================================================
 *
 * This script demonstrates how to:
 * 1. Authenticate with OAuth (Google, etc.)
 * 2. Get a session token
 * 3. Use the token to call MCP tools
 *
 * Usage:
 *     npm install axios open readline
 *     ts-node mcp-oauth-example.ts
 *
 * Or compile and run:
 *     tsc mcp-oauth-example.ts
 *     node mcp-oauth-example.js
 */

import axios, { AxiosError } from 'axios';
import open from 'open';
import * as readline from 'readline';
import * as fs from 'fs';

// Configuration
const GATEWAY_URL = 'http://localhost:8080';
const MCP_PROXY_URL = 'http://localhost:8040';
const PROVIDER_ID = 2; // Change to your OAuth provider ID

interface OAuthResponse {
  success: boolean;
  data: {
    authorization_url: string;
    state: string;
    session_token?: string;
    user_email?: string;
    user_name?: string;
  };
  error?: string;
  message?: string;
}

interface MCPTool {
  name: string;
  description: string;
  inputSchema: any;
}

interface MCPResponse {
  jsonrpc: string;
  id: number;
  result?: {
    tools?: MCPTool[];
    content?: any[];
  };
  error?: {
    code: number;
    message: string;
  };
}

function printHeader(text: string): void {
  console.log('\n' + '='.repeat(60));
  console.log(`  ${text}`);
  console.log('='.repeat(60));
}

async function prompt(question: string): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}

async function getOAuthToken(): Promise<string> {
  printHeader('🔐 Step 1: OAuth Authentication');

  console.log(`\n📡 Starting OAuth flow with provider ${PROVIDER_ID}...`);

  try {
    // Start OAuth flow
    const response = await axios.post<OAuthResponse>(
      `${GATEWAY_URL}/api/v1/oauth/authorize/${PROVIDER_ID}`
    );

    if (!response.data.success) {
      console.error(`❌ Error: ${response.data.error || 'Unknown error'}`);
      process.exit(1);
    }

    const { authorization_url, state } = response.data.data;

    console.log('✅ OAuth flow started successfully');
    console.log(`📋 State: ${state}`);

    // Open browser for user to login
    console.log('\n🌐 Opening browser for OAuth login...');
    await open(authorization_url);

    console.log('\n' + '─'.repeat(60));
    console.log('👤 Please complete the login in your browser');
    console.log('📋 After login, you\'ll be redirected to a URL');
    console.log('📋 Copy the ENTIRE redirect URL and paste it below');
    console.log('─'.repeat(60));

    const redirectUrl = await prompt('\n🔗 Paste redirect URL here: ');

    if (!redirectUrl.trim()) {
      console.error('❌ No URL provided');
      process.exit(1);
    }

    // Complete OAuth flow
    console.log('\n🔄 Completing OAuth flow...');
    const callbackResponse = await axios.get<OAuthResponse>(redirectUrl);

    if (!callbackResponse.data.success) {
      console.error(`❌ OAuth callback failed: ${callbackResponse.data.message}`);
      process.exit(1);
    }

    const {
      session_token,
      user_email,
      user_name,
    } = callbackResponse.data.data;

    if (!session_token) {
      console.error('❌ No session token received');
      process.exit(1);
    }

    console.log('\n✅ OAuth authentication successful!');
    console.log(`👤 Logged in as: ${user_name} (${user_email})`);
    console.log(`🔑 Session token: ${session_token.substring(0, 30)}...`);

    return session_token;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error(`\n❌ Network error: ${error.message}`);
    } else {
      console.error(`\n❌ Unexpected error: ${error}`);
    }
    process.exit(1);
  }
}

async function listMCPTools(sessionToken: string): Promise<MCPTool[]> {
  printHeader('🔧 Step 2: List MCP Tools');

  console.log(`\n📡 Connecting to MCP proxy at ${MCP_PROXY_URL}...`);

  const headers = {
    'Content-Type': 'application/json',
    'X-Session-Token': sessionToken,
  };

  const mcpRequest = {
    jsonrpc: '2.0',
    method: 'tools/list',
    id: 1,
  };

  try {
    const response = await axios.post<MCPResponse>(
      `${MCP_PROXY_URL}/mcp/tools/list`,
      mcpRequest,
      { headers }
    );

    if (!response.data.result?.tools) {
      console.error('❌ Unexpected response format');
      return [];
    }

    const tools = response.data.result.tools;

    console.log(`\n✅ Found ${tools.length} MCP tools:\n`);

    tools.forEach((tool, i) => {
      console.log(`  ${i + 1}. ${tool.name}`);
      console.log(`     📝 ${tool.description}`);
      if (i < tools.length - 1) {
        console.log();
      }
    });

    return tools;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        console.error('❌ Authentication failed!');
        console.error('   Check that:');
        console.error('   1. Your session token is valid');
        console.error('   2. The proxy has OAuth enabled');
        console.error('   3. You\'re using the correct provider ID');
      } else {
        console.error(`\n❌ Error calling MCP proxy: ${error.message}`);
      }
    } else {
      console.error(`\n❌ Unexpected error: ${error}`);
    }
    return [];
  }
}

async function callMCPTool(
  sessionToken: string,
  toolName: string,
  args: Record<string, any> = {}
): Promise<void> {
  printHeader(`⚡ Step 3: Call MCP Tool '${toolName}'`);

  const headers = {
    'Content-Type': 'application/json',
    'X-Session-Token': sessionToken,
  };

  const mcpRequest = {
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: args,
    },
    id: 2,
  };

  console.log(`\n📡 Calling tool '${toolName}'...`);

  try {
    const response = await axios.post<MCPResponse>(
      `${MCP_PROXY_URL}/mcp/tools/call`,
      mcpRequest,
      { headers }
    );

    if (response.data.result) {
      console.log('\n✅ Tool executed successfully!');
      console.log('\n📊 Result:');
      console.log(JSON.stringify(response.data.result, null, 2));
    } else if (response.data.error) {
      console.log('\n⚠️  Tool returned error:');
      console.log(`   ${response.data.error.message}`);
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error(`\n❌ Error calling tool: ${error.message}`);
    } else {
      console.error(`\n❌ Unexpected error: ${error}`);
    }
  }
}

function saveToken(sessionToken: string): void {
  try {
    fs.writeFileSync('.session_token', sessionToken);
    console.log('\n💾 Token saved to .session_token file');
    console.log('   Reuse it with: export SESSION_TOKEN=$(cat .session_token)');
  } catch (error) {
    console.error(`\n⚠️  Could not save token: ${error}`);
  }
}

async function main(): Promise<void> {
  printHeader('🚀 MCP OAuth Integration Example');
  console.log('\nThis script will:');
  console.log('  1. Authenticate you via OAuth');
  console.log('  2. Get a session token');
  console.log('  3. List available MCP tools');
  console.log('  4. (Optional) Call a tool');

  await prompt('\nPress Enter to start...');

  // Step 1: Get OAuth token
  let sessionToken: string;
  try {
    sessionToken = await getOAuthToken();
  } catch (error) {
    console.error(`\n❌ OAuth failed: ${error}`);
    process.exit(1);
  }

  // Step 2: List MCP tools
  let tools: MCPTool[];
  try {
    tools = await listMCPTools(sessionToken);
  } catch (error) {
    console.error(`\n❌ Failed to list tools: ${error}`);
    process.exit(1);
  }

  // Step 3: Optionally call a tool
  if (tools.length > 0) {
    console.log('\n' + '─'.repeat(60));
    const choice = await prompt('\n🔧 Want to call a tool? (y/N): ');

    if (choice.trim().toLowerCase() === 'y') {
      const toolName = await prompt('Enter tool name: ');
      await callMCPTool(sessionToken, toolName.trim());
    }
  }

  // Save token for reuse
  saveToken(sessionToken);

  // Success summary
  printHeader('✅ SUCCESS!');
  console.log('\n🎉 You\'ve successfully:');
  console.log('   ✓ Authenticated with OAuth');
  console.log('   ✓ Retrieved a session token');
  console.log('   ✓ Called MCP tools with user attribution');
  console.log('\n📝 All your requests are logged with your identity!');
  console.log(`   Check the audit logs at: ${GATEWAY_URL}/audit-logs`);

  console.log('\n💡 Next steps:');
  console.log('   • Save the token and reuse it in your scripts');
  console.log('   • Build your own MCP client with this pattern');
  console.log('   • Check token expiry and implement refresh logic');
  console.log();
}

// Run the example
main().catch((error) => {
  console.error('\n❌ Fatal error:', error);
  process.exit(1);
});
