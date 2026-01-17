"""CyberTriage AI - LLM Integration Client with Auto-Fallback (Fixed)"""
import os, json, asyncio
from enum import Enum
from fastmcp import Client

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

class LLMProvider(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    DETERMINISTIC = "deterministic"

DEMO_SCENARIOS = {
    "cybercrime": {"complaint_text": "I received a call from someone claiming to be a CBI officer. They said my Aadhaar is linked to money laundering. Under pressure, I transferred Rs 5,00,000 via NEFT. This happened 4 hours ago. I am a senior citizen, 68 years old.", "amount_inr": 500000, "time_since_hours": 4, "victim_context": "senior citizen, 68 years old", "channel": "helpline_1930"},
    "banking": {"complaint_text": "My credit card was charged Rs 2,50,000 for transactions I never made. The transactions happened at 3 AM. I suspect card skimming. This happened 6 hours ago.", "amount_inr": 250000, "time_since_hours": 6, "victim_context": "card skimming victim", "channel": "mobile_app"},
    "itsupport": {"complaint_text": "My laptop is showing blue screen errors repeatedly. I have an important presentation tomorrow. This started 2 hours ago after a Windows update.", "amount_inr": 0, "time_since_hours": 2, "victim_context": "urgent deadline", "channel": "web_form"}
}

async def call_mcp_tool(client, tool_name, arguments):
    try:
        result = await client.call_tool(tool_name, arguments)
        if hasattr(result, 'content') and result.content:
            return json.loads(result.content[0].text if result.content else "{}")
        return result if isinstance(result, dict) else {"raw": str(result)}
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# GEMINI INTEGRATION
# ============================================================================
async def run_gemini_integration(scenario):
    if not GOOGLE_API_KEY:
        return {"status": "skipped", "reason": "no_api_key"}
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return {"status": "skipped", "reason": "package_not_installed"}
    
    print(f"\n{'='*60}\nGEMINI LLM INTEGRATION\n{'='*60}\n")
    
    tool_declarations = [types.Tool(function_declarations=[
        types.FunctionDeclaration(name="intake_complaint", description="Register a new complaint. Returns case_id which MUST be used for subsequent calls.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={
                "complaint_text": types.Schema(type=types.Type.STRING, description="Full complaint text"),
                "amount_inr": types.Schema(type=types.Type.NUMBER, description="Amount lost in INR"),
                "time_since_hours": types.Schema(type=types.Type.NUMBER, description="Hours since incident"),
                "victim_context": types.Schema(type=types.Type.STRING, description="Victim details"),
                "channel": types.Schema(type=types.Type.STRING, description="Intake channel")
            }, required=["complaint_text"])),
        types.FunctionDeclaration(name="triage_complaint", description="Triage a complaint. MUST use the exact case_id returned from intake_complaint.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={
                "case_id": types.Schema(type=types.Type.STRING, description="The exact case_id from intake_complaint response")
            }, required=["case_id"])),
        types.FunctionDeclaration(name="route_complaint", description="Route a complaint. MUST use the exact case_id returned from intake_complaint.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={
                "case_id": types.Schema(type=types.Type.STRING, description="The exact case_id from intake_complaint response")
            }, required=["case_id"])),
        types.FunctionDeclaration(name="propose_next_action", description="Propose next action. MUST use the exact case_id returned from intake_complaint.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={
                "case_id": types.Schema(type=types.Type.STRING, description="The exact case_id from intake_complaint response")
            }, required=["case_id"]))
    ])]
    
    system_instruction = """You are CyberTriage AI. Process complaints using MCP tools in this EXACT order:
1. intake_complaint - register complaint, this returns a case_id (like "CYB-20260117-XXXXXX")
2. triage_complaint - use the EXACT case_id from step 1
3. route_complaint - use the EXACT case_id from step 1
4. propose_next_action - use the EXACT case_id from step 1

CRITICAL: You MUST use the exact case_id string returned from intake_complaint. Do NOT make up case IDs like "case_1".
After all tools complete, provide a summary."""

    client = genai.Client(api_key=GOOGLE_API_KEY)
    user_prompt = f"Process this complaint:\n{scenario['complaint_text']}\nAmount: Rs {scenario['amount_inr']}, Time: {scenario['time_since_hours']}h, Victim: {scenario['victim_context']}, Channel: {scenario['channel']}"
    
    messages = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]
    results = {"tools_called": [], "final_summary": "", "case_id": None}
    
    async with Client(MCP_SERVER_URL) as mcp_client:
        for iteration in range(10):
            print(f"--- Gemini Iteration {iteration + 1} ---")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=messages,
                config=types.GenerateContentConfig(system_instruction=system_instruction, tools=tool_declarations, temperature=0.1)
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
                print(f"\n{'='*60}\nGEMINI FINAL SUMMARY\n{'='*60}")
                print(text_response)
                results["final_summary"] = text_response
                break
            
            function_responses = []
            for fc in function_calls:
                tool_name = fc.name
                args = dict(fc.args) if fc.args else {}
                print(f"  Tool: {tool_name}")
                print(f"  Args: {json.dumps(args)[:80]}...")
                result = await call_mcp_tool(mcp_client, tool_name, args)
                results["tools_called"].append({"tool": tool_name, "result": result})
                if tool_name == "intake_complaint" and result.get("case_id"):
                    results["case_id"] = result["case_id"]
                print(f"  Result: {json.dumps(result)[:100]}...")
                function_responses.append(types.Part(function_response=types.FunctionResponse(name=tool_name, response={"result": result})))
            
            messages.append(types.Content(role="model", parts=[types.Part(function_call=fc) for fc in function_calls]))
            messages.append(types.Content(role="user", parts=function_responses))
    
    return results

