# CyberTriage AI - MCP Server

Intelligent Cyber Fraud Complaint Intake and Triage System using Model Context Protocol (MCP).

**Author:** Adithya N Murthy  
**Event:** Neutrinos Venture Studio  
**Track:** Intelligent Intake and Triage MCP Server

---

## Quick Start Guide

### Prerequisites
- Python 3.11+
- Docker (optional, for containerized deployment)
- API Keys for LLM integration (OpenAI/Gemini/Claude)

---

## Terminal 1: Start MCP Server

```bash
# Navigate to server directory
cd /workspace/cybertriage-mcp/mcp-server

# Install dependencies (first time only)
pip install -r requirements.txt

# Start server (Memory Mode - Default)
python cybertriage_mcp_server.py
```

Server will start at: `http://0.0.0.0:8000/mcp`

---

## Terminal 2: Run MCP Client Test

```bash
# Open a NEW terminal
cd /workspace/cybertriage-mcp/mcp-client

# Install dependencies (first time only)
pip install -r requirements.txt

# Run client test
python cybertriage_mcp_client.py
```

This tests all 14 MCP tools with a sample complaint.

---

## Terminal 3: SQLite Persistence (Optional)

If you want persistent storage instead of in-memory:

```bash
# Stop any running server first (Ctrl+C in Terminal 1)

# Navigate to server directory
cd /workspace/cybertriage-mcp/mcp-server

# Create data directory
mkdir -p data

# Set SQLite mode and start server
export PERSIST_MODE=sqlite
python cybertriage_mcp_server.py
```

To verify SQLite database:
```bash
cd /workspace/cybertriage-mcp/mcp-server/data
sqlite3 cases.db "SELECT case_id, status FROM cases;"
```

---

## Terminal 4: Docker Deployment (Optional)

```bash
# Navigate to server directory
cd /workspace/cybertriage-mcp/mcp-server

# Build Docker image
docker build -t cybertriage-mcp-server:latest .

# Run container
docker run -d --name cybertriage-server -p 8000:8000 cybertriage-mcp-server:latest

# Check container status
docker ps

# View logs
docker logs cybertriage-server
```

To stop and remove:
```bash
docker stop cybertriage-server
docker rm cybertriage-server
```

---

## Terminal 5: LLM Integration

### Option A: Using Environment Variables (Recommended)

First, create the `.env` file:
```bash
cat > /workspace/cybertriage-mcp/.env << 'EOF'
# LLM API Keys
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here

# MCP Server Configuration
MCP_HOST=0.0.0.0
MCP_PORT=8000
PERSIST_MODE=memory
EOF
```

Then load and run:
```bash
cd /workspace/cybertriage-mcp/mcp-client

# Load environment variables
set -a
source /workspace/cybertriage-mcp/.env
set +a

# Run LLM client (auto-detects available API keys)
python cybertriage_llm_client.py --provider auto
```

### Option B: Export API Key Directly

```bash
cd /workspace/cybertriage-mcp/mcp-client

# For OpenAI
export OPENAI_API_KEY='your_openai_api_key_here'
python cybertriage_llm_client.py --provider openai

# OR for Gemini
export GOOGLE_API_KEY='your_gemini_api_key_here'
python cybertriage_llm_client.py --provider gemini

# OR for Claude
export ANTHROPIC_API_KEY='your_claude_api_key_here'
python cybertriage_llm_client.py --provider claude
```

### Option C: Deterministic Mode (No API Key Required)

```bash
cd /workspace/cybertriage-mcp/mcp-client
python cybertriage_llm_client.py --provider deterministic
```

---

## LLM Provider Options

| Provider | Flag | Environment Variable |
|----------|------|---------------------|
| Auto (tries all) | `--provider auto` | Any available key |
| OpenAI | `--provider openai` | `OPENAI_API_KEY` |
| Gemini | `--provider gemini` | `GOOGLE_API_KEY` |
| Claude | `--provider claude` | `ANTHROPIC_API_KEY` |
| Deterministic | `--provider deterministic` | None required |

---

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_HOST` | Server host address | `0.0.0.0` |
| `MCP_PORT` | Server port | `8000` |
| `PERSIST_MODE` | Storage mode (`memory` or `sqlite`) | `memory` |
| `CONFIG_PATH` | Path to config files | `./configs` |
| `INDUSTRY_PROFILE` | Industry profile name | `cybercrime` |
| `GOOGLE_API_KEY` | Gemini API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Claude API key | - |

---

## Multi-Industry Support

Switch between industries by changing the config path:

```bash
# Cybercrime (default)
export CONFIG_PATH=/workspace/cybertriage-mcp/mcp-server/configs

# Banking
export CONFIG_PATH=/workspace/cybertriage-mcp/industry-configs/banking

