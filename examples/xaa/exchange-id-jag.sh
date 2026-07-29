#!/bin/bash

# Cross App Access (XAA): exchange an ID-JAG for a gateway access token, then use
# it. This is steps 3 and 4 of the profile. Step 1 (OIDC login) and step 2 (token
# exchange at your identity provider) happen at the IdP and produce the ID-JAG
# this script takes as input.
#
# The gateway is the Resource Authorization Server here: it validates the grant
# your IdP minted and issues an access token for the proxy.

set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
PROXY_URL="${PROXY_URL:-http://localhost:9101}"
PROXY_ID="${PROXY_ID:-}"
CLIENT_ID="${XAA_CLIENT_ID:-}"
CLIENT_SECRET="${XAA_CLIENT_SECRET:-}"
SCOPE="${XAA_SCOPE:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# decode_jwt_claim prints one claim from a JWT payload without verifying anything.
# Used for diagnostics only: never make an authorization decision on an unverified
# token, which is the entire reason the exchange below exists.
decode_jwt_claim() {
    local token=$1 claim=$2
    local payload
    payload=$(echo "$token" | cut -d. -f2)
    # base64url to base64, then pad to a multiple of 4
    payload=$(echo "$payload" | tr '_-' '/+')
    while [ $(( ${#payload} % 4 )) -ne 0 ]; do payload="${payload}="; done
    echo "$payload" | base64 -d 2>/dev/null | jq -r ".${claim} // empty"
}

# discover finds the token endpoint the way a client should: from the proxy's
# RFC 8414 metadata, rather than by assuming a path.
discover() {
    print_info "Discovering the token endpoint from ${PROXY_URL}"

    local metadata
    if ! metadata=$(curl -sf "${PROXY_URL}/.well-known/oauth-authorization-server"); then
        print_error "No OAuth metadata at ${PROXY_URL}. Is the proxy running, and is XAA enabled on it?"
        exit 1
    fi

    local profiles
    profiles=$(echo "$metadata" | jq -r '.authorization_grant_profiles_supported // [] | join(",")')
    if [[ "$profiles" != *"id-jag"* ]]; then
        print_warning "This proxy does not advertise the id-jag grant profile. XAA may not be enabled on it."
    fi

    echo "$metadata" | jq -r '.token_endpoint'
}

# exchange performs step 3: the RFC 7523 JWT bearer grant.
exchange() {
    local id_jag=$1 token_endpoint=$2

    print_info "Exchanging the ID-JAG at ${token_endpoint}"

    local form=(
        --data-urlencode "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer"
        --data-urlencode "assertion=${id_jag}"
        --data-urlencode "client_id=${CLIENT_ID}"
        --data-urlencode "client_secret=${CLIENT_SECRET}"
    )
    # Scope is optional. When sent it can only narrow what the grant already
    # carries; asking for more than the IdP authorized is refused, not widened.
    if [ -n "$SCOPE" ]; then
        form+=(--data-urlencode "scope=${SCOPE}")
    fi

    local response http_code body
    response=$(curl -s -w '\n%{http_code}' -X POST "$token_endpoint" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        "${form[@]}")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" != "200" ]; then
        local err desc
        err=$(echo "$body" | jq -r '.error // "unknown"')
        desc=$(echo "$body" | jq -r '.error_description // ""')
        print_error "Exchange failed (HTTP ${http_code}): ${err}"
        [ -n "$desc" ] && print_error "  ${desc}"
        case "$err" in
            invalid_grant)
                print_error "  The grant was rejected. Common causes: its aud is not this gateway's"
                print_error "  issuer URL, it has expired (they live ~5 minutes), or it has already"
                print_error "  been redeemed. Each ID-JAG is single use; get a fresh one from the IdP."
                ;;
            unauthorized_client)
                print_error "  This client has no mapping on this proxy. Add one under the proxy's"
                print_error "  Cross App Access settings, mapping the IdP client ID to a client ID here."
                ;;
            invalid_client)
                print_error "  Client authentication failed. Check XAA_CLIENT_ID and XAA_CLIENT_SECRET"
                print_error "  against the mapping. The secret is shown once, when the mapping is created."
                ;;
            insufficient_user_authentication)
                print_error "  The grant is valid but the user did not authenticate strongly or recently"
                print_error "  enough for this proxy. Send them back to the IdP to step up."
                ;;
        esac
        exit 1
    fi

    echo "$body" | jq -r '.access_token'
}