# ============================================================================
# OPENAI INTEGRATION (FIXED - Better prompting for case_id)
# ============================================================================
async def run_openai_integration(scenario):
    if not OPENAI_API_KEY:
        return {"status": "skipped", "reason": "no_api_key"}
    try:
        from openai import OpenAI
    except ImportError:
        return {"status": "skipped", "reason": "package_not_installed"}
    
    print(f"\n{'='*60}\nOPENAI LLM INTEGRATION\n{'='*60}\n")
    
    tools = [
        {"type": "function", "function": {"name": "intake_complaint", "description": "Register complaint. Returns case_id (format: CYB-YYYYMMDD-XXXXXX) which MUST be used exactly for all subsequent tool calls.", "parameters": {"type": "object", "properties": {"complaint_text": {"type": "string", "description": "Full complaint text"}, "amount_inr": {"type": "number", "description": "Amount lost"}, "time_since_hours": {"type": "number", "description": "Hours since incident"}, "victim_context": {"type": "string", "description": "Victim details"}, "channel": {"type": "string", "description": "Channel"}}, "required": ["complaint_text"]}}},
        {"type": "function", "function": {"name": "triage_complaint", "description": "Triage complaint. MUST use exact case_id from intake_complaint response.", "parameters": {"type": "object", "properties": {"case_id": {"type": "string", "description": "Exact case_id from intake_complaint (e.g., CYB-20260117-ABC123)"}}, "required": ["case_id"]}}},
        {"type": "function", "function": {"name": "route_complaint", "description": "Route complaint. MUST use exact case_id from intake_complaint response.", "parameters": {"type": "object", "properties": {"case_id": {"type": "string", "description": "Exact case_id from intake_complaint (e.g., CYB-20260117-ABC123)"}}, "required": ["case_id"]}}},
        {"type": "function", "function": {"name": "propose_next_action", "description": "Propose next action. MUST use exact case_id from intake_complaint response.", "parameters": {"type": "object", "properties": {"case_id": {"type": "string", "description": "Exact case_id from intake_complaint (e.g., CYB-20260117-ABC123)"}}, "required": ["case_id"]}}}
    ]
    
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    system_msg = """You are CyberTriage AI. Process complaints using tools in this EXACT order:
1. intake_complaint - returns a case_id like "CYB-20260117-ABC123"
2. triage_complaint - use the EXACT case_id from step 1 (copy it exactly)
3. route_complaint - use the EXACT case_id from step 1
4. propose_next_action - use the EXACT case_id from step 1

CRITICAL: The case_id from intake_complaint is a string like "CYB-20260117-ABC123". You MUST copy and use this EXACT string for all subsequent calls. Do NOT use placeholder values like "case_1" or "case_id".

After completing all 4 tools, provide a summary with: Case ID, Category, Severity, SLA, Assignee, and recommended next steps."""

    user_prompt = f"""Process this cyber fraud complaint:

COMPLAINT: {scenario['complaint_text']}
AMOUNT LOST: Rs {scenario['amount_inr']:,}
TIME SINCE INCIDENT: {scenario['time_since_hours']} hours
VICTIM CONTEXT: {scenario['victim_context']}
CHANNEL: {scenario['channel']}

Execute all 4 tools in order: intake_complaint -> triage_complaint -> route_complaint -> propose_next_action
Remember to use the EXACT case_id returned from intake_complaint for all subsequent calls."""

    messages = [{"role": "system", "content": system_msg}, {"role": "user", "content": user_prompt}]
    results = {"tools_called": [], "final_summary": "", "case_id": None}
    
    async with Client(MCP_SERVER_URL) as mcp_client:
        for iteration in range(10):
            print(f"--- OpenAI Iteration {iteration + 1} ---")
            response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools, tool_choice="auto", temperature=0.1)
            assistant_message = response.choices[0].message
            
            if not assistant_message.tool_calls:
                print(f"\n{'='*60}\nOPENAI FINAL SUMMARY\n{'='*60}")
                print(assistant_message.content)
                results["final_summary"] = assistant_message.content
                break
            
            messages.append(assistant_message)
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                print(f"  Tool: {tool_name}")
                print(f"  Args: {json.dumps(args)}")
                result = await call_mcp_tool(mcp_client, tool_name, args)
                results["tools_called"].append({"tool": tool_name, "args": args, "result": result})
                if tool_name == "intake_complaint" and result.get("case_id"):
                    results["case_id"] = result["case_id"]
                    print(f"  >>> CASE_ID: {result['case_id']} <<<")
                print(f"  Result: {json.dumps(result)[:120]}...")
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)})
    
    return results

