import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ─── Dashboard ────────────────────────────────────────────────────────────────
export const dashboardApi = {
  getProjects: () => api.get('/dashboard/projects'),
  getArtifacts: (projectId: string) => api.get(`/dashboard/projects/${projectId}/artifacts`),
  exportExcel: (projectId: string) =>
    api.get(`/dashboard/projects/${projectId}/export/excel`, { responseType: 'blob' }),
  exportXml: (projectId: string) =>
    api.get(`/dashboard/projects/${projectId}/export/xml`, { responseType: 'blob' }),
};

// ─── Generate ─────────────────────────────────────────────────────────────────
export const generateApi = {
  createProject: (data: { projectName: string; jiraProjectKey: string; notificationEmail: string; description?: string }) =>
    api.post('/generate/projects', data),

  uploadFiles: (projectId: string, files: File[]) => {
    const form = new FormData();
    files.forEach(f => form.append('files', f));
    return api.post(`/generate/projects/${projectId}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  reviewRequirements: (projectId: string, sessionId: string) =>
    api.post(`/generate/projects/${projectId}/review`, { sessionId }),

  reviewChat: (projectId: string, sessionId: string, message: string) =>
    api.post(`/generate/projects/${projectId}/review/chat`, { projectId, sessionId, message }),

  generateTestCases: (projectId: string, sessionId: string) =>
    api.post(`/generate/projects/${projectId}/generate`, { projectId, sessionId }),
};

// ─── Enhance ──────────────────────────────────────────────────────────────────
export const enhanceApi = {
  chat: (data: { projectId: string; artifactId: string; artifactType: string; sessionId?: string; message: string }) =>
    api.post('/enhance/chat', data),
  applyEnhancement: (data: { projectId: string; artifactId: string; artifactType: string; sessionId: string; updatedArtifact: Record<string, unknown> }) =>
    api.post('/enhance/apply', data),
};

// ─── Migrate ──────────────────────────────────────────────────────────────────
export const migrateApi = {
  uploadFiles: (projectId: string, files: File[]) => {
    const form = new FormData();
    form.append('project_id', projectId);
    files.forEach(f => form.append('files', f));
    return api.post('/migrate/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  configureMappings: (data: { projectId: string; sessionId: string; mappings: { sourceColumn: string; targetField: string }[] }) =>
    api.post('/migrate/configure', data),
  getArtifacts: (sessionId: string) => api.get(`/migrate/sessions/${sessionId}/artifacts`),
  execute: (projectId: string, sessionId: string) =>
    api.post('/migrate/execute', { projectId, sessionId }),
  getResults: (sessionId: string) => api.get(`/migrate/sessions/${sessionId}/results`),
};

// ─── Analytics ────────────────────────────────────────────────────────────────
export const analyticsApi = {
  getSummary: (projectId: string) => api.get(`/analytics/projects/${projectId}/summary`),
};

export default api;
