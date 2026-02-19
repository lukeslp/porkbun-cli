#!/usr/bin/env python3
import sys
import json
import logging
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__)))
try:
    from porkbun_cli.api import PorkbunAPI
except ImportError:
    from src.porkbun_cli.api import PorkbunAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("porkbun-mcp")

# API Keys from env
PK_API = os.getenv("PORKBUN_API_KEY")
PK_SECRET = os.getenv("PORKBUN_SECRET_KEY")

if PK_API and PK_SECRET:
    api = PorkbunAPI(api_key=PK_API, secret_api_key=PK_SECRET)
else:
    # Fallback to local config loading logic in class
    api = PorkbunAPI()

def list_tools():
    return [
        {
            "name": "dream_porkbun_list_domains",
            "description": "List all domains in the Porkbun account.",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "dream_porkbun_check_domain",
            "description": "Check if a domain is available and get pricing.",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "domain": {"type": "string", "description": "Domain to check (e.g. example.com)"}
                },
                "required": ["domain"]
            }
        },
        {
            "name": "dream_porkbun_dns_list",
            "description": "Get all DNS records for a domain.",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "domain": {"type": "string"}
                },
                "required": ["domain"]
            }
        },
        {
            "name": "dream_porkbun_dns_update",
            "description": "Create or update a DNS record.",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "domain": {"type": "string"},
                    "type": {"type": "string", "enum": ["A", "CNAME", "TXT", "MX"], "description": "Record type"},
                    "content": {"type": "string", "description": "Record content (IP or alias)"},
                    "name": {"type": "string", "description": "Subdomain (optional, e.g. 'www')"}
                },
                "required": ["domain", "type", "content"]
            }
        },
        {
             "name": "dream_porkbun_dns_delete",
             "description": "Delete a DNS record.",
             "inputSchema": {
                 "type": "object",
                 "properties": {
                     "domain": {"type": "string"},
                     "record_id": {"type": "string"}
                 },
                 "required": ["domain", "record_id"]
             }
        }
    ]

def handle_call_tool(name, arguments):
    if not api.api_key:
         return {"content": [{"type": "text", "text": "Error: PORKBUN_API_KEY and PORKBUN_SECRET_KEY not set."}], "isError": True}

    try:
        if name == "dream_porkbun_list_domains":
            res = api.domain_list()
            # Clean up listing
            domains = res.get('domains', [])
            summary = [{"domain": d['domain'], "status": d['status'], "autoRenew": d['autoRenew']} for d in domains]
            return {"content": [{"type": "text", "text": json.dumps(summary, indent=2)}]}

        elif name == "dream_porkbun_check_domain":
            res = api.domain_check(arguments["domain"])
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}

        elif name == "dream_porkbun_dns_list":
            res = api.dns_retrieve(arguments["domain"])
            return {"content": [{"type": "text", "text": json.dumps(res.get('records', []), indent=2)}]}

        elif name == "dream_porkbun_dns_update":
            # Using upsert logic
            res = api.dns_upsert(
                domain=arguments["domain"],
                record_type=arguments["type"],
                content=arguments["content"],
                name=arguments.get("name")
            )
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
            
        elif name == "dream_porkbun_dns_delete":
            res = api.dns_delete(arguments["domain"], arguments["record_id"])
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}

        return {"content": [{"type": "text", "text": f"Tool not found: {name}"}], "isError": True}

    except Exception as e:
         return {"content": [{"type": "text", "text": f"Error executing {name}: {str(e)}"}], "isError": True}

def run_server():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line)
            req_id = request.get("id")
            
            response = {"jsonrpc": "2.0", "id": req_id}
            
            if request.get("method") == "initialize":
                response["result"] = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "geepers-porkbun", "version": "1.0.0"}
                }
            elif request.get("method") == "tools/list":
                response["result"] = {"tools": list_tools()}
            elif request.get("method") == "tools/call":
                result = handle_call_tool(request["params"]["name"], request["params"]["arguments"])
                if result.get("isError"):
                     response["error"] = {"code": -32603, "message": result["content"][0]["text"]}
                else:
                     response["result"] = result
            else:
                continue
                
            print(json.dumps(response), flush=True)
        except Exception:
            break

if __name__ == "__main__":
    run_server()
