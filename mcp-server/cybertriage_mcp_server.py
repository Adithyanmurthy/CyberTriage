"""
CyberTriage AI - Intelligent Cyber Fraud Complaint Intake & Triage MCP Server

MCP Tools (14 total):
- classify_intake: Classify complaint into fraud category
- score_severity: Calculate urgency score and severity band
- route_case: Determine optimal routing and assignment
- get_routing_rules: Get routing rules from config
- intake_complaint: Full intake workflow
- triage_complaint: Full triage workflow
- route_complaint: Full routing workflow
- list_categories: List all fraud categories
- get_case_status: Get case details
- update_case: Update case information
- list_cases: List all cases
- get_statistics: Get system statistics
- propose_next_action: MCP sampling directive for manual review escalation
- request_human_review: Request manual review for complex cases

Storage: Pluggable (in-memory by default, SQLite optional via PERSIST_MODE env var)

Author: Adithya N Murthy
Hackathon: Neutrinos Venture Studio Hackathon
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Optional

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("CyberTriage AI")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Storage mode: "memory" (stateless) or "sqlite" (persistent)
PERSIST_MODE = os.environ.get("PERSIST_MODE", "memory").lower()
DB_FILE = os.path.join(DATA_DIR, "cases.db") if PERSIST_MODE == "sqlite" else None

# In-memory storage (stateless by default)
MEMORY_STORE = {"cases": {}, "metadata": {"created_at": datetime.utcnow().isoformat(), "total_cases": 0}}


# ============================================================================
# CONFIG LOADERS
# ============================================================================

def load_json_config(filename: str) -> dict:
    """Load a JSON configuration file."""
    filepath = os.path.join(CONFIGS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml_config(filename: str) -> dict:
    """Simple YAML parser for taxonomy file (no PyYAML dependency)."""
    filepath = os.path.join(CONFIGS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    categories = []
    current_category = None
    in_keywords = False
    
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- id:"):
            if current_category:
                categories.append(current_category)
            current_category = {"id": stripped.split(":", 1)[1].strip(), "keywords": []}
            in_keywords = False
        elif stripped.startswith("name:") and current_category:
            current_category["name"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("risk_score:") and current_category:
            current_category["risk_score"] = int(stripped.split(":", 1)[1].strip())
        elif stripped == "keywords:":
            in_keywords = True
        elif stripped.startswith("- ") and in_keywords and current_category:
            keyword = stripped[2:].strip()
            if keyword and keyword != "[]":
                current_category["keywords"].append(keyword.lower())
        elif not stripped.startswith("-") and in_keywords:
            in_keywords = False
    
    if current_category:
        categories.append(current_category)
    
    return {"categories": categories}


# ============================================================================
# STORAGE LAYER - PLUGGABLE (MEMORY OR SQLITE)
# ============================================================================

def init_sqlite_db() -> None:
    """Initialize SQLite database with schema."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            status TEXT,
            intake_data TEXT,
            triage_data TEXT,
            routing_data TEXT,
            notes TEXT,
            created_at TEXT,
            last_updated TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def load_cases() -> dict:
    """Load cases from storage (memory or SQLite)."""
    if PERSIST_MODE == "sqlite":
        if not os.path.exists(DB_FILE):
            init_sqlite_db()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT case_id, status, intake_data, triage_data, routing_data, notes, created_at, last_updated FROM cases")
        rows = cursor.fetchall()
        
        cases = {}
        for row in rows:
            case_id, status, intake_data, triage_data, routing_data, notes, created_at, last_updated = row
            cases[case_id] = {
                "case_id": case_id,
                "status": status,
                "intake": json.loads(intake_data) if intake_data else None,
                "triage": json.loads(triage_data) if triage_data else None,
                "routing": json.loads(routing_data) if routing_data else None,
                "notes": json.loads(notes) if notes else [],
                "created_at": created_at,
                "last_updated": last_updated
            }
        
        cursor.execute("SELECT value FROM metadata WHERE key = 'total_cases'")
        total_row = cursor.fetchone()
        total_cases = int(total_row[0]) if total_row else len(cases)
        
        conn.close()
        
        return {
            "cases": cases,
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "total_cases": total_cases,
                "storage_mode": "sqlite"
            }
        }
    else:
        # In-memory storage (stateless)
        MEMORY_STORE["metadata"]["storage_mode"] = "memory"
        return MEMORY_STORE


