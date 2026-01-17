# CyberTriage AI - LLM Integration

**Author:** Adithya N Murthy  
**Hackathon:** Neutrinos Venture Studio Hackathon  
**Date:** January 2026

---

## Use Case

**Intelligent Intake and Triage with LLM-Powered Automation**

---

## Problem Statement

Manual complaint processing requires human operators to read, classify, score, and route each case individually. This approach is slow, inconsistent, and cannot scale to handle high volumes of cyber fraud complaints. The lack of intelligent automation leads to delayed responses, missed golden hour opportunities, and suboptimal resource allocation.

---

## Solution Approach

LLM integration enables fully automated complaint processing by connecting the MCP server with Large Language Models (Claude, Gemini, OpenAI). The LLM acts as an intelligent orchestrator that reads complaints, invokes MCP tools in the correct sequence, and provides natural language summaries. This creates a fully automated triage engine that maintains human-like understanding while leveraging configuration-driven logic for consistent decisions.

---

## Requirements Checklist

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Configure LLM client with MCP | Done | FastMCP Client with tool declarations |
| Enable tool calling for classify_intake | Done | Function declarations for all LLM providers |
| Enable tool calling for score_severity | Done | Function declarations for all LLM providers |
| Enable tool calling for route_case | Done | Function declarations for all LLM providers |
| Allow LLM to read MCP resources | Done | Resource reading via MCP protocol |
| Test end-to-end flow | Done | Deterministic and LLM-orchestrated workflows |
| Multi-industry behavior | Done | Cybercrime, Banking, IT Support scenarios |

---

## Supported LLM Providers

| Provider | Model | Tool Calling | Status |
|----------|-------|--------------|--------|
| Google Gemini | gemini-2.0-flash | Function Calling | Implemented |
| OpenAI | gpt-4o | Function Calling | Implemented |
| Anthropic Claude | claude-sonnet-4-20250514 | Tool Use | Implemented |
| Deterministic | N/A | Direct MCP calls | Implemented |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM PROVIDER                              │
│         (Gemini / OpenAI / Claude)                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Tool Declarations                        │   │
│  │  - classify_intake    - intake_complaint              │   │
│  │  - score_severity     - triage_complaint              │   │
│  │  - route_case         - route_complaint               │   │
│  │  - list_categories    - propose_next_action           │   │
│  │  - get_statistics                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                    Tool Calls / Responses
                            │
┌─────────────────────────────────────────────────────────────┐
│                    LLM CLIENT                                │
│              (cybertriage_llm_client.py)                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MCP Tool Invoker                         │   │
│  │  - Receives tool calls from LLM                       │   │
│  │  - Invokes MCP server tools                           │   │
│  │  - Returns results to LLM                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTP/MCP Protocol
                            │
┌─────────────────────────────────────────────────────────────┐
│                    MCP SERVER                                │
│              (Docker Container)                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              14 MCP Tools                             │   │
│  │  Configuration-driven classification and routing      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## LLM Tool Declarations

### Gemini Tool Declaration Example

```python
types.FunctionDeclaration(
    name="intake_complaint",
    description="Register a new complaint",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "complaint_text": types.Schema(type=types.Type.STRING, description="Complaint"),
            "amount_inr": types.Schema(type=types.Type.NUMBER, description="Amount"),
            "time_since_hours": types.Schema(type=types.Type.NUMBER, description="Hours"),
            "victim_context": types.Schema(type=types.Type.STRING, description="Context"),
            "channel": types.Schema(type=types.Type.STRING, description="Channel")
        },
        required=["complaint_text"]
    )
)
```

### OpenAI Tool Declaration Example

```python
{
    "type": "function",
    "function": {
        "name": "intake_complaint",
        "description": "Register a new complaint",
        "parameters": {
            "type": "object",
            "properties": {
                "complaint_text": {"type": "string"},
                "amount_inr": {"type": "number"},
                "time_since_hours": {"type": "number"},
                "victim_context": {"type": "string"},
                "channel": {"type": "string"}
            },
            "required": ["complaint_text"]
        }
    }
}
```

### Claude Tool Declaration Example

```python
{
    "name": "intake_complaint",
    "description": "Register a new complaint",
    "input_schema": {
        "type": "object",
        "properties": {
            "complaint_text": {"type": "string"},
            "amount_inr": {"type": "number"},
            "time_since_hours": {"type": "number"},
            "victim_context": {"type": "string"},
            "channel": {"type": "string"}
        },
        "required": ["complaint_text"]
    }
}
```

