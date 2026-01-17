# CyberTriage AI - Docker Containerization

**Author:** Adithya N Murthy  
**Hackathon:** Neutrinos Venture Studio Hackathon  
**Date:** January 2026

---

## Use Case

**Containerized Deployment of CyberTriage AI MCP Server**

---

## Problem Statement

Deploying the CyberTriage AI MCP Server across different environments requires consistent configuration, dependency management, and runtime isolation. Manual deployment processes lead to environment-specific issues, dependency conflicts, and inconsistent behavior between development and production systems. The server needs to be portable, scalable, and production-ready with proper health monitoring and logging capabilities.

---

## Solution Approach

Docker containerization addresses these challenges by packaging the MCP server with all dependencies into a portable, isolated container. The solution implements a multi-stage build for optimized image size, health checks for container orchestration, environment variable configuration for runtime flexibility, and STDOUT logging for container-native log aggregation. The containerized server maintains full functionality while enabling deployment across any Docker-compatible environment.

---

## Requirements Checklist

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Multi-stage Docker build | Done | Builder + Runtime stages |
| Health check endpoint | Done | health_check.py with HEALTHCHECK directive |
| Environment variable configuration | Done | 6 configurable environment variables |
| STDOUT logging | Done | Python logging to console |
| Non-root user execution | Done | appuser with restricted permissions |
| Optimized image size | Done | Slim base image + multi-stage build |
| Volume mounts for configs | Done | /app/external_configs and /app/data |
| Port exposure | Done | Port 8000 exposed |

---

## Docker Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER HOST                               │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              DOCKER CONTAINER                          │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │           CyberTriage MCP Server                 │ │  │
│  │  │                                                  │ │  │
│  │  │  • FastMCP Framework                             │ │  │
│  │  │  • 14 MCP Tools                                  │ │  │
│  │  │  • 3 MCP Resources                               │ │  │
│  │  │  • 3 MCP Prompts                                 │ │  │
│  │  │  • Configuration-driven logic                    │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐                   │  │
│  │  │   Configs    │  │    Data      │                   │  │
│  │  │  /app/configs│  │  /app/data   │                   │  │
│  │  └──────────────┘  └──────────────┘                   │  │
│  │                                                        │  │
│  │  Port: 8000 ──────────────────────────────────────────│──│
│  │                                                        │  │
│  │  Health Check: python health_check.py                 │  │
│  │  User: appuser (non-root)                             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Dockerfile Implementation

### Multi-Stage Build

The Dockerfile implements a two-stage build process:

**Stage 1: Builder**
- Base image: python:3.11-slim
- Installs build dependencies (gcc)
- Installs Python packages to user directory
- Packages installed: fastmcp, uvicorn, pyyaml

**Stage 2: Runtime**
- Base image: python:3.11-slim
- Copies only installed packages from builder
- Creates non-root user (appuser)
- Configures environment variables
- Sets up health check
- Exposes port 8000

### Dockerfile Contents

```dockerfile
# CyberTriage AI - MCP Server Dockerfile
# Multi-stage build for optimized image size

# STAGE 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# STAGE 2: Runtime
FROM python:3.11-slim AS runtime
LABEL maintainer="Adithya N Murthy"
LABEL description="CyberTriage AI - Intelligent Cyber Fraud Complaint Intake & Triage MCP Server"
LABEL version="1.0.0"

RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Environment Variables
ENV PERSIST_MODE=memory
ENV CONFIG_PATH=/app/configs
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV LOG_LEVEL=INFO
ENV INDUSTRY_PROFILE=cybercrime

COPY --chown=appuser:appuser cybertriage_mcp_server.py .
COPY --chown=appuser:appuser health_check.py .
COPY --chown=appuser:appuser configs/ /app/configs/

RUN mkdir -p /app/data && chown appuser:appuser /app/data
RUN mkdir -p /app/external_configs && chown appuser:appuser /app/external_configs

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py || exit 1

VOLUME ["/app/external_configs", "/app/data"]
CMD ["python", "cybertriage_mcp_server.py"]
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PERSIST_MODE | memory | Storage mode: memory (stateless) or sqlite |
| CONFIG_PATH | /app/configs | Path to configuration files |
| MCP_HOST | 0.0.0.0 | Server bind address |
| MCP_PORT | 8000 | Server port |
| LOG_LEVEL | INFO | Logging level: DEBUG, INFO, WARNING, ERROR |
| INDUSTRY_PROFILE | cybercrime | Industry profile: cybercrime, banking, itsupport |

---

## Build and Run Commands

### Build Docker Image

```bash
cd /workspace/cybertriage-mcp/mcp-server
docker build -t cybertriage-mcp-server:latest .
```

### Run Container

```bash
docker run -d --name cybertriage-server -p 8000:8000 cybertriage-mcp-server:latest
```

### Check Container Status

```bash
docker ps
docker logs cybertriage-server
```

### Stop and Remove Container

```bash
docker stop cybertriage-server
docker rm cybertriage-server
```

---

## Docker Build Output

```
{hawcc}:/workspace/cybertriage-mcp/mcp-server$ docker build -t cybertriage-mcp-server:latest .
DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

