# CyberTriage AI - MCP Server and Client Implementation

**Author:** Adithya N Murthy  
**Event:** Neutrinos Venture Studio  
**Track:** Intelligent Intake and Triage MCP Server  
**Date:** January 2026

---

## Use Case

**Intelligent Intake and Triage for Cyber Fraud Complaints**

---

## Problem Statement

Cyber fraud complaints in India face significant challenges in processing efficiency and response time. Traditional manual triage systems struggle with inconsistent categorization, delayed severity assessment, and suboptimal routing decisions. This results in critical cases being deprioritized, evidence degradation during the golden hour window, and inefficient resource allocation across law enforcement agencies.

---

## Solution Approach

CyberTriage AI addresses these challenges through a Model Context Protocol based intelligent system that automates complaint intake, triage, and routing workflows. The solution implements configuration-driven classification using keyword-based taxonomy, multi-factor urgency scoring with golden hour detection, and policy-based routing to appropriate law enforcement agencies.

---

## System Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| MCP Server | FastMCP (Python) | Exposes 14 tools for complaint processing |
| MCP Client | FastMCP Client (Python) | Demonstrates tool usage and LLM integration |
| Configuration | YAML/JSON | Drives all classification and routing logic |
| Storage | Pluggable (Memory/SQLite) | In-memory by default, SQLite optional |
| Transport | HTTP | Enables remote access on port 8000 |

**Storage Architecture:**
- Default: In-memory storage (stateless, container-ready)
- Optional: SQLite persistence (set `PERSIST_MODE=sqlite`)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP CLIENT                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Deterministic│  │   Gemini     │  │   OpenAI     │      │
│  │   Workflow   │  │ Integration  │  │  Integration │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTP/MCP Protocol
                            │
┌─────────────────────────────────────────────────────────────┐
│                      MCP SERVER                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              14 MCP Tools                            │   │
│  │  • classify_intake       • intake_complaint          │   │
│  │  • score_severity        • triage_complaint          │   │
│  │  • route_case            • route_complaint           │   │
│  │  • get_routing_rules     • list_categories           │   │
│  │  • get_case_status       • update_case               │   │
│  │  • list_cases            • get_statistics            │   │
│  │  • propose_next_action   • request_human_review      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Configuration Files (YAML/JSON)              │   │
│  │  • category_taxonomy.yaml  • routing_matrix.json     │   │
│  │  • severity_rules.json     • policy_rules.json       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Pluggable Storage (Stateless by Default)          │   │
│  │  • In-Memory (default)   • SQLite (optional)         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## MCP Tools

The server exposes 14 tools organized into four functional categories:

### Hackathon Required Tools (4)

| Tool Name | Input Parameters | Output | Purpose |
|-----------|-----------------|--------|---------|
| classify_intake | complaint_text | category_id, category_name, risk_score, matched_keywords | Classify complaint into fraud category |
| score_severity | amount_inr, time_since_hours, type_risk_score, victim_context | urgency_score, severity_band, sla_hours, golden_hour | Calculate urgency and severity |
| route_case | category_id, severity_band, amount_inr | primary_assignee, secondary_assignee, jurisdiction | Determine optimal routing |
| get_routing_rules | category_id (optional) | routing_rules, amount_thresholds | Retrieve routing configuration |

### Full Workflow Tools (3)

| Tool Name | Input Parameters | Output | Purpose |
|-----------|-----------------|--------|---------|
| intake_complaint | complaint_text, amount_inr, time_since_hours, victim_context, channel | case_id, preliminary_category, evidence_checklist | Register new complaint |
| triage_complaint | case_id | urgency_score, severity, golden_hour, sla_hours | Analyze and score complaint |
| route_complaint | case_id | primary_assignee, jurisdiction, policy_actions | Route triaged complaint |

### Utility Tools (5)

| Tool Name | Input Parameters | Output | Purpose |
|-----------|-----------------|--------|---------|
| list_categories | None | categories list | List all fraud categories |
| get_case_status | case_id | complete case details | Retrieve case information |
| update_case | case_id, status, notes | updated case info | Modify case data |
| list_cases | status (optional), limit | filtered case list | List all cases |
| get_statistics | None | system metrics | Get system statistics |

### MCP Sampling Directives (2)

| Tool Name | Input Parameters | Output | Purpose |
|-----------|-----------------|--------|---------|
| propose_next_action | case_id | needs_human_review, confidence, reasons, recommended_action | Analyze case and propose next action |
| request_human_review | case_id, reason, priority | review_request_id, review_queue, estimated_review_time | Escalate case to manual review |

---

## MCP Resources

| Resource URI | Description | Content |
|--------------|-------------|---------|
| config://cybertriage | Complete system configuration | Domain profile, severity rules, categories |
| case://{case_id} | Specific case details | Full case data including intake, triage, routing |
| domain://profile | Domain metadata | System information and parameters |

