import { useQuery } from '@tanstack/react-query';
import { MdFileDownload, MdRefresh, MdCode, MdAutoAwesome, MdRateReview, MdSync, MdTune } from 'react-icons/md';
import toast from 'react-hot-toast';
import { dashboardApi } from '../../api/client';
import { useAppStore } from '../../store/appStore';
import { Project, ProjectArtifacts } from '../../types';
import ArtifactTree from '../../components/ArtifactTree';
import Spinner from '../../components/Spinner';

// ─── Client-side XML export ────────────────────────────────────────────────────
function esc(val: any): string {
  return String(val ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function exportArtifactsToXml(raw: any) {
  const jiraKey = raw.jiraProjectKey ?? raw.jira_project_key ?? '';
  const fileName = `${String(raw.projectName ?? 'artifacts').replace(/\s+/g, '_')}_artifacts`;

  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<project>\n';
  xml += `  <project_id>${esc(raw.projectId)}</project_id>\n`;
  xml += `  <name>${esc(raw.projectName)}</name>\n`;
  xml += `  <jira_project_key>${esc(jiraKey)}</jira_project_key>\n`;
  xml += `  <statistics>\n`;
  xml += `    <total_epics>${raw.totalEpics ?? 0}</total_epics>\n`;
  xml += `    <total_features>${raw.totalFeatures ?? 0}</total_features>\n`;
  xml += `    <total_use_cases>${raw.totalUseCases ?? 0}</total_use_cases>\n`;
  xml += `    <total_test_cases>${raw.totalTestCases ?? 0}</total_test_cases>\n`;
  xml += `  </statistics>\n`;
  xml += `  <epics>\n`;

  (raw.epics ?? []).forEach((epic: any) => {
    xml += `    <epic>\n`;
    xml += `      <epic_id>${esc(epic.epic_id)}</epic_id>\n`;
    xml += `      <title>${esc(epic.epic_name ?? epic.title)}</title>\n`;
    xml += `      <description>${esc(epic.description)}</description>\n`;
    xml += `      <priority>${esc(epic.priority ?? 'Medium')}</priority>\n`;
    xml += `      <jira_issue_key>${esc(epic.jira_issue_key)}</jira_issue_key>\n`;
    xml += `      <jira_project_key>${esc(jiraKey)}</jira_project_key>\n`;
    xml += `      <features>\n`;

    (epic.features ?? []).forEach((feat: any) => {
      xml += `        <feature>\n`;
      xml += `          <feature_id>${esc(feat.feature_id)}</feature_id>\n`;
      xml += `          <title>${esc(feat.feature_name ?? feat.title)}</title>\n`;
      xml += `          <description>${esc(feat.description)}</description>\n`;
      xml += `          <priority>${esc(feat.priority ?? epic.priority ?? 'Medium')}</priority>\n`;
      xml += `          <jira_issue_key>${esc(feat.jira_issue_key)}</jira_issue_key>\n`;
      xml += `          <jira_project_key>${esc(jiraKey)}</jira_project_key>\n`;
      xml += `          <use_cases>\n`;

      const useCases: any[] = feat.use_cases ?? feat.useCases ?? [];
      useCases.forEach((uc: any) => {
        xml += `            <use_case>\n`;
        xml += `              <use_case_id>${esc(uc.use_case_id)}</use_case_id>\n`;
        xml += `              <title>${esc(uc.use_case_title ?? uc.title)}</title>\n`;
        xml += `              <description>${esc(uc.description)}</description>\n`;
        xml += `              <priority>${esc(uc.priority ?? feat.priority ?? epic.priority ?? 'Medium')}</priority>\n`;
        xml += `              <jira_issue_key>${esc(uc.jira_issue_key)}</jira_issue_key>\n`;
        xml += `              <jira_project_key>${esc(jiraKey)}</jira_project_key>\n`;
        xml += `              <review_status>${esc(uc.review_status)}</review_status>\n`;
        if (uc.model_explanation) xml += `              <model_explanation>${esc(uc.model_explanation)}</model_explanation>\n`;
        xml += `              <test_cases>\n`;

        const testCases: any[] = uc.test_cases ?? uc.testCases ?? [];
        testCases.forEach((tc: any) => {
          xml += `                <test_case>\n`;
          xml += `                  <test_case_id>${esc(tc.test_case_id)}</test_case_id>\n`;
          xml += `                  <title>${esc(tc.test_case_title ?? tc.title)}</title>\n`;
          xml += `                  <priority>${esc(tc.priority ?? 'Medium')}</priority>\n`;
          xml += `                  <test_type>${esc(tc.test_type ?? 'Functional')}</test_type>\n`;
          xml += `                  <review_status>${esc(tc.review_status ?? 'Pending')}</review_status>\n`;
          xml += `                  <jira_issue_key>${esc(tc.jira_issue_key)}</jira_issue_key>\n`;
          xml += `                  <jira_project_key>${esc(jiraKey)}</jira_project_key>\n`;

          if (tc.preconditions?.length) {
            xml += `                  <preconditions>\n`;
            (Array.isArray(tc.preconditions) ? tc.preconditions : [tc.preconditions])
              .forEach((p: string) => { xml += `                    <precondition>${esc(p)}</precondition>\n`; });
            xml += `                  </preconditions>\n`;
          }
          if (tc.test_steps?.length) {
            xml += `                  <test_steps>\n`;
            (Array.isArray(tc.test_steps) ? tc.test_steps : [tc.test_steps])
              .forEach((s: string, i: number) => { xml += `                    <step step_number="${i + 1}">${esc(s)}</step>\n`; });
            xml += `                  </test_steps>\n`;
          }
          if (tc.expected_result) xml += `                  <expected_result>${esc(tc.expected_result)}</expected_result>\n`;
          if (tc.model_explanation) xml += `                  <model_explanation>${esc(tc.model_explanation)}</model_explanation>\n`;
          if (tc.comments) xml += `                  <comments>${esc(tc.comments)}</comments>\n`;
          if (tc.compliance_mapping?.length) {
            xml += `                  <compliance_mapping>\n`;
            (Array.isArray(tc.compliance_mapping) ? tc.compliance_mapping : [tc.compliance_mapping])
              .forEach((c: string) => { xml += `                    <compliance>${esc(c)}</compliance>\n`; });
            xml += `                  </compliance_mapping>\n`;
          }
          xml += `                </test_case>\n`;
        });

        xml += `              </test_cases>\n`;
        xml += `            </use_case>\n`;
      });

      xml += `          </use_cases>\n`;
      xml += `        </feature>\n`;
    });

    xml += `      </features>\n`;
    xml += `    </epic>\n`;
  });

  xml += `  </epics>\n</project>`;

  const blob = new Blob([xml], { type: 'application/xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${fileName}.xml`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function DashboardPage() {
  const { selectedProjectId, setSelectedProjectId } = useAppStore();

  // Load projects
  const { data: projectsData, isLoading: loadingProjects, refetch } = useQuery({
    queryKey: ['projects'],
    queryFn: () => dashboardApi.getProjects().then(r => r.data.projects as Project[]),
  });

  // Load artifacts for selected project
  const { data: artifacts, isLoading: loadingArtifacts } = useQuery<ProjectArtifacts>({
    queryKey: ['artifacts', selectedProjectId],
    queryFn: () => dashboardApi.getArtifacts(selectedProjectId!).then(r => r.data),
    enabled: !!selectedProjectId,
  });

  const handleExport = async (type: 'excel' | 'xml') => {
    if (!selectedProjectId) return;
    if (type === 'xml') {
      if (!artifacts) { toast.error('No artifacts loaded'); return; }
      exportArtifactsToXml(artifacts);
      toast.success('Exported as XML');
      return;
    }
    try {
      const res = await dashboardApi.exportExcel(selectedProjectId);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'artifacts.xlsx';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Exported as EXCEL');
    } catch {
      toast.error('Export failed');
    }
  };

  const projects = projectsData ?? [];

  return (
    <div className="page-container">

      {/* ── Hero / Solution Description ─────────────────────────── */}
      <div className="hero-banner">
        <div className="hero-content">
          <div className="hero-eyebrow">Powered by Azure AI Foundry · Multi-Agent Framework</div>
          <h1 className="hero-title">AI-Powered Test Case Generation</h1>
          <p className="hero-desc">
            Upload business requirements, let AI agents analyse, review, and generate structured
            test artifacts — then sync everything directly to Jira. From epics to test cases in minutes.
          </p>
          <div className="hero-features">
            {[
              { icon: <MdAutoAwesome size={18} />, label: 'Auto-Generate', desc: 'AI produces epics, features, use-cases & test cases' },
              { icon: <MdRateReview   size={18} />, label: 'AI Review',     desc: 'Requirement reviewer flags gaps before generation' },
              { icon: <MdTune         size={18} />, label: 'Smart Enhance', desc: 'Refine & improve existing test artifacts with AI' },
              { icon: <MdSync         size={18} />, label: 'Jira Sync',     desc: 'Push generated artifacts straight to your board' },
            ].map(f => (
              <div key={f.label} className="hero-feature-card">
                <div className="hero-feature-icon">{f.icon}</div>
                <div>
                  <div className="hero-feature-label">{f.label}</div>
                  <div className="hero-feature-desc">{f.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="hero-glow" />
      </div>

      {/* Header */}
      <div className="page-header">
        <div>
          <div className="page-title">Dashboard</div>
          <div className="page-subtitle">View and export test artifacts by project</div>
        </div>
        <button className="btn btn-secondary" onClick={() => refetch()}>
          <MdRefresh size={16} /> Refresh
        </button>
      </div>

      {/* Project selector + stats */}
      <div className="card">
        <div className="flex items-center gap-4" style={{ flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: 1, minWidth: 240 }}>
            <label className="form-label">Select Project</label>
            {loadingProjects ? <Spinner /> : (
              <select
                className="select"
                value={selectedProjectId ?? ''}
                onChange={e => setSelectedProjectId(e.target.value || null)}
              >
                <option value="">— Choose a project —</option>
                {projects.map(p => (
                  <option key={p.projectId} value={p.projectId}>
                    {p.projectName} ({p.jiraProjectKey})
                  </option>
                ))}
              </select>
            )}
          </div>

          {artifacts && (
            <div className="grid-4" style={{ flex: 2 }}>
              {[
                { label: 'Epics', value: artifacts.totalEpics, color: '#818cf8' },
                { label: 'Features', value: artifacts.totalFeatures, color: '#6366f1' },
                { label: 'Use Cases', value: artifacts.totalUseCases, color: '#22c55e' },
                { label: 'Test Cases', value: artifacts.totalTestCases, color: '#f59e0b' },
              ].map(s => (
                <div key={s.label} className="card stat-card" style={{ padding: 14 }}>
                  <div className="stat-value" style={{ color: s.color, fontSize: 22 }}>{s.value}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              ))}
            </div>
          )}

          {selectedProjectId && (
            <div className="flex gap-2">
              <button className="btn btn-secondary btn-sm" onClick={() => handleExport('excel')}>
                <MdFileDownload size={15} /> Excel
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => handleExport('xml')}>
                <MdCode size={15} /> XML
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Artifact tree */}
      <div className="card" style={{ minHeight: 400 }}>
        {!selectedProjectId && (
          <div className="empty-state">
            <div className="empty-state-icon">📂</div>
            <div className="empty-state-title">Select a project to view artifacts</div>
          </div>
        )}
        {loadingArtifacts && <div className="flex items-center gap-3" style={{ padding: 30 }}><Spinner /> Loading artifacts…</div>}
        {artifacts && !loadingArtifacts && (
          <>
            <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: 15 }}>{artifacts.projectName}</span>
                <span className="badge badge-accent" style={{ marginLeft: 10 }}>{artifacts.jiraProjectKey}</span>
              </div>
            </div>
            <ArtifactTree epics={artifacts.epics} />
          </>
        )}
      </div>
    </div>
  );
}
