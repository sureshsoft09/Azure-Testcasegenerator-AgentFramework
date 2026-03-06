import json
import logging
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

from core.config import settings
from core.cosmos_client import get_container

logger = logging.getLogger(__name__)


class CosmosService:
    # ─── Projects ──────────────────────────────────────────────────────────────

    async def create_project(self, project: dict) -> dict:
        container = await get_container(settings.COSMOS_PROJECTS_CONTAINER)
        result = await container.create_item(body=project)
        return result

    async def get_all_projects(self) -> List[dict]:
        container = await get_container(settings.COSMOS_PROJECTS_CONTAINER)
        items = []
        async for item in container.query_items(
            query="SELECT * FROM c ORDER BY c.createdAt DESC"
        ):
            items.append(item)
        return items

    async def get_project_by_id(self, project_id: str) -> Optional[dict]:
        container = await get_container(settings.COSMOS_PROJECTS_CONTAINER)
        try:
            async for item in container.query_items(
                query=f"SELECT * FROM c WHERE c.projectId = '{project_id}'"
            ):
                return item
        except Exception:
            return None
        return None

    # ─── Artifacts ─────────────────────────────────────────────────────────────

    async def save_artifacts(self, project_id: str, artifacts: dict) -> dict:
        container = await get_container(settings.COSMOS_ARTIFACTS_CONTAINER)
        artifacts["id"] = artifacts.get("id", str(uuid.uuid4()))
        artifacts["projectId"] = project_id
        artifacts["updatedAt"] = datetime.utcnow().isoformat()
        result = await container.upsert_item(body=artifacts)
        return result

    async def get_project_artifacts(self, project_id: str) -> Optional[dict]:
        container = await get_container(settings.COSMOS_ARTIFACTS_CONTAINER)
        async for item in container.query_items(
            query="SELECT * FROM c WHERE c.projectId = @projectId",
            parameters=[{"name": "@projectId", "value": project_id}]
        ):
            return item
        return None

    async def update_artifact(self, project_id: str, artifact_id: str, updated: dict) -> dict:
        container = await get_container(settings.COSMOS_ARTIFACTS_CONTAINER)
        # Fetch the full document first
        doc = await self.get_project_artifacts(project_id)
        if not doc:
            raise ValueError(f"No artifacts found for project {project_id}")
        # Update the specific artifact in the hierarchy
        self._update_artifact_in_tree(doc, artifact_id, updated)
        doc["updatedAt"] = datetime.utcnow().isoformat()
        return await container.upsert_item(body=doc)

    def _update_artifact_in_tree(self, doc: dict, artifact_id: str, updated: dict):
        for epic in doc.get("epics", []):
            if epic.get("id") == artifact_id:
                epic.update(updated)
                return
            for feature in epic.get("features", []):
                if feature.get("id") == artifact_id:
                    feature.update(updated)
                    return
                for uc in feature.get("useCases", []):
                    if uc.get("id") == artifact_id:
                        uc.update(updated)
                        return
                    for tc in uc.get("testCases", []):
                        if tc.get("id") == artifact_id:
                            tc.update(updated)
                            return

    # ─── Sessions ──────────────────────────────────────────────────────────────

    async def save_session(self, session: dict) -> dict:
        container = await get_container(settings.COSMOS_SESSIONS_CONTAINER)
        result = await container.upsert_item(body=session)
        return result

    async def get_session(self, session_id: str) -> Optional[dict]:
        container = await get_container(settings.COSMOS_SESSIONS_CONTAINER)
        async for item in container.query_items(
            query=f"SELECT * FROM c WHERE c.sessionId = '{session_id}'"
        ):
            return item
        return None


cosmos_service = CosmosService()