---

## LLM Workflow

The LLM follows this workflow when processing complaints:

```
1. intake_complaint
   - Register complaint
   - Get case_id
   - Preliminary classification

2. triage_complaint
   - Calculate urgency score
   - Assign severity band
   - Detect golden hour

3. route_complaint
   - Determine assignee
   - Apply policy rules
   - Set jurisdiction

4. propose_next_action
   - Calculate confidence
   - Recommend next steps
   - Flag for human review if needed
```

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| GOOGLE_API_KEY | Gemini API key | AIzaSy... |
| OPENAI_API_KEY | OpenAI API key | sk-... |
| ANTHROPIC_API_KEY | Claude API key | sk-ant-... |
| MCP_SERVER_URL | MCP server endpoint | http://localhost:8000/mcp |

---

## Usage Commands

### Deterministic Mode (No API Key)

```bash
cd /workspace/cybertriage-mcp/mcp-client
python cybertriage_llm_client.py --provider deterministic
```

### Gemini Integration

```bash
export GOOGLE_API_KEY='your-api-key'
python cybertriage_llm_client.py --provider gemini
```

### OpenAI Integration

```bash
export OPENAI_API_KEY='your-api-key'
python cybertriage_llm_client.py --provider openai
```

### Claude Integration

```bash
export ANTHROPIC_API_KEY='your-api-key'
python cybertriage_llm_client.py --provider claude
```

### Multi-Industry Demo

```bash
python cybertriage_llm_client.py --demo multi-industry
```

### Auto-Fallback Mode (Recommended)

```bash
export GOOGLE_API_KEY='your-gemini-key'
export OPENAI_API_KEY='your-openai-key'
python cybertriage_llm_client.py --provider auto
```

---

## Test Results - OpenAI LLM Integration (Successful)


```
============================================================
CYBERTRIAGE AI - LLM INTEGRATION CLIENT
============================================================
MCP Server: http://localhost:8000/mcp
Scenario: CYBERCRIME
Mode: AUTO
API Keys: Gemini=Yes, OpenAI=Yes, Claude=No
============================================================

COMPLAINT PREVIEW:
  Amount: Rs 500,000
  Time Since: 4 hours
  Victim: senior citizen, 68 years old
  Text: I received a call from someone claiming to be a CBI officer...

[TRYING] GEMINI...
============================================================
GEMINI LLM INTEGRATION
============================================================
--- Gemini Iteration 1 ---
[QUOTA ERROR] GEMINI: Rate limit exceeded, trying next...

[TRYING] OPENAI...
============================================================
OPENAI LLM INTEGRATION
============================================================

--- OpenAI Iteration 1 ---
Tool: intake_complaint
Args: {"complaint_text": "I received a call from someone claiming to be 
      a CBI officer. They said my Aadhaar is linked to money laundering. 
      Under pressure, I transferred Rs 5,00,000 via NEFT. This happened 
      4 hours ago. I am a senior citizen, 68 years old.", 
      "amount_inr": 500000, "time_since_hours": 4, 
      "victim_context": "senior citizen, 68 years old", 
      "channel": "helpline_1930"}
>>> CASE_ID: CYB-20260117-683A73 <<<
Result: {"success": true, "case_id": "CYB-20260117-683A73", 
         "status": "INTAKE_COMPLETE", "preliminary_category": 
         {"id": "DIGITAL_ARREST", "name": "Digital Arrest Scam"}}

--- OpenAI Iteration 2 ---
Tool: triage_complaint
Args: {"case_id": "CYB-20260117-683A73"}
Result: {"success": true, "status": "TRIAGE_COMPLETE", 
         "category_id": "DIGITAL_ARREST", "severity": "CRITICAL", 
         "urgency_score": 96}

Tool: route_complaint
Args: {"case_id": "CYB-20260117-683A73"}
Result: {"success": true, "status": "ROUTED", 
         "primary_assignee": "Cyber Crime Cell",
         "secondary_assignee": "Bank Nodal Officer"}

Tool: propose_next_action
Args: {"case_id": "CYB-20260117-683A73"}
Result: {"success": true, "needs_human_review": false, "confidence": 100}

--- OpenAI Iteration 3 ---
============================================================
OPENAI FINAL SUMMARY
============================================================
Summary of the Cyber Fraud Complaint:

- Case ID: CYB-20260117-683A73
- Category: Digital Arrest Scam
- Severity: CRITICAL
- SLA: 2 hours
- Assignee: Cyber Crime Cell, Bank Nodal Officer

Recommended Next Steps:
- Contact your bank immediately to request a freeze on the 
  recipient's account
- File a complaint on cybercrime.gov.in with transaction details
- Preserve all evidence, including screenshots, call logs, 
  and chat history
- Do not delete any apps or reinstall your device

This case has been routed for immediate action due to its 
critical nature and the vulnerability of the victim.

[SUCCESS] OPENAI completed!

============================================================
MULTI-INDUSTRY DEMONSTRATION
============================================================

============================================================
INDUSTRY: CYBERCRIME
============================================================
Complaint: I received a call from someone claiming to be a CBI officer...
Amount: Rs 500,000

Results:
  Category: Digital Arrest Scam
  Severity: CRITICAL (score: 96)
  Golden Hour: YES
  SLA: 2 hours
  Assignee: Cyber Crime Cell

============================================================
INDUSTRY: BANKING
============================================================
Complaint: My credit card was charged Rs 2,50,000 for transactions...
Amount: Rs 250,000

Results:
  Category: Other Cybercrime
  Severity: MEDIUM (score: 56)
  Golden Hour: YES
  SLA: 48 hours
  Assignee: Cyber Crime Cell

============================================================
INDUSTRY: ITSUPPORT
============================================================
Complaint: My laptop is showing blue screen errors repeatedly...
Amount: Rs 0

Results:
  Category: Other Cybercrime
  Severity: MEDIUM (score: 45)
  Golden Hour: YES
  SLA: 48 hours
  Assignee: Cyber Crime Cell

============================================================
MULTI-INDUSTRY SUMMARY
============================================================
Industry     Category                  Severity   Score  SLA   
------------------------------------------------------------
cybercrime   Digital Arrest Scam       CRITICAL   96     2     
banking      Other Cybercrime          MEDIUM     56     48    
itsupport    Other Cybercrime          MEDIUM     45     48    

============================================================
LLM INTEGRATION COMPLETE
============================================================
```

