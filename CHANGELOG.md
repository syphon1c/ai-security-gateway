# Changelog

All notable changes to the AI Security Gateway project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/).

## [v2026.8.1]

### First Full Release

**v2026.8.1** is the first full (non-beta) release of the **AI Security Gateway**. Where v2026.7.6 focused on new capability, agent attestation, shadow-AI inventory, and agentic discovery, this release focuses on **enterprise readiness**: a whole-platform security review, authentication and session hardening, stability and race-condition fixes across the proxy data path, and a documentation overhaul. It also lands two protocol upgrades: support for the **MCP 2026-07-28 specification** alongside the legacy protocol, and a **conformance-verified Cross App Access (XAA)** implementation. Every subsystem shipped in the beta series has been re-audited, exercised end-to-end, and wired into the dashboards, audit trail, and alerting pipeline.

---

#### 🔌 MCP 2026-07-28 Protocol Support

The gateway now speaks both eras of the Model Context Protocol side by side: the modern **2026-07-28** specification and the legacy **2024-11-05** specification.

- **Era-aware proxying**: enforcement follows the protocol era each request *declares*, never a guess, and the upstream's era is learned through a real `server/discover` probe rather than assumed
- **Conformance enforcement**: on modern requests, JSON-RPC batches are refused and the mirrored `MCP-Protocol-Version` / `Mcp-Method` / `Mcp-Name` / `Mcp-Param-*` headers are validated against the body, with spec-correct protocol errors (`-32020`) rather than opaque failures
- **Enforce or observe**: a per-proxy conformance mode (with an `MCP_CONFORMANCE_MODE` gateway default) lets you watch violations before you start blocking them
- **Compatibility bridge**: modern clients can reach legacy servers through a translation layer, and a bridged downgrade always raises an alert instead of happening silently
- **Streaming correctness**: SSE-over-POST responses are inspected event by event rather than buffered, so long-lived methods like `subscriptions/listen` no longer hang
- **New-surface security**: credential-phishing prompts inside multi-round-trip (elicitation) results raise alerts, tool schemas are analysed for unsafe shapes including `x-mcp-header` annotations, protocol extensions can be deny-listed, a minimum protocol version can be pinned per proxy, and deprecated feature use is reported
- **Tasks stay governed**: tool permissions and rate limits follow MCP task handles, so a tool that gets disabled cannot keep delivering results through a task created moments earlier
- **Built-in servers are dual-era**: the proxy discovery server, the ARD discovery server, and the Skill Security Hub answer clients of either era, and the vulnerability scanner and tool discovery understand modern servers
- **OAuth alignment**: RFC 9207 `iss` issued and validated in both proxy directions, upstream credentials bound to their issuer, `application_type` validation, and opt-in support for Client ID Metadata Documents (an HTTPS URL as `client_id`)

#### 🔁 Cross App Access (XAA) Conformance

XAA (🧪 experimental) went through a full conformance pass against `draft-ietf-oauth-identity-assertion-authz-grant-04` and the xaa.dev reference implementation. It is no longer an Okta-shaped special case:

- **End-to-end token exchange**: access tokens minted by the exchange are signed, typed `at+jwt`, and accepted at the resource step, closing the gap where the only working path was replaying the ID-JAG itself
- **Verifiable by resource servers**: tokens carry `aud`, `proxy_id`, and `token_use=xaa`, with keys published for verification
- **Grant hygiene**: grants are single-use, the audience is derived server-side and never caller-supplied, clock skew is tolerated within bounds, and grant lifetimes are capped
- **Independent lifetimes**: access-token TTL is configured on its own rather than inherited from the grant's expiry
- **Step-up authentication (RFC 9470)**: per-proxy step-up requirements for sensitive resources
- **Discovery, not guesswork**: JWKS is resolved through provider discovery instead of an assumed path
- **Fully UI-configurable**: client mappings, per-proxy enablement, statistics, and revocation are all managed from the dashboard, with complete audit logging

#### 🔐 Authentication & Session Hardening

A dedicated audit of the admin authentication stack, now enforced end-to-end:

