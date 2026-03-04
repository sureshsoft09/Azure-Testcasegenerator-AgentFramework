from fastapi import APIRouter, HTTPException
from services.cosmos_service import cosmos_service
from models.schemas import AnalyticsSummary

router = APIRouter()


@router.get("/projects/{project_id}/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(project_id: str):
    artifacts = await cosmos_service.get_project_artifacts(project_id)
    if not artifacts:
        raise HTTPException(status_code=404, detail="Project artifacts not found")

    project = await cosmos_service.get_project_by_id(project_id)
    project_name = project.get("projectName", "") if project else ""

    priority_breakdown = {"high": 0, "medium": 0, "low": 0}
    compliance_mapping: dict = {}
    jira_linked = 0
    jira_unlinked = 0
    recent_activity = []

    def process_tc(tc: dict):
        p = tc.get("priority", "medium").lower()
        priority_breakdown[p] = priority_breakdown.get(p, 0) + 1
        for c in tc.get("complianceMapping", []):
            compliance_mapping[c] = compliance_mapping.get(c, 0) + 1
        if tc.get("jiraIssueKey"):
            nonlocal jira_linked
            jira_linked += 1
        else:
            nonlocal jira_unlinked
            jira_unlinked += 1

    for epic in artifacts.get("epics", []):
        for feature in epic.get("features", []):
            for uc in feature.get("useCases", []):
                for tc in uc.get("testCases", []):
                    process_tc(tc)

    return AnalyticsSummary(
        projectId=project_id,
        projectName=project_name,
        totalEpics=artifacts.get("totalEpics", 0),
        totalFeatures=artifacts.get("totalFeatures", 0),
        totalUseCases=artifacts.get("totalUseCases", 0),
        totalTestCases=artifacts.get("totalTestCases", 0),
        priorityBreakdown=priority_breakdown,
        complianceMapping=compliance_mapping,
        jiraLinkedCount=jira_linked,
        jiraUnlinkedCount=jira_unlinked,
        recentActivity=recent_activity,
    )
