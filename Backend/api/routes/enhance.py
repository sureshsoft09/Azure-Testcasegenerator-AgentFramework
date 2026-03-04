import logging
import json
from fastapi import APIRouter, HTTPException
from models.schemas import EnhanceChatRequest, EnhanceChatResponse, ApplyEnhancementRequest, ChatMessage
from services import agent_service
from services.cosmos_service import cosmos_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _find_artifact(artifacts: dict, artifact_id: str) -> dict:
    for epic in artifacts.get("epics", []):
        if epic.get("id") == artifact_id:
            return epic
        for feature in epic.get("features", []):
            if feature.get("id") == artifact_id:
                return feature
            for uc in feature.get("useCases", []):
                if uc.get("id") == artifact_id:
                    return uc
                for tc in uc.get("testCases", []):
                    if tc.get("id") == artifact_id:
                        return tc
    return {}


@router.post("/chat", response_model=EnhanceChatResponse)
async def enhance_artifact_chat(body: EnhanceChatRequest):
    # Load artifact directly from CosmosDB
    artifacts = await cosmos_service.get_project_artifacts(body.projectId)
    artifact = _find_artifact(artifacts or {}, body.artifactId)

    # Delegate to EnhanceAgent via agent_service
    enhance_prompt = (
        f"Enhance the following artifact based on the user request.\n\n"
        f"Artifact ({body.artifactType}):\n{json.dumps(artifact, indent=2)}\n\n"
        f"User request: {body.message}"
    )
    messages = await agent_service.agent_workflow_run(enhance_prompt)
    agent_content = "\n".join(messages)

    return EnhanceChatResponse(
        sessionId=body.sessionId or "",
        messages=[
            ChatMessage(role="user", content=body.message),
            ChatMessage(role="agent", content=agent_content),
        ],
        updatedArtifact=None,
        readyToApply=False,
    )


@router.post("/apply")
async def apply_enhancement(body: ApplyEnhancementRequest):
    project = await cosmos_service.get_project_artifacts(body.projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project artifacts not found")

    # Update in CosmosDB
    try:
        await cosmos_service.update_artifact(body.projectId, body.artifactId, body.updatedArtifact)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CosmosDB update failed: {e}")

    # Update in Jira via MCP connector (with SDK fallback)
    jira_key = body.updatedArtifact.get("jiraIssueKey")
    if jira_key:
        try:
            update_prompt = (
                f"Update Jira issue {jira_key} with the following changes:\n"
                f"Title: {body.updatedArtifact.get('title', '')}\n"
                f"Description: {body.updatedArtifact.get('description', '')}"
            )
            await agent_service.agent_workflow_run(update_prompt)
        except Exception as e:
            logger.warning(f"Jira update warning: {e}")

    return {"status": "success", "artifactId": body.artifactId, "jiraKey": jira_key}