def save_cases(data: dict) -> None:
    """Save cases to storage (memory or SQLite)."""
    data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
    data["metadata"]["total_cases"] = len(data["cases"])
    
    if PERSIST_MODE == "sqlite":
        if not os.path.exists(DB_FILE):
            init_sqlite_db()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        for case_id, case_data in data["cases"].items():
            cursor.execute("""
                INSERT OR REPLACE INTO cases 
                (case_id, status, intake_data, triage_data, routing_data, notes, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                case_data.get("status"),
                json.dumps(case_data.get("intake")) if case_data.get("intake") else None,
                json.dumps(case_data.get("triage")) if case_data.get("triage") else None,
                json.dumps(case_data.get("routing")) if case_data.get("routing") else None,
                json.dumps(case_data.get("notes", [])),
                case_data.get("created_at", datetime.utcnow().isoformat()),
                datetime.utcnow().isoformat()
            ))
        
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", 
                      ("total_cases", str(data["metadata"]["total_cases"])))
        
        conn.commit()
        conn.close()
    else:
        # In-memory storage - just update the global dict
        MEMORY_STORE.update(data)


def load_yaml_config(filename: str) -> dict:
    """Simple YAML parser for taxonomy file (no PyYAML dependency)."""
    filepath = os.path.join(CONFIGS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    categories = []
    current_category = None
    in_keywords = False
    
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- id:"):
            if current_category:
                categories.append(current_category)
            current_category = {"id": stripped.split(":", 1)[1].strip(), "keywords": []}
            in_keywords = False
        elif stripped.startswith("name:") and current_category:
            current_category["name"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("risk_score:") and current_category:
            current_category["risk_score"] = int(stripped.split(":", 1)[1].strip())
        elif stripped == "keywords:":
            in_keywords = True
        elif stripped.startswith("- ") and in_keywords and current_category:
            keyword = stripped[2:].strip()
            if keyword and keyword != "[]":
                current_category["keywords"].append(keyword.lower())
        elif not stripped.startswith("-") and in_keywords:
            in_keywords = False
    
    if current_category:
        categories.append(current_category)
    
    return {"categories": categories}


# Load configurations at startup
TAXONOMY = load_yaml_config("category_taxonomy.yaml")
SEVERITY_RULES = load_json_config("severity_rules.json")
ROUTING_MATRIX = load_json_config("routing_matrix.json")
POLICY_RULES = load_json_config("policy_rules.json")
DOMAIN_PROFILE = load_json_config("domain_profile.json")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_case_id() -> str:
    """Generate a unique case ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"CYB-{timestamp}-{unique_part}"


def classify_category(complaint_text: str) -> tuple:
    """Classify complaint into fraud category using keyword matching."""
    text_lower = complaint_text.lower()
    best_match = None
    best_score = 0
    matched_keywords = []
    
    for category in TAXONOMY["categories"]:
        matches = [kw for kw in category["keywords"] if kw in text_lower]
        if len(matches) > best_score:
            best_score = len(matches)
            best_match = category
            matched_keywords = matches
    
    if best_match and best_score > 0:
        return (best_match["id"], best_match["name"], best_match["risk_score"], matched_keywords)
    
    other = next((c for c in TAXONOMY["categories"] if c["id"] == "OTHER"), None)
    if other:
        return ("OTHER", other["name"], other["risk_score"], [])
    return ("OTHER", "Other Cybercrime", 40, [])


def check_victim_flags(victim_context: str) -> tuple:
    """Check if victim context contains priority flags."""
    if not victim_context:
        return False, []
    context_lower = victim_context.lower()
    matched_flags = [flag for flag in SEVERITY_RULES["victim_flags"] if flag in context_lower]
    return len(matched_flags) > 0, matched_flags


def calculate_urgency_score(amount_inr: float, time_since_hours: float, type_risk_score: int, victim_has_flag: bool) -> tuple:
    """Calculate urgency score (0-100) with decision trace."""
    weights = SEVERITY_RULES["weights"]
    saturation = SEVERITY_RULES["amount_saturation_inr"]
    golden_hours = SEVERITY_RULES["golden_hour_hours"]
    
    # Amount score (0-100)
    if amount_inr <= 0:
        amount_score = 0
    else:
        normalized = min(amount_inr / saturation, 1.0)
        amount_score = normalized * 100
    
    # Time score (0-100)
    if time_since_hours <= 0:
        time_score = 100
    elif time_since_hours <= golden_hours:
        time_score = 100 * (1 - (time_since_hours / golden_hours) * 0.5)
    else:
        hours_over = time_since_hours - golden_hours
        time_score = max(0, 50 * (0.9 ** (hours_over / 24)))
    
    type_score = min(type_risk_score, 100)
    victim_score = 100 if victim_has_flag else 30
    
    raw_score = (
        weights["amount"] * amount_score +
        weights["time_since_hours"] * time_score +
        weights["type_risk"] * type_score +
        weights["victim_priority"] * victim_score
    )
    
    final_score = int(min(max(raw_score, 0), 100))
    
    decision_trace = {
        "components": {
            "amount_score": round(amount_score, 2),
            "time_score": round(time_score, 2),
            "type_risk_score": type_score,
            "victim_score": victim_score
        },
        "weights": weights,
        "raw_score": round(raw_score, 2),
        "final_score": final_score,
        "calculation": f"({weights['amount']}*{round(amount_score,1)}) + ({weights['time_since_hours']}*{round(time_score,1)}) + ({weights['type_risk']}*{type_score}) + ({weights['victim_priority']}*{victim_score}) = {round(raw_score,1)}"
    }
    
    return final_score, decision_trace


def get_severity_band(score: int) -> tuple:
    """Get severity band, SLA hours, and description from score."""
    bands = SEVERITY_RULES["bands"]
    for band_name in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        band = bands[band_name]
        if score >= band["min_score"]:
            return band_name, band["sla_hours"], band["description"]
    return "LOW", bands["LOW"]["sla_hours"], bands["LOW"]["description"]


def evaluate_policies(case_data: dict) -> list:
    """Evaluate policy rules and return triggered actions."""
    triggered = []
    for policy in POLICY_RULES["policies"]:
        condition = policy["condition"]
        matches = True
        
        if "severity" in condition:
            if case_data.get("triage", {}).get("severity") != condition["severity"]:
                matches = False
        if "category" in condition and matches:
            if case_data.get("triage", {}).get("category_id") != condition["category"]:
                matches = False
        if "amount_gte" in condition and matches:
            if case_data.get("intake", {}).get("amount_inr", 0) < condition["amount_gte"]:
                matches = False
        if "victim_flag_present" in condition and matches:
            if not case_data.get("triage", {}).get("victim_flag_present", False):
                matches = False
        if "golden_hour" in condition and matches:
            if case_data.get("triage", {}).get("golden_hour") != condition["golden_hour"]:
                matches = False
        
        if matches:
            action_msg = POLICY_RULES["action_messages"].get(policy["action"], policy["description"])
            triggered.append({
                "policy_id": policy["id"],
                "policy_name": policy["name"],
                "action": policy["action"],
                "message": action_msg,
                "priority": policy["priority"]
            })
    
    triggered.sort(key=lambda x: x["priority"])
    return triggered


def get_evidence_checklist(category_id: str) -> list:
    """Get evidence checklist based on fraud category."""
    base_checklist = [
        "Screenshot of fraudulent transaction(s)",
        "Bank statement showing debit (last 7 days)",
        "Any communication with scammer (SMS, WhatsApp, email)"
    ]
    category_specific = {
        "DIGITAL_ARREST": ["Call recording if available", "Screenshot of video call if taken", "Note the phone number that called you"],
        "UPI_FRAUD": ["UPI transaction ID/reference number", "Screenshot of UPI app showing transaction", "QR code image if scanned"],
        "OTP_SCAM": ["SMS showing OTP request", "Screenshot of fake website/link if clicked", "Bank alert SMS"],
        "REMOTE_APP": ["Name of app installed (AnyDesk, TeamViewer, etc.)", "Do NOT uninstall the app yet", "Screenshot of app showing connection ID"],
        "LOAN_APP": ["App name and download source", "Screenshots of harassment messages", "Loan agreement/terms if available"],
        "INVESTMENT_FRAUD": ["Investment app/website details", "Screenshots of promised returns", "All transaction receipts"]
    }
    specific = category_specific.get(category_id, [])
    return base_checklist + specific


# ============================================================================
# MCP TOOLS - HACKATHON REQUIRED (classify_intake, score_severity, route_case, get_routing_rules)
# ============================================================================

@mcp.tool()
def classify_intake(complaint_text: str) -> dict[str, Any]:
    """
    Classify a complaint into a fraud category using config-driven taxonomy.
    
    Args:
        complaint_text: Full description of the fraud incident
    
    Returns:
        category_id, category_name, risk_score, matched_keywords, confidence
    """
    if not complaint_text or len(complaint_text.strip()) < 5:
        return {"success": False, "error": "Complaint text required", "error_code": "INVALID_INPUT"}
    
    category_id, category_name, risk_score, matched_keywords = classify_category(complaint_text)
    confidence = min(len(matched_keywords) * 20, 100) if matched_keywords else 10
    
    return {
        "success": True,
        "category_id": category_id,
        "category_name": category_name,
        "risk_score": risk_score,
        "matched_keywords": matched_keywords,
        "confidence": confidence,
        "config_source": "category_taxonomy.yaml"
    }


@mcp.tool()
def score_severity(amount_inr: float = 0.0, time_since_hours: float = 0.0, type_risk_score: int = 50, victim_context: str = "") -> dict[str, Any]:
    """
    Calculate urgency score and severity band using config-driven rules.
    
    Args:
        amount_inr: Amount lost in Indian Rupees
        time_since_hours: Hours since incident occurred
        type_risk_score: Risk score from category (0-100)
        victim_context: Additional context about victim
    
    Returns:
        urgency_score, severity_band, sla_hours, golden_hour status, decision_trace
    """
    victim_has_flag, victim_flags = check_victim_flags(victim_context)
    urgency_score, decision_trace = calculate_urgency_score(amount_inr, time_since_hours, type_risk_score, victim_has_flag)
    severity, sla_hours, description = get_severity_band(urgency_score)
    golden_hour = time_since_hours <= SEVERITY_RULES["golden_hour_hours"]
    
    return {
        "success": True,
        "urgency_score": urgency_score,
        "severity_band": severity,
        "severity_description": description,
        "sla_hours": sla_hours,
        "golden_hour": golden_hour,
        "golden_hour_threshold": SEVERITY_RULES["golden_hour_hours"],
        "victim_flag_present": victim_has_flag,
        "victim_flags_matched": victim_flags,
        "decision_trace": decision_trace,
        "config_source": "severity_rules.json"
    }


@mcp.tool()
def route_case(category_id: str, severity_band: str = "MEDIUM", amount_inr: float = 0.0) -> dict[str, Any]:
    """
    Determine optimal routing using config-driven routing matrix.
    
    Args:
        category_id: Fraud category ID from classify_intake
        severity_band: Severity band from score_severity
        amount_inr: Amount lost for threshold-based routing
    
    Returns:
        primary_assignee, secondary_assignee, jurisdiction, escalation_path, routing_notes
    """
    routes = ROUTING_MATRIX["routes"]
    route_info = routes.get(category_id, routes.get("OTHER", {}))
    
    if not route_info:
        return {"success": False, "error": f"No routing rules for category: {category_id}", "error_code": "NO_ROUTE"}
    
    routing_notes = [route_info.get("notes", "")]
    thresholds = ROUTING_MATRIX["amount_thresholds"]
    
    if amount_inr >= thresholds["eow_referral"]:
        routing_notes.append(f"Amount >= {thresholds['eow_referral']:,} - EOW referral recommended")
    elif amount_inr >= thresholds["cyber_cell_mandatory"]:
        routing_notes.append(f"Amount >= {thresholds['cyber_cell_mandatory']:,} - Cyber Cell mandatory")
    elif amount_inr >= thresholds["bank_nodal_priority"]:
        routing_notes.append(f"Amount >= {thresholds['bank_nodal_priority']:,} - Bank Nodal priority")
    
    return {
        "success": True,
        "category_id": category_id,
        "primary_assignee": route_info.get("primary_assignee", "Cyber Crime Cell"),
        "secondary_assignee": route_info.get("secondary_assignee", "Local Police"),
        "jurisdiction": route_info.get("jurisdiction", "State Cyber Cell"),
        "escalation_path": route_info.get("escalation_path", []),
        "routing_notes": routing_notes,
        "config_source": "routing_matrix.json"
    }


@mcp.tool()
def get_routing_rules(category_id: str = "") -> dict[str, Any]:
    """
    Get routing rules from configuration.
    
    Args:
        category_id: Optional - specific category to get rules for. If empty, returns all rules.
    
    Returns:
        Routing rules from routing_matrix.json
    """
    if category_id:
        routes = ROUTING_MATRIX["routes"]
        if category_id in routes:
            return {
                "success": True,
                "category_id": category_id,
                "routing_rule": routes[category_id],
                "amount_thresholds": ROUTING_MATRIX["amount_thresholds"],
                "config_source": "routing_matrix.json"
            }
        else:
            return {"success": False, "error": f"Category {category_id} not found", "available_categories": list(routes.keys())}
    
    return {
        "success": True,
        "all_routes": ROUTING_MATRIX["routes"],
        "amount_thresholds": ROUTING_MATRIX["amount_thresholds"],
        "total_categories": len(ROUTING_MATRIX["routes"]),
        "config_source": "routing_matrix.json"
    }


# ============================================================================
# MCP TOOLS - FULL WORKFLOW (intake_complaint, triage_complaint, route_complaint)
# ============================================================================

@mcp.tool()
def intake_complaint(complaint_text: str, amount_inr: float = 0.0, time_since_hours: float = 0.0, victim_context: str = "", channel: str = "web_form") -> dict[str, Any]:
    """
    Receive and process a new cyber fraud complaint.
    
    Args:
        complaint_text: Full description of the fraud incident
        amount_inr: Amount lost in Indian Rupees (0 if unknown)
        time_since_hours: Hours since the incident occurred
        victim_context: Additional context about victim (e.g., senior citizen)
        channel: Intake channel (web_form, whatsapp, helpline_1930, mobile_app)
    
    Returns:
        case_id, preliminary category, evidence checklist
    """
    if not complaint_text or len(complaint_text.strip()) < 10:
        return {"success": False, "error": "Complaint text required (min 10 chars)", "error_code": "INVALID_INPUT"}
    
    case_id = generate_case_id()
    category_id, category_name, risk_score, matched_keywords = classify_category(complaint_text)
    evidence_checklist = get_evidence_checklist(category_id)
    
    case_data = {
        "case_id": case_id,
        "status": "INTAKE_COMPLETE",
        "intake": {
            "complaint_text": complaint_text,
            "amount_inr": amount_inr,
            "time_since_hours": time_since_hours,
            "victim_context": victim_context,
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat(),
            "preliminary_category": {"id": category_id, "name": category_name, "matched_keywords": matched_keywords}
        },
        "triage": None,
        "routing": None
    }
    
    cases_data = load_cases()
    cases_data["cases"][case_id] = case_data
    save_cases(cases_data)
    
    return {
        "success": True,
        "case_id": case_id,
        "status": "INTAKE_COMPLETE",
        "preliminary_category": {"id": category_id, "name": category_name},
        "evidence_checklist": evidence_checklist,
        "intake_timestamp": case_data["intake"]["timestamp"],
        "message": "Complaint registered. Gather evidence items and proceed to triage."
    }


@mcp.tool()
def triage_complaint(case_id: str) -> dict[str, Any]:
    """
    Analyze a complaint and assign urgency score, severity, and SLA.
    
    Args:
        case_id: The case ID from intake_complaint
    
    Returns:
        Urgency score, severity band, golden hour status, SLA, decision trace
    """
    cases_data = load_cases()
    if case_id not in cases_data["cases"]:
        return {"success": False, "error": f"Case {case_id} not found", "error_code": "CASE_NOT_FOUND"}
    
    case_data = cases_data["cases"][case_id]
    intake = case_data["intake"]
    
    category_id, category_name, type_risk_score, matched_keywords = classify_category(intake["complaint_text"])
    victim_has_flag, victim_flags_matched = check_victim_flags(intake["victim_context"])
    urgency_score, decision_trace = calculate_urgency_score(intake["amount_inr"], intake["time_since_hours"], type_risk_score, victim_has_flag)
    severity, sla_hours, severity_description = get_severity_band(urgency_score)
    golden_hour = intake["time_since_hours"] <= SEVERITY_RULES["golden_hour_hours"]
    
    golden_hour_recommendations = SEVERITY_RULES["golden_hour_recommendations"] if golden_hour else []
    
    triage_result = {
        "category_id": category_id,
        "category_name": category_name,
        "matched_keywords": matched_keywords,
        "urgency_score": urgency_score,
        "severity": severity,
        "severity_description": severity_description,
        "sla_hours": sla_hours,
        "golden_hour": golden_hour,
        "golden_hour_recommendations": golden_hour_recommendations,
        "victim_flag_present": victim_has_flag,
        "victim_flags_matched": victim_flags_matched,
        "decision_trace": decision_trace,
        "triage_timestamp": datetime.utcnow().isoformat()
    }
    
    case_data["triage"] = triage_result
    case_data["status"] = "TRIAGE_COMPLETE"
    cases_data["cases"][case_id] = case_data
    save_cases(cases_data)
    
    return {"success": True, "case_id": case_id, "status": "TRIAGE_COMPLETE", **triage_result}


@mcp.tool()
def route_complaint(case_id: str) -> dict[str, Any]:
    """
    Determine optimal routing for a triaged complaint.
    
    Args:
        case_id: The case ID that has been triaged
    
    Returns:
        Primary assignee, jurisdiction, escalation path, policy actions
    """
    cases_data = load_cases()
    if case_id not in cases_data["cases"]:
        return {"success": False, "error": f"Case {case_id} not found", "error_code": "CASE_NOT_FOUND"}
    
    case_data = cases_data["cases"][case_id]
    if not case_data.get("triage"):
        return {"success": False, "error": f"Case {case_id} not triaged yet", "error_code": "NOT_TRIAGED"}
    
    triage = case_data["triage"]
    intake = case_data["intake"]
    category_id = triage["category_id"]
    
    routes = ROUTING_MATRIX["routes"]
    route_info = routes.get(category_id, routes["OTHER"])
    policy_actions = evaluate_policies(case_data)
    
    routing_notes = [route_info["notes"]]
    amount = intake["amount_inr"]
    thresholds = ROUTING_MATRIX["amount_thresholds"]
    
    if amount >= thresholds["eow_referral"]:
        routing_notes.append(f"Amount >= {thresholds['eow_referral']:,} - EOW referral")
    elif amount >= thresholds["cyber_cell_mandatory"]:
        routing_notes.append(f"Amount >= {thresholds['cyber_cell_mandatory']:,} - Cyber Cell mandatory")
    
    routing_result = {
        "primary_assignee": route_info["primary_assignee"],
        "secondary_assignee": route_info["secondary_assignee"],
        "jurisdiction": route_info["jurisdiction"],
        "escalation_path": route_info["escalation_path"],
        "routing_notes": routing_notes,
        "policy_actions": policy_actions,
        "sla_hours": triage["sla_hours"],
        "routing_timestamp": datetime.utcnow().isoformat()
    }
    
    case_data["routing"] = routing_result
    case_data["status"] = "ROUTED"
    cases_data["cases"][case_id] = case_data
    save_cases(cases_data)
    
    return {
        "success": True,
        "case_id": case_id,
        "status": "ROUTED",
        **routing_result,
        "triage_summary": {
            "category": triage["category_name"],
            "severity": triage["severity"],
            "urgency_score": triage["urgency_score"],
            "golden_hour": triage["golden_hour"]
        }
    }


# ============================================================================
# MCP TOOLS - UTILITY (list_categories, get_case_status, update_case, list_cases, get_statistics)
# ============================================================================

@mcp.tool()
def list_categories() -> dict[str, Any]:
    """
    List all fraud categories from taxonomy configuration.
    
    Returns:
        List of all categories with id, name, risk_score, keyword_count
    """
    categories = []
    for cat in TAXONOMY["categories"]:
        categories.append({
            "id": cat["id"],
            "name": cat["name"],
            "risk_score": cat["risk_score"],
            "keyword_count": len(cat.get("keywords", []))
        })
    
    return {
        "success": True,
        "categories": categories,
        "total_categories": len(categories),
        "config_source": "category_taxonomy.yaml"
    }


@mcp.tool()
def get_case_status(case_id: str) -> dict[str, Any]:
    """
    Get current status and details of a case.
    
    Args:
        case_id: The case ID to look up
    
    Returns:
        Full case details including intake, triage, and routing
    """
    cases_data = load_cases()
    if case_id not in cases_data["cases"]:
        return {"success": False, "error": f"Case {case_id} not found", "error_code": "CASE_NOT_FOUND"}
    
    case = cases_data["cases"][case_id]
    return {"success": True, "case": case}


@mcp.tool()
def update_case(case_id: str, status: str = "", notes: str = "") -> dict[str, Any]:
    """
    Update case status or add notes.
    
    Args:
        case_id: The case ID to update
        status: New status (optional)
        notes: Additional notes to append (optional)
    
    Returns:
        Updated case information
    """
    cases_data = load_cases()
    if case_id not in cases_data["cases"]:
        return {"success": False, "error": f"Case {case_id} not found", "error_code": "CASE_NOT_FOUND"}
    
    case = cases_data["cases"][case_id]
    
    if status:
        case["status"] = status
    
    if notes:
        if "notes" not in case:
            case["notes"] = []
        case["notes"].append({"timestamp": datetime.utcnow().isoformat(), "note": notes})
    
    case["last_updated"] = datetime.utcnow().isoformat()
    cases_data["cases"][case_id] = case
    save_cases(cases_data)
    
    return {"success": True, "case_id": case_id, "status": case["status"], "message": "Case updated"}


@mcp.tool()
def list_cases(status: str = "", limit: int = 50) -> dict[str, Any]:
    """
    List all cases, optionally filtered by status.
    
    Args:
        status: Filter by status (optional)
        limit: Maximum number of cases to return
    
    Returns:
        List of cases with summary information
    """
    cases_data = load_cases()
    all_cases = cases_data["cases"]
    
    result = []
    for case_id, case in all_cases.items():
        if status and case.get("status") != status:
            continue
        
        summary = {
            "case_id": case_id,
            "status": case.get("status"),
            "category": case.get("intake", {}).get("preliminary_category", {}).get("name", "Unknown"),
            "amount_inr": case.get("intake", {}).get("amount_inr", 0),
            "created_at": case.get("intake", {}).get("timestamp", "")
        }
        
        if case.get("triage"):
            summary["severity"] = case["triage"].get("severity")
            summary["urgency_score"] = case["triage"].get("urgency_score")
        
        result.append(summary)
        
        if len(result) >= limit:
            break
    
    return {"success": True, "cases": result, "total_returned": len(result), "total_in_system": len(all_cases)}


@mcp.tool()
def get_statistics() -> dict[str, Any]:
    """
    Get system statistics and metrics.
    
    Returns:
        Statistics including case counts by status, severity distribution, category distribution
    """
    cases_data = load_cases()
    all_cases = cases_data["cases"]
    
    status_counts = {}
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    category_counts = {}
    total_amount = 0
    golden_hour_count = 0
    
    for case in all_cases.values():
        status = case.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if case.get("triage"):
            sev = case["triage"].get("severity", "LOW")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            if case["triage"].get("golden_hour"):
                golden_hour_count += 1
        
        cat = case.get("intake", {}).get("preliminary_category", {}).get("id", "OTHER")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        
        total_amount += case.get("intake", {}).get("amount_inr", 0)
    
    return {
        "success": True,
        "total_cases": len(all_cases),
        "status_distribution": status_counts,
        "severity_distribution": severity_counts,
        "category_distribution": category_counts,
        "total_amount_reported": total_amount,
        "golden_hour_cases": golden_hour_count,
        "metadata": cases_data.get("metadata", {})
    }


# ============================================================================
# MCP TOOLS - SAMPLING DIRECTIVES (propose_next_action, request_human_review)
# ============================================================================

@mcp.tool()
def propose_next_action(case_id: str) -> dict[str, Any]:
    """
    MCP Sampling Directive: Propose next action for a case with confidence scoring.
    LLM uses this to decide when to escalate or create manual review task.
    
    Args:
        case_id: The case ID to analyze
    
    Returns:
        Structured recommendation including needs_human_review, confidence, reason, suggested_queue
    """
    cases_data = load_cases()
    if case_id not in cases_data["cases"]:
        return {"success": False, "error": f"Case {case_id} not found", "error_code": "CASE_NOT_FOUND"}
    
    case = cases_data["cases"][case_id]
    intake = case.get("intake", {})
    triage = case.get("triage", {})
    routing = case.get("routing", {})
    
    # Calculate confidence score based on multiple factors
    confidence = 100
    reasons = []
    needs_human_review = False
    suggested_queue = "automated"
    
    # Factor 1: Category classification confidence
    category_id = triage.get("category_id", "OTHER") if triage else intake.get("preliminary_category", {}).get("id", "OTHER")
    matched_keywords = triage.get("matched_keywords", []) if triage else intake.get("preliminary_category", {}).get("matched_keywords", [])
    
    if category_id == "OTHER":
        confidence -= 40
        reasons.append("Category classified as OTHER - unclear fraud type")
        needs_human_review = True
        suggested_queue = "manual_review"
    elif len(matched_keywords) < 2:
        confidence -= 20
        reasons.append(f"Low keyword match count ({len(matched_keywords)}) - classification uncertain")
    
    # Factor 2: Severity and urgency
    if triage:
        severity = triage.get("severity", "LOW")
        urgency_score = triage.get("urgency_score", 0)
        
        if severity == "CRITICAL" and urgency_score >= 85:
            confidence += 10
            reasons.append("High confidence due to CRITICAL severity with clear indicators")
        elif severity == "LOW" and urgency_score < 30:
            confidence -= 15
            reasons.append("Low urgency score - may need additional information")
    
    # Factor 3: Amount and evidence
    amount = intake.get("amount_inr", 0)
    victim_context = intake.get("victim_context", "")
    
    if amount == 0:
        confidence -= 25
        reasons.append("No amount specified - financial impact unclear")
        needs_human_review = True
        suggested_queue = "information_gathering"
    elif amount >= 1000000:
        confidence += 5
        reasons.append("High-value case - clear financial impact")
    
    if not victim_context or len(victim_context) < 10:
        confidence -= 10
        reasons.append("Limited victim context - may need follow-up")
    
    # Factor 4: Policy actions triggered
    if routing:
        policy_actions = routing.get("policy_actions", [])
        if len(policy_actions) >= 3:
            confidence += 5
            reasons.append(f"{len(policy_actions)} policies triggered - clear action path")
        elif len(policy_actions) == 0:
            confidence -= 10
            reasons.append("No policies triggered - routing may need review")
    
    # Factor 5: Golden hour status
    if triage and triage.get("golden_hour"):
        confidence += 10
        reasons.append("Within golden hour - time-sensitive with clear urgency")
        suggested_queue = "priority_queue"
    
    # Clamp confidence to 0-100
    confidence = max(0, min(100, confidence))
    
    # Determine if human review is needed based on confidence threshold
    if confidence < 60:
        needs_human_review = True
        if suggested_queue == "automated":
            suggested_queue = "manual_review"
    
    # Determine recommended action
    if not triage:
        recommended_action = "triage_complaint"
        action_reason = "Case needs triage analysis"
    elif not routing:
        recommended_action = "route_complaint"
        action_reason = "Case needs routing decision"
    elif needs_human_review:
        recommended_action = "request_human_review"
        action_reason = "Case requires manual review due to low confidence or complexity"
    else:
        recommended_action = "proceed_automated"
        action_reason = "Case can proceed with automated workflow"
    
    return {
        "success": True,
        "case_id": case_id,
        "needs_human_review": needs_human_review,
        "confidence": confidence,
        "confidence_level": "high" if confidence >= 80 else "medium" if confidence >= 60 else "low",
        "reasons": reasons,
        "suggested_queue": suggested_queue,
        "recommended_action": recommended_action,
        "action_reason": action_reason,
        "case_status": case.get("status", "UNKNOWN"),
        "category": category_id,
        "severity": triage.get("severity") if triage else "NOT_TRIAGED",
        "sampling_directive": "LLM should use this to decide escalation path"
    }


@mcp.tool()
def request_human_review(case_id: str, reason: str, priority: str = "normal", reviewer_notes: str = "") -> dict[str, Any]:
    """
    Request manual human review for a case (MCP sampling directive action).
    
    Args:
        case_id: The case ID requiring review
        reason: Reason for manual review request
        priority: Priority level (low, normal, high, urgent)
        reviewer_notes: Additional notes for the reviewer
    
    Returns:
        Review request confirmation with queue assignment
    """
    cases_data = load_cases()
    if case_id not in cases_data["cases"]:
        return {"success": False, "error": f"Case {case_id} not found", "error_code": "CASE_NOT_FOUND"}
    
    case = cases_data["cases"][case_id]
    
    # Create review request
    review_request = {
        "requested_at": datetime.utcnow().isoformat(),
        "reason": reason,
        "priority": priority,
        "reviewer_notes": reviewer_notes,
        "status": "PENDING_REVIEW",
        "assigned_to": None
    }
    
    # Add to case
    if "review_requests" not in case:
        case["review_requests"] = []
    case["review_requests"].append(review_request)
    
    # Update case status
    case["status"] = "PENDING_HUMAN_REVIEW"
    case["last_updated"] = datetime.utcnow().isoformat()
    
    # Add note
    if "notes" not in case:
        case["notes"] = []
    case["notes"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "note": f"Manual review requested: {reason}"
    })
    
    cases_data["cases"][case_id] = case
    save_cases(cases_data)
    
    # Determine review queue based on priority and case characteristics
    triage = case.get("triage", {})
    severity = triage.get("severity", "LOW") if triage else "LOW"
    
    if priority == "urgent" or severity == "CRITICAL":
        review_queue = "urgent_review_queue"
    elif priority == "high" or severity == "HIGH":
        review_queue = "high_priority_review_queue"
    else:
        review_queue = "standard_review_queue"
    
    return {
        "success": True,
        "case_id": case_id,
        "review_request_id": len(case["review_requests"]) - 1,
        "status": "PENDING_HUMAN_REVIEW",
        "review_queue": review_queue,
        "priority": priority,
        "estimated_review_time_hours": 2 if priority == "urgent" else 8 if priority == "high" else 24,
        "message": f"Case {case_id} queued for manual review in {review_queue}",
        "next_steps": [
            "Case will be assigned to available reviewer",
            "Reviewer will analyze case details and evidence",
            "Manual decision will be recorded in case notes",
            "Case will proceed based on reviewer decision"
        ]
    }


