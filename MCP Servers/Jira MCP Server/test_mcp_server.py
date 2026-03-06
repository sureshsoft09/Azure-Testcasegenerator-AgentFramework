"""
Jira MCP Server – HTTP Test Script
====================================
Tests all 8 tools exposed by the MCP server running at http://localhost:8002/mcp
using raw JSON-RPC 2.0 over HTTP (no MCP SDK required – only `requests`).

Usage:
    python test_mcp_server.py
    python test_mcp_server.py --tool jira_list_projects
    python test_mcp_server.py --tool jira_get_issue --args '{"issue_key":"PROJ-1"}'
"""

import json
import sys
import argparse
import requests

MCP_URL = "http://localhost:8002/mcp"

_BASE_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

# Holds the session-id returned by the server after initialize
_session_id: str | None = None


def _headers() -> dict:
    h = dict(_BASE_HEADERS)
    if _session_id:
        h["mcp-session-id"] = _session_id
    return h


# ─── Low-level helpers ────────────────────────────────────────────────────────

def _post(payload: dict) -> dict:
    """Send a JSON-RPC request and return the parsed response."""
    resp = requests.post(MCP_URL, headers=_headers(), json=payload, timeout=15)
    resp.raise_for_status()

    # FastMCP streamable-HTTP may return SSE text or plain JSON
    content_type = resp.headers.get("Content-Type", "")
    if "text/event-stream" in content_type:
        # Parse the JSON-RPC result from first `data:` line in the SSE stream
        for line in resp.text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if data_str:
                    return json.loads(data_str)
        raise ValueError(f"No data in SSE response:\n{resp.text}")

    return resp.json()


def initialize() -> str | None:
    """Perform the MCP initialize handshake. Returns session-id if any."""
    global _session_id
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    resp = requests.post(MCP_URL, headers=_headers(), json=payload, timeout=15)
    resp.raise_for_status()

    # Capture session-id from response header (streamable-HTTP spec)
    _session_id = resp.headers.get("mcp-session-id") or resp.headers.get("Mcp-Session-Id")

    content_type = resp.headers.get("Content-Type", "")
    if "text/event-stream" in content_type:
        for line in resp.text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if data_str:
                    result = json.loads(data_str)
                    # Also try to find session-id inside the result body
                    if not _session_id:
                        _session_id = result.get("result", {}).get("sessionId")
                    return result
    else:
        result = resp.json()
        if not _session_id:
            _session_id = result.get("result", {}).get("sessionId")
        return result

    return {}


def _send_initialized():
    """Send the 'initialized' notification required by the MCP spec."""
    payload = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    try:
        requests.post(MCP_URL, headers=_headers(), json=payload, timeout=5)
    except Exception:
        pass  # Notification – ignore errors


def list_tools() -> list:
    """Call tools/list and return the list of tool definitions."""
    payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    result = _post(payload)
    return result.get("result", {}).get("tools", [])


def call_tool(name: str, arguments: dict) -> dict:
    """Call a specific tool with the given arguments."""
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    return _post(payload)


# ─── Individual tool tests ─────────────────────────────────────────────────────

def test_list_projects():
    print("\n[TEST] jira_list_projects")
    result = call_tool("jira_list_projects", {})
    _print_result(result)


def test_search_issues(jql: str = "order by created DESC", max_results: int = 5):
    print(f"\n[TEST] jira_search_issues  JQL='{jql}'")
    result = call_tool("jira_search_issues", {"jql": jql, "max_results": max_results})
    _print_result(result)


def test_get_issue(issue_key: str):
    print(f"\n[TEST] jira_get_issue  key={issue_key}")
    result = call_tool("jira_get_issue", {"issue_key": issue_key})
    _print_result(result)


def test_create_issue(project_key: str = "TEST"):
    print(f"\n[TEST] jira_create_issue  project={project_key}")
    result = call_tool("jira_create_issue", {
        "project_key": project_key,
        "issue_type": "Task",
        "summary": "[MCP Test] Auto-created task",
        "description": "Created by test_mcp_server.py",
        "priority": "Low",
    })
    _print_result(result)
    return result.get("result", {}).get("content", [{}])[0].get("text")


