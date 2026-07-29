//go:build ignore

// Cross App Access (XAA) client: steps 3 and 4 of the profile.
//
// Step 1 (OIDC login) and step 2 (RFC 8693 token exchange at the identity
// provider) produce an ID-JAG. Those happen at your IdP. This program takes the
// resulting grant, exchanges it at the gateway for an access token, and calls the
// proxy with that token.
//
// Run with:
//
//	export XAA_CLIENT_ID=... XAA_CLIENT_SECRET=...
//	go run xaa-client.go -proxy http://localhost:9101 -id-jag "$ID_JAG"
//
// The build tag keeps it out of the module build; it is a standalone example.
package main

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

const (
	// The profile's grant type. The assertion is the ID-JAG.
	jwtBearerGrantType = "urn:ietf:params:oauth:grant-type:jwt-bearer"
	// Advertised by a Resource AS that implements Cross App Access.
	idJAGGrantProfile = "urn:ietf:params:oauth:grant-profile:id-jag"
)

type authServerMetadata struct {
	Issuer                 string   `json:"issuer"`
	TokenEndpoint          string   `json:"token_endpoint"`
	GrantTypesSupported    []string `json:"grant_types_supported"`
	GrantProfilesSupported []string `json:"authorization_grant_profiles_supported"`
}

type tokenResponse struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresIn   int    `json:"expires_in"`
	Scope       string `json:"scope"`
}

type oauthError struct {
	Code        string `json:"error"`
	Description string `json:"error_description"`
}

func (e oauthError) Error() string {
	if e.Description == "" {
		return e.Code
	}
	return e.Code + ": " + e.Description
}

// discover reads the proxy's RFC 8414 metadata to find the token endpoint.
// A client should never assume the path: which endpoint serves the exchange is
// the authorization server's choice, and discovery is how it says so.
func discover(ctx context.Context, client *http.Client, proxyURL string) (*authServerMetadata, error) {
	metadataURL := strings.TrimRight(proxyURL, "/") + "/.well-known/oauth-authorization-server"

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, metadataURL, nil)
	if err != nil {
		return nil, err
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetching %s: %w", metadataURL, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("no OAuth metadata at %s (HTTP %d); is XAA enabled on this proxy?",
			metadataURL, resp.StatusCode)
	}

	var metadata authServerMetadata
	if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&metadata); err != nil {
		return nil, fmt.Errorf("parsing metadata: %w", err)
	}
	if metadata.TokenEndpoint == "" {
		return nil, fmt.Errorf("metadata names no token_endpoint")
	}

	if !contains(metadata.GrantProfilesSupported, idJAGGrantProfile) {
		log.Printf("warning: this server does not advertise %s; XAA may not be enabled on it", idJAGGrantProfile)
	}

	return &metadata, nil
}

// exchange is step 3: present the grant, receive an access token.
//
// Client credentials go in the POST body (client_secret_post). HTTP Basic is also
// accepted by this gateway, but the body form is what the profile describes.
func exchange(ctx context.Context, client *http.Client, tokenEndpoint, idJAG, clientID, clientSecret, scope string) (*tokenResponse, error) {
	form := url.Values{}
	form.Set("grant_type", jwtBearerGrantType)
	form.Set("assertion", idJAG)
	form.Set("client_id", clientID)
	form.Set("client_secret", clientSecret)
	// Optional, and can only narrow. Asking for more than the IdP authorized is
	// refused rather than granted.
	if scope != "" {
		form.Set("scope", scope)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, tokenEndpoint, strings.NewReader(form.Encode()))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("posting to token endpoint: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		var oerr oauthError
		if err := json.Unmarshal(body, &oerr); err != nil || oerr.Code == "" {
			return nil, fmt.Errorf("token endpoint returned HTTP %d: %s", resp.StatusCode, body)
		}
		return nil, explain(oerr)
	}

	var token tokenResponse
	if err := json.Unmarshal(body, &token); err != nil {
		return nil, fmt.Errorf("parsing token response: %w", err)
	}
	return &token, nil
}

