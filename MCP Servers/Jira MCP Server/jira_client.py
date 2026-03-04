"""
Jira Client – thin wrapper around the `jira` SDK.

Provides lazy initialisation and mock responses when credentials are not
configured, so the MCP server can start and respond to tool listings even
without a live Jira instance (useful for local development / tests).
"""
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

JIRA_URL = os.environ.get("JIRA_URL", "https://hsskill.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")


class JiraClient:
    """Lazy-initialised wrapper around the Atlassian `jira` SDK."""

    def __init__(self):
        self._client = None

    # ─── Connection ───────────────────────────────────────────────────────

    def _get(self):
        if self._client is not None:
            return self._client

        base_url = JIRA_URL
        if not base_url or not JIRA_EMAIL or not JIRA_API_TOKEN:
            logger.warning(
                "Jira credentials not configured. "
                "Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env"
            )
            return None

        try:
            from jira import JIRA
            self._client = JIRA(
                server=base_url,
                basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
                max_retries=1,
            )
            logger.info(f"Jira client connected to {base_url}")
        except Exception as exc:
            logger.error(f"Jira client init failed: {exc}")
            self._client = None

        return self._client

    def is_connected(self) -> bool:
        return self._get() is not None

    # ─── Projects ─────────────────────────────────────────────────────────

    def list_projects(self) -> List[Dict[str, Any]]:
        client = self._get()
        if not client:
            return [{"key": "MOCK", "name": "Mock Project (no Jira credentials)"}]
        return [
            {"key": p.key, "id": p.id, "name": p.name}
            for p in client.projects()
        ]

    # ─── Issues – Create ──────────────────────────────────────────────────

    def create_issue(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str = "",
        priority: str = "Medium",
        parent_key: Optional[str] = None,
        epic_link: Optional[str] = None,
        epic_name: Optional[str] = None,
        labels: Optional[List[str]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        client = self._get()
        if not client:
            mock_key = f"{project_key}-MOCK"
            return {"key": mock_key, "id": "mock-id", "url": "#", "mock": True}

        fields: Dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }

        if labels:
            fields["labels"] = labels

        # Epic-specific: set Epic Name custom field
        if issue_type.lower() == "epic":
            fields["customfield_10011"] = epic_name or summary  # Epic Name

        # Link to Epic via Epic Link (Jira Software cloud)
        if epic_link:
            fields["customfield_10014"] = epic_link

        # Sub-task / child issue parent
        if parent_key and issue_type.lower() not in ("epic",):
            fields["parent"] = {"key": parent_key}

        if extra_fields:
            fields.update(extra_fields)

        try:
            issue = client.create_issue(fields=fields)
            return {
                "key": issue.key,
                "id": issue.id,
                "url": issue.permalink(),
                "summary": summary,
                "issueType": issue_type,
            }
        except Exception as exc:
            logger.error(f"create_issue failed: {exc}")
            raise

    # ─── Issues – Read ────────────────────────────────────────────────────

    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        client = self._get()
        if not client:
            return {"key": issue_key, "summary": "Mock Issue", "mock": True}
        try:
            issue = client.issue(issue_key)
            fields = issue.fields
            return {
                "key": issue.key,
                "id": issue.id,
                "url": issue.permalink(),
                "summary": fields.summary,
                "description": fields.description or "",
                "status": fields.status.name,
                "priority": fields.priority.name if fields.priority else "Medium",
                "issueType": fields.issuetype.name,
                "assignee": fields.assignee.displayName if fields.assignee else None,
                "reporter": fields.reporter.displayName if fields.reporter else None,
                "labels": fields.labels or [],
                "created": str(fields.created),
                "updated": str(fields.updated),
            }
        except Exception as exc:
            logger.error(f"get_issue failed for {issue_key}: {exc}")
            raise

    # ─── Issues – Update ──────────────────────────────────────────────────

    def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_name: Optional[str] = None,
        labels: Optional[List[str]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        client = self._get()
        if not client:
            return {"key": issue_key, "updated": True, "mock": True}
        try:
            issue = client.issue(issue_key)
            update: Dict[str, Any] = {}
            if summary is not None:
                update["summary"] = summary
            if description is not None:
                update["description"] = description
            if priority is not None:
                update["priority"] = {"name": priority}
            if assignee_name is not None:
                update["assignee"] = {"name": assignee_name}
            if labels is not None:
                update["labels"] = labels
            if extra_fields:
                update.update(extra_fields)
            issue.update(fields=update)
            return {"key": issue_key, "updated": True}
        except Exception as exc:
            logger.error(f"update_issue failed for {issue_key}: {exc}")
            raise

    # ─── Issues – Search ──────────────────────────────────────────────────

    def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        client = self._get()
        if not client:
            return []
        try:
            field_str = ",".join(fields) if fields else "summary,status,priority,issuetype,assignee"
            results = client.search_issues(jql, maxResults=max_results, fields=field_str)
            return [
                {
                    "key": issue.key,
                    "id": issue.id,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "priority": issue.fields.priority.name if issue.fields.priority else "Medium",
                    "issueType": issue.fields.issuetype.name,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                }
                for issue in results
            ]
        except Exception as exc:
            logger.error(f"search_issues failed (JQL: {jql}): {exc}")
            raise

    # ─── Comments ─────────────────────────────────────────────────────────

    def add_comment(self, issue_key: str, body: str) -> Dict[str, Any]:
        client = self._get()
        if not client:
            return {"id": "mock-comment", "body": body, "mock": True}
        try:
            comment = client.add_comment(issue_key, body)
            return {"id": comment.id, "body": comment.body, "created": str(comment.created)}
        except Exception as exc:
            logger.error(f"add_comment failed for {issue_key}: {exc}")
            raise

    # ─── Transitions ──────────────────────────────────────────────────────

    def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        client = self._get()
        if not client:
            return [{"id": "11", "name": "To Do"}, {"id": "21", "name": "In Progress"}, {"id": "31", "name": "Done"}]
        try:
            transitions = client.transitions(issue_key)
            return [{"id": t["id"], "name": t["name"]} for t in transitions]
        except Exception as exc:
            logger.error(f"get_transitions failed for {issue_key}: {exc}")
            raise

    def transition_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        client = self._get()
        if not client:
            return {"key": issue_key, "transitioned": True, "mock": True}
        try:
            client.transition_issue(issue_key, transition_id)
            return {"key": issue_key, "transitioned": True, "transitionId": transition_id}
        except Exception as exc:
            logger.error(f"transition_issue failed for {issue_key}: {exc}")
            raise


# ─── Singleton ────────────────────────────────────────────────────────────────
jira_client = JiraClient()