def test_update_issue(issue_key: str):
    print(f"\n[TEST] jira_update_issue  key={issue_key}")
    result = call_tool("jira_update_issue", {
        "issue_key": issue_key,
        "summary": "[MCP Test] Updated by test script",
    })
    _print_result(result)


def test_add_comment(issue_key: str):
    print(f"\n[TEST] jira_add_comment  key={issue_key}")
    result = call_tool("jira_add_comment", {
        "issue_key": issue_key,
        "body": "Comment posted via MCP test script.",
    })
    _print_result(result)


def test_get_transitions(issue_key: str):
    print(f"\n[TEST] jira_get_transitions  key={issue_key}")
    result = call_tool("jira_get_transitions", {"issue_key": issue_key})
    _print_result(result)


def test_transition_issue(issue_key: str, transition_id: str):
    print(f"\n[TEST] jira_transition_issue  key={issue_key}  transition={transition_id}")
    result = call_tool("jira_transition_issue", {
        "issue_key": issue_key,
        "transition_id": transition_id,
    })
    _print_result(result)


# ─── Utility ──────────────────────────────────────────────────────────────────

def _print_result(result: dict):
    """Pretty-print the JSON-RPC result / error."""
    if "error" in result:
        print(f"  ERROR: {json.dumps(result['error'], indent=2)}")
        return

    content = result.get("result", {}).get("content", [])
    if content:
        for block in content:
            if block.get("type") == "text":
                try:
                    parsed = json.loads(block["text"])
                    print(f"  RESULT: {json.dumps(parsed, indent=2)}")
                except json.JSONDecodeError:
                    print(f"  RESULT: {block['text']}")
    else:
        print(f"  RESULT: {json.dumps(result.get('result'), indent=2)}")


# ─── Run all / selective ──────────────────────────────────────────────────────

def run_all_safe_tests():
    """Run tests that don't mutate data (safe to run anytime)."""
    # 1. Handshake
    print("=" * 60)
    print(f"MCP Server: {MCP_URL}")
    print("=" * 60)

    print("\n[STEP 1] Initialize handshake")
    try:
        initialize()
        _send_initialized()
        print(f"  Session ID: {_session_id or '(none)'}")
    except Exception as exc:
        print(f"  WARNING: initialize failed ({exc}) — continuing anyway")

    # 2. List tools
    print("\n[STEP 2] List registered tools")
    try:
        tools = list_tools()
        for t in tools:
            print(f"  • {t['name']}: {t.get('description', '')[:80]}")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        return

    # 3. Safe read-only tool calls
    test_list_projects()
    test_search_issues(jql="order by created DESC", max_results=3)

    print("\n" + "=" * 60)
    print("Safe tests complete.")
    print("To test write operations, pass an issue key:")
    print("  python test_mcp_server.py --tool jira_get_issue --args '{\"issue_key\":\"PROJ-1\"}'")
    print("=" * 60)


def run_single_tool(tool_name: str, args_json: str):
    # Always handshake first so mcp-session-id header is set
    initialize()
    _send_initialized()
    arguments = json.loads(args_json) if args_json else {}
    print(f"\n[SINGLE] Calling tool: {tool_name}")
    print(f"  Args: {arguments}")
    result = call_tool(tool_name, arguments)
    _print_result(result)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Jira MCP Server.")
    parser.add_argument("--url", default=MCP_URL, help="MCP server URL (default: %(default)s)")
    parser.add_argument("--tool", help="Call a specific tool by name")
    parser.add_argument("--args", default="{}", help='JSON arguments for --tool, e.g. \'{"issue_key":"PROJ-1"}\'')
    parsed = parser.parse_args()

    MCP_URL = parsed.url

    try:
        if parsed.tool:
            run_single_tool(parsed.tool, parsed.args)
        else:
            run_all_safe_tests()
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Cannot connect to {MCP_URL}")
        print("Make sure the MCP server is running:  python server.py")
        sys.exit(1)
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)