// explain turns an RFC 6749 error code into something actionable. Each of these
// is a hard failure with a distinct cause, and guessing between them wastes time.
func explain(e oauthError) error {
	var hint string
	switch e.Code {
	case "invalid_grant":
		hint = "the grant was rejected: its aud must be exactly the gateway's issuer URL, " +
			"it expires in about 5 minutes, and it is single use"
	case "unauthorized_client":
		hint = "this client has no mapping on this proxy; add one in the proxy's Cross App Access settings"
	case "invalid_client":
		hint = "client authentication failed; check the client ID and secret from the mapping"
	case "invalid_scope":
		hint = "the requested scope exceeds what the mapping or the grant allows"
	case "invalid_target":
		hint = "the grant's resource indicator names a different resource server"
	case "insufficient_user_authentication":
		hint = "the user must step up at the identity provider and obtain a new grant"
	default:
		return e
	}
	return fmt.Errorf("%w (%s)", e, hint)
}

// callResource is step 4. The access token is the only credential presented here.
// The ID-JAG must not be sent: it is a grant, and the proxy refuses it with a 401
// pointing at the token endpoint.
func callResource(ctx context.Context, client *http.Client, proxyURL, accessToken string) error {
	payload := `{"jsonrpc":"2.0","id":1,"method":"tools/list"}`

	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		strings.TrimRight(proxyURL, "/")+"/mcp", strings.NewReader(payload))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+accessToken)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("calling the resource: %w", err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))

	if resp.StatusCode == http.StatusUnauthorized {
		return fmt.Errorf("resource returned 401. An access token is bound to the proxy it was "+
			"issued for via its proxy_id claim, so a token from another proxy is refused here. Body: %s", body)
	}
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("resource returned HTTP %d: %s", resp.StatusCode, body)
	}

	fmt.Printf("resource responded:\n%s\n", body)
	return nil
}

// describeToken prints the claims worth looking at when something goes wrong.
// Nothing here is verified: it is diagnostics, never an authorization decision.
func describeToken(label, token string) {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return
	}
	raw, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return
	}
	var claims map[string]interface{}
	if err := json.Unmarshal(raw, &claims); err != nil {
		return
	}

	fmt.Printf("%s:\n", label)
	for _, name := range []string{"iss", "sub", "aud", "client_id", "scope", "resource", "jti", "proxy_id", "token_use", "exp"} {
		if value, ok := claims[name]; ok {
			fmt.Printf("  %-10s %v\n", name, value)
		}
	}
}

func contains(haystack []string, needle string) bool {
	for _, item := range haystack {
		if item == needle {
			return true
		}
	}
	return false
}

func main() {
	proxyURL := flag.String("proxy", "http://localhost:9101", "proxy base URL")
	idJAG := flag.String("id-jag", "", "the ID-JAG obtained from your identity provider (step 2)")
	scope := flag.String("scope", "", "optional scope to narrow the request")
	verbose := flag.Bool("v", false, "print token claims")
	flag.Parse()

	clientID := os.Getenv("XAA_CLIENT_ID")
	clientSecret := os.Getenv("XAA_CLIENT_SECRET")

	switch {
	case *idJAG == "":
		log.Fatal("-id-jag is required. Obtain one from your identity provider with an RFC 8693 " +
			"token exchange requesting urn:ietf:params:oauth:token-type:id-jag")
	case clientID == "" || clientSecret == "":
		log.Fatal("XAA_CLIENT_ID and XAA_CLIENT_SECRET are required. Both come from the client ID " +
			"mapping on the proxy; the secret is shown once, when the mapping is created")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	client := &http.Client{Timeout: 15 * time.Second}

	metadata, err := discover(ctx, client, *proxyURL)
	if err != nil {
		log.Fatalf("discovery failed: %v", err)
	}
	log.Printf("token endpoint: %s", metadata.TokenEndpoint)

	if *verbose {
		describeToken("ID-JAG (step 2 output)", *idJAG)
	}

	token, err := exchange(ctx, client, metadata.TokenEndpoint, *idJAG, clientID, clientSecret, *scope)
	if err != nil {
		log.Fatalf("exchange failed: %v", err)
	}
	log.Printf("access token issued, expires in %ds, scope %q", token.ExpiresIn, token.Scope)

	if *verbose {
		describeToken("Access token (step 3 output)", token.AccessToken)
	}

	if err := callResource(ctx, client, *proxyURL, token.AccessToken); err != nil {
		log.Fatalf("step 4 failed: %v", err)
	}
}
