import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { MdUploadFile, MdCheckCircle, MdCloudUpload } from 'react-icons/md';
import toast from 'react-hot-toast';
import { generateApi } from '../../api/client';
import { useAppStore } from '../../store/appStore';
import Spinner from '../../components/Spinner';
import ChatPanel from '../../components/ChatPanel';
import ArtifactTree from '../../components/ArtifactTree';
import { ChatMessage, GenerationResult } from '../../types';

// ─── Step indicators ───────────────────────────────────────────────────────────
const STEPS = ['Create Project', 'Upload Requirements', 'Review & Chat', 'Generated Artifacts'];

function StepBar({ current }: { current: number }) {
  return (
    <div className="steps">
      {STEPS.map((label, i) => {
        const num = i + 1;
        const done = current > num;
        const active = current === num;
        return (
          <div key={num} className="step-item">
            <div className={`step-circle ${done ? 'done' : active ? 'active' : ''}`}>
              {done ? '✓' : num}
            </div>
            <span className={`step-label ${done ? 'done' : active ? 'active' : ''}`}>{label}</span>
            {i < STEPS.length - 1 && <div className={`step-line${done ? ' done' : ''}`} />}
          </div>
        );
      })}
    </div>
  );
}

// ─── Step 1: Create Project ────────────────────────────────────────────────────
function Step1CreateProject({ onNext }: { onNext: (projectId: string) => void }) {
  const [form, setForm] = useState({ projectName: '', jiraProjectKey: '', notificationEmail: '', description: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.projectName || !form.jiraProjectKey || !form.notificationEmail) {
      toast.error('Please fill all required fields');
      return;
    }
    setLoading(true);
    try {
      const res = await generateApi.createProject(form);
      toast.success('Project created!');
      onNext(res.data.projectId);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 560 }}>
      <h3 style={{ marginBottom: 20, fontSize: 16, fontWeight: 600 }}>Create New Project</h3>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="form-group">
          <label className="form-label">Project Name *</label>
          <input className="input" placeholder="e.g. E-Commerce Platform" value={form.projectName}
            onChange={e => setForm(f => ({ ...f, projectName: e.target.value }))} />
        </div>
        <div className="form-group">
          <label className="form-label">Jira Project Key *</label>
          <input className="input" placeholder="e.g. ECP" value={form.jiraProjectKey}
            onChange={e => setForm(f => ({ ...f, jiraProjectKey: e.target.value.toUpperCase() }))} />
        </div>
        <div className="form-group">
          <label className="form-label">Notification Email *</label>
          <input className="input" type="email" placeholder="you@example.com" value={form.notificationEmail}
            onChange={e => setForm(f => ({ ...f, notificationEmail: e.target.value }))} />
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea className="textarea" placeholder="Brief project description…" value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
        </div>
        <button className="btn btn-primary btn-lg" type="submit" disabled={loading}>
          {loading ? <><Spinner size={16} /> Creating…</> : 'Create Project & Continue'}
        </button>
      </form>
    </div>
  );
}

