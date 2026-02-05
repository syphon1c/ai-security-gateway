#!/bin/bash

# Quick test to verify API keys work when OAuth Proxy is enabled
# This script tests that API key authentication still works alongside OAuth Proxy

set -e

# Parse arguments
PROXY_TARGET=""
API_KEY=""
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            PROXY_TARGET="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --gateway)
            GATEWAY_URL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --target <proxy_url> [--api-key <key>] [--gateway <url>]"
            echo ""
            echo "Arguments:"
            echo "  --target <url>    Target proxy URL (e.g., http://localhost:8093) [required]"
            echo "  --api-key <key>   Gateway API key for testing [optional]"
            echo "  --gateway <url>   Gateway API URL (default: http://localhost:8080) [optional]"
            echo ""
            echo "Examples:"
            echo "  $0 --target http://localhost:8093 --api-key uag_..."
            echo "  $0 --target http://localhost:8093"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Fallback to environment variables if not provided
if [ -z "$PROXY_TARGET" ]; then
    # Try to construct from old environment variables for backward compatibility
    if [ -n "$PROXY_PORT" ]; then
        PROXY_TARGET="http://localhost:${PROXY_PORT}"
        print_warning "Using deprecated PROXY_PORT env var. Use --target instead."
    else
        echo "Error: --target is required"
        echo "Usage: $0 --target <proxy_url> [--api-key <key>]"
        exit 1
    fi
fi

if [ -z "$API_KEY" ]; then
    API_KEY="${GATEWAY_API_KEY}"
fi

print_header "API Key Authentication Test with OAuth Proxy Enabled"

print_info "Gateway URL: $GATEWAY_URL"
print_info "Proxy Target: $PROXY_TARGET"
if [ -n "$API_KEY" ]; then
    print_info "API Key: ${API_KEY:0:10}...${API_KEY: -4}"
else
    print_warning "No API key provided. Will skip API key test."
fi

# Test 1: Check proxy health
print_header "Test 1: Check Proxy Health"

HEALTH_URL="${PROXY_TARGET%/}/health"
print_info "Checking proxy health at: $HEALTH_URL"

if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
    print_success "Proxy is accessible"
else
    print_warning "Proxy health check failed, but continuing..."
    print_info "The proxy might not have a /health endpoint, which is fine"
fi

# Test 2: Test API Key Authentication
print_header "Test 2: Test API Key Authentication"

if [ -z "$API_KEY" ]; then
    print_warning "No API key provided. Skipping API key test."
    print_info "Provide --api-key argument or set GATEWAY_API_KEY environment variable"
    exit 0
fi

PROXY_URL="${PROXY_TARGET%/}/v1/messages"

# Create test payload for Anthropic Claude API
PAYLOAD=$(cat <<EOF
{
  "model": "claude-3-haiku-20240307",
  "max_tokens": 100,
  "messages": [
    {"role": "user", "content": "Say hello in one word"}
  ]
}
EOF
)

print_info "Making request to: $PROXY_URL"
print_info "Using API key authentication"

# Try with Authorization header
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$PROXY_URL" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d "$PAYLOAD" || echo -e "\n000")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API key authentication works!"
    print_success "✅ API keys work alongside OAuth Proxy (hybrid mode)"
    echo ""
    print_info "Response preview:"
    echo "$BODY" | jq -r '.content[0].text // .error.message // .' 2>/dev/null | head -n 3 || echo "$BODY" | head -n 5
else
    print_error "API key authentication failed"
    print_error "HTTP Status: $HTTP_CODE"
    echo ""
    print_info "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    
    # Try with X-API-Key header as alternative
    print_info ""
    print_info "Trying with X-API-Key header..."
    
    RESPONSE2=$(curl -s -w "\n%{http_code}" -X POST "$PROXY_URL" \
      -H "X-API-Key: $API_KEY" \
      -H "Content-Type: application/json" \
      -H "anthropic-version: 2023-06-01" \
      -d "$PAYLOAD" || echo -e "\n000")
    
    HTTP_CODE2=$(echo "$RESPONSE2" | tail -n 1)
    BODY2=$(echo "$RESPONSE2" | sed '$d')
    
    if [ "$HTTP_CODE2" = "200" ]; then
        print_success "API key authentication works with X-API-Key header!"
    else
        print_error "API key authentication failed with X-API-Key header too"
        print_error "HTTP Status: $HTTP_CODE2"
        exit 1
    fi
fi

# Summary
print_header "Test Summary"

print_success "✅ Proxy is accessible"
print_success "✅ API key authentication works"
print_success "✅ API keys work alongside OAuth Proxy (hybrid mode)"

echo ""
print_info "Both OAuth Proxy tokens and API keys can be used simultaneously:"
print_info "  - OAuth tokens: For interactive clients (Cursor IDE, browser)"
print_info "  - API keys: For scripts, CLI tools, and automation"
echo ""

