import os
import uuid
import logging
import json
import re
from typing import List, Dict, Optional

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


def extract_json_from_content(content: str) -> Optional[dict]:
    """
    Extract and parse JSON from agent response content.
    Handles cases where JSON might be wrapped in markdown code blocks, mixed with text,
    or prefixed with agent names like "## [Master]: ".
    """
    try:
        # Try direct JSON parse first
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Find the first '{' and try to parse from there (handles agent prefixes)
    start_idx = content.find('{')
    if start_idx != -1:
        try:
            # Try to parse from the first brace to the end
            return json.loads(content[start_idx:])
        except json.JSONDecodeError:
            pass
        
        # Try to find a complete JSON object starting from first brace
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i in range(start_idx, len(content)):
            char = content[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found complete JSON object
                        try:
                            return json.loads(content[start_idx:i+1])
                        except json.JSONDecodeError:
                            break
    
    return None


def format_review_response(json_data: dict) -> str:
    """
    Format the requirement reviewer's JSON response into user-friendly text.
    """
    if not json_data:
        return "Unable to parse agent response."
    
    lines = []
    overall_status = json_data.get("overall_status", "")
    
    # Check if this is a clarification request
    if overall_status == "Clarifications Needed":
        lines.append("## 📋 Requirement Review")
        lines.append("")
        
        readiness = json_data.get("readiness_plan", {})
        if readiness:
            lines.append("### 📊 Estimated Test Artifacts")
            lines.append(f"- **Epics:** {readiness.get('estimated_epics', 0)}")
            lines.append(f"- **Features:** {readiness.get('estimated_features', 0)}")
            lines.append(f"- **Use Cases:** {readiness.get('estimated_use_cases', 0)}")
            lines.append(f"- **Test Cases:** {readiness.get('estimated_test_cases', 0)}")
            lines.append("")
        
        # Questions from assistant_response
        questions = json_data.get("assistant_response", [])
        if questions:
            lines.append("### 💬 Clarifications Needed:")
            lines.append("")
            for q in questions:
                lines.append(f"- {q}")
            lines.append("")
        
        next_action = json_data.get("next_action", "")
        if next_action:
            lines.append(f"**Next Step:** {next_action}")
        
    # Check if this is an approval response
    elif overall_status == "Ready for Test Generation" or json_data.get("test_generation_status", {}).get("ready_for_generation"):
        lines.append("## ✅ Requirements Approved!")
        lines.append("")
        
        readiness = json_data.get("readiness_plan", {})
        lines.append("### 📊 Estimated Test Artifacts")
        lines.append(f"- **Epics:** {readiness.get('estimated_epics', 0)}")
        lines.append(f"- **Features:** {readiness.get('estimated_features', 0)}")
        lines.append(f"- **Use Cases:** {readiness.get('estimated_use_cases', 0)}")
        lines.append(f"- **Test Cases:** {readiness.get('estimated_test_cases', 0)}")
        lines.append("")
        
        breakdown = readiness.get("estimated_breakdown", {})
        if breakdown:
            lines.append("### 🧪 Test Coverage Breakdown")
            for test_type, count in breakdown.items():
                formatted_type = test_type.replace('_', ' ').title()
                lines.append(f"- {formatted_type}: {count}")
            lines.append("")
        
        # Show response messages if any
        responses = json_data.get("assistant_response", [])
        if responses:
            for msg in responses:
                lines.append(msg)
            lines.append("")
        
        lines.append("✨ Ready to generate test cases!")
    
    return "\n".join(lines) if lines else json.dumps(json_data, indent=2)


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

    # Build a comprehensive prompt for the agent
    prompt = f"""
    ROUTE TO: testcasegenerator_requirement_reviewer_agent

    You are the requirement reviewer agent. Review and analyze the following requirement specifications for project '{project_id}'.

    If any requirements are ambiguous, incomplete, or have compliance gaps, identify them clearly and ask for specific clarifications in the below JSON output response.
    
    Do NOT transfer to any other agent. Do NOT call any tools.

    Queries to User - Response format:
    {{
        "overall_status": "Clarifications Needed",
        "readiness_plan": {{
            "estimated_epics": 5,
            "estimated_features": 10,
            "estimated_use_cases": 18,
            "estimated_test_cases": 30
        }},
        "assistant_response": [
            "Requirement REQ-12 is vague. Please specify acceptable response time (e.g., in seconds).",
            "Requirement REQ-27 mentions compliance but does not specify which standard — please confirm if FDA or IEC 62304 applies."
        ],
        "test_generation_status": {{}},
        "next_action": "Awaiting user clarifications or confirmation for pending items."
    }}

    If all requirements are clear, complete, and compliant, respond with an approval and readiness plan in the below JSON format:
    
    {{
        "overall_status": "Ready for Test Generation",
        "readiness_plan": {{
            "estimated_epics": 5,
            "estimated_features": 10,
            "estimated_use_cases": 18,
            "estimated_test_cases": 30
        }},
        "assistant_response": [
            "All clarifications have been addressed or confirmed. The document is ready for test case generation."
        ],
        "test_generation_status": {{"ready_for_generation": true}},
        "next_action": "User can proceed to click 'Generate Test Cases'."
    }}

    Requirements content:
    {combined_text}

    """
    messages = await agent_service.agent_workflow_run(prompt)

    # Join all messages from agents
    agent_content = "\n\n".join(msg for msg in messages if msg)

    print(f"Agent response for review:\n{agent_content[:3000]}...")  # Log first 3000 chars of response
    
    logger.info(f"Raw agent response length: {len(agent_content)}")

    return {
        "sessionId": session_id,
        "messages": [{"content": agent_content}]
    }


# ─── Step 3: Chat ──────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/review/chat", response_model=ReviewChatResponse)
async def review_chat(project_id: str, body: ReviewChatRequest):

    prompt = f"""
    ROUTE TO: testcasegenerator_requirement_reviewer_agent

    You are the requirement reviewer agent. The user has provided a clarification response for an ongoing requirement review.
    Evaluate whether the clarification resolves the outstanding questions or if more clarifications are needed.

    Context:
    - Type: Clarification Interaction
    - Intent: Resolve pending ambiguities, provide clarification, or confirm requirements as complete.
    - User message: {body.message}

    Do NOT transfer to any other agent. Do NOT call any tools.

    If there are still outstanding clarifications needed, respond in this JSON format:
    {{
        "overall_status": "Clarifications Needed",
        "readiness_plan": {{
            "estimated_epics": 5,
            "estimated_features": 10,
            "estimated_use_cases": 18,
            "estimated_test_cases": 30
        }},
        "assistant_response": [
            "Requirement REQ-12 is vague. Please specify acceptable response time (e.g., in seconds).",
            "Requirement REQ-27 mentions compliance but does not specify which standard — please confirm if FDA or IEC 62304 applies."
        ],
        "test_generation_status": {{}},
        "next_action": "Awaiting user clarifications or confirmation for pending items."
    }}

    If all requirements are clear, complete, and compliant, respond with an approval and readiness plan in the below JSON format:
    
    {{
        "overall_status": "Ready for Test Generation",
        "readiness_plan": {{
            "estimated_epics": 5,
            "estimated_features": 10,
            "estimated_use_cases": 18,
            "estimated_test_cases": 30
        }},
        "assistant_response": [
            "All clarifications have been addressed or confirmed. The document is ready for test case generation."
        ],
        "test_generation_status": {{"ready_for_generation": true}},
        "next_action": "User can proceed to click 'Generate Test Cases'."
    }}
    
    """
    # Call agent service directly with the user message
    messages = await agent_service.agent_workflow_run(prompt)
    agent_content = "\n\n".join(msg for msg in messages if msg)

    logger.info(f"Chat response length: {len(agent_content)}")

    print(f"Agent response for chat:\n{agent_content[:3000]}...")  # Log first 3000 chars of response

    # Try to extract and parse JSON from the response
    json_data = extract_json_from_content(agent_content)
    
    # Format the response for display
    if json_data:
        formatted_content = format_review_response(json_data)
        logger.info("Successfully parsed and formatted JSON response from chat")
        
        # Extract readiness plan if available
        readiness_plan = json_data.get("readiness_plan", {})
        estimated_artifacts = None
        all_clarified = json_data.get("overall_status") == "Ready for Test Generation" or json_data.get("test_generation_status", {}).get("ready_for_generation", False)
        
        if readiness_plan and readiness_plan.get("estimated_epics"):
            estimated_artifacts = {
                "epics": readiness_plan.get("estimated_epics", 0),
                "features": readiness_plan.get("estimated_features", 0),
                "useCases": readiness_plan.get("estimated_use_cases", 0),
                "testCases": readiness_plan.get("estimated_test_cases", 0),
            }
    else:
        # Fallback to raw content if JSON parsing fails
        formatted_content = agent_content
        estimated_artifacts = None
        all_clarified = False
        logger.warning("Could not parse JSON from chat response, using raw content")

    return ReviewChatResponse(
        sessionId=body.sessionId or "",
        messages=[
            ChatMessage(role="user", content=body.message),
            ChatMessage(role="agent", content=formatted_content),
        ],
        estimatedArtifacts=estimated_artifacts,
        allClarified=all_clarified,
    )


# ─── Step 4: Generate Test Cases ──────────────────────────────────────────────

@router.post("/projects/{project_id}/generate", response_model=GenerationResult)
async def generate_test_cases(project_id: str, body: GenerateTestCasesRequest):
    project = await cosmos_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build prompt from any context included in the request
    _tc_format_example = """
    {
    "project_id": "testpro12_2432",
    "epics": [
        {
        "epic_id": "E001",
        "epic_name": "User Authentication & Access Control",
        "description": "Handles user login, authentication, and access management functionalities.",
        "priority": "Critical",
        "jira_issue_id": null,
        "jira_issue_key": null,
        "jira_issue_url": null,
        "jira_status": "Not Pushed",
        "features": [
            {
            "feature_id": "F001",
            "feature_name": "Login Validation",
            "description": "Handles user login processes including credential validation and session management.",
            "priority": "High",
            "jira_issue_id": null,
            "jira_issue_key": null,
            "jira_issue_url": null,
            "jira_status": "Not Pushed",
            "use_cases": [
                {
                "use_case_id": "UC001",
                "title": "User logs in with valid credentials",
                "description": "System validates user credentials and provides access.",
                "acceptance_criteria": [
                    "Given valid user credentials, when the user attempts to log in, then the system should grant access and log the event in the audit trail.",
                    "Given invalid user credentials, when the user attempts to log in, then the system should deny access and log the failed attempt in the audit trail."
                ],
                "priority": "Medium",
                "jira_issue_id": null,
                "jira_issue_key": null,
                "jira_issue_url": null,
                "jira_status": "Not Pushed",
                "test_scenarios_outline": [
                    "Verify login success for valid credentials",
                    "Validate error handling for invalid password",
                    "Check audit log entry after login"
                ],
                "model_explanation": "Derived from authentication and access control requirements validated under ISO 9001 and FDA 820.30(g).",
                "review_status": "Approved",
                "comments": "Use case well-defined and compliant.",
                "test_cases": [
                    {
                    "test_case_id": "TC001",
                    "test_case_title": "Valid User Login",
                    "preconditions": [
                        "User exists in system",
                        "Credentials are valid"
                    ],
                    "test_steps": [
                        "Navigate to login page",
                        "Enter username and password",
                        "Click login"
                    ],
                    "expected_result": "System grants access and logs event in audit trail.",
                    "test_type": "Functional",
                    "priority": "High",
                    "jira_issue_id": null,
                    "jira_issue_key": null,
                    "jira_issue_url": null,
                    "jira_status": "Not Pushed",
                    "compliance_mapping": [
                        "FDA 820.30(g)",
                        "IEC 62304:5.1",
                        "ISO 13485:7.3",
                        "ISO 9001:8.5"
                    ],
                    "model_explanation": "Derived from validated requirement-to-test linkage under ISO and FDA frameworks.",
                    "review_status": "Approved",
                    "comments": "Test case meets all compliance and explainability criteria."
                    },
                    {
                    "test_case_id": "TC002",
                    "test_case_title": "Invalid Password Login Attempt",
                    "preconditions": [
                        "User exists in system"
                    ],
                    "test_steps": [
                        "Enter incorrect password",
                        "Click login"
                    ],
                    "expected_result": "System displays error and logs failed attempt.",
                    "test_type": "Negative",
                    "priority": "Low",
                    "jira_issue_id": null,
                    "jira_issue_key": null,
                    "jira_issue_url": null,
                    "jira_status": "Not Pushed",
                    "compliance_mapping": [
                        "FDA 820.30(g)",
                        "IEC 62304:5.1"
                    ],
                    "model_explanation": "Derived from negative path validation requirements.",
                    "review_status": "Needs Clarification",
                    "comments": "Missing ISO 9001 mapping; clarify expected validation method."
                    }
                ],
                "compliance_mapping": [
                    "FDA 820.30(g)",
                    "IEC 62304:5.1",
                    "ISO 13485:7.3",
                    "ISO 9001:8.5"
                ]
                }
            ]
            }
        ]
        }
    ],
    "epics_generated": 1,
    "features_generated": 4,
    "use_cases_generated": 10,
    "test_cases_generated": 25,
    "pushed_to_jira": false,
    "next_action": "Generated artifacts to be pushed to Jira and update the jira ids in the above artifacts",
    "status": "generation_completed"
    }
    """

    jira_project_key = project.get("jiraProjectKey", "PROJ")

    generate_prompt = f"""
    ROUTE TO: testcasegenerator_testcasegenerator_agent

    You are the test case generator agent. Generate complete test cases from the previously reviewed and approved requirements.
    Produce structured test artifacts (Epics, Features, Use Cases, Test Cases) with full compliance mappings.

    Once you generate the artifacts, only output the artifact JSON.

    Use the following JSON format for the generated test cases and related artifacts:

    {_tc_format_example}

    """
    messages = await agent_service.agent_workflow_run(generate_prompt)

    print(f"Agent messages:\n{messages}")

    jira_updated_messages = messages

    
    if(os.getenv("JIRA_MCP_ENABLED", "false").lower() == "true"):
        # Push to Jira
        try:
            jira_prompt1 = f"""
            ROUTE TO: testcasegenerator_testcasegenerator_agent
            
            Push the generated artifacts to Jira project {jira_project_key} in FOUR sequential steps through JiraMCP Server tools . 
            Wait for each step to complete and capture the returned Jira keys and URLs before proceeding.

            STEP 1 - Create Epics
            Call jira_batch_create_issues with all Epic-level items:
                issue_type  = "Epic"
                summary     = epic name
                description = epic description
            Save each returned jira_issue_key and jira_issue_url as the epic's Jira fields.

            STEP 2 - Create Features
            Call jira_batch_create_issues with all Feature-level items:
                issue_type  = "New Feature"
                summary     = feature name
                description = feature description
                epic_link   = parent epic's Jira key from Step 1
            Save each returned jira_issue_key and jira_issue_url as the feature's Jira fields.

            STEP 3 - Create Use Cases
            Call jira_batch_create_issues with all Use Case items:
                issue_type  = "Improvement"
                summary     = use case title
                description = use case description (include acceptance criteria) + append at the end:
                            "\n\nRelated Feature: <feature_jira_url>" using the parent feature URL from Step 2
            No epic_link or parent_key needed.
            Save each returned jira_issue_key and jira_issue_url as the use case's Jira fields.

            STEP 4 - Create Test Cases
            Call jira_batch_create_issues with all Test Case items:
                issue_type  = "Task"
                summary     = test case title
                description = full test case text (preconditions, steps, expected result, compliance) + append at the end:
                            "\n\nRelated Use Case: <use_case_jira_url>" using the parent use case URL from Step 3
            No epic_link or parent_key needed.
            Save each returned jira_issue_key and jira_issue_url as the test case's Jira fields.

            After all four steps, update every artifact in the JSON with its Jira fields
            (jira_issue_key, jira_issue_id, jira_issue_url) and return the fully updated artifact JSON.

            """

            jira_prompt =(
                f"ROUTE TO: testcasegenerator_testcasegenerator_agent\n"
                f"Connect to the JIRA MCP Server and push the following artifacts to Jira project '{jira_project_key}' "
                f"in FOUR sequential steps. Wait for each step to complete and capture the returned Jira keys and URLs before proceeding.\n\n"
                f"ARTIFACTS:\n{messages}\n\n"
                f"Consider Priority Highest for Critical\n"
                f"STEP 1 - Create Epics\n"
                f"  Call jira_batch_create_issues:\n"
                f"    issue_type  = 'Epic'\n"
                f"    summary     = epic name\n"
                f"    description = epic description\n"
                f"  Save each returned jira_issue_key and jira_issue_url as that epic's Jira fields.\n\n"
                f"STEP 2 - Create Features\n"
                f"  Call jira_batch_create_issues:\n"
                f"    issue_type  = 'New Feature'\n"
                f"    summary     = feature name\n"
                f"    description = feature description\n"
                f"    epic_link   = parent epic's Jira key from Step 1\n"
                f"  Save each returned jira_issue_key and jira_issue_url as that feature's Jira fields.\n\n"
                f"STEP 3 - Create Use Cases\n"
                f"  Call jira_batch_create_issues:\n"
                f"    issue_type  = 'Improvement'\n"
                f"    summary     = use case title\n"
                f"    description = use case description (include acceptance criteria) + append at the end:\n"
                f"                  '\\n\\nRelated Feature: <feature_jira_url>' using the parent feature URL from Step 2\n"
                f"  No epic_link or parent_key needed.\n"
                f"  Save each returned jira_issue_key and jira_issue_url as that use case's Jira fields.\n\n"
                f"STEP 4 - Create Test Cases\n"
                f"  Call jira_batch_create_issues:\n"
                f"    issue_type  = 'Task'\n"
                f"    summary     = test case title\n"
                f"    description = full test case text (preconditions, steps, expected result, compliance) + append at the end:\n"
                f"                  '\\n\\nRelated Use Case: <use_case_jira_url>' using the parent use case URL from Step 3\n"
                f"  No epic_link or parent_key needed.\n"
                f"  Save each returned jira_issue_key and jira_issue_url as that test case's Jira fields.\n\n"
                f"After all four steps, update every artifact with its Jira fields "
                f"(jira_issue_key, jira_issue_id, jira_issue_url) and return the fully updated artifact JSON."
            )

            jira_updated_messages = await agent_service.agent_workflow_run(jira_prompt)
            print(f"Agent messages after Jira push:\n{jira_updated_messages}")

        except Exception as e:
            logger.warning(f"Jira push encountered errors: {e}")

    # Join all message parts and extract the JSON artifact payload
    agent_content = "\n\n".join(msg for msg in jira_updated_messages if msg)
    artifact_data = extract_json_from_content(agent_content)

    if not artifact_data:
        logger.warning("Could not parse JSON artifacts from agent response")
        artifact_data = {}

    epics = artifact_data.get("epics", [])

    # Count artifacts directly from the parsed JSON
    epic_count = artifact_data.get("epics_generated", len(epics))
    feat_count = artifact_data.get("features_generated",
        sum(len(e.get("features", [])) for e in epics))
    uc_count = artifact_data.get("use_cases_generated",
        sum(len(f.get("use_cases", [])) for e in epics for f in e.get("features", [])))
    tc_count = artifact_data.get("test_cases_generated",
        sum(len(uc.get("test_cases", []))
            for e in epics
            for f in e.get("features", [])
            for uc in f.get("use_cases", [])))    

    # Save full artifact document to CosmosDB
    cosmos_doc = {
        "projectId": project_id,
        "projectName": project.get("projectName", ""),
        "jiraProjectKey": jira_project_key,
        "epics": epics,
        "totalEpics": epic_count,
        "totalFeatures": feat_count,
        "totalUseCases": uc_count,
        "totalTestCases": tc_count,
        "pushedToJira": False,
        "status": artifact_data.get("status", "generation_completed"),
        "nextAction": artifact_data.get("next_action", ""),
        "rawArtifactData": artifact_data,
    }
    try:
        await cosmos_service.save_artifacts(project_id, cosmos_doc)
        logger.info(f"Saved artifacts to CosmosDB: {epic_count} epics, {feat_count} features, {uc_count} use cases, {tc_count} test cases")
    except Exception as e:
        logger.error(f"Cosmos save failed: {e}")

    return GenerationResult(
        projectId=project_id,
        sessionId=body.sessionId,
        epicsCreated=epic_count,
        featuresCreated=feat_count,
        useCasesCreated=uc_count,
        testCasesCreated=tc_count,
        jiraIssuesCreated=0,
        status="completed",
    )