---

## MCP Prompts

| Prompt Name | Purpose | Usage |
|-------------|---------|-------|
| process_complaint | Step-by-step workflow guidance | Guides LLM through classify → score → route |
| triage_guidance | Tool usage instructions | Provides comprehensive tool documentation |
| golden_hour_alert | Urgent case alert template | Generates immediate action recommendations |

---

## Configuration Files

| Configuration File | Format | Purpose | Key Elements |
|-------------------|--------|---------|--------------|
| category_taxonomy.yaml | YAML | Fraud classification | 9 categories with keywords and risk scores |
| severity_rules.json | JSON | Urgency scoring | Weights, bands, SLA hours, golden hour threshold |
| routing_matrix.json | JSON | Case routing | Assignees, jurisdictions, escalation paths |
| policy_rules.json | JSON | Automated actions | 5 policies with conditions and triggers |
| domain_profile.json | JSON | System metadata | Domain info, version, operational parameters |

---

## Classification Engine

The classification system implements keyword-based matching with frequency scoring.

**Supported Fraud Categories:**

| Category ID | Category Name | Risk Score | Example Keywords |
|-------------|---------------|------------|------------------|
| DIGITAL_ARREST | Digital Arrest Scam | 90 | digital arrest, cbi officer, fake police |
| INVESTMENT_FRAUD | Investment/Trading Fraud | 85 | investment, trading, guaranteed returns |
| UPI_FRAUD | UPI/Payment Fraud | 70 | upi, phonepe, google pay, qr code |
| OTP_SCAM | OTP/Phishing Scam | 75 | otp, cvv, phishing, fake website |
| LOAN_APP | Loan App Harassment | 80 | loan app, harassment, morphed photos |
| REMOTE_APP | Remote Access Scam | 85 | anydesk, teamviewer, remote access |
| JOB_FRAUD | Job/Employment Fraud | 65 | job offer, work from home, registration fee |
| ECOMMERCE_FRAUD | E-commerce Fraud | 55 | online shopping, fake product, empty box |
| OTHER | Other Cybercrime | 40 | (fallback category) |

---

## Severity Scoring Engine

The urgency score calculation implements a weighted multi-factor model:

**Scoring Components:**

| Component | Weight | Range | Calculation Method |
|-----------|--------|-------|-------------------|
| Amount Score | 0.25 | 0-100 | Saturation curve (Rs 500,000 saturation) |
| Time Score | 0.30 | 0-100 | Golden hour boost + exponential decay |
| Type Risk Score | 0.25 | 0-100 | Direct category risk score |
| Victim Score | 0.20 | 30/100 | Binary (100 if vulnerable, 30 otherwise) |

**Formula:**
```
Urgency Score = (0.25 × Amount) + (0.30 × Time) + (0.25 × Type Risk) + (0.20 × Victim)
```

**Severity Bands:**

| Band | Score Range | SLA Hours | Description |
|------|-------------|-----------|-------------|
| CRITICAL | 80-100 | 2 | Immediate action required - money recovery possible |
| HIGH | 60-79 | 12 | Urgent attention needed - within golden hour |
| MEDIUM | 40-59 | 48 | Standard processing - good evidence available |
| LOW | 0-39 | 168 | Routine handling - limited recovery probability |

**Golden Hour Detection:**
- Threshold: 48 hours from incident
- Cases within golden hour receive time score boost
- Automatic policy triggers for golden hour cases

**Victim Vulnerability Flags:**
- Age-based: senior citizen, elderly, pensioner, student, minor
- Disability: disabled, handicapped
- Economic: widow, single mother, unemployed, farmer, daily wage, life savings

---

## Routing Engine

The routing system implements category-based routing with amount threshold overrides.

**Routing Matrix:**

| Category | Primary Assignee | Secondary Assignee | Jurisdiction |
|----------|-----------------|-------------------|--------------|
| DIGITAL_ARREST | Cyber Crime Cell | Bank Nodal Officer | State Cyber Cell |
| INVESTMENT_FRAUD | Economic Offences Wing | Cyber Crime Cell | EOW / State Cyber |
| UPI_FRAUD | Bank Nodal Officer | Cyber Crime Cell | Bank + Local Cyber |
| OTP_SCAM | Cyber Crime Cell | Bank Nodal Officer | State Cyber Cell |
| LOAN_APP | Cyber Crime Cell | RBI Ombudsman | State Cyber + RBI |
| REMOTE_APP | Cyber Crime Cell | Bank Nodal Officer | State Cyber Cell |
| JOB_FRAUD | Cyber Crime Cell | Labour Department | Local Police + Cyber |
| ECOMMERCE_FRAUD | Consumer Forum | Cyber Crime Cell | Consumer Court + Police |
| OTHER | Cyber Crime Cell | Local Police | State Cyber Cell |