Sending build context to Docker daemon  67.58kB
Step 1/29 : FROM python:3.11-slim AS builder
3.11-slim: Pulling from library/python
119d43eec815: Pull complete
5b09819094bb: Pull complete
3e731abb5c1d: Pull complete
0b2bf04f68e9: Pull complete
Digest: sha256:5be45dbade29bebd6886af6b438fd7e0b4eb7b611f39ba62b430263f82de36d2
Status: Downloaded newer image for python:3.11-slim
 ---> fa659464a114
Step 2/29 : WORKDIR /build
 ---> Running in 14eb0315a720
 ---> 63a3bc245c2c
Step 3/29 : RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
 ---> Running in 31d087715e09
...
Step 5/29 : RUN pip install --no-cache-dir --user -r requirements.txt
 ---> Running in 2c5152715244
Collecting fastmcp>=2.0.0 (from -r requirements.txt (line 1))
  Downloading fastmcp-2.14.3-py3-none-any.whl.metadata (20 kB)
Collecting uvicorn>=0.30.0 (from -r requirements.txt (line 2))
  Downloading uvicorn-0.40.0-py3-none-any.whl.metadata (6.7 kB)
...
Successfully installed PyYAML-6.0.3 annotated-types-0.7.0 anyio-4.12.1 
attrs-25.4.0 authlib-1.6.6 beartype-0.22.9 cachetools-6.2.4 certifi-2026.1.4 
cffi-2.0.0 click-8.3.1 cloudpickle-3.1.2 cryptography-46.0.3 cyclopts-4.5.0 
fastmcp-2.14.3 httpx-0.28.1 mcp-1.25.0 pydantic-2.12.5 rich-14.2.0 
starlette-0.51.0 uvicorn-0.40.0 websockets-16.0 ...
 ---> a506a41e2f4b
Step 6/29 : FROM python:3.11-slim AS runtime
 ---> fa659464a114
Step 7/29 : LABEL maintainer="Adithya N Murthy"
 ---> 6a7eb391ad17
...
Step 27/29 : HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD python health_check.py || exit 1
 ---> f0c179c1e57c
Step 28/29 : VOLUME ["/app/external_configs", "/app/data"]
 ---> 5925c20746f8
Step 29/29 : CMD ["python", "cybertriage_mcp_server.py"]
 ---> f2f248efb67c
Successfully built f2f248efb67c
Successfully tagged cybertriage-mcp-server:latest
```

---

## Container Runtime Output

```
{hawcc}:/workspace/cybertriage-mcp/mcp-server$ docker run -d --name cybertriage-server -p 8000:8000 cybertriage-mcp-server:latest
b491bdec1a81560daa3a8bdfbf354824cba0d8dc57c6a816594e6e2708682c42

{hawcc}:/workspace/cybertriage-mcp/mcp-server$ docker ps
CONTAINER ID   IMAGE                          COMMAND                  CREATED          STATUS                    PORTS                    NAMES
b491bdec1a81   cybertriage-mcp-server:latest  "python cybertriage_…"   38 seconds ago   Up 37 seconds (health: starting)   0.0.0.0:8000->8000/tcp   cybertriage-server

{hawcc}:/workspace/cybertriage-mcp/mcp-server$ docker logs cybertriage-server
╭──────────────────────────────────────────────────────────────────────────────╮
│                                                                              │
│                                                                              │
│    ▄▀▀ ▄▀█ █▀▀ ▀█▀ █▀▄▀█ █▀▀ █▀█                                            │
│    █▀  █▀█ ▄▄█  █  █ ▀ █ █▄▄ █▀▀                                            │
│                                                                              │
│                                                                              │
│    FastMCP 2.14.3                                                            │
│    https://gofastmcp.com                                                     │
│                                                                              │
│    Server: CyberTriage AI                                                    │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

[01/17/26 11:41:05] INFO     Starting MCP server 'CyberTriage AI'    server.py:2585
                             with transport 'http' on
                             http://0.0.0.0:8000/mcp
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

============================================================
CyberTriage AI - MCP Server Starting
============================================================
Domain: Cyber Fraud Triage
Categories loaded: 9
Policies loaded: 5
Storage Mode: MEMORY (stateless)

