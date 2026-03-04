import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { MdCloudUpload, MdUploadFile, MdArrowForward } from 'react-icons/md';
import toast from 'react-hot-toast';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi, migrateApi } from '../../api/client';
import { useAppStore } from '../../store/appStore';
import { Project, MigrationResult } from '../../types';
import Spinner from '../../components/Spinner';

const STEPS = ['Upload Files', 'Configure Mapping', 'Review & Validate', 'Execute Migration', 'Results'];

const TARGET_FIELDS = ['title', 'description', 'preconditions', 'steps', 'expectedResult', 'priority', 'tags', 'skip'];

function StepBar({ current }: { current: number }) {
  return (
    <div className="steps" style={{ flexWrap: 'wrap', gap: 4 }}>
      {STEPS.map((label, i) => {
        const num = i + 1;
        const done = current > num;
        const active = current === num;
        return (
          <div key={num} className="step-item" style={{ flex: 'unset' }}>
            <div className={`step-circle ${done ? 'done' : active ? 'active' : ''}`}>
              {done ? '✓' : num}
            </div>
            <span className={`step-label ${done ? 'done' : active ? 'active' : ''}`}>{label}</span>
            {i < STEPS.length - 1 && <div className={`step-line${done ? ' done' : ''}`} style={{ minWidth: 24 }} />}
          </div>
        );
      })}
    </div>
  );
}

// ─── Step 1: Upload ────────────────────────────────────────────────────────────
function Step1Upload({ onNext }: { onNext: (sessionId: string, columns: string[], projectId: string) => void }) {
  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: () => dashboardApi.getProjects().then((r: any) => r.data.projects as Project[]),
  });

  const [selectedProject, setSelectedProject] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'], 'application/vnd.ms-excel': ['.xls'] },
    onDrop: f => setFiles(prev => [...prev, ...f]),
  });

  const handleUpload = async () => {
    if (!selectedProject) { toast.error('Select a project'); return; }
    if (!files.length) { toast.error('Add at least one Excel file'); return; }
    setUploading(true);
    try {
      const res = await migrateApi.uploadFiles(selectedProject, files);
      toast.success(`Uploaded ${res.data.totalRows} rows`);
      onNext(res.data.sessionId, res.data.columns, selectedProject);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 620 }}>
      <h3 style={{ marginBottom: 20, fontSize: 16, fontWeight: 600 }}>Upload Test Case Files</h3>
      <div className="form-group" style={{ marginBottom: 16 }}>
        <label className="form-label">Target Project *</label>
        <select className="select" value={selectedProject} onChange={e => setSelectedProject(e.target.value)}>
          <option value="">— Select project —</option>
          {(projectsData ?? []).map((p: Project) => (
            <option key={p.projectId} value={p.projectId}>{p.projectName} ({p.jiraProjectKey})</option>
          ))}
        </select>
      </div>
      <div {...getRootProps()} className={`dropzone${isDragActive ? ' active' : ''}`} style={{ marginBottom: 16 }}>
        <input {...getInputProps()} />
        <div className="dropzone-icon"><MdCloudUpload /></div>
        <p style={{ fontWeight: 600 }}>Drag & drop Excel files (.xlsx)</p>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>or click to browse</p>
      </div>
      {files.map((f, i) => (
        <div key={i} className="flex items-center gap-2" style={{ padding: '5px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
          <MdUploadFile size={16} style={{ color: 'var(--accent)' }} />
          <span style={{ flex: 1 }}>{f.name}</span>
          <button className="btn btn-sm btn-danger" style={{ padding: '2px 6px' }}
            onClick={() => setFiles(prev => prev.filter((_, j) => j !== i))}>✕</button>
        </div>
      ))}
      <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={handleUpload} disabled={uploading}>
        {uploading ? <><Spinner size={15} /> Uploading…</> : <><MdArrowForward size={16} /> Upload & Continue</>}
      </button>
    </div>
  );
}

// ─── Step 2: Configure Mapping ─────────────────────────────────────────────────
function Step2Mapping({ sessionId, columns, projectId, onNext }: {
  sessionId: string; columns: string[]; projectId: string; onNext: () => void;
}) {
  const [mappings, setMappings] = useState<Record<string, string>>(
    Object.fromEntries(columns.map(c => [c, 'skip']))
  );
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    const mappingArr = Object.entries(mappings)
      .filter(([, v]) => v !== 'skip')
      .map(([sourceColumn, targetField]) => ({ sourceColumn, targetField }));
    setSaving(true);
    try {
      await migrateApi.configureMappings({ projectId, sessionId, mappings: mappingArr });
      toast.success('Mapping configured');
      onNext();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Mapping failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 680 }}>
      <h3 style={{ marginBottom: 16, fontSize: 16, fontWeight: 600 }}>Configure Column Mapping</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>
        Map your Excel columns to the target artifact fields.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {columns.map(col => (
          <div key={col} className="flex items-center gap-3">
            <span style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{col}</span>
            <span style={{ color: 'var(--text-muted)' }}>→</span>
            <select className="select" style={{ flex: 1 }}
              value={mappings[col] ?? 'skip'}
              onChange={e => setMappings(m => ({ ...m, [col]: e.target.value }))}>
              {TARGET_FIELDS.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
        ))}
      </div>
      <button className="btn btn-primary" style={{ marginTop: 20 }} onClick={handleSave} disabled={saving}>
        {saving ? <><Spinner size={15} /> Saving…</> : 'Save Mapping & Continue'}
      </button>
    </div>
  );
}

