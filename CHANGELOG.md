# Changelog

All notable changes to the AI Security Gateway project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/).

## [v2026.7.5-6]

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
- LLM and MCP Proxy performance improvements

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


## [2026.2.4-beta]

### 🎉 Fourth Public Beta Release

This release introduces the **AI Security Skills Hub**, a centralised skill approval authority for AI assistants. It also adds **Agent-to-Agent (A2A) Card Change Detection** to protect against rug-pull attacks, and redesigned dashboards across the platform.


## [2026.2.3-beta]

### 🎉 Third Public Beta Release

The **AI Security Gateway** is a unified security platform providing real-time monitoring, policy enforcement, and threat detection for Large Language Model (LLM) APIs and Model Context Protocol (MCP) servers. This beta release represents a comprehensive security proxy and monitoring platform for AI infrastructure.

This release introduces our Guardrails Evaluation scanning tool, improved relationship visualisation graphs on the dashboard, and enhancements to the Canary Token detection feature.

## [2026.2.3-beta]

### 🎉 Third Public Beta Release

The **AI Security Gateway** is a unified security platform providing real-time monitoring, policy enforcement, and threat detection for Large Language Model (LLM) APIs and Model Context Protocol (MCP) servers. This beta release represents a comprehensive security proxy and monitoring platform for AI infrastructure.

This release introduces our Guardrails Evaluation scanning tool, improved relationship visualisation graphs on the dashboard, and enhancements to the Canary Token detection feature.


## [2026.2.2-beta]

### Second Public Release

#### Canary Token Detection
Canary Token Injection is a security feature that helps detect when data from one user or session is accidentally exposed to another user. Think of it like a "tripwire" for an early warning system that alerts you to potential data leakage in your AI systems.
- **Cross User**: Canary from user A appeared in response to user B 
- **Cross Session**: Canary from session A appeared in user's different session B 
- **Memorization**: Provider-specific memorization detection 
- **Stale Canary**: Canary older than 7 days appeared (possible memorization) 

#### Improved MCP Tool Rate limiter
- Improvements to the per-user/per-tool rate limiter for MCP Server PRoxies
- Improved OAuth MCP Tool permission overrides per-user

#### Bug fixes & UI Improvements
- Improved visual indicators for Proxy audit features (enabled or disabled)
- Moved all MCP/LLM Dashboard API Endpoints behind Auth
- Global AI Security Gateway User-Agent applied to all tool requests


## [2026.2.1-beta]

### 🎉 First Public Beta Release

The **AI Security Gateway** is a unified security platform providing real-time monitoring, policy enforcement, and threat detection for Large Language Model (LLM) APIs, Model Context Protocol (MCP) servers and Agent-to-Agent (A2A) registry. This beta release represents a comprehensive security proxy and monitoring platform for AI infrastructure.