- **Session lifecycle**: changing a user's role or disabling an account invalidates their active sessions immediately; logout revokes the token server-side (JTI blacklist) rather than only clearing the client
- **Session management UI**: admins can list and revoke any user's active sessions; per-user session caps prevent unbounded session growth
- **Forced password rotation**: `must_change_password` flow, admins can require a password change at next login
- **Login protection**: IP-based rate limits on login and refresh endpoints, and a timing-oracle fix so username enumeration via response timing is not possible
- **Deployment safety**: the gateway refuses to start with a missing or default `JWT_SECRET`, and refuses the placeholder `JWT_SECRET` / `ENCRYPTION_KEY` values from the environment template in every environment
- **Last-admin guard**: the final admin account cannot be deleted or demoted (returns `409`)
- **Token refresh**: hardened refresh flow with rotation, plus a fixed frontend refresh path and refresh-aware WebSocket reconnection

#### 🛡️ Platform Security Review

A full-backend, multi-pass security review ahead of release. Highlights:

- **Fail-closed consistency**: policy loading, skill approval guards, and MCP tool-permission checks now block on error instead of failing open
- **SSRF protection everywhere**: dial-time guards on proxy targets (`PROXY_TARGET_*` env controls), scanner targets, discovery metadata fetches, and `did:web` resolution
- **Audit completeness**: privileged admin actions, policy create/update/delete/toggle, settings changes, and permission changes all emit structured audit events
- **Secrets at rest**: guardrail provider credentials, evaluation endpoint secrets, and inventory connector auth headers are encrypted at rest and masked in every API response
- **Request hygiene**: body-size limits on unauthenticated endpoints, LIKE-wildcard escaping on all search filters, and stricter input validation across handlers
- **Concurrency fixes**: WebSocket write serialization, policy-engine metrics race fixes, proxy supervisor race fix, and a sweep of data-path race conditions found under load

#### 🪪 Agent Identity Hardening

A dedicated four-phase audit of the Cryptographic Agent Identity feature:

- **`did:key` trust gate**: self-certifying `did:key` identities must now be **registered** before they verify; previously any freshly-minted keypair could satisfy a `required` proxy
- **Full DPoP proof verification (RFC 9449)**: proofs must be signed by their own embedded key, match the pinned thumbprint, bind to the live request (`htm`/`htu`), be fresh (60 s), and carry a single-use `jti` (replay cache); previously only the thumbprint was compared
- **Credentials stop at the gateway**: on a verifying proxy the `X-Agent-Identity` / `X-Agent-DPoP` / delegation-chain headers are stripped before forwarding upstream; with verification off they pass through untouched
- **Per-proxy enforcement UI**: enforcement mode, trust-domain allowlist, autonomy floor, and proof-of-possession step-up are now configurable in the proxy settings form (previously API-only)
- **Trust-bundle correctness**: `did-method` bundles no longer require dummy key material, `x509-roots` PEM and refresh URLs are validated at save time, refresh is scoped to `spiffe-jwks` bundles, and deleting a bundle or identity frees its trust domain / URI for immediate reuse
- **Governance polish**: update API distinguishes omitted-vs-cleared fields, status changes stamp full revocation bookkeeping, agent tool rules are cleaned up with their identity and audited under dedicated event types, and verification settings are bounds-checked with live-applied refresh intervals
- **Clearer API errors platform-wide**: the error sanitizer now targets genuine internal-detail leaks (paths, stack traces, SQL) instead of scrubbing any message containing a URL or common word; validation feedback reaches admins intact
- **Coverage**: an 18-route authentication/authorization test matrix mirrors the production middleware chain

#### 🚦 Proxy & Data-Path Improvements

- **Deterministic policy ordering**: policy assignment priority is now enforced everywhere policies are evaluated (previously nondeterministic map ordering)
- **Global policy toggle**: deactivating a policy now takes effect on every proxy using it, with automatic reload
- **Synchronous start**: proxy start now confirms the port has actually bound before reporting success; port conflicts are caught at create/edit time with a suggested free port
- **Live vs restart updates**: cosmetic edits (name, description, tags) no longer restart a running proxy or drop client connections
- **Viewer read-only**: non-admin users get a consistent read-only proxy view; proxy state changes broadcast over WebSocket in real time
- **Upstream resilience**: shared upstream transport with configurable response-header timeout and per-proxy circuit breakers

#### 🧪 Guardrails & Detection Quality

