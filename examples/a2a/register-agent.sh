#!/bin/bash

# A2A Agent Registration Example Script
# This script demonstrates how to register an A2A agent in the AI Security Gateway

set -e

# Configuration
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to login and get JWT token
login() {
    print_info "Logging in as admin user..."
    
    RESPONSE=$(curl -s -X POST "${GATEWAY_URL}/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"${ADMIN_USERNAME}\",
            \"password\": \"${ADMIN_PASSWORD}\"
        }")
    
    if [ $? -ne 0 ]; then
        print_error "Failed to connect to Gateway at ${GATEWAY_URL}"
        exit 1
    fi
    
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    
    if [ "$SUCCESS" != "true" ]; then
        ERROR=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"')
        print_error "Login failed: $ERROR"
        exit 1
    fi
    
    TOKEN=$(echo "$RESPONSE" | jq -r '.data.token // empty')
    
    if [ -z "$TOKEN" ]; then
        print_error "No token received from login"
        exit 1
    fi
    
    print_info "Login successful"
    echo "$TOKEN"
}

# Function to register agent via URL
register_agent_url() {
    local TOKEN=$1
    local AGENT_NAME=$2
    local AGENT_URL=$3
    
    print_info "Registering agent '${AGENT_NAME}' from URL: ${AGENT_URL}"
    
    RESPONSE=$(curl -s -X POST "${GATEWAY_URL}/api/v1/agents" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN}" \
        -d "{
            \"name\": \"${AGENT_NAME}\",
            \"url\": \"${AGENT_URL}\"
        }")
    
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    
    if [ "$SUCCESS" != "true" ]; then
        ERROR=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"')
        print_error "Registration failed: $ERROR"
        return 1
    fi
    
    AGENT_ID=$(echo "$RESPONSE" | jq -r '.data.id // empty')
    AGENT_NAME_RESP=$(echo "$RESPONSE" | jq -r '.data.name // empty')
    
    print_info "Agent registered successfully!"
    print_info "Agent ID: ${AGENT_ID}"
    print_info "Agent Name: ${AGENT_NAME_RESP}"
    
    echo "$AGENT_ID"
}

# Function to register agent via AgentCard JSON
register_agent_json() {
    local TOKEN=$1
    local AGENT_NAME=$2
    local AGENT_CARD_FILE=$3
    
    if [ ! -f "$AGENT_CARD_FILE" ]; then
        print_error "AgentCard file not found: ${AGENT_CARD_FILE}"
        return 1
    fi
    
    print_info "Registering agent '${AGENT_NAME}' from AgentCard JSON file: ${AGENT_CARD_FILE}"
    
    AGENT_CARD_JSON=$(cat "$AGENT_CARD_FILE" | jq -c .)
    
    RESPONSE=$(curl -s -X POST "${GATEWAY_URL}/api/v1/agents" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN}" \
        -d "{
            \"name\": \"${AGENT_NAME}\",
            \"agent_card\": ${AGENT_CARD_JSON}
        }")
    
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    
    if [ "$SUCCESS" != "true" ]; then
        ERROR=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"')
        print_error "Registration failed: $ERROR"
        return 1
    fi
    
    AGENT_ID=$(echo "$RESPONSE" | jq -r '.data.id // empty')
    AGENT_NAME_RESP=$(echo "$RESPONSE" | jq -r '.data.name // empty')
    
    print_info "Agent registered successfully!"
    print_info "Agent ID: ${AGENT_ID}"
    print_info "Agent Name: ${AGENT_NAME_RESP}"
    
    echo "$AGENT_ID"
}

# Function to list agents
list_agents() {
    local TOKEN=$1
    
    print_info "Listing registered agents..."
    
    RESPONSE=$(curl -s -X GET "${GATEWAY_URL}/api/v1/agents" \
        -H "Authorization: Bearer ${TOKEN}")
    
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    
    if [ "$SUCCESS" != "true" ]; then
        ERROR=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"')
        print_error "Failed to list agents: $ERROR"
        return 1
    fi
    
    echo "$RESPONSE" | jq -r '.data.agents[] | "\(.id) - \(.name) (\(.status))"'
}

# Main script
main() {
    print_info "A2A Agent Registration Script"
    print_info "Gateway URL: ${GATEWAY_URL}"
    echo ""
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Please install jq first."
        exit 1
    fi
    
    # Login
    TOKEN=$(login)
    
    # Parse command line arguments
    case "${1:-}" in
        register-url)
            if [ -z "$2" ] || [ -z "$3" ]; then
                print_error "Usage: $0 register-url <agent-name> <agent-url>"
                exit 1
            fi
            register_agent_url "$TOKEN" "$2" "$3"
            ;;
        register-json)
            if [ -z "$2" ] || [ -z "$3" ]; then
                print_error "Usage: $0 register-json <agent-name> <agentcard-file>"
                exit 1
            fi
            register_agent_json "$TOKEN" "$2" "$3"
            ;;
        list)
            list_agents "$TOKEN"
            ;;
        *)
            echo "Usage: $0 {register-url|register-json|list} [args...]"
            echo ""
            echo "Commands:"
            echo "  register-url <name> <url>    Register agent via URL (auto-discovery)"
            echo "  register-json <name> <file>  Register agent via AgentCard JSON file"
            echo "  list                         List all registered agents"
            echo ""
            echo "Environment Variables:"
            echo "  GATEWAY_URL       Gateway URL (default: http://localhost:8080)"
            echo "  ADMIN_USERNAME    Admin username (default: admin)"
            echo "  ADMIN_PASSWORD   Admin password (default: admin)"
            echo ""
            echo "Examples:"
            echo "  $0 register-url echo-agent http://127.0.0.1:9001"
            echo "  $0 register-json my-agent ./agent-card.json"
            echo "  $0 list"
            exit 1
            ;;
    esac
}

main "$@"

