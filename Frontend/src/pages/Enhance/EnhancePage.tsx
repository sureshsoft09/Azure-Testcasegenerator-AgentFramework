import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MdClose, MdCheckCircle } from 'react-icons/md';
import toast from 'react-hot-toast';
import { dashboardApi, enhanceApi } from '../../api/client';
import { Project, ProjectArtifacts, UseCase, TestCase, ChatMessage, ArtifactType } from '../../types';
import ArtifactTree from '../../components/ArtifactTree';
import ChatPanel from '../../components/ChatPanel';
import Spinner from '../../components/Spinner';

// ─── Enhance Modal ─────────────────────────────────────────────────────────────
interface EnhanceModalProps {
  projectId: string;
  artifact: UseCase | TestCase;
  onClose: () => void;
}

function EnhanceModal({ projectId, artifact, onClose }: EnhanceModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [updatedArtifact, setUpdatedArtifact] = useState<Record<string, unknown> | null>(null);
  const [readyToApply, setReadyToApply] = useState(false);
  const [applying, setApplying] = useState(false);

  const artifactType: ArtifactType = (artifact as any).artifactType ?? 'test_case';

  const handleSend = async (text: string) => {
    const userMsg: ChatMessage = { role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await enhanceApi.chat({
        projectId,
        artifactId: artifact.id,
        artifactType,
        sessionId,
        message: text,
      });
      const { messages: msgs, sessionId: sid, updatedArtifact: ua, readyToApply: rta } = res.data;
      setMessages(msgs);
      setSessionId(sid);
      if (ua) setUpdatedArtifact(ua);
      setReadyToApply(rta);
    } catch {
      toast.error('Chat error');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!sessionId || !updatedArtifact) return;
    setApplying(true);
    try {
      await enhanceApi.applyEnhancement({
        projectId,
        artifactId: artifact.id,
        artifactType,
        sessionId,
        updatedArtifact,
      });
      toast.success('Enhancement applied to Jira & CosmosDB!');
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Apply failed');
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-box">
        <div className="modal-header">
          <div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>✨ Enhance Artifact</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 2 }}>{artifact.title}</div>
          </div>
          <button className="btn btn-secondary btn-icon" onClick={onClose}><MdClose size={18} /></button>
        </div>

        <div className="modal-body">
          {/* Artifact details panel */}
          <div style={{ padding: '12px 20px', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', fontSize: 12 }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>{artifact.description}</p>
            {'steps' in artifact && (artifact as TestCase).steps.length > 0 && (
              <ol style={{ paddingLeft: 16, color: 'var(--text-muted)' }}>
                {(artifact as TestCase).steps.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            )}
          </div>
          {/* Chat */}
          <div style={{ flex: 1, overflow: 'hidden', height: 360 }}>
            <ChatPanel
              messages={messages}
              onSend={handleSend}
              loading={loading}
              placeholder="Describe the enhancement you want…"
            />
          </div>
        </div>

        <div className="modal-footer">
          {readyToApply && updatedArtifact && (
            <button className="btn btn-success" onClick={handleApply} disabled={applying}>
              {applying ? <><Spinner size={15} /> Applying…</> : <><MdCheckCircle size={16} /> Apply Enhancement</>}
            </button>
          )}
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
export default function EnhancePage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [refactorTarget, setRefactorTarget] = useState<UseCase | TestCase | null>(null);

  const { data: projectsData, isLoading: loadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => dashboardApi.getProjects().then((r: any) => r.data.projects as Project[]),
  });

  const { data: artifacts, isLoading: loadingArtifacts, refetch } = useQuery<ProjectArtifacts>({
    queryKey: ['artifacts', selectedProjectId],
    queryFn: () => dashboardApi.getArtifacts(selectedProjectId).then((r: any) => r.data),
    enabled: !!selectedProjectId,
  });

  const projects = projectsData ?? [];

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="page-title">Enhance Artifacts</div>
          <div className="page-subtitle">Refactor Use Cases and Test Cases with AI assistance</div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-4" style={{ flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: 1, minWidth: 240 }}>
            <label className="form-label">Select Project</label>
            {loadingProjects ? <Spinner /> : (
              <select className="select" value={selectedProjectId}
                onChange={e => setSelectedProjectId(e.target.value)}>
                <option value="">— Choose a project —</option>
                {projects.map(p => (
                  <option key={p.projectId} value={p.projectId}>
                    {p.projectName} ({p.jiraProjectKey})
                  </option>
                ))}
              </select>
            )}
          </div>
          {selectedProjectId && (
            <button className="btn btn-secondary" onClick={() => refetch()} style={{ marginTop: 18 }}>
              Refresh
            </button>
          )}
        </div>
      </div>

      <div className="card" style={{ minHeight: 400 }}>
        {!selectedProjectId && (
          <div className="empty-state">
            <div className="empty-state-icon">🔧</div>
            <div className="empty-state-title">Select a project to view and enhance artifacts</div>
          </div>
        )}
        {loadingArtifacts && <div className="flex items-center gap-3" style={{ padding: 30 }}><Spinner /> Loading…</div>}
        {artifacts && !loadingArtifacts && (
          <>
            <div style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontWeight: 600 }}>{artifacts.projectName}</span>
              <span className="badge badge-accent">{artifacts.jiraProjectKey}</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Click <strong>Refactor</strong> on any Use Case or Test Case to enhance it
              </span>
            </div>
            <ArtifactTree
              epics={artifacts.epics}
              onRefactor={(item) => setRefactorTarget(item as UseCase | TestCase)}
            />
          </>
        )}
      </div>

      {refactorTarget && selectedProjectId && (
        <EnhanceModal
          projectId={selectedProjectId}
          artifact={refactorTarget}
          onClose={() => setRefactorTarget(null)}
        />
      )}
    </div>
  );
}