// ─── Step 3: Review & Validate ─────────────────────────────────────────────────
function Step3Review({ sessionId, onNext }: { sessionId: string; onNext: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ['migrate-artifacts', sessionId],
    queryFn: () => migrateApi.getArtifacts(sessionId).then((r: any) => r.data),
  });

  return (
    <div className="card">
      <h3 style={{ marginBottom: 16, fontSize: 16, fontWeight: 600 }}>Review Mapped Artifacts</h3>
      {isLoading && <div className="flex items-center gap-3"><Spinner /> Loading preview…</div>}
      {data && (
        <>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 14 }}>
            Found <strong>{data.totalRows}</strong> rows. Showing first 10 for review.
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Title</th>
                  <th>Description</th>
                  <th>Priority</th>
                  <th>Expected Result</th>
                </tr>
              </thead>
              <tbody>
                {(data.artifacts ?? []).slice(0, 10).map((row: any, i: number) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td>{row.title ?? '—'}</td>
                    <td style={{ maxWidth: 200 }} className="truncate">{row.description ?? '—'}</td>
                    <td>{row.priority ?? '—'}</td>
                    <td style={{ maxWidth: 180 }} className="truncate">{row.expectedResult ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={onNext}>
            Looks Good → Execute Migration
          </button>
        </>
      )}
    </div>
  );
}

// ─── Step 4: Execute ───────────────────────────────────────────────────────────
function Step4Execute({ sessionId, projectId, onNext }: { sessionId: string; projectId: string; onNext: (r: MigrationResult) => void }) {
  const [running, setRunning] = useState(false);

  const handleExecute = async () => {
    setRunning(true);
    try {
      const res = await migrateApi.execute(projectId, sessionId);
      toast.success('Migration completed!');
      onNext(res.data);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Migration failed');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 500, textAlign: 'center', padding: 40 }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>🚀</div>
      <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Ready to Migrate</h3>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
        The agent will normalize your test cases and push them to Jira and CosmosDB.
      </p>
      <button className="btn btn-primary btn-lg" onClick={handleExecute} disabled={running} style={{ width: '100%', justifyContent: 'center' }}>
        {running ? <><Spinner size={16} /> Migrating… This may take a moment</> : '⚡ Execute Migration'}
      </button>
    </div>
  );
}

// ─── Step 5: Results ──────────────────────────────────────────────────────────
function Step5Results({ result }: { result: MigrationResult }) {
  return (
    <div className="card" style={{ maxWidth: 600 }}>
      <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Migration Results</h3>
      <div className="grid-2" style={{ marginBottom: 16 }}>
        {[
          { label: 'Total Rows', value: result.totalRows },
          { label: 'Valid Artifacts', value: result.validArtifacts },
          { label: 'Migrated to Jira', value: result.migratedToJira },
          { label: 'Saved to CosmosDB', value: result.migratedToCosmos },
        ].map(s => (
          <div key={s.label} className="card stat-card" style={{ padding: 14 }}>
            <div className="stat-value" style={{ fontSize: 22 }}>{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>
      <div className={`badge ${result.status === 'completed' ? 'badge-accent' : 'badge-medium'}`} style={{ marginBottom: 12 }}>
        Status: {result.status}
      </div>
      {result.errors.length > 0 && (
        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: 12, fontSize: 12 }}>
          <div style={{ fontWeight: 600, color: '#ef4444', marginBottom: 6 }}>Errors ({result.errors.length})</div>
          {result.errors.map((e, i) => <p key={i} style={{ color: 'var(--text-secondary)' }}>• {e}</p>)}
        </div>
      )}
      <a href="/dashboard" className="btn btn-primary" style={{ marginTop: 16, display: 'inline-flex' }}>
        View in Dashboard →
      </a>
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
export default function MigratePage() {
  const { migrateStep, setMigrateStep, migrateSessionId, setMigrateSessionId,
    migrateProjectId, setMigrateProjectId, migrateColumns, setMigrateColumns } = useAppStore();
  const [result, setResult] = useState<MigrationResult | null>(null);

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="page-title">Migrate Test Cases</div>
          <div className="page-subtitle">Import existing test cases from Excel files</div>
        </div>
      </div>

      <StepBar current={migrateStep} />

      {migrateStep === 1 && (
        <Step1Upload onNext={(sid, cols, pid) => {
          setMigrateSessionId(sid);
          setMigrateColumns(cols);
          setMigrateProjectId(pid);
          setMigrateStep(2);
        }} />
      )}
      {migrateStep === 2 && migrateSessionId && migrateProjectId && (
        <Step2Mapping sessionId={migrateSessionId} columns={migrateColumns} projectId={migrateProjectId}
          onNext={() => setMigrateStep(3)} />
      )}
      {migrateStep === 3 && migrateSessionId && (
        <Step3Review sessionId={migrateSessionId} onNext={() => setMigrateStep(4)} />
      )}
      {migrateStep === 4 && migrateSessionId && migrateProjectId && (
        <Step4Execute sessionId={migrateSessionId} projectId={migrateProjectId}
          onNext={(r) => { setResult(r); setMigrateStep(5); }} />
      )}
      {migrateStep === 5 && result && <Step5Results result={result} />}

      {migrateStep > 1 && migrateStep < 5 && (
        <button className="btn btn-secondary btn-sm" style={{ width: 'fit-content' }}
          onClick={() => setMigrateStep(migrateStep - 1)}>← Back</button>
      )}
    </div>
  );
}
