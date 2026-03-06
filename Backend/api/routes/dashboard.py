from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from services.cosmos_service import cosmos_service
from services.export_service import export_to_excel, export_to_xml
import io

router = APIRouter()


@router.get("/projects")
async def get_all_projects():
    """Get all projects from CosmosDB."""
    try:
        projects = await cosmos_service.get_all_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/artifacts")
async def get_project_artifacts_hierarchy(project_id: str):
    """Get full artifact hierarchy for a project."""
    try:
        artifacts = await cosmos_service.get_project_artifacts(project_id)
        if not artifacts:
            # Return an empty structure rather than 404 so the frontend
            # renders cleanly for projects that haven't been generated yet.
            return {
                "projectId": project_id,
                "projectName": "",
                "jiraProjectKey": "",
                "epics": [],
                "totalEpics": 0,
                "totalFeatures": 0,
                "totalUseCases": 0,
                "totalTestCases": 0,
            }
        return artifacts
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/export/excel")
async def export_project_excel(project_id: str):
    """Export project artifacts to Excel."""
    try:
        artifacts = await cosmos_service.get_project_artifacts(project_id)
        if not artifacts:
            raise HTTPException(status_code=404, detail="Project artifacts not found")
        excel_bytes = export_to_excel(artifacts)
        filename = f"{artifacts.get('projectName', project_id)}_artifacts.xlsx"
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/export/xml")
async def export_project_xml(project_id: str):
    """Export project artifacts to XML."""
    try:
        artifacts = await cosmos_service.get_project_artifacts(project_id)
        if not artifacts:
            raise HTTPException(status_code=404, detail="Project artifacts not found")
        xml_bytes = export_to_xml(artifacts)
        filename = f"{artifacts.get('projectName', project_id)}_artifacts.xml"
        return StreamingResponse(
            io.BytesIO(xml_bytes),
            media_type="application/xml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
