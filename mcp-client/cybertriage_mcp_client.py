"""
CyberTriage AI - MCP Client with Gemini LLM Integration

Demonstrates:
- Connecting to CyberTriage MCP server
- Using all 14 MCP tools (including sampling directives)
- Gemini orchestration (optional)
- Deterministic workflow (no API key needed)

Author: Adithya N Murthy
Hackathon: Neutrinos Venture Studio Hackathon
"""

import os
import json
import asyncio
from typing import Any

from fastmcp import Client

# ============================================================================
# CONFIGURATION
# ============================================================================

# UPDATE THIS to your HAWCC public server URL + /mcp
REMOTE_SERVER_URL = "http://localhost:8000/mcp"

# Get API key from environment (optional)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Demo complaint scenarios
DEMO_SCENARIOS = {
    "critical": {
        "complaint_text": """I received a call from someone claiming to be a CBI officer. 
        They said my Aadhaar is linked to money laundering and I will be arrested immediately. 
        They made me do a video call and showed fake arrest warrant. Under pressure, I transferred 
        Rs 5,00,000 via NEFT to avoid arrest. This happened just 4 hours ago. I am a senior citizen, 
        68 years old. Please help recover my life savings. The caller ID showed +91-9876543210.""",
        "amount_inr": 500000,
        "time_since_hours": 4,
        "victim_context": "senior citizen, 68 years old, life savings lost",
        "channel": "web_form"
    },
    "high": {
        "complaint_text": """Someone sent me a QR code on WhatsApp saying I won a lottery prize 
        of Rs 10 lakhs. When I scanned the QR code to receive the money, Rs 85,000 was debited from 
        my account instead of credited. I have the screenshot of the UPI transaction and the 
        WhatsApp chat with the scammer. The UPI ID was fraud@ybl. This happened yesterday evening, 
        about 18 hours ago.""",
        "amount_inr": 85000,
        "time_since_hours": 18,
        "victim_context": "have screenshot evidence",
        "channel": "whatsapp"
    },
    "medium": {
        "complaint_text": """I was cheated on an e-commerce website. I paid Rs 12,000 for a 
        smartphone but received an empty box. The seller is not responding to my messages. 
        I found the seller on Instagram and paid via Google Pay. This happened 5 days ago. 
        I don't have much evidence except the payment screenshot.""",
        "amount_inr": 12000,
        "time_since_hours": 120,
        "victim_context": "",
        "channel": "web_form"
    }
}

ACTIVE_SCENARIO = "critical"


# ============================================================================
# MCP CLIENT FUNCTIONS
# ============================================================================