# ============================================================================
# MCP PROMPTS (for LLM guidance)
# ============================================================================

@mcp.prompt()
def process_complaint(complaint_text: str, amount: str = "0", hours_ago: str = "0") -> str:
    """Guide LLM to process a cyber fraud complaint through the full workflow."""
    return f"""Process this cyber fraud complaint using the CyberTriage AI tools:

COMPLAINT: {complaint_text}
AMOUNT LOST: Rs {amount}
TIME SINCE INCIDENT: {hours_ago} hours

WORKFLOW:
1. First call classify_intake with the complaint text to get category
2. Then call score_severity with amount, time, and risk_score from step 1
3. Finally call route_case with category_id and severity_band

Provide a summary with: category, severity, urgency score, golden hour status, assignee, and SLA."""


@mcp.prompt()
def triage_guidance() -> str:
    """Provide guidance on how to use the triage tools."""
    return """CyberTriage AI - Tool Usage Guide

REQUIRED TOOLS (Hackathon):
1. classify_intake(complaint_text) - Returns category_id, risk_score
2. score_severity(amount_inr, time_since_hours, type_risk_score, victim_context) - Returns urgency_score, severity_band
3. route_case(category_id, severity_band, amount_inr) - Returns assignee, jurisdiction
4. get_routing_rules(category_id) - Returns routing configuration

WORKFLOW TOOLS:
- intake_complaint -> triage_complaint -> route_complaint (full case management)

SAMPLING DIRECTIVES (MCP):
- propose_next_action(case_id) - Returns confidence score and needs_human_review flag
- request_human_review(case_id, reason, priority) - Escalate to manual review queue

USAGE:
After processing a case, call propose_next_action to get confidence score.
If confidence < 60 or category = OTHER, call request_human_review.
LLM should use sampling directives to decide when to escalate.

All tools are config-driven. Check config_source in responses to verify.
Storage mode: {storage_mode} (stateless by default, SQLite optional).""".format(
    storage_mode=PERSIST_MODE
)


