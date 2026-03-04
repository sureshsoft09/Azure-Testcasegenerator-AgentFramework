import { useQuery } from '@tanstack/react-query';
import { MdFileDownload, MdRefresh, MdCode, MdAutoAwesome, MdRateReview, MdSync, MdTune } from 'react-icons/md';
import toast from 'react-hot-toast';
import { dashboardApi } from '../../api/client';
import { useAppStore } from '../../store/appStore';
import { Project, ProjectArtifacts } from '../../types';
import ArtifactTree from '../../components/ArtifactTree';
import Spinner from '../../components/Spinner';

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
    try {
      const res = type === 'excel'
        ? await dashboardApi.exportExcel(selectedProjectId)
        : await dashboardApi.exportXml(selectedProjectId);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `artifacts.${type === 'excel' ? 'xlsx' : 'xml'}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Exported as ${type.toUpperCase()}`);
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