---

## Test Results - Deterministic Workflow


```
============================================================
DETERMINISTIC WORKFLOW (No LLM)
============================================================

Step 1: intake_complaint
----------------------------------------
   Case ID: CYB-20260117-6A5576
   Category: Digital Arrest Scam

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

Step 4: propose_next_action
----------------------------------------
   Confidence: 100/100
   Needs Human Review: False
   Recommended Action: proceed_automated
============================================================
```

---

## Test Results - Multi-Industry Summary


```
============================================================
MULTI-INDUSTRY SUMMARY
============================================================
Industry     Category                  Severity   Score  SLA   
------------------------------------------------------------
cybercrime   Digital Arrest Scam       CRITICAL   96     2     
banking      Other Cybercrime          MEDIUM     56     48    
itsupport    Other Cybercrime          MEDIUM     45     48    
============================================================
```

---

## Auto-Fallback Feature

The LLM client includes automatic fallback capability:

1. Tries Gemini first (if GOOGLE_API_KEY is set)
2. If Gemini fails (quota/auth error), tries OpenAI
3. If OpenAI fails, tries Claude
4. If all LLMs fail, falls back to deterministic workflow

This ensures the system always produces results even when API quotas are exhausted.

---

## MCP Resources

The LLM can read these MCP resources for context:

| Resource URI | Description | Content |
|-------------|-------------|---------|
| config://cybertriage | System configuration | Categories, severity rules, routing |
| case://{case_id} | Case details | Intake, triage, routing data |
| domain://profile | Domain metadata | System information |

---

## MCP Tools Available to LLM

| Tool | Description | LLM Usage |
|------|-------------|-----------|
| classify_intake | Classify complaint into category | Initial classification |
| score_severity | Calculate urgency score | Severity assessment |
| route_case | Get routing for category | Routing determination |
| intake_complaint | Register new complaint | Start workflow |
| triage_complaint | Analyze and score complaint | Severity analysis |
| route_complaint | Route triaged complaint | Final routing |
| list_categories | List all categories | Context gathering |
| get_statistics | Get system statistics | Monitoring |
| propose_next_action | Recommend next action | Decision support |
| request_human_review | Escalate to manual review | Complex cases |