MCP Tools (14):
  - classify_intake       : Classify complaint into category
  - score_severity        : Calculate urgency score
  - route_case            : Get routing for category
  - get_routing_rules     : Get routing config
  - intake_complaint      : Full intake workflow
  - triage_complaint      : Full triage workflow
  - route_complaint       : Full routing workflow
  - list_categories       : List all categories
  - get_case_status       : Get case details
  - update_case           : Update case
  - list_cases            : List all cases
  - get_statistics        : Get system stats
  - propose_next_action   : MCP sampling directive (confidence scoring)
  - request_human_review  : MCP sampling directive (manual escalation)

MCP Resources (3):
  - config://cybertriage
  - case://{case_id}
  - domain://profile

MCP Prompts (3):
  - process_complaint     : Guide LLM through workflow
  - triage_guidance       : Tool usage instructions
  - golden_hour_alert     : Urgent case alert

Storage Configuration:
  - Default: In-memory (stateless)
  - Optional: SQLite (set PERSIST_MODE=sqlite)
  - Stateless container ready

Server: http://0.0.0.0:8000
MCP Endpoint: http://0.0.0.0:8000/mcp
============================================================
```

---

## Client Test Results

```
{hawcc}:/workspace/cybertriage-mcp/mcp-client$ python cybertriage_mcp_client.py

============================================================
CYBERTRIAGE AI - MCP CLIENT
============================================================
Server URL: http://localhost:8000/mcp
Scenario: CRITICAL
Gemini API: Not configured (deterministic mode)
============================================================

COMPLAINT PREVIEW:
Amount: Rs 500,000
Time Since: 4 hours
Victim: senior citizen, 68 years old, life savings lost
Text: I received a call from someone claiming to be a CBI officer.They said ...

============================================================
HACKATHON REQUIRED TOOLS DEMO
============================================================

1. classify_intake
----------------------------------------
Category: Digital Arrest Scam (DIGITAL_ARREST)
Risk Score: 90
Matched Keywords: ['cbi officer', 'money laundering', 'arrest warrant']
Config Source: category_taxonomy.yaml

2. score_severity
----------------------------------------
Urgency Score: 96/100
Severity Band: CRITICAL
SLA Hours: 2
Golden Hour: True
Config Source: severity_rules.json

3. route_case
----------------------------------------
Primary Assignee: Cyber Crime Cell
Secondary Assignee: Bank Nodal Officer
Jurisdiction: State Cyber Cell
Config Source: routing_matrix.json

4. get_routing_rules
----------------------------------------
Routing Rule Found: True
Escalation Path: ['District SP', 'State Cyber Head', 'CBI Cyber']
Config Source: routing_matrix.json

============================================================
FULL WORKFLOW DEMO (intake -> triage -> route)
============================================================

Step 1: intake_complaint
----------------------------------------
Case ID: CYB-20260117-B3F7C7
Category: Digital Arrest Scam
Evidence Checklist: 6 items

Step 2: triage_complaint
----------------------------------------
Severity: CRITICAL
Urgency Score: 96/100
Golden Hour: YES
SLA: 2 hours

Step 3: route_complaint
----------------------------------------
Primary Assignee: Cyber Crime Cell
Jurisdiction: State Cyber Cell
Policy Actions: 5

============================================================
UTILITY TOOLS DEMO
============================================================

list_categories
----------------------------------------
Total Categories: 9
  - DIGITAL_ARREST: Digital Arrest Scam (risk: 90)
  - INVESTMENT_FRAUD: Investment/Trading Fraud (risk: 85)
  - UPI_FRAUD: UPI/Payment Fraud (risk: 70)
  - OTP_SCAM: OTP/Phishing Scam (risk: 75)
  - LOAN_APP: Loan App Harassment (risk: 80)
  ... and 4 more

list_cases
----------------------------------------
Total in System: 1
  - CYB-20260117-B3F7C7: ROUTED (Digital Arrest Scam)

