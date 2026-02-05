# AI Security Gateway

[![Beta Release](https://img.shields.io/badge/Release-v2026.2.1--beta-orange?style=flat-square)](https://github.com/syphon1c/ai-security-gateway/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)


> **🚀 First Public Beta Release** - A security gateway and monitoring platform for LLM APIs, Model Context Protocol (MCP) servers and Agent-to-Agent (A2A) Registry.

## What is the AI Security Gateway?

The **AI Security Gateway** is a unified security platform that provides **real-time monitoring**, **policy enforcement**, and **threat detection** and a number of **new security controls** for Large Language Model (LLM) APIs, Model Context Protocol (MCP) servers and Agent-to-Agent (A2A). It acts as an intelligent proxy layer between your applications and AI services and tooling, giving you complete visibility and security control over AI interactions and automations.

Think of it as a **security gateway** for your AI infrastructure - monitoring every request, applying various security policies, tracking usage, and ensuring compliance with your organization's security requirements. Although this is just a personal project for my own testing and needs its grown a lot and ready for more users.

Getting started document can be found at [AI Security Gateway Docs](https://syphon1c.github.io/)

## ⚠️ Beta Release Notice

This is the **first public beta release (v2026.1.1-beta)** of the AI Security Gateway. While the software has been tested, please note:

- **Test thoroughly** before deploying to production/personal environments
- **Report bugs** and provide feedback via [GitHub Issues](https://github.com/syphon1c/ai-security-gateway/issues)
- **Review the [CHANGELOG.md](CHANGELOG.md)** for complete feature details and known limitations
- **Community feedback** is welcomed to help improve the software

**This is my personal project for testing, learning and personal requirements**


## 🎯 Key Features

### 💰 Budget Limits & Cost Control
Control spending and manage costs across teams and API keys:
- **Monthly Budget Limits**: Set spending limits per user group/team in USD
- **Configurable Warning Thresholds**: Alert when spending reaches a percentage of budget (e.g., 80%)
- **Flexible Enforcement**: Choose to block requests at threshold or just warn (allows continued access with warnings)
- **Automatic Monthly Reset**: Budgets automatically reset at the start of each calendar month
- **Manual Reset**: Reset budgets manually via API or web interface when needed
- **Real-Time Tracking**: Monitor current month spending, budget utilization, and remaining budget
- **Dashboard Metrics**: View budget status across all teams in the AI Usage Metrics dashboard
- **Request Blocking**: Automatic blocking when budget is exceeded (HTTP 402 Payment Required)

### 🔄 Multi-Proxy Management
Run and manage **multiple MCP and LLM proxy instances** simultaneously through an intuitive web interface:
- Create, configure, start, stop, and restart proxies with a few clicks
- Support for HTTP, WebSocket, and Server-Sent Events (SSE) transport protocols
- Centralized dashboard showing real-time status of all proxy instances
- Database-backed persistence for configurations, alerts, and audit logs
- Per-proxy health monitoring and performance metrics

### 🛡️ Custom Security Policies (Gaurdrails)
Apply **granular security policies** to individual proxies or groups:
- **250+ built-in default detection rules** across critical, high, medium, and low severity levels
- JSON-based policy configuration for easy customization
- Real-time threat detection and blocking (SQL injection, command injection, path traversal, Prompt Injection, Jailbreaking etc.)
- **Data Redaction & Unmasking**: Redact sensitive data sent to LLMs with automatic unmasking of responses - mask PII, secrets, and sensitive content before sending to providers, then automatically restore original values in responses for seamless user experience
- Policy templates: `llm-critical-security`, `llm-standard-security`, `mcp-advanced-security`, `mcp-encoding-detection-security.json`, `llm-compliance-gdpr.json` and more...
- Per-proxy policy assignment - different security levels for different use cases
- Custom policy creation for organization-specific requirements

### 💬 System Prompt Injection Governance
Inject **security controls and behavioral guidelines** directly into LLM requests:
- **Automatic Injection**: System governance prompts are automatically injected into LLM requests based on proxy or user group assignments
- **Priority-Based Selection**: Only the highest priority prompt is injected per request (user group prompts take precedence over proxy prompts)
- **Template Variables**: Dynamic variable substitution (e.g., `{{.User}}`, `{{.Date}}`, `{{.Organization}}`)
- **Per-Proxy Assignment**: Assign different prompts to different LLM proxies
- **Per-User Group Assignment**: Assign prompts to specific user groups/API keys for fine-grained control
- **Security & Compliance**: Enforce data protection policies, compliance requirements, and behavioral guidelines
- **Audit Logging**: All prompt operations are logged for compliance and security auditing

### 🔐 OAuth Proxy with Dynamic Client Registration
Flexible OAuth 2.1 proxy with automatic client registration and dual operating modes:
- **Dynamic Client Registration (DCR)**: RFC 7591 compliant - MCP/LLM clients automatically register and authenticate without manual configuration
- **Dual Operating Modes**:
  - **Upstream Mode**: Pass-through proxy forwarding tokens directly to OAuth providers 
  - **Gateway Mode**: Full OAuth 2.1 Authorization Server managing tokens on behalf of clients
- **Automatic Discovery**: RFC 8414 compliant well-known endpoints for zero-configuration client setup
- **PKCE Enforcement**: Complete RFC 7636 support with dual PKCE flows in Gateway mode (Client↔Gateway, Gateway↔Provider)
- **Supported Providers**: Google, GitHub, Azure AD, Okta, Auth0, GitLab, Keycloak, and custom OAuth 2.0/2.1 providers
- **Hybrid Authentication**: OAuth tokens AND API keys work simultaneously on the same proxy
- **User Attribution**: Full request attribution with user identity, email, timestamps, and risk scores
- **Secure Token Management**: AES-256-GCM encrypted token storage with automatic refresh in Gateway mode
- **Consent Screens**: Optional user consent for OAuth flows with scope visibility
- **Audit Logging**: Complete OAuth transaction logging for compliance (SOC2, ISO 27001, HIPAA, GDPR)
- **Zero Configuration Clients**: Cursor IDE, Claude Desktop, and other MCP clients work out-of-the-box

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

### 📊 Real-Time Monitoring & Analytics
Comprehensive visibility into your AI infrastructure:
- **Live Dashboard**: Real-time metrics, request rates, error rates, and security alerts
- **Traffic Analysis**: Monitor all requests and responses passing through proxies
- **MCP Tool Discovery & Control**: Automatic discovery with fail-closed security (tools disabled by default)
- **LLM Token Usage Tracking**: Monitor token consumption, costs, and usage patterns per proxy
- **Budget Limits & Cost Control**: Set monthly spending limits per team/API key with configurable warning thresholds and blocking
- **WebSocket Integration**: Real-time updates pushed to the web interface without polling
- **Alert Management**: Advanced filtering, pagination, and status workflow for security alerts
- **Observability & Monitoring:** - Langfuse, Prometheus, Grafana, OpenTelemetry, and Jaeger integration
- **Integrations & Notifications:** - SIEM, SOAR, and Slack notifications

### 📈 Observability & Metrics Monitoring
Enterprise-grade observability with industry-standard tools and Langfuse ready:
- **Langfuse**: Send LLM traces to Langfuse for observability and analytics, easily configured from the Settings
- **Prometheus Metrics**: Native Prometheus-compatible metrics endpoint (`/api/v1/metrics/prometheus`) with comprehensive system, request, database, and proxy metrics
- **Grafana Integration**: Pre-built dashboard queries and panels for visualizing gateway performance, error rates, request durations, and system health
- **OpenTelemetry Tracing**: Distributed tracing support via OTLP protocol for end-to-end request visibility across handlers, services, and repositories
- **Jaeger Integration**: Full Jaeger support for trace visualization and debugging with automatic span creation and context propagation
- **Comprehensive Metrics**: Request metrics (p50, p95, p99 percentiles), database query performance, connection pool utilization, policy evaluation statistics, WebSocket metrics, and system resource usage
- **Production Ready**: Configurable sampling rates, trace context propagation, and integration with any OTLP-compatible backend (Datadog, New Relic, custom collectors)
- **Zero Configuration**: Metrics enabled by default; tracing configurable via environment variables

### 🛡️ MCP Vulnerability Scanner
Advanced security scanning specifically for Model Context Protocol (MCP) servers:
- **Runtime Security Analysis**: Real-time vulnerability scanning of active MCP server endpoints
- **Tool Permission Auditing**: Monitor and validate MCP tool capabilities and access levels
- **API Surface Assessment**: Comprehensive scanning of exposed MCP methods and resources
- **Malicious Payload Detection**: Identify potential security risks in MCP tool responses
- **Compliance Validation**: Ensure MCP servers meet security standards and best practices
- **Integration with Policy Engine**: Automatic blocking of vulnerable MCP endpoints based on scan results

### 🚨 MCP Tool Change & Rug Pull Detection
Protect against malicious changes and supply chain attacks in MCP tools:
- **Tool Behavior Monitoring**: Continuous analysis of MCP tool execution patterns and capabilities
- **Change Detection**: Alert on unauthorized modifications to tool definitions, permissions, or behavior
- **Rug Pull Prevention**: Detect when MCP tools are suddenly removed, disabled, or their functionality changes
- **Supply Chain Security**: Monitor for malicious updates or compromised MCP server dependencies
- **Baseline Establishment**: Create security baselines for tool behavior and alert on deviations
- **Attribution Tracking**: Maintain audit trails of who made changes to MCP tool configurations
- **Automated Response**: Automatically disable or quarantine suspicious tools based on detection rules

### 🤖 Agent-to-Agent (A2A) Registry
Centralized management for A2A-compatible agents with complete security and access control:
- **Agent Registration**: Auto-discover agents via AgentCard URLs or manually register with JSON
- **AgentCard Management**: Automatic fetching and updating of agent capabilities and metadata
- **Access Control**: Fine-grained user group-based access with per-agent rate limiting
- **Agent Invocation**: Send messages to agents with support for streaming responses (SSE)
- **Task Management**: Track stateful operations with lifecycle states (submitted, working, completed, failed)
- **Security Integration**: All invocations validated by policy engine with risk scoring and blocking
- **Audit Logging**: Complete audit trails with user attribution, request/response payloads, and security events
- **Real-Time Monitoring**: View invocation logs, task states, and agent usage analytics


## 🚀 Quick Start

### Download Pre-Built Release (Recommended)

Download the latest release for your operating system from the [GitHub Releases](https://github.com/syphon1c/ai-security-gateway/releases) page:

**Available Platforms:**
- **Linux** (amd64, arm64): `unified-admin-linux-<arch>.tar.gz`
- **macOS** (amd64, arm64): `unified-admin-darwin-<arch>.tar.gz`
- **Windows** (amd64): `unified-admin-windows-amd64.zip`

### Easy Installation (3 Steps)

**Linux/macOS:**
```bash
# 1. Download and extract
curl -LO https://github.com/syphon1c/ai-security-gateway/releases/latest/download/unified-admin-linux-amd64.tar.gz
tar -xzf unified-admin-linux-amd64.tar.gz
cd unified-admin-linux-amd64

# 2. Run installation script (generates secure keys automatically) Optional - skip to ./start.sh
chmod +x install.sh verify.sh start.sh
./install.sh # skip for now and run ./verify.sj

# 3. Start the gateway
./start.sh
```

**Windows:**
```powershell
# 1. Extract unified-admin-windows-amd64.zip to a folder
cd unified-admin-windows-amd64

# 2. Copy environment template and edit
Copy-Item env.example .env
notepad .env  # Set JWT_SECRET and ENCRYPTION_KEY (see below)

# 3. Start the gateway
.\start.ps1
```

### Manual Installation (Alternative)

If you prefer to configure manually:

**Linux/macOS:**
```bash
# 1. Extract the release package
tar -xzf unified-admin-linux-amd64.tar.gz
cd unified-admin-linux-amd64

# 2. Copy environment template
cp env.example .env

# 3. Generate secure keys and edit .env
openssl rand -hex 32        # For JWT_SECRET
openssl rand -base64 32 | cut -c1-32  # For ENCRYPTION_KEY
nano .env  # Edit and set the keys

# 4. Verify installation (optional)
./verify.sh

# 5. Start the gateway
./start.sh
# Or manually: ./unified-admin
```

**Windows:**
```powershell
# 1. Extract the release package
cd unified-admin-windows-amd64

# 2. Copy environment template
Copy-Item env.example .env

# 3. Generate secure keys (using Git Bash or WSL)
# openssl rand -hex 32        # For JWT_SECRET
# openssl rand -base64 32 | cut -c1-32  # For ENCRYPTION_KEY
notepad .env  # Edit and set JWT_SECRET and ENCRYPTION_KEY

# 4. Start the gateway
.\start.ps1
# Or manually: .\unified-admin.exe
```

### Helper Scripts

The release package includes helpful scripts to make setup easier:

- **`install.sh`** (Linux/macOS) - Interactive installation (this is optional - quickstart with start.sh):
  - Generates secure JWT_SECRET and ENCRYPTION_KEY automatically
  - Creates and configures .env file
  - Optionally installs as a system service
  - Run: `./install.sh`

- **`verify.sh`** (Linux/macOS) - Verify installation:
  - Checks binary is executable
  - Validates .env configuration
  - Tests port availability
  - Checks Docker setup
  - Run: `./verify.sh`

- **`start.sh`** (Linux/macOS) / **`start.ps1`** (Windows) - Start services:
  - Starts backend API server
  - Optionally starts Docker frontend
  - Shows admin password on first run
  - Redirects logs to keep terminal clean
  - Run: `./start.sh` or `.\start.ps1`

### What's Included in Release Packages

Each release package includes everything you need:
- ✅ **Pre-built API server binary** (`unified-admin` or `unified-admin.exe`) - no Docker required
- ✅ **Helper scripts** - `install.sh`, `verify.sh`, `start.sh` (Unix) or `start.ps1` (Windows)
- ✅ **Service files** - Systemd service (Linux) or Launchd plist (macOS) for production
- ✅ **Pre-built frontend** - Production-optimized Vue.js app ready for Docker deployment
- ✅ **Docker configuration** - `docker-compose.frontend.yml` and `Dockerfile.frontend`
- ✅ **Default security policies** - 13 JSON policy files with 250+ detection rules
- ✅ **Configuration templates** - `env.example`
- ✅ **Documentation** - `QUICKSTART.md` and `INSTALL.md` guides

**No compilation required** - download, configure, and run!


### Required Configuration

Before running the gateway, you **MUST** configure these critical environment variables:

**Easiest way:** Use the installation script which generates secure keys automatically:
```bash
./install.sh  # Linux/macOS
```

**Manual configuration:**

1. **Copy environment template:**
   ```bash
   cp env.example .env  # Linux/macOS
   # or
   Copy-Item env.example .env  # Windows
   ```

2. **Generate Security Keys:**
   ```bash
   # Generate JWT secret (required for authentication)
   openssl rand -hex 32
   
   # Generate encryption key (required for OAuth session encryption)
   openssl rand -base64 32 | cut -c1-32
   ```

3. **Edit .env file** and set the generated keys:
   ```bash
   nano .env  # Linux/macOS
   # or
   notepad .env  # Windows
   ```
   
   Required variables:
   ```env
   JWT_SECRET=your-generated-jwt-secret-here
   ENCRYPTION_KEY=your-generated-encryption-key-here
   ENVIRONMENT=production  # Change from 'development' for production
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

4. **Verify configuration:**
   ```bash
   ./verify.sh  # Linux/macOS - checks your setup
   ```

5. **Start the Gateway:**
   ```bash
   ./start.sh  # Linux/macOS - starts backend + optional frontend
   # or
   .\start.ps1  # Windows
   # or manually:
   ./unified-admin  # Linux/macOS
   .\unified-admin.exe  # Windows
   ```

See `QUICKSTART.md` in the release package for detailed instructions.

### First Time Setup

1. **Start the gateway** using `./start.sh` (or `.\start.ps1` on Windows)
   - The script will display the admin password on first run
   - **Save this password immediately** - it's shown only once!

2. **Access the web interface**:
   - **Docker frontend**: http://localhost (if Docker frontend is running)
   - **Native backend**: http://localhost:8080

3. **Login** using:
   - Username: `admin`
   - Password: The temporary password shown during startup

4. **Change your password** immediately after first login

5. **Create Your First Proxy**:
   - Navigate to "Infrastructure → Proxy Management"
   - Click "Create Proxy" in the dashboard
   - Choose proxy type (MCP or LLM)
   - Configure target URL and port
   - Configure the listening port
   - Select security policies to apply
   - Click "Create" and then "Start"

6. **Monitor Traffic**: View real-time requests, alerts, and metrics in the dashboard

That's it! You now have a fully functional AI Security Gateway running.

**For detailed setup instructions, see `QUICKSTART.md` in the release package.**

#### Option 3: Frontend Deployment Options (Production)

For production deployments, you have two options for serving the frontend:

**A. Docker-based Frontend (Recommended):**
```bash
# 1. Start API server binary (as shown above)
./unified-admin &

# 2. Serve frontend via Docker + Nginx
# Frontend .env is already included in the release package
# Edit frontend/.env if needed to configure VITE_API_BASE_URL
docker-compose -f docker-compose.frontend.yml up -d
# Frontend available at http://localhost:80
```

**B. Manual Nginx/Apache Deployment:**
```bash
# 1. Build frontend for production
cd frontend
npm install
npm run build
# Frontend built to frontend/dist/

# 2. Deploy dist/ contents to your web server
# - Copy frontend/dist/* to nginx/apache document root
# - Configure reverse proxy for /api/* and /ws to backend:8080
```

**No Docker required for API server** - uses native Go binaries for optimal performance!


## 📖 Documentation

For detailed guides and advanced configuration, see the online documentation:

[AI Security Gateway Docs](https://syphon1c.github.io/)

## 🛠️ Basic Usage Examples

### Using the Web Interface (Recommended)

The easiest way to use the AI Security Gateway is through the web interface:

1. **Start the gateway**: `./unified-admin`
2. **Access the dashboard**: `http://localhost:8080`
3. **Create a proxy**:
   - Click "Add Proxy"
   - Enter proxy name and target URL
   - Select security policies
   - Click "Create" and "Start"
4. **Monitor traffic**: View real-time requests, alerts, and metrics


## 🤝 Support & Contributing

### 📚 Documentation
Documents can be found at [AI Security Gateway Docs](https://syphon1c.github.io/)

### 🐛 Bug Reports & Feature Requests  
This is a beta release - community feedback is welcomed! Use [GitHub Issues](https://github.com/syphon1c/ai-security-gateway/issues) to:
- Report bugs and unexpected behaviour
- Request new features or improvements  
- Share usage experiences and suggestions
- Contribute to documentation improvements

### 🤝 Contributing
Contributions will be welcomed once the full source code is released:
- Bug fixes and improvements
- New security detection rules and policies
- Documentation enhancements
- Test coverage improvements

**Note**: When using AI assistance for contributions, always verify the code works as expected and include appropriate tests, not against it buit verify please.

### 📞 Support
- **GitHub Issues**: Primary support channel for bug reports and questions
- **Documentation**: Comprehensive guides available: [AI Security Gateway Docs](https://syphon1c.github.io/)
- **Examples**: Sample configurations and usage patterns in [`/examples`](examples/)

## 📝 Development Note

This project has utilized AI assistance for portions of code implementation and documentation to enhance development efficiency while maintaining code quality and security standards through comprehensive testing and manual verification.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Special thanks to:
- Contributors and early adopters providing valuable feedback

---

**AI Security Gateway 2026.2.1-beta** - Test and secure your AI instances - meant for research and testing!

*Released as-is for testing and community feedback.*