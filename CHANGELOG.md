# Changelog

All notable changes to the AI Security Gateway project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/).


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