Getting started document can be found at [AI Security Gateway Docs](https://syphon1c.github.io/)

### ✨ Core Features

#### 💰 Budget Limits & Cost Control
- **Monthly Budget Limits**: Set spending limits per user group/team in USD
- **Configurable Warning Thresholds**: Alert when spending reaches configured percentage (e.g., 80%)
- **Flexible Enforcement**: Block requests at threshold or continue with warnings
- **Automatic Monthly Reset**: Budgets automatically reset at month start
- **Manual Reset**: Reset budgets on-demand via API or web interface
- **Real-Time Tracking**: Monitor current spending, utilization, and remaining budget
- **Dashboard Metrics**: View budget status across all teams
- **Request Blocking**: Automatic blocking when budget exceeded (HTTP 402 Payment Required)

#### 🔄 Multi-Proxy Management
- **Unlimited Proxy Instances**: Run multiple MCP and LLM proxies simultaneously
- **Transport Protocol Support**: HTTP, WebSocket, and Server-Sent Events (SSE)
- **Centralized Management**: Create, configure, start, stop, and restart via web interface
- **Database Persistence**: Configurations, alerts, and audit logs stored in SQLite
- **Per-Proxy Monitoring**: Individual health checks and performance metrics
- **Auto-Start Support**: Configure proxies to start automatically on system boot

#### 🛡️ Custom Security Policies
- **200+ Detection Rules**: Built-in rules across critical, high, medium, and low severity
- **JSON-Based Configuration**: Easy-to-customize policy definitions
- **Real-Time Threat Detection**: SQL injection, command injection, path traversal, XSS, and more
- **Policy Templates**: `critical-security`, `standard-security`, `mcp-advanced-security`, `llm-security`
- **Per-Proxy Assignment**: Different security levels for different use cases
- **Custom Policy Creation**: Organization-specific security requirements
- **Advanced Pattern Matching**: Regex-based rules with polymorphic detection

#### 💬 System Prompt Injection
- **Automatic Injection**: Security controls injected into LLM requests automatically
- **Priority-Based Selection**: Highest priority prompt per request (user group > proxy)
- **Template Variables**: Dynamic substitution (`{{.User}}`, `{{.Date}}`, `{{.Organization}}`)
- **Per-Proxy Assignment**: Different prompts for different LLM proxies
- **Per-User Group Assignment**: Fine-grained control via API keys/groups
- **Security & Compliance**: Enforce data protection, compliance, and behavioral guidelines
- **Audit Logging**: Complete logging of all prompt operations

#### 🔐 OAuth Proxy with Dynamic Client Registration
- **Dynamic Client Registration (DCR)**: RFC 7591 compliant automatic client registration
- **Dual Operating Modes**:
  - **Upstream Mode**: Pass-through proxy forwarding tokens to OAuth providers
  - **Gateway Mode**: Full OAuth 2.1 Authorization Server managing tokens
- **Automatic Discovery**: RFC 8414 compliant well-known endpoints
- **PKCE Enforcement**: Complete RFC 7636 support with dual PKCE flows
- **Supported Providers**: Google, GitHub, Azure AD, Okta, Auth0, GitLab, Keycloak, custom OAuth 2.0/2.1
- **Hybrid Authentication**: OAuth tokens AND API keys work simultaneously
- **User Attribution**: Full request attribution with identity, email, timestamps, risk scores
- **Secure Token Management**: AES-256-GCM encrypted storage with automatic refresh
- **Consent Screens**: Optional user consent for OAuth flows
- **Audit Logging**: Complete OAuth transaction logging for compliance (SOC2, ISO 27001, HIPAA, GDPR)
- **Zero Configuration Clients**: Works with Cursor IDE, Claude Desktop, and other MCP clients

#### 📊 Real-Time Monitoring & Analytics
- **Live Dashboard**: Real-time metrics, request rates, error rates, security alerts
- **Traffic Analysis**: Monitor all requests and responses through proxies
- **MCP Tool Discovery & Control**: Automatic discovery with fail-closed security (disabled by default)
- **LLM Token Usage Tracking**: Monitor consumption, costs, and usage patterns per proxy
- **WebSocket Integration**: Real-time updates without polling
- **Alert Management**: Advanced filtering, pagination, status workflow
- **Observability & Monitoring**: Langfuse, Prometheus, Grafana, OpenTelemetry, Jaeger integration
- **Integrations & Notifications**: SIEM, SOAR, Slack notifications

#### 📈 Observability & Metrics Monitoring
- **Langfuse**: Send LLM traces to Langfuse for observability and analytics, easily configured from the Settings
- **Prometheus Metrics**: Native metrics endpoint (`/api/v1/metrics/prometheus`)
- **Grafana Integration**: Pre-built dashboard queries and panels
- **OpenTelemetry Tracing**: Distributed tracing via OTLP protocol
- **Jaeger Integration**: Full support for trace visualization and debugging
- **Comprehensive Metrics**: Request percentiles (p50, p95, p99), database performance, connection pools, policy stats, WebSocket metrics, system resources
- **Production Ready**: Configurable sampling rates, trace propagation, OTLP-compatible backends
- **Zero Configuration**: Metrics enabled by default; tracing configurable via environment

#### 🛡️ MCP Vulnerability Scanner
- **Runtime Security Analysis**: Real-time vulnerability scanning of active MCP servers
- **Tool Permission Auditing**: Monitor and validate MCP tool capabilities and access levels
- **API Surface Assessment**: Comprehensive scanning of exposed methods and resources
- **Malicious Payload Detection**: Identify security risks in tool responses
- **Compliance Validation**: Ensure MCP servers meet security standards
- **Policy Integration**: Automatic blocking of vulnerable endpoints

#### 🚨 MCP Tool Change & Rug Pull Detection
- **Tool Behavior Monitoring**: Continuous analysis of execution patterns and capabilities
- **Change Detection**: Alert on unauthorized modifications to tool definitions, permissions, behavior
- **Rug Pull Prevention**: Detect sudden removal, disabling, or functionality changes
- **Supply Chain Security**: Monitor for malicious updates or compromised dependencies
- **Baseline Establishment**: Create security baselines and alert on deviations
- **Attribution Tracking**: Audit trails of configuration changes
- **Automated Response**: Automatically disable or quarantine suspicious tools

#### 🤖 Agent-to-Agent (A2A) Registry
- **Agent Registration**: Auto-discover via AgentCard URLs or manual JSON registration
- **AgentCard Management**: Automatic fetching and updating of capabilities/metadata
- **Access Control**: Fine-grained user group-based access with per-agent rate limiting
- **Agent Invocation**: Send messages with streaming response support (SSE)
- **Task Management**: Track stateful operations (submitted, working, completed, failed)
- **Security Integration**: All invocations validated by policy engine with risk scoring
- **Audit Logging**: Complete audit trails with user attribution and request/response payloads
- **Real-Time Monitoring**: View invocation logs, task states, agent usage analytics

#### 🕵️ Canary Token Detection
Canary Token Injection is a security feature that helps detect when data from one user or session is accidentally exposed to another. Think of it as a tripwire — an early warning system that alerts you to potential data leakage in your AI systems.

When proxying requests, the gateway silently injects unique, invisible tokens into each user's conversation. If a token surfaces where it shouldn't, you'll know immediately.

**Detection types:**
- **Cross-User Leakage**: A canary from User A appeared in a response to User B, indicating data bleed between users
- **Cross-Session Leakage**: A canary from Session A appeared in the same user's Session B, indicating session isolation failure
- **Provider Memorisation**: A canary resurfaced without being present in the current context, suggesting the LLM provider has memorised prior conversation data
- **Stale Canary**: A canary older than 7 days reappeared, a strong indicator of long-term memorisation by the model provider

#### 🛡️ Guardrails Evaluation
Guardrails Evaluation is automated penetration testing for your AI safety controls. It runs a comprehensive suite of security test cases against your endpoints and scores the results against the **OWASP LLM Top 10** and **NIST AI Risk Management Framework**.

**Key features:**

- **80+ built-in test cases** across 12 categories, with the ability to add your own custom tests
- **Compliance scoring** mapped to OWASP LLM Top 10 and NIST AI RMF
- **Test any endpoint**: works with any API that wraps an LLM, not just direct LLM providers. Import endpoints via curl command paste
- **Multi-turn attack simulation**: tests that span multiple conversation turns to detect escalation vulnerabilities
- **Per-category risk breakdown** with pass/fail rates and weighted risk scores

### 🔄 Cross App Access (XAA) - 🧪 Experimental
Okta Identity-JAG token support for cross-application access control:
- **ID-JAG Token Exchange**: Validate and exchange Okta Identity-JAG tokens for cross-app authorization
- **Client ID Mapping**: Configure mappings between IdP client IDs and resource authorization server client IDs
- **Token Revocation**: Revoke ID-JAG tokens individually by JTI or in bulk by subject/IdP provider
- **JWKS Caching**: Automatic fetching and caching of JWKS from Okta IdP for efficient token validation
- **Per-Proxy Configuration**: Enable XAA on specific proxy instances through the web interface
- **Statistics Dashboard**: Real-time monitoring of ID-JAG token usage, JWKS cache status, and client mapping counts
- **Audit Integration**: Complete audit logging of XAA events (token exchange, validation, revocation) for compliance
- **Web UI Management**: UI components for managing client mappings, viewing stats, and revoking tokens

**⚠️ Experimental Feature**: XAA currently supports Okta's proprietary ID-JAG token format. This feature is under active development and may change significantly as cross-app access standards evolve. Use with caution in production environments.


### ⚠️ Known Limitations

- **Beta Software**: Thorough testing recommended before production deployment
- **Static Analysis Limits**: Cannot detect all vulnerability types (e.g., semantic issues, prompt injection - Works to improve are planned)
- **Performance Variability**: May vary with large codebases or high-traffic environments
- **MCP Protocol Coverage**: Some advanced features may not be fully covered
- **Test Environments**: Recommended for testing and development environments


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