**Amount-Based Thresholds:**

| Threshold | Amount (INR) | Action |
|-----------|-------------|--------|
| Bank Nodal Priority | ≥ 100,000 | Prioritize bank nodal officer involvement |
| Cyber Cell Mandatory | ≥ 1,000,000 | Mandatory cyber cell investigation |
| EOW Referral | ≥ 5,000,000 | Refer to Economic Offences Wing |

---

## Policy Engine

**Policy Rules:**

| Policy ID | Policy Name | Condition | Action | Priority |
|-----------|-------------|-----------|--------|----------|
| POL001 | Critical Digital Arrest Dual Routing | Severity=CRITICAL + Category=DIGITAL_ARREST | Dual routing to Cyber Cell and Bank | 1 |
| POL002 | High Amount Bank Freeze | Amount ≥ Rs 100,000 | Recommend immediate bank freeze | 2 |
| POL003 | Vulnerable Victim Escalation | Victim flag present | Auto-escalate severity by one level | 3 |
| POL004 | Evidence Cold Warning | Time ≥ 72 hours | Attach evidence degradation warning | 4 |
| POL005 | Golden Hour Alert | Within 48 hours | Trigger golden hour protocol | 1 |

---

## Storage Architecture

### Pluggable Storage Design

| Storage Mode | Description | Use Case | Container Ready |
|--------------|-------------|----------|-----------------|
| Memory (default) | In-memory dictionary storage | Development, demos, stateless containers | Yes - fully stateless |
| SQLite (optional) | SQLite database persistence | Production, data retention required | Yes - with volume mount |

**Configuration:**
```bash
# Stateless mode (default)
python cybertriage_mcp_server.py

# Persistent mode with SQLite
PERSIST_MODE=sqlite python cybertriage_mcp_server.py
```

**SQLite Schema:**
```sql
CREATE TABLE cases (
    case_id TEXT PRIMARY KEY,
    status TEXT,
    intake_data TEXT,      -- JSON
    triage_data TEXT,      -- JSON
    routing_data TEXT,     -- JSON
    notes TEXT,            -- JSON array
    created_at TEXT,
    last_updated TEXT
);

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

---

## Data Flow

### Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    INTAKE PHASE                              │
│  Complaint Submission → Generate Case ID → Classify         │
│  → Generate Evidence Checklist → Persist to Storage         │
│  → Return: case_id, category, checklist                     │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    TRIAGE PHASE                              │
│  Retrieve Case → Calculate Amount Score → Calculate Time    │
│  Score → Get Type Risk → Detect Victim Vulnerability        │
│  → Compute Weighted Urgency → Assign Severity Band + SLA    │
│  → Return: urgency_score, severity, sla, golden_hour        │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    ROUTING PHASE                             │
│  Retrieve Case + Triage → Apply Routing Matrix              │
│  → Evaluate Amount Thresholds → Evaluate Policy Rules       │
│  → Generate Routing Notes → Persist Routing Decisions       │
│  → Return: assignee, jurisdiction, policies, notes          │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Configuration-Driven Design

All system behavior is externalized to configuration files:

| Aspect | Configuration File | Modifiable Without Code |
|--------|-------------------|------------------------|
| Fraud Categories | category_taxonomy.yaml | Yes |
| Severity Scoring | severity_rules.json | Yes |
| Routing Rules | routing_matrix.json | Yes |
| Policy Actions | policy_rules.json | Yes |
| System Metadata | domain_profile.json | Yes |

### 2. Stateless Container Architecture

- Default: In-memory storage (fully stateless)
- No file system writes required
- Container restarts reset state
- Perfect for demos and horizontal scaling

### 3. MCP Sampling Directives

Intelligent case escalation with LLM-driven decision making:

- **propose_next_action**: Multi-factor confidence scoring (0-100)
- **request_human_review**: Escalates cases to manual review queues

**Confidence Thresholds:**
- ≥ 80: High confidence, proceed automated
- 60-79: Medium confidence, monitor
- < 60: Low confidence, human review recommended

### 4. Golden Hour Detection

48-hour critical window for maximum money recovery probability:
- Time score boost in urgency calculation
- Automatic policy trigger (POL005)
- Attached action recommendations

### 5. Multi-Factor Urgency Scoring

Combines four weighted factors:
- Amount Impact (25%)
- Temporal Urgency (30%)
- Fraud Type Severity (25%)
- Victim Vulnerability (20%)

### 6. Policy-Based Automation

Five automated policies trigger actions based on case characteristics.

---

## Deployment

### Local Development Setup

**Server:**
```bash
cd cybertriage-mcp/mcp-server
pip install -r requirements.txt
python cybertriage_mcp_server.py
```

**Client:**
```bash
cd cybertriage-mcp/mcp-client
pip install -r requirements.txt
python cybertriage_mcp_client.py
```

### Docker Deployment

**Build and Run:**
```bash
cd cybertriage-mcp/mcp-server
docker build -t cybertriage-mcp-server:latest .

