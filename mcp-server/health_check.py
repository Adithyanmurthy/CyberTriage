#!/usr/bin/env python3
"""
CyberTriage AI - Health Check Script for Docker
"""

import os
import sys
import urllib.request
import urllib.error
import json

MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = os.environ.get("MCP_PORT", "8000")

HEALTH_URL = f"http://127.0.0.1:{MCP_PORT}/health"
MCP_URL = f"http://127.0.0.1:{MCP_PORT}/mcp"


def check_health():
    """Check if the MCP server is healthy."""
    try:
        try:
            req = urllib.request.Request(HEALTH_URL, method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get("status") == "healthy":
                        print(f"Health check passed: {data}")
                        return True
        except urllib.error.HTTPError:
            pass
        
        req = urllib.request.Request(MCP_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print(f"MCP endpoint responding: status={response.status}")
                return True
        
        return False
        
    except urllib.error.URLError as e:
        print(f"Health check failed: Connection error - {e}")
        return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