- **Guardrails Evaluation**: 85-case built-in test corpus, conclusive-based scoring, cancellable runs, and expanded engine test coverage
- **Custom test-case management**: author your own single-turn and multi-turn test cases with a guided turns editor, compliance mappings inherited from the category, per-row highlighting and a source filter, delete support, JSON import/export of test suites, and built-in-test immutability enforced end-to-end
- **Guardrail Providers**: hardened provider CRUD (admin-only API), health checks, per-request log merge, and transactional deletes
- **Canary Detection**: cross-user leak detection (`unknown_recipient`), sliding-window extraction to defeat evasion, corrected survival aggregation, and live-applied thresholds
- **MCP Vulnerability Scanner & Tool Change Monitoring**: shared content-aware severity analysis, fail-closed baselines, triage workflow, and reflection false-positive fixes
- **Traffic analysis**: built-in heuristic detections wired into the alerts pipeline

#### 🤝 A2A & Discovery

- **A2A spec v1.0**: migrated to the a2a-go v2 SDK with native spec v1.0 support, real task listing, and rug-pull detection extensions
- **Agent Card Monitor**: fail-closed baselines, content-aware severity, and settings persistence, at parity with the MCP tool-change monitor
- **ARD & AI Inventory**: completed audits, tombstone-safe deletes, retention sweeps, real host/path matching for discovery rules, 15-minute auto-sync, and WebSocket shadow-AI alerts

#### 📊 Interface & Observability

- **Dashboard revamp**: security timeline, theme-aware charts, and lazy-loaded tabs across the Security, Alerts, LLM, and MCP pages
- **Alert management**: global summary cards, persistent dismiss (false-positive tracking), and shared filtering
- **Settings**: rebuilt settings pipeline with validation, secret masking on read, live-apply where safe, and explicit restart-required flags
- **API Playground**: the OAuth tutorial no longer loses your place on every submit, the authorization code is returned to the page automatically once its `state` is verified, client secrets and tokens are masked behind a reveal toggle, the API key panel shows the team, rate limit and reachable proxies it always meant to, and token validation now answers for the selected proxy rather than accepting any valid gateway token

#### 📚 Documentation