# Run container (stateless)
docker run -d --name cybertriage-server -p 8000:8000 cybertriage-mcp-server:latest

# Run with SQLite persistence
docker run -d --name cybertriage-server -p 8000:8000 \
  -e PERSIST_MODE=sqlite \
  -v cybertriage-data:/app/data \
  cybertriage-mcp-server:latest
```

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| PERSIST_MODE | memory | Storage mode (memory/sqlite) |
| CONFIG_PATH | /app/configs | Configuration directory |
| MCP_HOST | 0.0.0.0 | Server bind address |
| MCP_PORT | 8000 | Server port |
| LOG_LEVEL | INFO | Logging level |
| INDUSTRY_PROFILE | cybercrime | Industry profile name |

### Industry Configuration Switching

Mount different config directories to switch industries:
```bash
# Banking industry
docker run -d -p 8000:8000 \
  -v ./industry-configs/banking:/app/configs:ro \
  cybertriage-mcp-server:latest

# IT Support industry
docker run -d -p 8001:8000 \
  -v ./industry-configs/itsupport:/app/configs:ro \
  cybertriage-mcp-server:latest
```

---

## Usage Examples

### Example 1: Basic Classification

**Input:**
```python
classify_intake(
    complaint_text="Someone called claiming to be CBI officer and threatened me with digital arrest."
)
```

**Output:**
```json
{
  "success": true,
  "category_id": "DIGITAL_ARREST",
  "category_name": "Digital Arrest Scam",
  "risk_score": 90,
  "matched_keywords": ["cbi officer", "digital arrest"]
}
```

### Example 2: Severity Assessment

**Input:**
```python
score_severity(
    amount_inr=200000,
    time_since_hours=6,
    type_risk_score=90,
    victim_context="senior citizen, 72 years old"
)
```

**Output:**
```json
{
  "success": true,
  "urgency_score": 87,
  "severity_band": "CRITICAL",
  "sla_hours": 2,
  "golden_hour": true,
  "victim_flag_present": true
}
```

### Example 3: Full Workflow

```python
# Step 1 - Intake
intake_complaint(complaint_text="UPI fraud - scanned QR code, Rs 50,000 debited", amount_inr=50000, time_since_hours=12)
# Returns: case_id="CYB-20260117-A3F2E1"

# Step 2 - Triage
triage_complaint(case_id="CYB-20260117-A3F2E1")
# Returns: urgency_score=68, severity="HIGH", golden_hour=true

# Step 3 - Route
route_complaint(case_id="CYB-20260117-A3F2E1")
# Returns: primary_assignee="Bank Nodal Officer"
```

---

## Technical Specifications

### Technology Stack

| Layer | Server | Client |
|-------|--------|--------|
| Framework | FastMCP | FastMCP Client |
| Language | Python 3.8+ | Python 3.8+ |
| Protocol | MCP over HTTP | MCP over HTTP |
| Configuration | YAML/JSON | N/A |
| Storage | Memory/SQLite | N/A |
| LLM Integration | N/A | OpenAI, Gemini, Claude |

### API Endpoints

| Endpoint | Protocol | Purpose |
|----------|----------|---------|
| http://0.0.0.0:8000 | HTTP | Server health check |
| http://0.0.0.0:8000/mcp | MCP | MCP protocol endpoint |

### Performance Characteristics

| Operation | Execution Time | Scalability |
|-----------|---------------|-------------|
| Classification | < 10ms | Linear with categories |
| Severity Scoring | < 5ms | Constant |
| Routing Lookup | < 5ms | O(1) dictionary lookup |
| Policy Evaluation | < 10ms | Linear with policies |

---

## Conclusion

CyberTriage AI demonstrates a production-ready MCP server and client implementation for intelligent cyber fraud complaint intake and triage. The configuration-driven architecture enables domain expert customization without code changes. The multi-factor urgency scoring with golden hour detection ensures critical cases receive immediate attention, while the policy-based automation streamlines routing decisions.

**Key Achievements:**
- 14 MCP tools for complete complaint processing
- Configuration-driven logic (no hardcoding)
- Multi-industry support (Cybercrime, Banking, IT Support)
- LLM integration with auto-fallback
- Docker containerization with health checks
- SQLite persistence option
- MCP Sampling Directives for human review escalation

**All components tested and verified working.**
