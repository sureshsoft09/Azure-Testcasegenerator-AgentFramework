// ─── Shared Types ──────────────────────────────────────────────────────────────

export type Priority = 'high' | 'medium' | 'low';
export type ArtifactType = 'epic' | 'feature' | 'use_case' | 'test_case';

export interface Project {
  id: string;
  projectId: string;
  projectName: string;
  jiraProjectKey: string;
  notificationEmail: string;
  description?: string;
  createdAt: string;
  status: string;
}

export interface TestCase {
  id: string;
  title: string;
  description: string;
  preconditions?: string;
  steps: string[];
  expectedResult: string;
  priority: Priority;
  artifactType: ArtifactType;
  jiraIssueKey?: string;
  jiraIssueId?: string;
  jiraIssueUrl?: string;
  tags: string[];
  complianceMapping: string[];
}

export interface UseCase {
  id: string;
  title: string;
  description: string;
  actors: string[];
  preconditions?: string;
  mainFlow: string[];
  alternateFlows: string[];
  postconditions?: string;
  priority: Priority;
  artifactType: ArtifactType;
  jiraIssueKey?: string;
  jiraIssueId?: string;
  jiraIssueUrl?: string;
  testCases: TestCase[];
  complianceMapping: string[];
}

export interface Feature {
  id: string;
  title: string;
  description: string;
  priority: Priority;
  artifactType: ArtifactType;
  jiraIssueKey?: string;
  jiraIssueId?: string;
  jiraIssueUrl?: string;
  useCases: UseCase[];
}

export interface Epic {
  id: string;
  title: string;
  description: string;
  priority: Priority;
  artifactType: ArtifactType;
  jiraIssueKey?: string;
  jiraIssueId?: string;
  jiraIssueUrl?: string;
  features: Feature[];
}

export interface ProjectArtifacts {
  projectId: string;
  projectName: string;
  jiraProjectKey: string;
  epics: Epic[];
  totalEpics: number;
  totalFeatures: number;
  totalUseCases: number;
  totalTestCases: number;
}

export interface ChatMessage {
  role: 'user' | 'agent';
  content: string;
  timestamp: string;
}

export interface ReviewChatResponse {
  sessionId: string;
  messages: ChatMessage[];
  estimatedArtifacts?: { epics: number; features: number; useCases: number; testCases: number } | null;
  allClarified: boolean;
}

export interface GenerationResult {
  projectId: string;
  sessionId: string;
  epicsCreated: number;
  featuresCreated: number;
  useCasesCreated: number;
  testCasesCreated: number;
  jiraIssuesCreated: number;
  status: string;
}

export interface EnhanceChatResponse {
  sessionId: string;
  messages: ChatMessage[];
  updatedArtifact?: Record<string, unknown> | null;
  readyToApply: boolean;
}

export interface AnalyticsSummary {
  projectId: string;
  projectName: string;
  totalEpics: number;
  totalFeatures: number;
  totalUseCases: number;
  totalTestCases: number;
  priorityBreakdown: Record<string, number>;
  complianceMapping: Record<string, number>;
  jiraLinkedCount: number;
  jiraUnlinkedCount: number;
}

export interface MigrationResult {
  sessionId: string;
  totalRows: number;
  validArtifacts: number;
  migratedToJira: number;
  migratedToCosmos: number;
  errors: string[];
  status: string;
}
