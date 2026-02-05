#!/bin/bash

# Example: Invoke an A2A agent via Gateway JSON-RPC with streaming
# This demonstrates how to use the A2A protocol to invoke agents with streaming responses

set -e

# Configuration
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
API_KEY="${API_KEY:-}"
AGENT_ID="${AGENT_ID:-1}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== A2A Agent Invocation (Streaming) via Gateway JSON-RPC ===${NC}\n"

# Check if API key is provided
if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}Warning: API_KEY not set. Using unauthenticated request (may fail for invocation).${NC}"
    echo "Set API_KEY environment variable to authenticate."
    echo ""
fi

# Prepare JSON-RPC request
JSON_RPC_REQUEST=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "agents/invoke",
  "params": {
    "agent_id": ${AGENT_ID},
    "message": {
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "Hello, agent! Please respond with a streaming message."
        }
      ]
    },
    "streaming": true
  }
}
EOF
)

echo -e "${GREEN}Request:${NC}"
echo "$JSON_RPC_REQUEST" | jq '.'
echo ""

# Make streaming request
echo -e "${GREEN}Streaming Response (SSE):${NC}\n"

if [ -z "$API_KEY" ]; then
    curl -X POST "${GATEWAY_URL}/a2a/v1" \
        -H "Content-Type: application/json" \
        -H "Accept: text/event-stream" \
        -d "$JSON_RPC_REQUEST" \
        --no-buffer \
        -N
else
    curl -X POST "${GATEWAY_URL}/a2a/v1" \
        -H "Content-Type: application/json" \
        -H "Accept: text/event-stream" \
        -H "X-API-Key: ${API_KEY}" \
        -d "$JSON_RPC_REQUEST" \
        --no-buffer \
        -N
fi

echo -e "\n${BLUE}=== Streaming Complete ===${NC}"