# ============================================================================
# DETERMINISTIC WORKFLOW
# ============================================================================
async def run_deterministic_workflow(scenario):
    print(f"\n{'='*60}\nDETERMINISTIC WORKFLOW (No LLM)\n{'='*60}\n")
    async with Client(MCP_SERVER_URL) as client:
        print("Step 1: intake_complaint\n" + "-"*40)
        intake = await call_mcp_tool(client, "intake_complaint", {"complaint_text": scenario["complaint_text"], "amount_inr": scenario["amount_inr"], "time_since_hours": scenario["time_since_hours"], "victim_context": scenario["victim_context"], "channel": scenario["channel"]})
        if not intake.get("success"): print(f"   ERROR: {intake}"); return {"status": "error"}
        case_id = intake["case_id"]
        print(f"   Case ID: {case_id}\n   Category: {intake.get('preliminary_category', {}).get('name')}")
        
        print("\nStep 2: triage_complaint\n" + "-"*40)
        triage = await call_mcp_tool(client, "triage_complaint", {"case_id": case_id})
        print(f"   Severity: {triage.get('severity')}\n   Urgency Score: {triage.get('urgency_score')}/100\n   Golden Hour: {'YES' if triage.get('golden_hour') else 'NO'}\n   SLA: {triage.get('sla_hours')} hours")
        
        print("\nStep 3: route_complaint\n" + "-"*40)
        route = await call_mcp_tool(client, "route_complaint", {"case_id": case_id})
        print(f"   Primary Assignee: {route.get('primary_assignee')}\n   Jurisdiction: {route.get('jurisdiction')}\n   Policy Actions: {len(route.get('policy_actions', []))}")
        
        print("\nStep 4: propose_next_action\n" + "-"*40)
        propose = await call_mcp_tool(client, "propose_next_action", {"case_id": case_id})
        print(f"   Confidence: {propose.get('confidence')}/100\n   Needs Human Review: {propose.get('needs_human_review')}\n   Recommended Action: {propose.get('recommended_action')}")
    return {"status": "success", "case_id": case_id}

# ============================================================================
# AUTO-FALLBACK RUNNER
# ============================================================================
async def run_with_fallback(scenario):
    providers = [
        ("GEMINI", GOOGLE_API_KEY, run_gemini_integration),
        ("OPENAI", OPENAI_API_KEY, run_openai_integration),
    ]
    for name, api_key, runner in providers:
        if not api_key:
            print(f"\n[SKIP] {name}: No API key set")
            continue
        print(f"\n[TRYING] {name}...")
        try:
            result = await runner(scenario)
            if result.get("status") not in ["skipped", "error"]:
                print(f"\n[SUCCESS] {name} completed!")
                return result
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "resource" in error_msg.lower():
                print(f"\n[QUOTA ERROR] {name}: Rate limit exceeded, trying next...")
            else:
                print(f"\n[ERROR] {name}: {error_msg[:80]}..., trying next...")
            continue
    print("\n[FALLBACK] Using deterministic workflow...")
    return await run_deterministic_workflow(scenario)

