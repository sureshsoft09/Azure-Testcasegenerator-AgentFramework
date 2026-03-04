import logging
import os

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from enum import Enum
from jira_client import jira_client

from fastmcp import FastMCP


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_TRANSPORTS = ["stdio", "http", "streamable-http", "sse"]

MCP_SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "Jira MCP Server")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", 8002))    
MCP_DEBUG = os.environ.get("MCP_DEBUG", "false")

mcp = FastMCP(
    name=MCP_SERVER_NAME,
    instructions=(
        "Jira MCP Server – use these tools to create, read, update and search "
        "Jira issues, add comments, manage transitions, and list projects."
    ),
    host=MCP_HOST,
    port=MCP_PORT,
    log_level="DEBUG" if MCP_DEBUG.lower() == "true" else "INFO",
)

# ─── jira_list_projects ───────────────────────────────────────────────

@mcp.tool()
def jira_list_projects() -> list:
    """
    List all Jira projects accessible to the authenticated user.
    Returns a list of project objects with keys: key, id, name.
    """
    return jira_client.list_projects()

# ─── jira_create_issue ────────────────────────────────────────────────

@mcp.tool()
def jira_create_issue(
    project_key: str,
    issue_type: str,
    summary: str,
    description: str = "",
    priority: str = "Medium",
    parent_key: Optional[str] = None,
    epic_link: Optional[str] = None,
    epic_name: Optional[str] = None,
    labels: Optional[List[str]] = None,
) -> dict:
    """
    Create a new Jira issue.

    Args:
        project_key: Jira project key e.g. PROJ.
        issue_type:  Epic | Story | Bug | Test | Task.
        summary:     Issue title / summary.
        description: Issue body text.
        priority:    Highest | High | Medium | Low | Lowest.
        parent_key:  Parent issue key for child issues.
        epic_link:   Epic key to link this issue to (Jira cloud).
        epic_name:   Display name for Epic type (defaults to summary).
        labels:      List of label strings.

    Returns:
        dict with key, id, url, summary, issueType.
    """
    return jira_client.create_issue(
        project_key=project_key,
        issue_type=issue_type,
        summary=summary,
        description=description,
        priority=priority,
        parent_key=parent_key,
        epic_link=epic_link,
        epic_name=epic_name,
        labels=labels,
    )

# ─── jira_get_issue ───────────────────────────────────────────────────

@mcp.tool()
def jira_get_issue(issue_key: str) -> dict:
    """
    Get full details of a Jira issue by its key (e.g. PROJ-42).

    Returns dict with: key, id, url, summary, description, status,
    priority, issueType, assignee, reporter, labels, created, updated.
    """
    return jira_client.get_issue(issue_key)

# ─── jira_update_issue ────────────────────────────────────────────────

@mcp.tool()
def jira_update_issue(
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_name: Optional[str] = None,
    labels: Optional[List[str]] = None,
) -> dict:
    """
    Update an existing Jira issue. Only supplied fields are changed.

    Args:
        issue_key:     Jira issue key e.g. PROJ-42.
        summary:       New title (optional).
        description:   New description (optional).
        priority:      New priority string (optional).
        assignee_name: Username of new assignee (optional).
        labels:        Replacement label list (optional).

    Returns:
        dict with key, updated.
    """
    return jira_client.update_issue(
        issue_key=issue_key,
        summary=summary,
        description=description,
        priority=priority,
        assignee_name=assignee_name,
        labels=labels,
    )

# ─── jira_search_issues ───────────────────────────────────────────────

@mcp.tool()
def jira_search_issues(jql: str, max_results: int = 50) -> list:
    """
    Search Jira issues using JQL (Jira Query Language).

    Args:
        jql:         JQL query e.g. 'project = PROJ AND issuetype = Epic ORDER BY created DESC'.
        max_results: Maximum results to return (default 50, max 100).

    Returns:
        List of issue dicts with key, id, summary, status, priority, issueType, assignee.
    """
    return jira_client.search_issues(jql=jql, max_results=min(max_results, 100))

# ─── jira_add_comment ─────────────────────────────────────────────────

@mcp.tool()
def jira_add_comment(issue_key: str, body: str) -> dict:
    """
    Add a comment to an existing Jira issue.

    Args:
        issue_key: Jira issue key e.g. PROJ-42.
        body:      Comment text.

    Returns:
        dict with id, body, created.
    """
    return jira_client.add_comment(issue_key=issue_key, body=body)

# ─── jira_get_transitions ─────────────────────────────────────────────

@mcp.tool()
def jira_get_transitions(issue_key: str) -> list:
    """
    Get available workflow transitions for a Jira issue.
    Use this before jira_transition_issue to discover valid transition IDs.

    Args:
        issue_key: Jira issue key e.g. PROJ-42.

    Returns:
        List of dicts with id (str) and name (str).
    """
    return jira_client.get_transitions(issue_key)

# ─── jira_transition_issue ────────────────────────────────────────────

@mcp.tool()
def jira_transition_issue(issue_key: str, transition_id: str) -> dict:
    """
    Move a Jira issue to a new workflow status using a transition ID.
    Use jira_get_transitions first to get the valid transition IDs.

    Args:
        issue_key:     Jira issue key e.g. PROJ-42.
        transition_id: Numeric transition ID as string e.g. '31'.

    Returns:
        dict with key, transitioned, transitionId.
    """
    return jira_client.transition_issue(issue_key=issue_key, transition_id=transition_id)

logger.info("Registered 8 Jira MCP tools.")




if __name__ == "__main__":
    import os

    mcp.run(transport=MCP_TRANSPORT, host=MCP_HOST, port=MCP_PORT)
