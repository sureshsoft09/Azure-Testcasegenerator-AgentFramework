import uuid
import logging
from typing import List, Dict

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from models.schemas import (
    ProjectCreate, Project, ReviewChatRequest, ReviewChatResponse,
    ChatMessage, GenerateTestCasesRequest, GenerationResult,
    AgentWorkflowRequest, AgentWorkflowResponse,
)
from services.cosmos_service import cosmos_service
from services.blob_storage import upload_blob
from services.document_parser import parse_document
from services import agent_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Temporary in-memory storage for parsed documents by session
# In production, consider using Redis or similar for distributed systems
_session_storage: Dict[str, List[Dict]] = {}


# ─── Step 1: Create Project ────────────────────────────────────────────────────

@router.post("/projects", response_model=Project)
async def create_new_project(payload: ProjectCreate):
    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        projectId=project_id,
        projectName=payload.projectName,
        jiraProjectKey=payload.jiraProjectKey,
        notificationEmail=payload.notificationEmail,
        description=payload.description or "",
    )
    try:
        saved = await cosmos_service.create_project(project.model_dump())
        return saved
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = await cosmos_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ─── Step 2: Upload Files ──────────────────────────────────────────────────────

@router.post("/projects/{project_id}/upload")
async def upload_requirement_files(
    project_id: str,
    files: List[UploadFile] = File(...),
):
    uploaded = []
    parsed_texts = []

    for file in files:
        content = await file.read()
        blob_name = f"{project_id}/{uuid.uuid4()}_{file.filename}"
        try:
            blob_url = await upload_blob(content, blob_name, file.content_type or "application/octet-stream")
        except Exception:
            blob_url = f"mock://blob/{blob_name}"

        text, _ = parse_document(content, file.filename)
        parsed_texts.append({"filename": file.filename, "text": text})
        uploaded.append({"filename": file.filename, "blobUrl": blob_url, "blobName": blob_name})

    # Generate session ID and store parsed documents for later use
    session_id = str(uuid.uuid4())
    _session_storage[session_id] = parsed_texts
    
    logger.info(f"Stored {len(parsed_texts)} parsed documents for session {session_id}")

    return {
        "sessionId": session_id,
        "uploadedFiles": uploaded, 
        "parsedDocuments": parsed_texts
    }


# ─── Step 2b: Review Requirements ─────────────────────────────────────────────

@router.post("/projects/{project_id}/review")
async def review_requirements(project_id: str, body: dict):
    # Get sessionId from request body
    session_id = body.get("sessionId", "")
    
    # Try to get parsed documents from session storage first
    parsed_documents = _session_storage.get(session_id, [])
    
    # Fallback: accept parsedDocuments passed directly from the request
    if not parsed_documents:
        parsed_documents = body.get("parsedDocuments", [])
    
    if not parsed_documents:
        raise HTTPException(
            status_code=400, 
            detail="No documents found. Please upload files first or provide parsedDocuments."
        )

    logger.info(f"Processing review for session {session_id} with {len(parsed_documents)} documents")

    combined_text = "\n\n---\n\n".join(
        f"File: {d['filename']}\n{d['text']}"
        for d in parsed_documents
    )

    print(f"Combined text for agent:\n{combined_text[:1000]}...")  # Log first 1000 chars

    # Build a comprehensive prompt for the agent
    prompt = f"""
    Please review and analyze the following requirement specifications for project '{project_id}':

    pass this to requirement_reviewer_agent not any other tools.

    EXTRACTED CONTENT:
    {combined_text}

    """
    messages = await agent_service.agent_workflow_run(prompt)
    
    agent_content = "\n".join(messages)

    return {
        "sessionId": session_id,
        "messages": [{"role": "agent", "content": agent_content}],
        "estimatedArtifacts": None,
        "allClarified": False,
    }


# ─── Step 3: Chat ──────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/review/chat", response_model=ReviewChatResponse)
async def review_chat(project_id: str, body: ReviewChatRequest):
    # Call agent service directly with the user message
    messages = await agent_service.agent_workflow_run(body.message)
    agent_content = "\n".join(messages)

    return ReviewChatResponse(
        sessionId=body.sessionId or "",
        messages=[
            ChatMessage(role="user", content=body.message),
            ChatMessage(role="agent", content=agent_content),
        ],
        estimatedArtifacts=None,
        allClarified=False,
    )


# ─── Step 4: Generate Test Cases ──────────────────────────────────────────────

@router.post("/projects/{project_id}/generate", response_model=GenerationResult)
async def generate_test_cases(project_id: str, body: GenerateTestCasesRequest):
    project = await cosmos_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build prompt from any context included in the request
    generate_prompt = "Generate test cases for this project."
    messages = await agent_service.agent_workflow_run(generate_prompt)
    epics = []  # Structured artifacts parsed from agent messages if needed

    # Count artifacts
    epic_count = len(epics)
    feat_count = sum(len(e.get("features", [])) for e in epics)
    uc_count = sum(len(f.get("useCases", [])) for e in epics for f in e.get("features", []))
    tc_count = sum(
        len(uc.get("testCases", []))
        for e in epics
        for f in e.get("features", [])
        for uc in f.get("useCases", [])
    )

    jira_key = project.get("jiraProjectKey", "PROJ")

    # Push to Jira via agent
    jira_count = 0
    if epics:
        try:
            import json as _json
            jira_prompt = f"Push the following test artifacts to Jira project {jira_key}:\n{_json.dumps(epics, indent=2)}"
            await agent_service.agent_workflow_run(jira_prompt)
        except Exception as e:
            logger.warning(f"Jira push encountered errors: {e}")

    # Save to CosmosDB
    cosmos_doc = {
        "projectId": project_id,
        "projectName": project.get("projectName", ""),
        "jiraProjectKey": jira_key,
        "epics": epics,
        "totalEpics": epic_count,
        "totalFeatures": feat_count,
        "totalUseCases": uc_count,
        "totalTestCases": tc_count,
    }
    try:
        await cosmos_service.save_artifacts(project_id, cosmos_doc)
    except Exception as e:
        logger.error(f"Cosmos save failed: {e}")

    return GenerationResult(
        projectId=project_id,
        sessionId=body.sessionId,
        epicsCreated=epic_count,
        featuresCreated=feat_count,
        useCasesCreated=uc_count,
        testCasesCreated=tc_count,
        jiraIssuesCreated=jira_count,
        status="completed",
    )