# ============================================================================
# MULTI-INDUSTRY DEMO
# ============================================================================
async def demo_multi_industry():
    print(f"\n{'='*60}\nMULTI-INDUSTRY DEMONSTRATION\n{'='*60}")
    results = {}
    for industry, scenario in DEMO_SCENARIOS.items():
        print(f"\n{'='*60}\nINDUSTRY: {industry.upper()}\n{'='*60}")
        print(f"Complaint: {scenario['complaint_text'][:70]}...\nAmount: Rs {scenario['amount_inr']:,.0f}")
        async with Client(MCP_SERVER_URL) as client:
            classify = await call_mcp_tool(client, "classify_intake", {"complaint_text": scenario["complaint_text"]})
            severity = await call_mcp_tool(client, "score_severity", {"amount_inr": scenario["amount_inr"], "time_since_hours": scenario["time_since_hours"], "type_risk_score": classify.get("risk_score", 50), "victim_context": scenario["victim_context"]})
            route = await call_mcp_tool(client, "route_case", {"category_id": classify.get("category_id"), "severity_band": severity.get("severity_band"), "amount_inr": scenario["amount_inr"]})
            results[industry] = {"category": classify.get("category_name"), "severity": severity.get("severity_band"), "urgency_score": severity.get("urgency_score"), "golden_hour": severity.get("golden_hour"), "sla_hours": severity.get("sla_hours"), "assignee": route.get("primary_assignee")}
            print(f"\nResults:\n  Category: {results[industry]['category']}\n  Severity: {results[industry]['severity']} (score: {results[industry]['urgency_score']})\n  Golden Hour: {'YES' if results[industry]['golden_hour'] else 'NO'}\n  SLA: {results[industry]['sla_hours']} hours\n  Assignee: {results[industry]['assignee']}")
    print(f"\n{'='*60}\nMULTI-INDUSTRY SUMMARY\n{'='*60}")
    print(f"{'Industry':<12} {'Category':<25} {'Severity':<10} {'Score':<6} {'SLA':<6}\n" + "-"*60)
    for ind, d in results.items(): print(f"{ind:<12} {str(d['category'])[:24]:<25} {d['severity']:<10} {d['urgency_score']:<6} {d['sla_hours']:<6}")

# ============================================================================
# MAIN
# ============================================================================
async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["gemini", "openai", "deterministic", "auto"], default="auto")
    parser.add_argument("--scenario", choices=["cybercrime", "banking", "itsupport"], default="cybercrime")
    parser.add_argument("--demo", choices=["workflow", "multi-industry", "all"], default="all")
    args = parser.parse_args()
    
    print("\n" + "="*60 + "\nCYBERTRIAGE AI - LLM INTEGRATION CLIENT\n" + "="*60)
    print(f"MCP Server: {MCP_SERVER_URL}")
    print(f"Scenario: {args.scenario.upper()}")
    print(f"Mode: {args.provider.upper()}")
    print(f"API Keys: Gemini={'Yes' if GOOGLE_API_KEY else 'No'}, OpenAI={'Yes' if OPENAI_API_KEY else 'No'}, Claude={'Yes' if ANTHROPIC_API_KEY else 'No'}")
    print("="*60)
    
    scenario = DEMO_SCENARIOS[args.scenario]
    print(f"\nCOMPLAINT PREVIEW:\n  Amount: Rs {scenario['amount_inr']:,.0f}\n  Time Since: {scenario['time_since_hours']} hours\n  Victim: {scenario['victim_context']}\n  Text: {scenario['complaint_text'][:80]}...")
    
    if args.demo in ["workflow", "all"]:
        if args.provider == "auto":
            await run_with_fallback(scenario)
        elif args.provider == "gemini":
            await run_gemini_integration(scenario)
        elif args.provider == "openai":
            await run_openai_integration(scenario)
        else:
            await run_deterministic_workflow(scenario)
    
    if args.demo in ["multi-industry", "all"]:
        await demo_multi_industry()
    
    print("\n" + "="*60 + "\nLLM INTEGRATION COMPLETE\n" + "="*60)

if __name__ == "__main__": asyncio.run(main())