get_statistics
----------------------------------------
Total Cases: 1
Total Amount Reported: Rs 500,000
Golden Hour Cases: 1
Severity Distribution: {'CRITICAL': 1, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
Storage Mode: memory

============================================================
MCP SAMPLING DIRECTIVES DEMO
============================================================

Creating low-confidence case for sampling directive demo...
----------------------------------------
Case ID: CYB-20260117-189946
Category: Other Cybercrime

1. propose_next_action (MCP Sampling Directive)
----------------------------------------
Confidence: 10/100 (low)
Needs Human Review: True
Suggested Queue: information_gathering
Recommended Action: route_complaint
Reasons:
  - Category classified as OTHER - unclear fraud type
  - Low urgency score - may need additional information
  - No amount specified - financial impact unclear

2. request_human_review (MCP Sampling Directive)
----------------------------------------
Review Queue: high_priority_review_queue
Priority: high
Estimated Review Time: 8 hours
Status: PENDING_HUMAN_REVIEW

============================================================
FINAL SUMMARY - CYBERTRIAGE AI
============================================================

HACKATHON TOOLS (Config-Driven):
  Category: Digital Arrest Scam (risk: 90)
  Severity: CRITICAL (score: 96)
  Golden Hour: YES
  Assignee: Cyber Crime Cell

FULL WORKFLOW:
  Case ID: CYB-20260117-B3F7C7
  Status: ROUTED
  Category: Digital Arrest Scam
  Severity: CRITICAL (score: 96)
  Golden Hour: YES
  SLA: 2 hours
  Primary Assignee: Cyber Crime Cell
  Jurisdiction: State Cyber Cell

GOLDEN HOUR RECOMMENDATIONS:
  - Contact your bank immediately to request freeze on recipient account
  - File complaint on cybercrime.gov.in with transaction details
  - Preserve all evidence - screenshots, call logs, chat history

POLICY ACTIONS TRIGGERED:
  - [POL001] Case routed to both Cyber Cell and Bank Nodal Officer
  - [POL005] GOLDEN HOUR ACTIVE: Prioritize for immediate action
  - [POL002] URGENT: Initiate bank account freeze immediately
============================================================
```

---

## Health Check Configuration

The container includes a health check mechanism for container orchestration:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Interval | 30s | Time between health checks |
| Timeout | 10s | Maximum time for health check response |
| Start Period | 5s | Grace period before first check |
| Retries | 3 | Failed checks before unhealthy status |

**Health Check Script (health_check.py):**

```python
#!/usr/bin/env python3
import urllib.request
import sys

try:
    response = urllib.request.urlopen("http://127.0.0.1:8000/mcp", timeout=5)
    sys.exit(0)
except Exception:
    sys.exit(1)
```

---

## Industry Configuration Switching

The container supports multiple industry profiles through environment variables:

| Profile | Description | Config Path |
|---------|-------------|-------------|
| cybercrime | Default cyber fraud triage | /app/configs |
| banking | Banking fraud specialization | /app/external_configs/banking |
| itsupport | IT support ticket triage | /app/external_configs/itsupport |

**Running with Different Profiles:**

```bash
# Default cybercrime profile
docker run -d --name cybertriage-server -p 8000:8000 cybertriage-mcp-server:latest

# Banking profile with external configs
docker run -d --name cybertriage-server -p 8000:8000 \
  -e INDUSTRY_PROFILE=banking \
  -v ./industry-configs/banking:/app/external_configs/banking \
  cybertriage-mcp-server:latest

# IT Support profile
docker run -d --name cybertriage-server -p 8000:8000 \
  -e INDUSTRY_PROFILE=itsupport \
  -v ./industry-configs/itsupport:/app/external_configs/itsupport \
  cybertriage-mcp-server:latest
```

---

## Security Features

| Feature | Implementation |
|---------|----------------|
| Non-root execution | Container runs as appuser |
| Minimal base image | python:3.11-slim |
| No unnecessary packages | Multi-stage build removes build tools |
| Read-only configs | Config files owned by appuser |
| Volume isolation | Separate volumes for configs and data |

---

## Logging

Container logs are written to STDOUT for container-native log aggregation:

```bash
# View logs
docker logs cybertriage-server

# Follow logs
docker logs -f cybertriage-server

# View last 100 lines
docker logs --tail 100 cybertriage-server
```

---

## Summary

| Component | Details |
|-----------|---------|
| Base Image | python:3.11-slim |
| Build Type | Multi-stage (builder + runtime) |
| Image Tag | cybertriage-mcp-server:latest |
| Exposed Port | 8000 |
| Health Check | Every 30 seconds |
| User | appuser (non-root) |
| Storage Mode | Memory (stateless by default) |
| MCP Tools | 14 tools available |
| MCP Resources | 3 resources available |
| MCP Prompts | 3 prompts available |
| Categories | 9 fraud categories |
| Policies | 5 policy rules |

---

## Files Reference

| File | Purpose |
|------|---------|
| mcp-server/Dockerfile | Multi-stage Docker build configuration |
| mcp-server/health_check.py | Container health check script |
| mcp-server/.dockerignore | Files excluded from Docker context |
| mcp-server/requirements.txt | Python dependencies |
| docker-compose.yml | Multi-container orchestration |
| industry-configs/banking/* | Banking industry configuration |
| industry-configs/itsupport/* | IT Support industry configuration |