- **New guides**: [Proxy Management](https://docs.aisecgateway.com/configuration/proxy-management-guide.html) and [MCP Tool Permissions & Rate Limiting](https://docs.aisecgateway.com/features/mcp-tool-permissions.html)
- **Site quality**: every guide is now reachable from the sidebar, dead links fail the docs build, and previously unlisted guides (Session Quarantine, Traffic Analysis, Guardrail Providers, Guardrails Evaluation Operations, API Authentication) are published in navigation

---

#### Upgrade Notes

- **Release packages no longer include a pre-created `.env`.** Run `./install.sh` (Linux/macOS) or copy `env.example` to `.env` and set your keys (Windows). The gateway refuses to start on the template's placeholder `JWT_SECRET` / `ENCRYPTION_KEY` values, in development mode included
- **Set `JWT_SECRET`** before upgrading, the gateway will not start without a non-default value
- Existing sessions are invalidated on upgrade; users must sign in again
- All new controls remain **opt-in**; existing proxy configurations continue to behave as before
- Review the `PROXY_TARGET_*` environment variables if your proxies target private networks

## [v2026.7.6]

### Seventh Public Beta Release

The **AI Security Gateway** is a unified security platform providing real-time monitoring, policy enforcement, and threat detection for Large Language Model (LLM) APIs and Model Context Protocol (MCP) servers. This is a major release that extends the gateway from securing *human-attributed* traffic to **attesting the agent workloads themselves**, inventorying **every AI asset it can see**, and publishing a standards-compliant **discovery layer** in front of your agents, MCP servers, and skills. Headline additions are **Cryptographic Agent Identity** (SPIFFE / DID / X.509), **Shadow-AI Discovery & AI Asset Inventory**, and **Agentic Resource Discovery (ARD)**, alongside finer-grained per-tool and per-user rate limiting and a round of Agent-to-Agent reliability fixes.

---

#### 🛡️ Cryptographic Agent Identity (SPIFFE / DID / X.509)

The gateway already records **which human** is behind a request (attribution); Agent Identity adds **attestation**, a verifiable cryptographic identity for the **agent workload itself**, proven on every request. Each action now ties to *both* a person *and* a specific, verified agent (e.g. `spiffe://acme.org/checkout-bot`). The gateway is a **verifier first**, it validates identities issued by your SPIRE / IdP / DID infrastructure, and never a CA, except for an explicit, opt-in issuance mode.

- **Three identity formats, one pipeline**: SPIFFE **JWT-SVIDs** (header-borne), SPIFFE **X.509-SVIDs** (mTLS, or a forwarded client-cert header behind a trusted front proxy), and **DIDs**, `did:key` (key embedded in the identifier) and `did:web` (resolved from admin-approved hosts, SSRF-guarded)
- **Opt-in per proxy**: `off` / `optional` (verify-and-attribute) / `required` (fail-closed `401`), plus a global default and per-proxy allowed-trust-domain lists
- **Identity-based enforcement**: a **deny-biased** Agent dimension on the MCP tool-permission hierarchy (an agent rule can only *further restrict* the human decision, never escalate) and a per-proxy **autonomy floor** that rejects insufficiently-trusted agents
- **Verifiable delegation chains**: an `X-Agent-Delegation-Chain` of signed on-behalf-of hops, verified end-to-end with a confused-deputy guard
- **Proof-of-possession & step-up**: optional DPoP sender-constraint (enforced when an identity pins a key); a proxy can **require** proof-of-possession and answer bearer-only credentials with a `WWW-Authenticate: DPoP` step-up challenge
- **A2A impersonation detection**: bind an identity to a registered A2A agent and the card monitor flags any AgentCard not signed by the bound key (Critical), complementing rug-pull field-diff detection
- **Revocation that reaches live sessions**: revoking an identity blocks it on the next request **and** tears down its in-flight A2A streams and SSE proxy connections within seconds
- **Opt-in gateway issuance**: when enabled, mint short-lived (DPoP-bindable) agent SVIDs, the signing key lives in memory only and rotates on restart, so the gateway never becomes a persistent CA
- **Security-first**: verifier by default, write-only key material, SSRF-guarded fetches, admin-gated mutations, and full audit logging
- **Dashboard tile**: active identities, verifications, and failures surfaced on the Security dashboard

---

#### 🔍 Shadow-AI Discovery & AI Asset Inventory

A unified, governed **inventory of every AI asset the gateway can see**, LLM providers / models, MCP servers / tools, A2A agents, and skills, that automatically flags **shadow AI**: anything observed but never sanctioned. It is the inbound mirror of ARD: where ARD publishes what you *advertise*, the AI Inventory records what you actually *observe*, and turns that into a control point.

- **Three observation planes**: *in-band* (projects assets from gateway-proxied traffic, token usage + request audits, with zero added request latency), *ingest* (catches AI that **bypasses** the gateway entirely via a push endpoint and SSRF-guarded pull connectors for CASB / DNS / OTel / Langfuse egress logs), and *active scanning* (planned)
- **Governance lifecycle**: every asset carries a state, `sanctioned`, `observed`, `unsanctioned` (shadow), `quarantined`, or `denied`, with first-seen / last-seen tracking, risk scoring, and per-asset observation timelines
- **Enforcement, not just reporting**: moving an asset to `quarantined` or `denied` **blocks it at the proxy** (MCP tools, LLM models, or entire providers) via an in-memory denylist refreshed on every state change; a blocked provider blocks all of its models
- **Opt-in auto-quarantine**: newly-discovered shadow AI can be automatically quarantined and blocked on its very next request (off by default, observe-only posture)
- **Provider fingerprint catalog**: built-in signatures for OpenAI, Anthropic, Google Gemini, AWS Bedrock, Azure OpenAI, Cohere, Mistral, and more, plus custom host / regex / path / model fingerprints so self-hosted and internal AI is classified correctly
- **Shadow-AI alerts**: raises a security alert the first time an unsanctioned asset is discovered, with full attribution (user, host, source)
- **Security-first**: observe-only by default, observations store fingerprints / hosts / model names only (never raw payloads), SSRF protection on all connector fetches, and admin-only mutations
- **Dashboard tile**: total assets, shadow count, and blocked count surfaced on the Security dashboard

---

#### 🧭 Agentic Resource Discovery (ARD)

Turns the gateway into a **discovery service for agentic resources** using the open [Agentic Resource Discovery](https://agenticresourcediscovery.org/) standard. ARD sits *before* invocation, it lets an AI client ask "what's available for this task?" and answers with matching A2A agents, MCP servers, and skills, which are then called through their own native protocols. It does not replace A2A, MCP, or Skills; it's the discovery layer in front of them.

- **Publishes your catalog**: serves a standards-compliant `/.well-known/ai-catalog.json` AI Catalog manifest describing your agentic resources
- **Auto-projection**: automatically projects your public A2A agents, public MCP proxies / tools, and approved skills into the catalog, no separate source of truth to maintain
- **Registry search API**: exposes `POST /search` (natural-language query with 0–100 relevance scoring), `POST /explore` (facet aggregation), and `GET /agents` (deterministic browsing) for any ARD-compliant client
- **Federation**: query trusted upstream registries with `referrals` (return pointers) or `auto` (merge results) modes, with SSRF protection, trust gating, and de-duplication
- **Native MCP discovery**: AI assistants connect to a built-in MCP server (`/api/v1/mcp/ard`) exposing `ard_search` and `ard_explore` tools to discover capabilities on the fly
- **A2A skill**: the gateway's AgentCard advertises a `resource-discovery` skill so A2A orchestrators can find this capability
- **Security-first**: opt-in publishing (disabled by default), access-restricted resources excluded, domain-anchored URN / identity binding, upstream trust verification, rate limiting, and full audit logging
- **Dashboard tile**: catalog and federation status surfaced in the Security dashboard

---

#### 🚦 Per-Tool & Per-User Rate Limiting

Rate limiting is now enforced at finer granularity, in addition to the existing proxy-level controls.

- **Per-tool limits**: sliding-window rate limits applied per MCP tool, keyed by user · proxy · tool (`0` = unlimited)
- **Per-user limits**: proxy-wide sliding-window limits keyed by user · proxy
- **Hierarchy-aware**: per-tool limits resolve through the User override → Group → Global proxy-setting hierarchy alongside the enable / disable decision for each tool

---

#### 🤝 Agent-to-Agent Reliability & Fixes

- Fixed A2A invocation handling and corrected **group access mode** evaluation
- Hardened **fail-closed** behaviour for A2A access control, so denied or unverified agents are rejected by default
- Expanded database test coverage and internal refactors across the API, database, and frontend layers for maintainability

---

> **Upgrading?** Every new capability in this release is **opt-in and disabled by default**. Existing proxies behave exactly as before until you explicitly enable Agent Identity, AI Inventory enforcement, or ARD publishing.

## [2026.4.1-beta]

### Sixth Public Beta Release

The **AI Security Gateway** is a unified security platform providing real-time monitoring, policy enforcement, and threat detection for Large Language Model (LLM) APIs and Model Context Protocol (MCP) servers. This release introduces **Session Quarantine** (kill switch), **Accumulated Session Risk Scoring**, **Scope Change Auto-Pause**, **Cross-Chain Trace Correlation**, **Guardrail Confidence Thresholds**, **Skill Package Registry & Distribution**, and **Skill Version Diff Analysis**, implementing key controls from the AWARE Framework for AI agent governance and expanding the Skill Security Hub into a curated skill distribution platform.

---

#### 🔒 Session Quarantine (Kill Switch)

A surgical kill switch that blocks individual user sessions without stopping the entire proxy. Administrators can quarantine specific OAuth users, API keys, or IP addresses, and all further requests from that session are immediately rejected with HTTP 403.

- **Per-session blocking** across HTTP, WebSocket, and SSE transports for both MCP and LLM proxies
- **Active session discovery**: The quarantine modal shows all sessions that made requests in the last 24 hours, with API key name, masked key prefix, request count, and last seen time
- **TTL support**: Quarantine entries can auto-expire after a configurable duration, or persist permanently until manually released
- **Bulk release**: Release all quarantined sessions for a proxy in one action
- **Audit logging**: All quarantine and release actions are logged with full admin attribution
- **Alert deduplication**: Blocked request alerts are rate-limited to one per session per minute to prevent alert floods

---

#### 📊 Accumulated Session Risk Scoring

Tracks cumulative risk per user session across multiple requests. Each request's risk score is added to a running total that decays over time, with escalating responses as thresholds are exceeded.

- **Time-decaying accumulation**: Risk halves every 30 minutes, preventing normal activity from permanently accumulating
- **Four escalation thresholds**: Warn (100), Rate Limit (200), Escalate (300), Block (500)
- **Auto-quarantine**: Sessions exceeding the block threshold are automatically quarantined without manual intervention
- **Risk visibility**: The quarantine modal shows per-session risk levels with colour-coded badges (green/yellow/orange/red) and a "Reset Risk" action per session
- **Severity-based alerts**: Each new escalation generates an alert at the appropriate severity level

---

#### ⏸️ Scope Change Auto-Pause

When rug-pull detection identifies significant tool or agent card changes, the proxy can be automatically paused, requiring administrator re-approval before resuming.

- **Severity-based decision logic**: Critical/High severity changes trigger immediate pause; 3+ Medium severity changes trigger pause; Low severity generates alerts only
- **Manual pause**: Administrators can manually pause any proxy for security review with a reason
- **Review modal**: Shows the pause reason, timestamp, detected changes with severity badges, and an "Approve & Resume" button
- **Opt-in per proxy**: Controlled via the `scope_change_auto_pause` proxy setting (disabled by default)

---

#### 🔗 Cross-Chain Trace Correlation

W3C trace context is now propagated through Agent-to-Agent (A2A) invocations, enabling multi-hop agent workflows to appear as a single distributed trace in Jaeger, Langfuse, or any OTLP-compatible backend.

- **Automatic header injection**: Outgoing A2A HTTP requests include `traceparent` and `tracestate` headers via OpenTelemetry-instrumented transport
- **Audit trail enrichment**: `trace_id` and `span_id` are recorded in every agent invocation audit log for cross-reference
- **Zero configuration**: Works automatically when tracing is enabled (`TRACING_ENABLED=true`)

---

#### 🎯 Guardrail Confidence Thresholds

Guardrail providers can now be configured with a minimum confidence threshold. Violations reported below the threshold are downgraded from block to monitor, reducing false positives while still logging the finding for review.

- **Per-provider threshold**: Set `min_confidence_threshold` (0.0–1.0) on any guardrail provider configuration
- **Backward compatible**: Default threshold of 0 preserves existing behaviour (all violations processed at face value)
- **Transparent downgrade logging**: Downgraded violations are logged with provider name, reported confidence, and configured threshold

---

#### 📦 Skill Package Registry & Distribution

The Skill Security Hub now includes a **Package Registry**: admins upload skill packages (ZIP files) that are scanned, stored, and made available for download by AI agents via MCP. This transforms the Hub from analysis-only into a curated skill distribution platform.

- **Persistent package storage**: Uploaded ZIP files are stored on disk in a content-hash-based directory structure, configurable via `SKILL_PACKAGE_STORAGE_PATH` (defaults to `./data/skill-packages`)
- **Automatic package creation**: ZIP uploads via the admin UI now persist the file and create a `SkillPackage` record linked to the registry entry, no separate upload step needed
- **MCP `download_skill` tool**: AI agents can download approved skill packages directly via MCP. Only skills with status `approved` and an uploaded package are downloadable. Returns base64-encoded ZIP content with filename, size, and content hash
- **MCP `search_skills` tool**: Rich search across the registry with filters for query text, category, risk level, author, and package availability (`has_package`). Returns download counts per skill, richer than the existing `list_approved_skills`
- **Download audit trail**: Every package download is recorded with agent name, IP address, and timestamp in a dedicated `skill_downloads` table for compliance tracking
- **Packages tab**: New tab in the Skill Security Hub UI showing all uploaded packages with file name, size, download count, skill.json status, uploader, and date. Includes download and delete actions for admins
- **skill.json manifest support**: When a ZIP contains a `skill.json` file, the Gateway stores its contents for future manifest validation and capability declaration

---

#### 🔀 Skill Version Comparison & Diff Analysis

When a skill is re-submitted with changed source code, reviewers can now instantly see what changed, no more reviewing all findings from scratch.

- **Finding diff**: Shows new findings (added risks), resolved findings (improvements), and unchanged count between two versions of the same skill
- **Risk score delta**: Displays the net risk score change with breakdown, so reviewers see at a glance whether an update improved or worsened security posture
- **Automated recommendations**: Generates human-readable review guidance (e.g., "This update resolved 2 High findings and added none. Recommend re-approval.")
- **Compare Versions button**: Appears in the Registry tab for skills with more than one submission. Opens a diff modal with colour-coded findings and the recommendation
- **MCP `compare_skill_versions` tool**: AI agents can programmatically compare two versions of a skill, useful for automated CI/CD pipelines and agent-driven security reviews
- **REST endpoint**: `GET /api/v1/security/skills/registry/{id}/diff` with optional `previous_id` parameter (auto-detected if omitted)

## [2026.3.1-beta]

### Fifth Public Beta Release

The **AI Security Gateway** is a unified security platform providing real-time monitoring, policy enforcement, and threat detection for Large Language Model (LLM) APIs and Model Context Protocol (MCP) servers. This release introduces **Guardrail Providers** for real-time third-party content screening, a redesigned navigation layout, and a new visual Pipeline view for OAuth access management.

---

#### 🛡️ Guardrail Providers

A new integration layer that connects the AI Security Gateway to third-party guardrail services for real-time content screening of LLM requests and responses. Multiple providers can run concurrently using a fan-out/fan-in pattern, where total latency equals the slowest provider rather than the sum.

**Supported providers:**

- **Groq Safeguard** : High-speed safety classification with configurable safety policy prompts
- **EnkryptAI** : Comprehensive guardrail API with policy-based detection across NSFW, toxicity, PII, injection attacks, and more
- **DynamoAI DynamoGuard** : Multi-policy moderation with per-policy scoring for prompt injection, toxicity, PII, hate speech, and violence
- **GuardrailsAI** : Self-hosted, open-source guardrail with 67+ validators from Guardrails Hub covering jailbreak detection, PII, toxicity, and content policy
- **Fiddler AI Guardrails** : Sub-second safety classification across 11 dimensions with optional 24-type PII detection

**Key features:**

- **Per-Proxy & Per-Team Assignment**: Apply providers globally to a proxy or scope them to specific teams for layered screening
- **Configurable Behaviour**: Set direction (request/response/both), action (block/monitor), failure mode (fail-open/fail-closed), timeout (500ms–60s), and priority
- **Health Checks & Test Playground**: Verify provider connectivity and test content screening directly from the dashboard
- **Audit Logging**: Every provider check is logged with verdict, categories, confidence score, latency, and tokens used
- **Dashboard & Metrics**: Per-provider and per-proxy statistics with top violation category breakdowns

---

#### 🧪 Guardrail Evaluation Enhancements

Guardrail Evaluations can now target **configured Guardrail Providers directly**, in addition to HTTP endpoints. This makes it easy to benchmark provider detection rates against the built-in 71 test cases across 12 attack categories without needing to set up a separate endpoint.

---

#### 🔔 Granular Alert Notifications

Email and Slack integrations now support fine-grained control over which alerts trigger notifications:

- **Per-Category Filtering**: Enable or disable notifications for specific alert categories : policy violations, tool access attempts, security events, system events, and compliance alerts
- **Minimum Severity Threshold**: Set a minimum severity level (Critical, High, Medium, Low, Info) per integration channel
- Each integration channel can be configured independently

---

#### 🧭 Redesigned Navigation

The main sidebar navigation has been reorganised for improved clarity as the platform grows:

- **Security Tools**: Hosts System Prompts, Canary Detection, and the Skill Security Hub
- **Guardrails**: New menu group for Guardrail Providers and Guardrail Evaluations
- **Access & Identity**: Teams & API Keys, OAuth Access, OAuth Proxy, User Activity, and Playground
- **Infrastructure**: Proxy Management, A2A Agents, and Audit Logs

---

#### 🔀 OAuth Access Pipeline View

A new visual Pipeline view for OAuth Access Management that shows the full user journey from provider to permissions:

**Provider → Rules → Teams → Users → Tool Overrides → Summary**

Each stage is an interactive section where administrators can drill into provider configurations, group assignment rules, team memberships, individual users, and per-user tool permission overrides. A summary bar displays quick statistics across the pipeline. The view mode (Pipeline or Table) is persisted across sessions.

---

#### 🐛 Bug Fixes & Improvements

- Improvements to Canary Token Detection reliability and accuracy
- System Prompt Injection stability fixes
- External Storage sync and configuration improvements
- General UI polish and consistency updates

### 🔧 Technical Architecture

#### Backend (Built using Go)
- **Unified API Server**: Central management hub with 90+ REST endpoints (port 8080)
- **Multi-Proxy Engine**: Support for HTTP, WebSocket, SSE transport protocols
- **Policy Engine**: JSON-based security rules with compiled regex patterns
- **Alert System**: Real-time threat detection and notification pipeline
- **Database Layer**: SQLite with GORM ORM (6 core models)
- **Authentication**: JWT-based auth, RBAC, OAuth 2.1 support
- **Audit Logging**: 35+ event types for compliance and security monitoring
- **WebSocket Server**: Real-time updates to web interface

#### Frontend (Vue.js + TypeScript)
- **Framework**: Vue 3 with Composition API, TypeScript, Vite build system
- **State Management**: Pinia stores for reactive data
- **Real-Time Updates**: WebSocket integration for live dashboard
- **Responsive UI**: Modern design system with Chart.js analytics
- **Hot Module Replacement**: Fast development with instant updates

#### Database Schema
- **ProxyConfig**: Proxy instance configurations (name, type, target, port, policies, transport)
- **Alert**: Security alert records (severity, status, policy name, evidence)
- **RequestLog**: HTTP/WebSocket traffic logs (method, path, status, duration, risk level)
- **TokenUsage**: Token consumption tracking (input/output tokens, cost, model)
- **MCPTool**: MCP tool configurations (name, enabled status, usage count)
- **PolicyConfig**: Security policy assignments per proxy

### 📦 Deployment & Distribution

#### Release Packages
- **Pre-built Binaries**: Linux (amd64/arm64), macOS (amd64/arm64), Windows (amd64)
- **Helper Scripts**: `install.sh`, `verify.sh`, `start.sh` (Unix) / `start.ps1` (Windows)
- **Service Files**: Systemd (Linux), Launchd (macOS) for production deployment
- **Pre-built Frontend**: Production-optimized Vue.js app
- **Docker Configuration**: `docker-compose.frontend.yml` and `Dockerfile.frontend`
- **Security Policies**: 7 JSON policy files with 250+ detection rules
- **Configuration Templates**: `env.example`, `config.example.yaml`
- **Documentation**: Complete setup and usage guides

#### Deployment Options
- **Docker Frontend**: Nginx-based container serving Vue.js app (recommended)
- **Manual Web Server**: Deploy to nginx/apache with reverse proxy configuration
- **Native Binary**: Go binary for optimal performance (no Docker required for backend)
- **Hybrid Deployment**: Mixed environment support (binary + Docker, manual web server)

### 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication with role-based access control (RBAC)
- **OAuth 2.1 Support**: Full OAuth integration with Dynamic Client Registration (DCR)
- **Session Encryption**: AES-256-GCM encryption for OAuth session tokens
- **Policy-Based Blocking**: Real-time threat blocking based on security policies
- **Audit Logging**: Comprehensive logging of all security events and user actions
- **CORS Protection**: Configurable CORS policies with security headers
- **Rate Limiting**: Per-user and per-IP rate limiting to prevent abuse
- **Input Validation**: Comprehensive validation of all API inputs
- **SQL Injection Prevention**: Parameterized queries throughout the application

### 📚 Documentation

Complete documentation suite included:
- Installation and setup guides
- Multi-proxy management documentation
- A2A Agent Registry guide
- Security policies and custom policy creation
- OAuth proxy setup and configuration
- API reference with 90+ endpoints
- Alert system and traffic analysis guides
- Observability and monitoring integration
- Docker and hybrid deployment guides
- Troubleshooting and best practices

### 🧪 Testing & Quality

- **Unit Tests**: Comprehensive test coverage for core components
- **Integration Tests**: End-to-end testing with mock servers
- **Benchmarks**: Performance testing suite
- **CI/CD**: GitHub Actions workflow with automated testing
- **Code Quality**: golangci-lint with security rules enabled
- **Security Scanning**: gosec security analysis

### ⚠️ Known Limitations

- **Beta Software**: Thorough testing recommended before production deployment
- **Static Analysis Limits**: Cannot detect all vulnerability types (e.g., semantic issues, prompt injection)
- **Performance Variability**: May vary with large codebases or high-traffic environments
- **MCP Protocol Coverage**: Some advanced features may not be fully covered
- **Test Environments**: Recommended for testing and development environments

### 📈 Project Metrics

- **250+ Detection Rules**: Across all security policies
- **90+ API Endpoints**: Complete REST API coverage
- **35+ Audit Event Types**: Comprehensive compliance logging
- **6 Database Models**: Efficient data persistence layer
- **7 Pre-built Policies**: Ready-to-use security configurations
- **3 Transport Protocols**: HTTP, WebSocket, SSE support
- **5 Platform Builds**: Linux, macOS, Windows (multiple architectures)

### 🎯 Next Steps

- Community feedback incorporation
- Performance optimization based on real-world usage
- Enhanced security policy templates
- Additional enterprise integrations
- Extended observability features
- Stable release planning

---

**Note**: This is a beta release intended for testing and development. While the software has been thoroughly tested, users should conduct their own validation in production-like environments. Community feedback is welcomed and encouraged to help improve the software.

For detailed release information and downloads, see the [GitHub Releases](https://github.com/syphon1c/ai-security-gateway/releases) page.
