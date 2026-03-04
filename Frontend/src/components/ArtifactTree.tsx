import { useState } from 'react';
import {
  MdExpandMore, MdExpandLess, MdAccountTree,
  MdViewModule, MdAssignment, MdBugReport,
  MdOpenInNew,
} from 'react-icons/md';
import { Epic, Feature, UseCase, TestCase } from '../types';
import PriorityBadge from './PriorityBadge';

// ─── Leaf: Test Case ───────────────────────────────────────────────────────────
function TestCaseRow({ tc, onRefactor }: { tc: TestCase; onRefactor?: (tc: TestCase) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="tree-node">
      <div className={`tree-row${open ? ' active' : ''}`} onClick={() => setOpen(o => !o)}>
        <MdBugReport size={15} style={{ color: '#f59e0b', flexShrink: 0 }} />
        <span style={{ flex: 1 }}>{tc.title}</span>
        <PriorityBadge priority={tc.priority} />
        {tc.jiraIssueKey && (
          <a href={tc.jiraIssueUrl || '#'} target="_blank" rel="noreferrer"
            className="badge badge-info" onClick={e => e.stopPropagation()}
            style={{ textDecoration: 'none' }}>
            {tc.jiraIssueKey} <MdOpenInNew size={10} />
          </a>
        )}
        {onRefactor && (
          <button className="btn btn-sm btn-secondary" style={{ padding: '2px 8px', fontSize: 11 }}
            onClick={e => { e.stopPropagation(); onRefactor(tc); }}>
            Refactor
          </button>
        )}
        {open ? <MdExpandLess size={16} /> : <MdExpandMore size={16} />}
      </div>
      {open && (
        <div style={{ marginLeft: 32, padding: '8px 0', fontSize: 12, color: 'var(--text-secondary)' }}>
          <p style={{ marginBottom: 6 }}>{tc.description}</p>
          {tc.steps.length > 0 && (
            <ol style={{ paddingLeft: 16, marginBottom: 6 }}>
              {tc.steps.map((s, i) => <li key={i}>{s}</li>)}
            </ol>
          )}
          {tc.expectedResult && <p><strong>Expected:</strong> {tc.expectedResult}</p>}
        </div>
      )}
    </div>
  );
}

// ─── Use Case ─────────────────────────────────────────────────────────────────
function UseCaseRow({ uc, onRefactor }: { uc: UseCase; onRefactor?: (item: UseCase | TestCase) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="tree-node">
      <div className={`tree-row${open ? ' active' : ''}`} onClick={() => setOpen(o => !o)}>
        <MdAssignment size={15} style={{ color: '#22c55e', flexShrink: 0 }} />
        <span style={{ flex: 1 }}>{uc.title}</span>
        <PriorityBadge priority={uc.priority} />
        {uc.jiraIssueKey && (
          <a href={uc.jiraIssueUrl || '#'} target="_blank" rel="noreferrer"
            className="badge badge-info" onClick={e => e.stopPropagation()}
            style={{ textDecoration: 'none' }}>
            {uc.jiraIssueKey} <MdOpenInNew size={10} />
          </a>
        )}
        {onRefactor && (
          <button className="btn btn-sm btn-secondary" style={{ padding: '2px 8px', fontSize: 11 }}
            onClick={e => { e.stopPropagation(); onRefactor(uc); }}>
            Refactor
          </button>
        )}
        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{uc.testCases.length} TCs</span>
        {open ? <MdExpandLess size={16} /> : <MdExpandMore size={16} />}
      </div>
      {open && (
        <div className="tree-children">
          {uc.testCases.map(tc => (
            <TestCaseRow key={tc.id} tc={tc} onRefactor={onRefactor ? () => onRefactor(tc) : undefined} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Feature ──────────────────────────────────────────────────────────────────
function FeatureRow({ feat, onRefactor }: { feat: Feature; onRefactor?: (item: UseCase | TestCase) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="tree-node">
      <div className={`tree-row${open ? ' active' : ''}`} onClick={() => setOpen(o => !o)}>
        <MdViewModule size={15} style={{ color: '#818cf8', flexShrink: 0 }} />
        <span style={{ flex: 1 }}>{feat.title}</span>
        <PriorityBadge priority={feat.priority} />
        {feat.jiraIssueKey && (
          <a href={feat.jiraIssueUrl || '#'} target="_blank" rel="noreferrer"
            className="badge badge-info" onClick={e => e.stopPropagation()}
            style={{ textDecoration: 'none' }}>
            {feat.jiraIssueKey} <MdOpenInNew size={10} />
          </a>
        )}
        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{feat.useCases.length} UCs</span>
        {open ? <MdExpandLess size={16} /> : <MdExpandMore size={16} />}
      </div>
      {open && (
        <div className="tree-children">
          {feat.useCases.map(uc => (
            <UseCaseRow key={uc.id} uc={uc} onRefactor={onRefactor} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Epic ─────────────────────────────────────────────────────────────────────
function EpicRow({ epic, onRefactor }: { epic: Epic; onRefactor?: (item: UseCase | TestCase) => void }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="tree-node">
      <div className={`tree-row${open ? ' active' : ''}`} onClick={() => setOpen(o => !o)}
        style={{ background: open ? 'rgba(99,102,241,0.08)' : undefined }}>
        <MdAccountTree size={16} style={{ color: 'var(--accent-light)', flexShrink: 0 }} />
        <span style={{ flex: 1, fontWeight: 600 }}>{epic.title}</span>
        <PriorityBadge priority={epic.priority} />
        {epic.jiraIssueKey && (
          <a href={epic.jiraIssueUrl || '#'} target="_blank" rel="noreferrer"
            className="badge badge-info" onClick={e => e.stopPropagation()}
            style={{ textDecoration: 'none' }}>
            {epic.jiraIssueKey} <MdOpenInNew size={10} />
          </a>
        )}
        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{epic.features.length} Features</span>
        {open ? <MdExpandLess size={16} /> : <MdExpandMore size={16} />}
      </div>
      {open && (
        <div className="tree-children">
          {epic.features.map(f => (
            <FeatureRow key={f.id} feat={f} onRefactor={onRefactor} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Public Export ─────────────────────────────────────────────────────────────
interface ArtifactTreeProps {
  epics: Epic[];
  onRefactor?: (item: UseCase | TestCase) => void;
}

export default function ArtifactTree({ epics, onRefactor }: ArtifactTreeProps) {
  if (!epics.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🌲</div>
        <div className="empty-state-title">No artifacts yet</div>
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {epics.map(epic => <EpicRow key={epic.id} epic={epic} onRefactor={onRefactor} />)}
    </div>
  );
}