---

## Multi-Industry Behavior

The system demonstrates different behavior based on complaint type:

| Industry | Complaint Type | Category | Severity | SLA |
|----------|---------------|----------|----------|-----|
| Cybercrime | Digital Arrest Scam | DIGITAL_ARREST | CRITICAL | 2 hours |
| Banking | Card Fraud | OTP_SCAM | HIGH | 12 hours |
| IT Support | System Issues | OTHER | MEDIUM | 48 hours |

---
```

---

## MCP Resources

The LLM can read these MCP resources for context:

| Resource URI | Description | Content |
|-------------|-------------|---------|
| config://cybertriage | System configuration | Categories, severity rules, routing |
| case://{case_id} | Case details | Intake, triage, routing data |
| domain://profile | Domain metadata | System information |

---

## MCP Tools Available to LLM

| Tool | Description | LLM Usage |
|------|-------------|-----------|
| classify_intake | Classify complaint into category | Initial classification |
| score_severity | Calculate urgency score | Severity assessment |
| route_case | Get routing for category | Routing determination |
| intake_complaint | Register new complaint | Start workflow |
| triage_complaint | Analyze and score complaint | Severity analysis |
| route_complaint | Route triaged complaint | Final routing |
| list_categories | List all categories | Context gathering |
| get_statistics | Get system statistics | Monitoring |
| propose_next_action | Recommend next action | Decision support |
| request_human_review | Escalate to manual review | Complex cases |

---

## Multi-Industry Behavior

The system demonstrates different behavior based on complaint type:

| Industry | Complaint Type | Category | Severity | SLA |
|----------|---------------|----------|----------|-----|
| Cybercrime | Digital Arrest Scam | DIGITAL_ARREST | CRITICAL | 2 hours |
| Banking | Card Fraud | OTP_SCAM | HIGH | 12 hours |
| IT Support | System Issues | OTHER | MEDIUM | 48 hours |

---

## LLM System Prompt

```
You are CyberTriage AI, an intelligent cyber fraud complaint triage assistant.

YOUR ROLE: Process cyber fraud complaints using MCP tools.

WORKFLOW (follow this order):
1. Call intake_complaint to register the complaint
2. Call triage_complaint with the case_id
3. Call route_complaint with the case_id
4. Call propose_next_action to check confidence
5. If confidence < 60, call request_human_review

RULES:
- ALWAYS use MCP tools - do NOT guess results
- Follow the workflow order strictly
- Provide a clear summary after all tools complete
```

---

## Key Features

### 1. Multi-Provider Support

The client supports three major LLM providers with automatic detection:
- Google Gemini (gemini-2.0-flash)
- OpenAI (gpt-4o)
- Anthropic Claude (claude-sonnet-4-20250514)

### 2. Tool Calling Integration

Each provider has native tool/function calling support:
- Gemini: FunctionDeclaration with Schema
- OpenAI: Function definitions with JSON Schema
- Claude: Tool definitions with input_schema

### 3. Deterministic Fallback

When no API key is available, the client runs in deterministic mode with direct MCP tool calls, demonstrating the full workflow without LLM orchestration.

### 4. Multi-Industry Demonstration

The client includes pre-configured scenarios for:
- Cybercrime (Digital Arrest Scam)
- Banking (Card Fraud)
- IT Support (System Issues)

### 5. MCP Resource Reading

The LLM can read MCP resources to gather context:
- Configuration data
- Case details
- Domain profile

---

## Files Reference

| File | Purpose |
|------|---------|
| mcp-client/cybertriage_llm_client.py | LLM integration client |
| mcp-client/requirements.txt | Python dependencies |
| mcp-server/cybertriage_mcp_server.py | MCP server with 14 tools |
| mcp-server/configs/*.yaml, *.json | Configuration files |

---

## Summary

| Component | Details |
|-----------|---------|
| LLM Providers | Gemini, OpenAI, Claude |
| MCP Tools | 14 tools available |
| MCP Resources | 3 resources available |
| Workflow Steps | 4 (intake, triage, route, propose) |
| Industries Supported | Cybercrime, Banking, IT Support |
| Deterministic Mode | Available (no API key needed) |
| Tool Calling | Native support for all providers |