# IT Support
export CONFIG_PATH=/workspace/cybertriage-mcp/industry-configs/itsupport
```

---

## Project Structure and File Descriptions

```
cybertriage-mcp/
├── .env                          # Environment variables (API keys, config)
├── README.md                     # This file - setup and usage guide
├── docker-compose.yml            # Docker Compose for multi-container setup
│
├── mcp-server/                   # MCP Server Implementation
│   ├── cybertriage_mcp_server.py # Main MCP server with 14 tools, 3 resources, 3 prompts
│   ├── requirements.txt          # Python dependencies (fastmcp, uvicorn)
│   ├── Dockerfile                # Multi-stage Docker build configuration
│   ├── health_check.py           # Health check endpoint for Docker
│   ├── configs/                  # Configuration files (Cybercrime domain)
│   │   ├── category_taxonomy.yaml    # Fraud categories with keywords and risk scores
│   │   ├── severity_rules.json       # Severity bands, weights, golden hour rules
│   │   ├── routing_matrix.json       # Routing rules, assignees, escalation paths
│   │   ├── policy_rules.json         # Policy triggers and automated actions
│   │   └── domain_profile.json       # Domain metadata and settings
│   └── data/                     # Data storage directory
│       └── cases.db              # SQLite database (when PERSIST_MODE=sqlite)
│
├── mcp-client/                   # MCP Client Implementations
│   ├── cybertriage_mcp_client.py     # Test client - validates all MCP tools
│   ├── cybertriage_llm_client.py     # LLM client - OpenAI/Gemini/Claude integration
│   └── requirements.txt              # Python dependencies (httpx, openai, google-genai)
│
├── industry-configs/             # Industry-Specific Configurations
│   ├── banking/                  # Banking complaint handling configs
│   │   ├── category_taxonomy.yaml    # Banking fraud categories
│   │   ├── severity_rules.json       # Banking severity rules
│   │   ├── routing_matrix.json       # Banking routing rules
│   │   ├── policy_rules.json         # Banking policies
│   │   └── domain_profile.json       # Banking domain profile
│   └── itsupport/                # IT Support ticket handling configs
│       ├── category_taxonomy.yaml    # IT issue categories
│       ├── severity_rules.json       # IT severity rules
│       ├── routing_matrix.json       # IT routing rules
│       ├── policy_rules.json         # IT policies
│       └── domain_profile.json       # IT domain profile
│
└── Documentation/
    ├── COMPLETE_SOLUTION_DOCUMENTATION.html  # Full solution with terminal outputs
    ├── MCP_IMPLEMENTATION_DOCUMENTATION.md   # Technical implementation details
    ├── LLM_INTEGRATION_DOCUMENTATION.md      # LLM integration guide
    └── DOCKER_CONTAINERIZATION_DOCUMENTATION.md  # Docker setup guide
```

---

## File Descriptions

### MCP Server Files

| File | Description |
|------|-------------|
| `cybertriage_mcp_server.py` | Main MCP server implementing 14 tools for complaint intake, classification, severity scoring, and routing. Supports memory and SQLite storage modes. |
| `requirements.txt` | Server dependencies: fastmcp, uvicorn, sqlite3 |
| `Dockerfile` | Multi-stage Docker build with health checks and non-root user |
| `health_check.py` | HTTP health check endpoint for container orchestration |

### Configuration Files

| File | Description |
|------|-------------|
| `category_taxonomy.yaml` | Defines fraud categories with keywords for classification and risk scores (0-100) |
| `severity_rules.json` | Severity bands (CRITICAL/HIGH/MEDIUM/LOW), scoring weights, golden hour threshold, victim flags |
| `routing_matrix.json` | Routing rules mapping categories to assignees, jurisdictions, and escalation paths |
| `policy_rules.json` | Automated policy triggers based on severity, amount, and case attributes |
| `domain_profile.json` | Domain metadata including name, version, and supported features |

### MCP Client Files

| File | Description |
|------|-------------|
| `cybertriage_mcp_client.py` | Test client that validates all 14 MCP tools with sample complaints |
| `cybertriage_llm_client.py` | LLM integration client supporting OpenAI, Gemini, Claude with auto-fallback |
| `requirements.txt` | Client dependencies: httpx, openai, google-generativeai, anthropic |

---

## MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `classify_intake` | Classify complaint into fraud category using keyword matching |
| `score_severity` | Calculate urgency score (0-100) and severity band |
| `route_case` | Determine routing based on category and severity |
| `get_routing_rules` | Get routing configuration for a category |
| `intake_complaint` | Full intake workflow - creates case with evidence checklist |
| `triage_complaint` | Full triage workflow - scores and classifies case |
| `route_complaint` | Full routing workflow - assigns and triggers policies |
| `list_categories` | List all fraud categories from taxonomy |
| `get_case_status` | Get current status and details of a case |
| `update_case` | Update case information and notes |
| `list_cases` | List all cases in the system |
| `get_statistics` | Get system statistics and metrics |
| `propose_next_action` | MCP Sampling - confidence scoring for next action |
| `request_human_review` | MCP Sampling - escalate to manual review queue |

---

## MCP Resources

| Resource | Description |
|----------|-------------|
| `config://cybertriage` | Server configuration and capabilities |
| `case://{case_id}` | Individual case details by ID |
| `domain://profile` | Domain profile and metadata |

---

## Support

For issues or questions, refer to the documentation files or contact the author.