# call_resource performs step 4: present the access token to the proxy.
call_resource() {
    local access_token=$1

    print_info "Calling the proxy with the access token"

    local response http_code body
    response=$(curl -s -w '\n%{http_code}' -X POST "${PROXY_URL}/mcp" \
        -H "Authorization: Bearer ${access_token}" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}')
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" != "200" ]; then
        print_error "Resource call failed (HTTP ${http_code})"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        if [ "$http_code" = "401" ]; then
            print_error "  A 401 here usually means the token was issued for a different proxy."
            print_error "  Access tokens carry a proxy_id claim and are refused elsewhere."
        fi
        exit 1
    fi

    print_info "Resource responded:"
    echo "$body" | jq . 2>/dev/null || echo "$body"
}

usage() {
    cat <<'USAGE'
Usage: exchange-id-jag.sh <command> [args]

Commands:
  discover                 Print the token endpoint this proxy advertises
  exchange <id-jag>        Exchange an ID-JAG for an access token, print the token
  run <id-jag>             Exchange, then call the proxy with the result (steps 3 and 4)
  inspect <token>          Print the interesting claims of an ID-JAG or access token

Environment:
  GATEWAY_URL         Gateway base URL      (default: http://localhost:8080)
  PROXY_URL           Proxy base URL        (default: http://localhost:9101)
  PROXY_ID            Proxy config ID, only needed for the gateway-API endpoint
  XAA_CLIENT_ID       Client ID at Resource AS, from the client mapping
  XAA_CLIENT_SECRET   Client secret issued when the mapping was created
  XAA_SCOPE           Optional scope to narrow the request

Examples:
  export XAA_CLIENT_ID=mcp-client-at-gateway
  export XAA_CLIENT_SECRET=<secret shown when the mapping was created>
  ./exchange-id-jag.sh run "$ID_JAG"

Getting an ID-JAG is step 2 and happens at your identity provider, not here:

  curl -X POST https://your-okta-tenant/oauth2/v1/token \
    -d grant_type=urn:ietf:params:oauth:grant-type:token-exchange \
    -d requested_token_type=urn:ietf:params:oauth:token-type:id-jag \
    -d subject_token_type=urn:ietf:params:oauth:token-type:id_token \
    -d subject_token=<the ID token from step 1> \
    -d audience=<your GATEWAY_ISSUER_URL> \
    -d resource=<the API being called> \
    -d client_id=<IdP client ID> -d client_secret=<IdP client secret>
USAGE
    exit 1
}

main() {
    command -v jq >/dev/null 2>&1 || { print_error "jq is required but not installed."; exit 1; }

    case "${1:-}" in
        discover)
            discover
            ;;
        exchange)
            [ -n "${2:-}" ] || usage
            [ -n "$CLIENT_ID" ] || { print_error "XAA_CLIENT_ID is required"; exit 1; }
            [ -n "$CLIENT_SECRET" ] || { print_error "XAA_CLIENT_SECRET is required"; exit 1; }
            exchange "$2" "$(discover)"
            ;;
        run)
            [ -n "${2:-}" ] || usage
            [ -n "$CLIENT_ID" ] || { print_error "XAA_CLIENT_ID is required"; exit 1; }
            [ -n "$CLIENT_SECRET" ] || { print_error "XAA_CLIENT_SECRET is required"; exit 1; }
            token=$(exchange "$2" "$(discover)")
            print_info "Access token issued (aud=$(decode_jwt_claim "$token" aud), proxy_id=$(decode_jwt_claim "$token" proxy_id))"
            call_resource "$token"
            ;;
        inspect)
            [ -n "${2:-}" ] || usage
            for claim in iss sub aud client_id scope resource jti exp proxy_id token_use; do
                value=$(decode_jwt_claim "$2" "$claim")
                [ -n "$value" ] && printf '  %-12s %s\n' "$claim" "$value"
            done
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"
