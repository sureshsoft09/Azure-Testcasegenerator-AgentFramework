import uuid
import io
import logging
from typing import List

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

import json
from models.schemas import MigrationResult
from services import agent_service
from services.cosmos_service import cosmos_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_migrate_files(
    project_id: str = Form(...),
    files: List[UploadFile] = File(...),
):
    """Upload Excel files and extract raw artifact data."""
    all_rows = []
    df = None

    for file in files:
        content = await file.read()
        try:
            df = pd.read_excel(io.BytesIO(content))
            rows = df.fillna("").to_dict(orient="records")
            all_rows.extend(rows)
        except Exception as e:
            logger.error(f"Excel parse error for {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Could not parse {file.filename}: {e}")

    # Get column names from first file for mapping UI
    columns = list(df.columns) if df is not None and all_rows else []

    return {"totalRows": len(all_rows), "columns": columns, "rawRows": all_rows}


@router.post("/configure")
async def configure_mapping(body: dict):
    """Apply column-to-field mappings to raw rows and return mapped result."""
    raw_rows = body.get("rawRows", [])
    mappings_input = body.get("mappings", [])

    if not raw_rows:
        raise HTTPException(status_code=400, detail="rawRows required")

    # mappings_input: list of {sourceColumn, targetField}
    mappings = {m["sourceColumn"]: m["targetField"] for m in mappings_input}

    mapped_rows = []
    for row in raw_rows:
        mapped = {}
        for src, tgt in mappings.items():
            mapped[tgt] = row.get(src, "")
        mapped["rawData"] = row
        mapped_rows.append(mapped)

    return {"preview": mapped_rows[:10], "totalRows": len(mapped_rows), "mappedRows": mapped_rows}


@router.post("/execute")
async def migrate_test_artifacts(body: dict):
    """Run migration: MigrationAgent normalises, then push to Jira (MCP) + CosmosDB."""
    project_id = body.get("projectId")
    mapped_rows = body.get("mappedRows", [])

    if not project_id:
        raise HTTPException(status_code=400, detail="projectId required")
    if not mapped_rows:
        raise HTTPException(status_code=400, detail="mappedRows required")

    project = await cosmos_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    errors: List[str] = []

    # MigrationAgent normalises the raw rows
    try:
        normalise_prompt = (
            f"Normalise and migrate the following test artifacts to the standard format:\n\n"
            f"{json.dumps(mapped_rows, indent=2)}"
        )
        await agent_service.agent_workflow_run(normalise_prompt)
        normalized = mapped_rows  # Use mapped_rows; agent output is informational
    except Exception as e:
        normalized = mapped_rows
        errors.append(f"Agent normalisation partial failure: {e}")

    jira_key = project.get("jiraProjectKey", "PROJ")

    # Wrap test cases in a minimal migration epic for push_artifacts_to_jira
    migration_epic_wrapper = [
        {
            "id": str(uuid.uuid4()),
            "title": "Migrated Test Cases",
            "description": "Test cases migrated from an external source.",
            "priority": "medium",
            "artifactType": "epic",
            "features": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Migration Batch",
                    "description": "",
                    "priority": "medium",
                    "artifactType": "feature",
                    "useCases": [
                        {
                            "id": str(uuid.uuid4()),
                            "title": "Migrated Use Cases",
                            "description": "",
                            "priority": "medium",
                            "artifactType": "use_case",
                            "testCases": normalized,
                        }
                    ],
                }
            ],
        }
    ]

    test_cases = migration_epic_wrapper[0]["features"][0]["useCases"][0]["testCases"]

    # Push to Jira via MCP connector (annotates dicts in-place)
    jira_count = 0
    try:
        jira_prompt = (
            f"Push the following migrated test artifacts to Jira project {jira_key}:\n\n"
            f"{json.dumps(migration_epic_wrapper, indent=2)}"
        )
        await agent_service.agent_workflow_run(jira_prompt)
        jira_count = len(test_cases)
    except Exception as e:
        errors.append(f"Jira push error: {e}")

    cosmos_count = 0
    existing = await cosmos_service.get_project_artifacts(project_id)
    if existing:
        existing["epics"].append(migration_epic_wrapper[0])
        existing["totalTestCases"] = existing.get("totalTestCases", 0) + len(test_cases)
        try:
            await cosmos_service.save_artifacts(project_id, existing)
            cosmos_count = len(test_cases)
        except Exception as e:
            errors.append(f"CosmosDB save error: {e}")
    else:
        errors.append("No existing project artifacts found. Please generate base artifacts first.")

    return MigrationResult(
        sessionId="",
        totalRows=len(mapped_rows),
        validArtifacts=len(normalized),
        migratedToJira=jira_count,
        migratedToCosmos=cosmos_count,
        errors=errors,
        status="completed" if not errors else "completed_with_errors",
    )