@mcp.prompt()
def golden_hour_alert(case_id: str) -> str:
    """Generate golden hour alert for urgent cases."""
    return f"""GOLDEN HOUR ALERT - Case {case_id}

This case is within the critical 48-hour window where money recovery is possible.

IMMEDIATE ACTIONS REQUIRED:
1. Contact victim's bank to freeze recipient account
2. File report on cybercrime.gov.in
3. Preserve all evidence (screenshots, call logs, chat history)
4. Do NOT delete apps or reinstall device

Use get_case_status('{case_id}') to view full case details."""


# ============================================================================
# MCP RESOURCES
# ============================================================================

@mcp.resource("config://cybertriage")
def get_config() -> str:
    """Get the complete CyberTriage AI configuration."""
    config = {
        "domain_profile": DOMAIN_PROFILE,
        "severity_rules": {
            "bands": SEVERITY_RULES["bands"],
            "weights": SEVERITY_RULES["weights"],
            "golden_hour_hours": SEVERITY_RULES["golden_hour_hours"]
        },
        "categories": [{"id": c["id"], "name": c["name"], "risk_score": c["risk_score"]} for c in TAXONOMY["categories"]],
        "routing_summary": list(ROUTING_MATRIX["routes"].keys()),
        "policy_count": len(POLICY_RULES["policies"])
    }
    return json.dumps(config, indent=2)


