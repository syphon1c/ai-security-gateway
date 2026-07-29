# Cross App Access (XAA) Examples

Working code for steps 3 and 4 of the Cross App Access flow: exchanging an ID-JAG
for a gateway access token, then using that token against a proxy.

Steps 1 and 2 happen at your identity provider and are not covered here. They
produce the ID-JAG that both examples take as input.

## What each file does

| File | Purpose |
|---|---|
| `exchange-id-jag.sh` | Shell client. Discovery, exchange, resource call, and a token inspector for debugging. |
| `xaa-client.go` | The same flow in Go, with the error handling written out. Standalone: `go run xaa-client.go`. |

Both discover the token endpoint from the proxy's RFC 8414 metadata rather than
assuming a path, which is what a real client should do.

## Before you start

XAA is off by default. On the proxy you intend to use:

1. Enable Cross App Access and select the identity provider that will mint grants.
2. Add a client ID mapping, from the client ID at your IdP to a client ID here.
3. Save the client secret shown when the mapping is created. It is displayed once.

Set `GATEWAY_ISSUER_URL` on the gateway to its real public URL. Grants are minted
with that value as their `aud`, and a mismatch is the single most common cause of
`invalid_grant`.

## Getting an ID-JAG (step 2)

At your identity provider, exchange the user's ID token for a grant:

```bash
curl -X POST https://your-tenant.okta.com/oauth2/v1/token \
  -d grant_type=urn:ietf:params:oauth:grant-type:token-exchange \
  -d requested_token_type=urn:ietf:params:oauth:token-type:id-jag \
  -d subject_token_type=urn:ietf:params:oauth:token-type:id_token \
  -d subject_token="$ID_TOKEN" \
  -d audience="$GATEWAY_ISSUER_URL" \
  -d resource="https://mcp.example.com/api" \
  -d client_id="$IDP_CLIENT_ID" \
  -d client_secret="$IDP_CLIENT_SECRET"
```

`audience` names the authorization server that may redeem the grant, which is the
gateway. `resource` names the API being called. Both are required and they are
different things.

## Running the examples

```bash
export XAA_CLIENT_ID=mcp-client-at-gateway
export XAA_CLIENT_SECRET=<the secret from the mapping>
export PROXY_URL=http://localhost:9101

./exchange-id-jag.sh run "$ID_JAG"
```

```bash
go run xaa-client.go -proxy http://localhost:9101 -id-jag "$ID_JAG" -v
```

`-v` prints the claims of both tokens, which is the fastest way to see what the
gateway thought it was given.

Other subcommands:

```bash
./exchange-id-jag.sh discover              # what token endpoint does this proxy advertise
./exchange-id-jag.sh exchange "$ID_JAG"    # step 3 only, prints the access token
./exchange-id-jag.sh inspect "$TOKEN"      # decode either token, no verification
```

## Two things that surprise people

**The grant is single use.** A second exchange of the same ID-JAG is rejected as a
replay. To get another access token, go back to your IdP for a fresh grant. This
is deliberate: it is an authorization grant, not a refreshable credential.

**The grant cannot be sent to the proxy.** Only the exchanged access token is
accepted there. Presenting an ID-JAG in an `Authorization` header returns 401 with
a message pointing at the token endpoint, rather than falling through to another
authentication method where the mistake would be invisible.

## When it fails

The error code tells you which of four unrelated things went wrong. `invalid_grant`
is the grant itself: wrong `aud`, expired, or already spent. `unauthorized_client`
means the client has no mapping on this proxy. `invalid_client` means the ID and
secret did not match the mapping. `insufficient_user_authentication` means the
grant was fine but the user needs to step up at the IdP.

A 401 at step 4, after a successful exchange, usually means the token was issued
through a different proxy. Access tokens carry a `proxy_id` claim and are refused
elsewhere.

