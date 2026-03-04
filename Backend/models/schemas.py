from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
import uuid


class ArtifactType(str, Enum):
    EPIC = "epic"
    FEATURE = "feature"
    USE_CASE = "use_case"
    TEST_CASE = "test_case"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ArtifactStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


# ─── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    projectName: str
    jiraProjectKey: str
    notificationEmail: str
    description: Optional[str] = ""


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    projectId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    projectName: str
    jiraProjectKey: str
    notificationEmail: str
    description: Optional[str] = ""
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "active"


# ─── Artifacts ─────────────────────────────────────────────────────────────────

class TestCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    preconditions: Optional[str] = ""
    steps: List[str] = []
    expectedResult: str = ""
    priority: Priority = Priority.MEDIUM
    artifactType: ArtifactType = ArtifactType.TEST_CASE
    jiraIssueKey: Optional[str] = None
    jiraIssueId: Optional[str] = None
    jiraIssueUrl: Optional[str] = None
    tags: List[str] = []
    complianceMapping: List[str] = []


class UseCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    actors: List[str] = []
    preconditions: Optional[str] = ""
    mainFlow: List[str] = []
    alternateFlows: List[str] = []
    postconditions: Optional[str] = ""
    priority: Priority = Priority.MEDIUM
    artifactType: ArtifactType = ArtifactType.USE_CASE
    jiraIssueKey: Optional[str] = None
    jiraIssueId: Optional[str] = None
    jiraIssueUrl: Optional[str] = None
    testCases: List[TestCase] = []
    complianceMapping: List[str] = []


class Feature(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    priority: Priority = Priority.MEDIUM
    artifactType: ArtifactType = ArtifactType.FEATURE
    jiraIssueKey: Optional[str] = None
    jiraIssueId: Optional[str] = None
    jiraIssueUrl: Optional[str] = None
    useCases: List[UseCase] = []


class Epic(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    priority: Priority = Priority.MEDIUM
    artifactType: ArtifactType = ArtifactType.EPIC
    jiraIssueKey: Optional[str] = None
    jiraIssueId: Optional[str] = None
    jiraIssueUrl: Optional[str] = None
    features: List[Feature] = []


class ProjectArtifacts(BaseModel):
    projectId: str
    projectName: str
    jiraProjectKey: str
    epics: List[Epic] = []
    totalEpics: int = 0
    totalFeatures: int = 0
    totalUseCases: int = 0
    totalTestCases: int = 0


# ─── Generate ──────────────────────────────────────────────────────────────────

class ReviewRequirementsRequest(BaseModel):
    projectId: str
    sessionId: str
    filePaths: List[str]


class ChatMessage(BaseModel):
    role: str  # "user" | "agent"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ReviewChatRequest(BaseModel):
    projectId: str
    sessionId: str
    message: str


class ReviewChatResponse(BaseModel):
    sessionId: str
    messages: List[ChatMessage]
    estimatedArtifacts: Optional[Dict[str, int]] = None
    allClarified: bool = False


class GenerateTestCasesRequest(BaseModel):
    projectId: str
    sessionId: str


class GenerationResult(BaseModel):
    projectId: str
    sessionId: str
    epicsCreated: int
    featuresCreated: int
    useCasesCreated: int
    testCasesCreated: int
    jiraIssuesCreated: int
    status: str


class AgentWorkflowRequest(BaseModel):
    userRequest: str


class AgentWorkflowResponse(BaseModel):
    messages: List[str]
    status: str = "success"


# ─── Enhance ───────────────────────────────────────────────────────────────────

class EnhanceChatRequest(BaseModel):
    projectId: str
    artifactId: str
    artifactType: ArtifactType
    sessionId: Optional[str] = None
    message: str


class EnhanceChatResponse(BaseModel):
    sessionId: str
    messages: List[ChatMessage]
    updatedArtifact: Optional[Dict[str, Any]] = None
    readyToApply: bool = False


class ApplyEnhancementRequest(BaseModel):
    projectId: str
    artifactId: str
    artifactType: ArtifactType
    sessionId: str
    updatedArtifact: Dict[str, Any]


# ─── Migrate ───────────────────────────────────────────────────────────────────

class MigrationMapping(BaseModel):
    sourceColumn: str
    targetField: str


class MigrationConfig(BaseModel):
    projectId: str
    sessionId: str
    mappings: List[MigrationMapping]


class MigrationArtifact(BaseModel):
    title: str
    description: str
    steps: Optional[List[str]] = []
    expectedResult: Optional[str] = ""
    priority: Optional[str] = "medium"
    rawData: Optional[Dict[str, Any]] = {}


class MigrationResult(BaseModel):
    sessionId: str
    totalRows: int
    validArtifacts: int
    migratedToJira: int
    migratedToCosmos: int
    errors: List[str] = []
    status: str


# ─── Analytics ─────────────────────────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    projectId: str
    projectName: str
    totalEpics: int
    totalFeatures: int
    totalUseCases: int
    totalTestCases: int
    priorityBreakdown: Dict[str, int]
    complianceMapping: Dict[str, int]
    jiraLinkedCount: int
    jiraUnlinkedCount: int
    recentActivity: List[Dict[str, Any]] = []