@mcp.resource("case://{case_id}")
def get_case(case_id: str) -> str:
    """Get details of a specific case."""
    cases_data = load_cases()
    if case_id in cases_data["cases"]:
        return json.dumps(cases_data["cases"][case_id], indent=2, default=str)
    return json.dumps({"error": f"Case {case_id} not found"})


@mcp.resource("domain://profile")
def get_domain_profile() -> str:
    """Get the domain profile configuration."""
    return json.dumps(DOMAIN_PROFILE, indent=2)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CyberTriage AI - MCP Server Starting")
    print("=" * 60)
    print(f"Domain: {DOMAIN_PROFILE['label']}")
    print(f"Categories loaded: {len(TAXONOMY['categories'])}")
    print(f"Policies loaded: {len(POLICY_RULES['policies'])}")
    print(f"Storage Mode: {PERSIST_MODE.upper()} ({'stateless' if PERSIST_MODE == 'memory' else 'persistent'})")
    if PERSIST_MODE == "sqlite":
        print(f"Database: {DB_FILE}")
    print()
    print("MCP Tools (14):")
    print("  - classify_intake       : Classify complaint into category")
    print("  - score_severity        : Calculate urgency score")
    print("  - route_case            : Get routing for category")
    print("  - get_routing_rules     : Get routing config")
    print("  - intake_complaint      : Full intake workflow")
    print("  - triage_complaint      : Full triage workflow")
    print("  - route_complaint       : Full routing workflow")
    print("  - list_categories       : List all categories")
    print("  - get_case_status       : Get case details")
    print("  - update_case           : Update case")
    print("  - list_cases            : List all cases")
    print("  - get_statistics        : Get system stats")
    print("  - propose_next_action   : MCP sampling directive (confidence scoring)")
    print("  - request_human_review  : MCP sampling directive (manual escalation)")
    print()
    print("MCP Resources (3):")
    print("  - config://cybertriage")
    print("  - case://{case_id}")
    print("  - domain://profile")
    print()
    print("MCP Prompts (3):")
    print("  - process_complaint  : Guide LLM through workflow")
    print("  - triage_guidance    : Tool usage instructions")
    print("  - golden_hour_alert  : Urgent case alert")
    print()
    print("Storage Configuration:")
    print("  - Default: In-memory (stateless)")
    print("  - Optional: SQLite (set PERSIST_MODE=sqlite)")
    print("  - Stateless container ready")
    print()
    print(f"Server: http://0.0.0.0:8000")
    print(f"MCP Endpoint: http://0.0.0.0:8000/mcp")
    print("=" * 60)
    
    mcp.run(transport="http", host="0.0.0.0", port=8000)