async def call_mcp_tool(client: Client, tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool and return the result."""
    try:
        result = await client.call_tool(tool_name, arguments)
        if hasattr(result, 'content') and result.content:
            text_content = result.content[0].text if result.content else "{}"
            return json.loads(text_content)
        elif isinstance(result, dict):
            return result
        else:
            return {"raw_result": str(result)}
    except Exception as e:
        return {"error": str(e), "tool": tool_name}


async def demo_hackathon_tools(scenario: dict) -> dict:
    """Demo the 4 hackathon-required tools: classify_intake, score_severity, route_case, get_routing_rules."""
    results = {}
    
    print(f"\n{'='*60}")
    print("HACKATHON REQUIRED TOOLS DEMO")
    print(f"{'='*60}\n")
    
    async with Client(REMOTE_SERVER_URL) as client:
        # Tool 1: classify_intake
        print("1. classify_intake")
        print("-" * 40)
        result = await call_mcp_tool(client, "classify_intake", {
            "complaint_text": scenario["complaint_text"]
        })
        results["classify_intake"] = result
        print(f"   Category: {result.get('category_name')} ({result.get('category_id')})")
        print(f"   Risk Score: {result.get('risk_score')}")
        print(f"   Matched Keywords: {result.get('matched_keywords')}")
        print(f"   Config Source: {result.get('config_source')}")
        
        # Tool 2: score_severity
        print("\n2. score_severity")
        print("-" * 40)
        result = await call_mcp_tool(client, "score_severity", {
            "amount_inr": scenario["amount_inr"],
            "time_since_hours": scenario["time_since_hours"],
            "type_risk_score": results["classify_intake"].get("risk_score", 50),
            "victim_context": scenario["victim_context"]
        })
        results["score_severity"] = result
        print(f"   Urgency Score: {result.get('urgency_score')}/100")
        print(f"   Severity Band: {result.get('severity_band')}")
        print(f"   SLA Hours: {result.get('sla_hours')}")
        print(f"   Golden Hour: {result.get('golden_hour')}")
        print(f"   Config Source: {result.get('config_source')}")
        
        # Tool 3: route_case
        print("\n3. route_case")
        print("-" * 40)
        result = await call_mcp_tool(client, "route_case", {
            "category_id": results["classify_intake"].get("category_id"),
            "severity_band": results["score_severity"].get("severity_band"),
            "amount_inr": scenario["amount_inr"]
        })
        results["route_case"] = result
        print(f"   Primary Assignee: {result.get('primary_assignee')}")
        print(f"   Secondary Assignee: {result.get('secondary_assignee')}")
        print(f"   Jurisdiction: {result.get('jurisdiction')}")
        print(f"   Config Source: {result.get('config_source')}")
        
        # Tool 4: get_routing_rules
        print("\n4. get_routing_rules")
        print("-" * 40)
        result = await call_mcp_tool(client, "get_routing_rules", {
            "category_id": results["classify_intake"].get("category_id")
        })
        results["get_routing_rules"] = result
        print(f"   Routing Rule Found: {result.get('success')}")
        print(f"   Escalation Path: {result.get('routing_rule', {}).get('escalation_path', [])}")
        print(f"   Config Source: {result.get('config_source')}")
    
    return results


async def demo_full_workflow(scenario: dict) -> dict:
    """Demo the full workflow: intake -> triage -> route."""
    results = {"intake": None, "triage": None, "routing": None}
    
    print(f"\n{'='*60}")
    print("FULL WORKFLOW DEMO (intake -> triage -> route)")
    print(f"{'='*60}\n")
    
    async with Client(REMOTE_SERVER_URL) as client:
        # Step 1: Intake
        print("Step 1: intake_complaint")
        print("-" * 40)
        result = await call_mcp_tool(client, "intake_complaint", {
            "complaint_text": scenario["complaint_text"],
            "amount_inr": scenario["amount_inr"],
            "time_since_hours": scenario["time_since_hours"],
            "victim_context": scenario["victim_context"],
            "channel": scenario["channel"]
        })
        results["intake"] = result
        
        if not result.get("success"):
            print(f"   ERROR: {result.get('error')}")
            return results
        
        case_id = result["case_id"]
        print(f"   Case ID: {case_id}")
        print(f"   Category: {result.get('preliminary_category', {}).get('name')}")
        print(f"   Evidence Checklist: {len(result.get('evidence_checklist', []))} items")
        
        # Step 2: Triage
        print("\nStep 2: triage_complaint")
        print("-" * 40)
        result = await call_mcp_tool(client, "triage_complaint", {"case_id": case_id})
        results["triage"] = result
        
        if not result.get("success"):
            print(f"   ERROR: {result.get('error')}")
            return results
        
        print(f"   Severity: {result.get('severity')}")
        print(f"   Urgency Score: {result.get('urgency_score')}/100")
        print(f"   Golden Hour: {'YES' if result.get('golden_hour') else 'NO'}")
        print(f"   SLA: {result.get('sla_hours')} hours")
        
        # Step 3: Route
        print("\nStep 3: route_complaint")
        print("-" * 40)
        result = await call_mcp_tool(client, "route_complaint", {"case_id": case_id})
        results["routing"] = result
        
        if not result.get("success"):
            print(f"   ERROR: {result.get('error')}")
            return results
        
        print(f"   Primary Assignee: {result.get('primary_assignee')}")
        print(f"   Jurisdiction: {result.get('jurisdiction')}")
        print(f"   Policy Actions: {len(result.get('policy_actions', []))}")
    
    return results


async def demo_utility_tools() -> dict:
    """Demo utility tools: list_categories, list_cases, get_statistics."""
    results = {}
    
    print(f"\n{'='*60}")
    print("UTILITY TOOLS DEMO")
    print(f"{'='*60}\n")
    
    async with Client(REMOTE_SERVER_URL) as client:
        # list_categories
        print("list_categories")
        print("-" * 40)
        result = await call_mcp_tool(client, "list_categories", {})
        results["list_categories"] = result
        print(f"   Total Categories: {result.get('total_categories')}")
        for cat in result.get("categories", [])[:5]:
            print(f"   - {cat['id']}: {cat['name']} (risk: {cat['risk_score']})")
        if result.get("total_categories", 0) > 5:
            print(f"   ... and {result.get('total_categories') - 5} more")
        
        # list_cases
        print("\nlist_cases")
        print("-" * 40)
        result = await call_mcp_tool(client, "list_cases", {"limit": 5})
        results["list_cases"] = result
        print(f"   Total in System: {result.get('total_in_system')}")
        for case in result.get("cases", []):
            print(f"   - {case['case_id']}: {case['status']} ({case.get('category', 'N/A')})")
        
        # get_statistics
        print("\nget_statistics")
        print("-" * 40)
        result = await call_mcp_tool(client, "get_statistics", {})
        results["get_statistics"] = result
        print(f"   Total Cases: {result.get('total_cases')}")
        print(f"   Total Amount Reported: Rs {result.get('total_amount_reported', 0):,.0f}")
        print(f"   Golden Hour Cases: {result.get('golden_hour_cases')}")
        print(f"   Severity Distribution: {result.get('severity_distribution')}")
        print(f"   Storage Mode: {result.get('metadata', {}).get('storage_mode', 'unknown')}")
    
    return results


async def demo_sampling_directives() -> dict:
    """Demo MCP sampling directives: propose_next_action, request_human_review."""
    results = {}
    
    print(f"\n{'='*60}")
    print("MCP SAMPLING DIRECTIVES DEMO")
    print(f"{'='*60}\n")
    
    # Create a low-confidence case for demo
    low_confidence_scenario = {
        "complaint_text": "Someone cheated me online. Not sure what type of fraud.",
        "amount_inr": 0,
        "time_since_hours": 100,
        "victim_context": "",
        "channel": "web_form"
    }
    
    async with Client(REMOTE_SERVER_URL) as client:
        # Create and triage a case
        print("Creating low-confidence case for sampling directive demo...")
        print("-" * 40)
        
        intake_result = await call_mcp_tool(client, "intake_complaint", low_confidence_scenario)
        if not intake_result.get("success"):
            print(f"   ERROR: {intake_result.get('error')}")
            return results
        
        case_id = intake_result["case_id"]
        print(f"   Case ID: {case_id}")
        print(f"   Category: {intake_result.get('preliminary_category', {}).get('name')}")
        
        # Triage the case
        await call_mcp_tool(client, "triage_complaint", {"case_id": case_id})
        
        # Sampling Directive 1: propose_next_action
        print("\n1. propose_next_action (MCP Sampling Directive)")
        print("-" * 40)
        result = await call_mcp_tool(client, "propose_next_action", {"case_id": case_id})
        results["propose_next_action"] = result
        
        if result.get("success"):
            print(f"   Confidence: {result.get('confidence')}/100 ({result.get('confidence_level')})")
            print(f"   Needs Human Review: {result.get('needs_human_review')}")
            print(f"   Suggested Queue: {result.get('suggested_queue')}")
            print(f"   Recommended Action: {result.get('recommended_action')}")
            print(f"   Reasons:")
            for reason in result.get('reasons', [])[:3]:
                print(f"     - {reason}")
            
            # Sampling Directive 2: request_human_review (if needed)
            if result.get("needs_human_review"):
                print("\n2. request_human_review (MCP Sampling Directive)")
                print("-" * 40)
                review_result = await call_mcp_tool(client, "request_human_review", {
                    "case_id": case_id,
                    "reason": result.get('reasons', ['Low confidence'])[0],
                    "priority": "high",
                    "reviewer_notes": "Automated escalation based on confidence score"
                })
                results["request_human_review"] = review_result
                
                if review_result.get("success"):
                    print(f"   Review Queue: {review_result.get('review_queue')}")
                    print(f"   Priority: {review_result.get('priority')}")
                    print(f"   Estimated Review Time: {review_result.get('estimated_review_time_hours')} hours")
                    print(f"   Status: {review_result.get('status')}")
                else:
                    print(f"   ERROR: {review_result.get('error')}")
            else:
                print("\n2. request_human_review - SKIPPED (high confidence case)")
        else:
            print(f"   ERROR: {result.get('error')}")
    
    return results


# ============================================================================
# GEMINI LLM INTEGRATION (Optional)
# ============================================================================

async def run_with_gemini(scenario: dict) -> None:
    """Run workflow with Gemini orchestrating tool calls."""
    
    if not GOOGLE_API_KEY:
        print("\nGOOGLE_API_KEY not set - skipping Gemini integration")
        return
    
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("\ngoogle-genai not installed - skipping Gemini integration")
        return
    
    print(f"\n{'='*60}")
    print("GEMINI LLM INTEGRATION")
    print(f"{'='*60}\n")
    
    # Tool declarations for Gemini
    tool_declarations = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="classify_intake",
                    description="Classify complaint into fraud category",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "complaint_text": types.Schema(type=types.Type.STRING, description="Complaint description")
                        },
                        required=["complaint_text"]
                    )
                ),
                types.FunctionDeclaration(
                    name="score_severity",
                    description="Calculate urgency score and severity",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "amount_inr": types.Schema(type=types.Type.NUMBER, description="Amount lost"),
                            "time_since_hours": types.Schema(type=types.Type.NUMBER, description="Hours since incident"),
                            "type_risk_score": types.Schema(type=types.Type.INTEGER, description="Category risk score"),
                            "victim_context": types.Schema(type=types.Type.STRING, description="Victim context")
                        },
                        required=["amount_inr", "time_since_hours"]
                    )
                ),
                types.FunctionDeclaration(
                    name="route_case",
                    description="Get routing for a fraud category",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "category_id": types.Schema(type=types.Type.STRING, description="Category ID"),
                            "severity_band": types.Schema(type=types.Type.STRING, description="Severity band"),
                            "amount_inr": types.Schema(type=types.Type.NUMBER, description="Amount lost")
                        },
                        required=["category_id"]
                    )
                ),
                types.FunctionDeclaration(
                    name="intake_complaint",
                    description="Register a new complaint",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "complaint_text": types.Schema(type=types.Type.STRING, description="Complaint description"),
                            "amount_inr": types.Schema(type=types.Type.NUMBER, description="Amount lost"),
                            "time_since_hours": types.Schema(type=types.Type.NUMBER, description="Hours since incident"),
                            "victim_context": types.Schema(type=types.Type.STRING, description="Victim context"),
                            "channel": types.Schema(type=types.Type.STRING, description="Intake channel")
                        },
                        required=["complaint_text"]
                    )
                ),
                types.FunctionDeclaration(
                    name="triage_complaint",
                    description="Triage a registered complaint",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "case_id": types.Schema(type=types.Type.STRING, description="Case ID")
                        },
                        required=["case_id"]
                    )
                ),
                types.FunctionDeclaration(
                    name="route_complaint",
                    description="Route a triaged complaint",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "case_id": types.Schema(type=types.Type.STRING, description="Case ID")
                        },
                        required=["case_id"]
                    )
                )
            ]
        )
    ]
    
    system_instruction = """You are an AI assistant for CyberTriage AI cyber fraud complaint system.
    
RULES:
1. Use MCP tools to process complaints - do NOT guess results
2. Workflow: intake_complaint -> triage_complaint -> route_complaint
3. After all tools complete, provide a clear summary

Process the complaint and summarize: category, severity, urgency score, golden hour status, assignee, SLA."""

    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    user_prompt = f"""Process this cyber fraud complaint:

COMPLAINT: {scenario['complaint_text']}
AMOUNT: Rs {scenario['amount_inr']:,.0f}
TIME SINCE: {scenario['time_since_hours']} hours
VICTIM: {scenario['victim_context'] or 'Not specified'}
CHANNEL: {scenario['channel']}

Use the MCP tools to register, triage, and route this complaint."""

    messages = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]
    
    async with Client(REMOTE_SERVER_URL) as mcp_client:
        for iteration in range(10):
            print(f"\n--- Gemini Iteration {iteration + 1} ---")
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tool_declarations,
                    temperature=0.1
                )
            )
            
            function_calls = []
            text_response = ""
            
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
                    elif hasattr(part, 'text') and part.text:
                        text_response += part.text
            
            if not function_calls:
                print("\n" + "="*60)
                print("GEMINI SUMMARY")
                print("="*60)
                print(text_response)
                break
            
            function_responses = []
            for fc in function_calls:
                tool_name = fc.name
                args = dict(fc.args) if fc.args else {}
                print(f"Tool: {tool_name}({json.dumps(args)[:100]}...)")
                
                result = await call_mcp_tool(mcp_client, tool_name, args)
                print(f"Result: {json.dumps(result)[:200]}...")
                
                function_responses.append(
                    types.Part(function_response=types.FunctionResponse(name=tool_name, response={"result": result}))
                )
            
            messages.append(types.Content(role="model", parts=[types.Part(function_call=fc) for fc in function_calls]))
            messages.append(types.Content(role="user", parts=function_responses))


# ============================================================================
# SUMMARY PRINTER
# ============================================================================

def print_final_summary(hackathon_results: dict, workflow_results: dict) -> None:
    """Print final summary of all demos."""
    print("\n" + "="*60)
    print("FINAL SUMMARY - CYBERTRIAGE AI")
    print("="*60)
    
    # Hackathon tools summary
    if hackathon_results.get("classify_intake", {}).get("success"):
        ci = hackathon_results["classify_intake"]
        ss = hackathon_results.get("score_severity", {})
        rc = hackathon_results.get("route_case", {})
        
        print("\nHACKATHON TOOLS (Config-Driven):")
        print(f"  Category: {ci.get('category_name')} (risk: {ci.get('risk_score')})")
        print(f"  Severity: {ss.get('severity_band')} (score: {ss.get('urgency_score')})")
        print(f"  Golden Hour: {'YES' if ss.get('golden_hour') else 'NO'}")
        print(f"  Assignee: {rc.get('primary_assignee')}")
    
    # Workflow summary - check if workflow_results is not None and has data
    if workflow_results and workflow_results.get("routing", {}).get("success"):
        intake = workflow_results["intake"]
        triage = workflow_results["triage"]
        routing = workflow_results["routing"]
        
        print("\nFULL WORKFLOW:")
        print(f"  Case ID: {intake.get('case_id')}")
        print(f"  Status: {routing.get('status')}")
        print(f"  Category: {triage.get('category_name')}")
        print(f"  Severity: {triage.get('severity')} (score: {triage.get('urgency_score')})")
        print(f"  Golden Hour: {'YES' if triage.get('golden_hour') else 'NO'}")
        print(f"  SLA: {triage.get('sla_hours')} hours")
        print(f"  Primary Assignee: {routing.get('primary_assignee')}")
        print(f"  Jurisdiction: {routing.get('jurisdiction')}")
        
        if triage.get("golden_hour"):
            print("\n  GOLDEN HOUR RECOMMENDATIONS:")
            for rec in triage.get("golden_hour_recommendations", [])[:3]:
                print(f"    - {rec}")
        
        if routing.get("policy_actions"):
            print("\n  POLICY ACTIONS TRIGGERED:")
            for pa in routing.get("policy_actions", [])[:3]:
                print(f"    - [{pa['policy_id']}] {pa['message']}")
    elif not workflow_results or not workflow_results.get("intake", {}).get("success"):
        print("\nFULL WORKFLOW: Skipped due to server error")
        print("  Note: Restart the server to fix storage issues")
    
    print("\n" + "="*60)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("CYBERTRIAGE AI - MCP CLIENT")
    print("="*60)
    print(f"Server URL: {REMOTE_SERVER_URL}")
    print(f"Scenario: {ACTIVE_SCENARIO.upper()}")
    print(f"Gemini API: {'Configured' if GOOGLE_API_KEY else 'Not configured (deterministic mode)'}")
    print("="*60)
    
    scenario = DEMO_SCENARIOS[ACTIVE_SCENARIO]
    
    print(f"\nCOMPLAINT PREVIEW:")
    print(f"  Amount: Rs {scenario['amount_inr']:,.0f}")
    print(f"  Time Since: {scenario['time_since_hours']} hours")
    print(f"  Victim: {scenario['victim_context'] or 'Not specified'}")
    print(f"  Text: {scenario['complaint_text'][:80]}...")
    
    # Demo 1: Hackathon required tools
    hackathon_results = await demo_hackathon_tools(scenario)
    
    # Demo 2: Full workflow
    workflow_results = await demo_full_workflow(scenario)
    
    # Demo 3: Utility tools
    await demo_utility_tools()
    
    # Demo 4: MCP Sampling Directives
    await demo_sampling_directives()
    
    # Demo 4: MCP Sampling Directives
    await demo_sampling_directives()
    
    # Demo 5: Gemini integration (if API key available)
    if GOOGLE_API_KEY:
        await run_with_gemini(scenario)
    
    # Final summary
    print_final_summary(hackathon_results, workflow_results)


if __name__ == "__main__":
    asyncio.run(main())