// ─── Step 2: Upload Requirements ───────────────────────────────────────────────
function Step2Upload({ projectId, onNext }: { projectId: string; onNext: (sessionId: string) => void }) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    onDrop: accepted => setFiles(prev => [...prev, ...accepted]),
  });

  const handleUpload = async () => {
    if (!files.length) { toast.error('Add at least one file'); return; }
    setUploading(true);
    try {
      const res = await generateApi.uploadFiles(projectId, files);
      setSessionId(res.data.sessionId);
      toast.success(`${files.length} file(s) uploaded`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleReview = async () => {
    // If files haven't been uploaded yet, upload them first
    if (!sessionId) {
      if (!files.length) {
        toast.error('Add at least one file');
        return;
      }
      setUploading(true);
      try {
        const res = await generateApi.uploadFiles(projectId, files);
        const newSessionId = res.data.sessionId;
        setSessionId(newSessionId);
        toast.success(`${files.length} file(s) uploaded`);
        
        // Now start the review
        setReviewing(true);
        await generateApi.reviewRequirements(projectId, newSessionId);
        toast.success('Review started');
        onNext(newSessionId);
      } catch (err: any) {
        toast.error(err?.response?.data?.detail ?? 'Upload or review failed');
      } finally {
        setUploading(false);
        setReviewing(false);
      }
      return;
    }
    
    // If already uploaded, just start review
    setReviewing(true);
    try {
      await generateApi.reviewRequirements(projectId, sessionId);
      toast.success('Review started');
      onNext(sessionId);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Review failed');
    } finally {
      setReviewing(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 680 }}>
      <h3 style={{ marginBottom: 20, fontSize: 16, fontWeight: 600 }}>Upload Requirement Documents</h3>

      <div {...getRootProps()} className={`dropzone${isDragActive ? ' active' : ''}`} style={{ marginBottom: 16 }}>
        <input {...getInputProps()} />
        <div className="dropzone-icon"><MdCloudUpload /></div>
        <p style={{ fontWeight: 600 }}>Drag & drop PDF or DOCX files here</p>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>or click to browse</p>
      </div>

      {files.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {files.map((f, i) => (
            <div key={i} className="flex items-center gap-2" style={{ padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
              <MdUploadFile size={16} style={{ color: 'var(--accent)' }} />
              <span style={{ flex: 1 }}>{f.name}</span>
              <span style={{ color: 'var(--text-muted)' }}>{(f.size / 1024).toFixed(1)} KB</span>
              <button className="btn btn-sm btn-danger" style={{ padding: '2px 6px' }}
                onClick={() => setFiles(prev => prev.filter((_, j) => j !== i))}>✕</button>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-3">
        <button className="btn btn-primary" onClick={handleUpload} disabled={uploading || !files.length || sessionId !== null}>
          {uploading ? <><Spinner size={15} /> Uploading…</> : <><MdUploadFile size={16} /> Upload Files</>}
        </button>
        <button className="btn btn-success" onClick={handleReview} disabled={!files.length || uploading || reviewing}>
          {(uploading || reviewing) ? <><Spinner size={15} /> {uploading ? 'Uploading & ' : ''}Starting Review…</> : <><MdCheckCircle size={16} /> Review Documents</>}
        </button>
      </div>
      {sessionId && <p style={{ marginTop: 10, fontSize: 12, color: 'var(--success)' }}>✓ Files uploaded. Click Review Documents to proceed.</p>}
    </div>
  );
}

// ─── Step 3: Review & Chat ─────────────────────────────────────────────────────
function Step3ReviewChat({ projectId, sessionId, onNext }: { projectId: string; sessionId: string; onNext: (result: GenerationResult) => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [allClarified, setAllClarified] = useState(false);
  const [estimated, setEstimated] = useState<{ epics: number; features: number; useCases: number; testCases: number } | null>(null);

  const handleSend = async (text: string) => {
    const userMsg: ChatMessage = { role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await generateApi.reviewChat(projectId, sessionId, text);
      const { messages: msgs, allClarified: done, estimatedArtifacts } = res.data;
      setMessages(msgs);
      setAllClarified(done);
      if (estimatedArtifacts) setEstimated(estimatedArtifacts);
    } catch {
      toast.error('Chat error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await generateApi.generateTestCases(projectId, sessionId);
      toast.success('Test cases generated!');
      onNext(res.data);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 20 }}>
      <div className="card" style={{ padding: 0, height: 560, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', fontWeight: 600 }}>
          🤖 Requirement Review Chat
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <ChatPanel
            messages={messages}
            onSend={handleSend}
            loading={loading}
            placeholder="Answer the agent's questions…"
            extraActions={
              allClarified ? (
                <button className="btn btn-success" onClick={handleGenerate} disabled={generating}>
                  {generating ? <><Spinner size={15} /> Generating…</> : '⚡ Generate Test Cases'}
                </button>
              ) : undefined
            }
          />
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="card">
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Session Info</div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', wordBreak: 'break-all' }}>Session: {sessionId}</p>
          {allClarified && <p style={{ marginTop: 8, color: 'var(--success)', fontSize: 12, fontWeight: 600 }}>✓ All clarifications complete</p>}
        </div>

        {estimated && (
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 10 }}>Estimated Artifacts</div>
            {Object.entries(estimated).map(([k, v]) => (
              <div key={k} className="flex justify-between" style={{ padding: '5px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{k}</span>
                <span style={{ fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Step 4: Generated Artifacts ──────────────────────────────────────────────
function Step4Results({ result }: { result: GenerationResult }) {
  return (
    <div className="card" style={{ maxWidth: 600 }}>
      <div style={{ textAlign: 'center', padding: '20px 0' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>🎉</div>
        <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>Test Cases Generated!</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
          All artifacts have been pushed to Jira and saved in CosmosDB.
        </p>
      </div>
      <div className="grid-2" style={{ marginBottom: 20 }}>
        {[
          { label: 'Epics', value: result.epicsCreated, color: '#818cf8' },
          { label: 'Features', value: result.featuresCreated, color: '#6366f1' },
          { label: 'Use Cases', value: result.useCasesCreated, color: '#22c55e' },
          { label: 'Test Cases', value: result.testCasesCreated, color: '#f59e0b' },
          { label: 'Jira Issues', value: result.jiraIssuesCreated, color: '#3b82f6' },
        ].map(s => (
          <div key={s.label} className="card stat-card" style={{ padding: 14 }}>
            <div className="stat-value" style={{ color: s.color, fontSize: 22 }}>{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>
      <a href="/dashboard" className="btn btn-primary w-full" style={{ justifyContent: 'center' }}>
        View in Dashboard →
      </a>
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
export default function GeneratePage() {
  const { generateStep, setGenerateStep, generateProjectId, setGenerateProjectId, generateSessionId, setGenerateSessionId } = useAppStore();
  const [result, setResult] = useState<GenerationResult | null>(null);

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="page-title">Generate Test Cases</div>
          <div className="page-subtitle">AI-powered test artifact generation from requirement documents</div>
        </div>
      </div>

      <StepBar current={generateStep} />

      {generateStep === 1 && (
        <Step1CreateProject onNext={(id) => { setGenerateProjectId(id); setGenerateStep(2); }} />
      )}
      {generateStep === 2 && generateProjectId && (
        <Step2Upload projectId={generateProjectId} onNext={(sid) => { setGenerateSessionId(sid); setGenerateStep(3); }} />
      )}
      {generateStep === 3 && generateProjectId && generateSessionId && (
        <Step3ReviewChat
          projectId={generateProjectId}
          sessionId={generateSessionId}
          onNext={(res) => { setResult(res); setGenerateStep(4); }}
        />
      )}
      {generateStep === 4 && result && <Step4Results result={result} />}

      {generateStep > 1 && generateStep < 4 && (
        <button className="btn btn-secondary btn-sm" style={{ width: 'fit-content' }}
          onClick={() => setGenerateStep(generateStep - 1)}>
          ← Back
        </button>
      )}
    </div>
  );
}
