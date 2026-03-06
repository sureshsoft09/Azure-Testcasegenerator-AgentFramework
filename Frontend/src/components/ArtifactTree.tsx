import React, { useState } from 'react';
import {
  MdExpandMore, MdExpandLess, MdAccountTree,
  MdViewModule, MdAssignment, MdBugReport,
  MdOpenInNew, MdAutoAwesome, MdClose,
} from 'react-icons/md';
import { Epic, Feature, UseCase, TestCase } from '../types';
import PriorityBadge from './PriorityBadge';

// ─── Normalisers: accept both camelCase and snake_case from the API ────────────
function normalizeTestCase(tc: any, idx: number): TestCase {
  return {
    id:               tc.id ?? tc.test_case_id ?? `tc-${idx}`,
    title:            tc.title ?? tc.test_case_title ?? tc.name ?? tc.test_case_name ?? tc.testCaseName ?? '',
    description:      tc.description ?? '',
    preconditions:    tc.preconditions ?? tc.pre_conditions,
    steps:            tc.steps ?? tc.test_steps ?? [],
    expectedResult:   tc.expectedResult ?? tc.expected_result ?? '',
    priority:         tc.priority ?? 'medium',
    artifactType:     tc.artifactType ?? tc.artifact_type ?? 'test_case',
    jiraIssueKey:     tc.jiraIssueKey ?? tc.jira_issue_key,
    jiraIssueId:      tc.jiraIssueId ?? tc.jira_issue_id,
    jiraIssueUrl:     tc.jiraIssueUrl ?? tc.jira_issue_url,
    tags:             tc.tags ?? [],
    complianceMapping: tc.complianceMapping ?? tc.compliance_mapping ?? [],
    testType:         tc.testType ?? tc.test_type,
    reviewStatus:     tc.reviewStatus ?? tc.review_status,
    modelExplanation: tc.modelExplanation ?? tc.model_explanation,
  };
}

function normalizeUseCase(uc: any, idx: number): UseCase {
  const testCases: any[] = uc.testCases ?? uc.test_cases ?? [];
  return {
    id:               uc.id ?? uc.use_case_id ?? `uc-${idx}`,
    title:            uc.title ?? uc.name ?? uc.use_case_name ?? uc.useCaseName ?? '',
    description:      uc.description ?? '',
    actors:           uc.actors ?? [],
    preconditions:    uc.preconditions ?? uc.pre_conditions,
    mainFlow:         uc.mainFlow ?? uc.main_flow ?? [],
    alternateFlows:   uc.alternateFlows ?? uc.alternate_flows ?? [],
    postconditions:   uc.postconditions,
    priority:         uc.priority ?? 'medium',
    artifactType:     uc.artifactType ?? uc.artifact_type ?? 'use_case',
    jiraIssueKey:     uc.jiraIssueKey ?? uc.jira_issue_key,
    jiraIssueId:      uc.jiraIssueId ?? uc.jira_issue_id,
    jiraIssueUrl:     uc.jiraIssueUrl ?? uc.jira_issue_url,
    testCases:        testCases.map(normalizeTestCase),
    complianceMapping: uc.complianceMapping ?? uc.compliance_mapping ?? [],
    reviewStatus:     uc.reviewStatus ?? uc.review_status,
    modelExplanation: uc.modelExplanation ?? uc.model_explanation,
  };
}

function normalizeFeature(feat: any, idx: number): Feature {
  const useCases: any[] = feat.useCases ?? feat.use_cases ?? [];
  return {
    id:           feat.id ?? feat.feature_id ?? `feat-${idx}`,
    title:        feat.title ?? feat.name ?? feat.feature_name ?? feat.featureName ?? '',
    description:  feat.description ?? '',
    priority:     feat.priority ?? 'medium',
    artifactType: feat.artifactType ?? feat.artifact_type ?? 'feature',
    jiraIssueKey: feat.jiraIssueKey ?? feat.jira_issue_key,
    jiraIssueId:  feat.jiraIssueId ?? feat.jira_issue_id,
    jiraIssueUrl: feat.jiraIssueUrl ?? feat.jira_issue_url,
    useCases:     useCases.map(normalizeUseCase),
  };
}

function normalizeEpic(epic: any, idx: number): Epic {
  const features: any[] = epic.features ?? [];
  return {
    id:           epic.id ?? epic.epic_id ?? `epic-${idx}`,
    title:        epic.title ?? epic.name ?? epic.epic_name ?? epic.epicName ?? '',
    description:  epic.description ?? '',
    priority:     epic.priority ?? 'medium',
    artifactType: epic.artifactType ?? epic.artifact_type ?? 'epic',
    jiraIssueKey: epic.jiraIssueKey ?? epic.jira_issue_key,
    jiraIssueId:  epic.jiraIssueId ?? epic.jira_issue_id,
    jiraIssueUrl: epic.jiraIssueUrl ?? epic.jira_issue_url,
    features:     features.map(normalizeFeature),
  };
}

// ─── AI Model Explanation Modal ───────────────────────────────────────────────
function ModelExplanationModal({ text, onClose }: { text: string; onClose: () => void }) {
  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 2000,
        background: 'rgba(1, 12, 46, 0.82)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 24, backdropFilter: 'blur(4px)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)',
          padding: '20px 24px',
          maxWidth: 580, width: '100%',
          boxShadow: '0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(0,116,217,0.15)',
          position: 'relative',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 14,
          paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: 'rgba(0,116,217,0.15)',
            border: '1px solid rgba(0,116,217,0.3)', display: 'flex', alignItems: 'center',
            justifyContent: 'center', flexShrink: 0 }}>
            <MdAutoAwesome size={16} style={{ color: 'var(--accent-light)' }} />
          </div>
          <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', flex: 1 }}>
            AI Model Explanation
          </span>
          <button
            style={{ background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', padding: 4, borderRadius: 4,
              display: 'flex', alignItems: 'center', lineHeight: 1 }}
            onClick={onClose}
          >
            <MdClose size={18} />
          </button>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.75,
          whiteSpace: 'pre-wrap' }}>
          {text}
        </p>
      </div>
    </div>
  );
}

// ─── Shared inline badge helpers ──────────────────────────────────────────────
const reviewBadgeStyle = (status?: string): React.CSSProperties => ({
  fontSize: 10, padding: '2px 8px', borderRadius: 4, fontWeight: 700,
  letterSpacing: '0.03em', flexShrink: 0,
  background: status === 'Approved' ? 'rgba(0,200,122,0.12)' : 'rgba(245,166,35,0.12)',
  color:      status === 'Approved' ? 'var(--success)'       : 'var(--warning)',
  border:     status === 'Approved' ? '1px solid rgba(0,200,122,0.3)' : '1px solid rgba(245,166,35,0.3)',
});

const testTypeBadgeStyle: React.CSSProperties = {
  fontSize: 10, padding: '2px 8px', borderRadius: 4, fontWeight: 700,
  letterSpacing: '0.03em', flexShrink: 0,
  background: 'rgba(99,102,241,0.13)', color: '#a5b4fc',
  border: '1px solid rgba(99,102,241,0.28)',
};

const sectionLabel: React.CSSProperties = {
  fontSize: 10, fontWeight: 800, color: 'var(--text-muted)',
  letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 5,
};

const complianceTag: React.CSSProperties = {
  fontSize: 10, padding: '2px 9px', borderRadius: 20, fontWeight: 600,
  background: 'rgba(59,180,255,0.09)', color: 'var(--info)',
  border: '1px solid rgba(59,180,255,0.22)',
};

// ─── Leaf: Test Case ───────────────────────────────────────────────────────────
function TestCaseRow({ tc, onRefactor }: { tc: TestCase; onRefactor?: (tc: TestCase) => void }) {
  const [open, setOpen] = useState(false);
  const [showExpl, setShowExpl] = useState(false);
  const steps      = tc.steps ?? [];
  const compliance = tc.complianceMapping ?? [];

  return (
    <div className="tree-node">
      {showExpl && tc.modelExplanation && (
        <ModelExplanationModal text={tc.modelExplanation} onClose={() => setShowExpl(false)} />
      )}
      <div className={`tree-row${open ? ' active' : ''}`} onClick={() => setOpen(o => !o)}>
        <MdBugReport size={15} style={{ color: '#f59e0b', flexShrink: 0 }} />
        <span style={{ flex: 1, fontWeight: 500 }}>{tc.title || <em style={{ color: 'var(--text-muted)' }}>Untitled</em>}</span>
        {tc.testType && <span style={testTypeBadgeStyle}>{tc.testType}</span>}
        {tc.reviewStatus && <span style={reviewBadgeStyle(tc.reviewStatus)}>{tc.reviewStatus}</span>}
        <PriorityBadge priority={tc.priority} />
        {tc.jiraIssueKey && (
          <a href={tc.jiraIssueUrl || '#'} target="_blank" rel="noreferrer"
            className="badge badge-info" onClick={e => e.stopPropagation()}
            style={{ textDecoration: 'none' }}>
            {tc.jiraIssueKey} <MdOpenInNew size={10} />
          </a>
        )}
        {tc.modelExplanation && (
          <button title="AI Model Explanation"
            style={{ background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--accent-light)', padding: '2px 3px', lineHeight: 1,
              display: 'flex', alignItems: 'center', flexShrink: 0 }}
            onClick={e => { e.stopPropagation(); setShowExpl(true); }}>
            <MdAutoAwesome size={14} />
          </button>
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
        <div style={{ marginLeft: 32, paddingBottom: 10 }}>
          {/* Description */}
          {tc.description && (
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '8px 0 10px', lineHeight: 1.65 }}>
              {tc.description}
            </p>
          )}

          {/* Preconditions */}
          {tc.preconditions && (
            <div style={{ marginBottom: 10 }}>
              <div style={sectionLabel}>Preconditions</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.65,
                background: 'rgba(0,86,184,0.07)', border: '1px solid rgba(0,116,217,0.14)',
                borderRadius: 6, padding: '7px 11px' }}>
                {Array.isArray(tc.preconditions)
                  ? <ul style={{ paddingLeft: 16, margin: 0 }}>
                      {tc.preconditions.map((p: string, i: number) => <li key={i}>{p}</li>)}
                    </ul>
                  : tc.preconditions}
              </div>
            </div>
          )}

          {/* Test Steps */}
          {steps.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={sectionLabel}>Test Steps</div>
              <ol style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 5 }}>
                {steps.map((s, i) => (
                  <li key={i} style={{ display: 'flex', gap: 8, fontSize: 12,
                    color: 'var(--text-secondary)', alignItems: 'flex-start' }}>
                    <span style={{ minWidth: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                      background: 'rgba(0,116,217,0.18)', color: 'var(--accent-light)',
                      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 10, fontWeight: 700, marginTop: 1 }}>
                      {i + 1}
                    </span>
                    <span style={{ lineHeight: 1.65 }}>{s}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Expected Result */}
          {tc.expectedResult && (
            <div style={{ marginBottom: 10 }}>
              <div style={sectionLabel}>Expected Result</div>
              <div style={{ fontSize: 12, color: '#00C87A', lineHeight: 1.65,
                background: 'rgba(0,200,122,0.06)', border: '1px solid rgba(0,200,122,0.18)',
                borderRadius: 6, padding: '7px 11px' }}>
                {tc.expectedResult}
              </div>
            </div>
          )}

          {/* Compliance Mapping */}
          {compliance.length > 0 && (
            <div style={{ marginBottom: 4 }}>
              <div style={sectionLabel}>Compliance Mapping</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                {compliance.map((c, i) => <span key={i} style={complianceTag}>{c}</span>)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Use Case ─────────────────────────────────────────────────────────────────
function UseCaseRow({ uc, onRefactor }: { uc: UseCase; onRefactor?: (item: UseCase | TestCase) => void }) {
  const [open, setOpen] = useState(false);
  const [showExpl, setShowExpl] = useState(false);
  const compliance = uc.complianceMapping ?? [];

  return (
    <div className="tree-node">
      {showExpl && uc.modelExplanation && (
        <ModelExplanationModal text={uc.modelExplanation} onClose={() => setShowExpl(false)} />
      )}
      <div className={`tree-row${open ? ' active' : ''}`} onClick={() => setOpen(o => !o)}>
        <MdAssignment size={15} style={{ color: '#22c55e', flexShrink: 0 }} />
        <span style={{ flex: 1 }}>{uc.title || <em style={{ color: 'var(--text-muted)' }}>Untitled</em>}</span>
        {uc.reviewStatus && <span style={reviewBadgeStyle(uc.reviewStatus)}>{uc.reviewStatus}</span>}
        <PriorityBadge priority={uc.priority} />
        {uc.jiraIssueKey && (
          <a href={uc.jiraIssueUrl || '#'} target="_blank" rel="noreferrer"
            className="badge badge-info" onClick={e => e.stopPropagation()}
            style={{ textDecoration: 'none' }}>
            {uc.jiraIssueKey} <MdOpenInNew size={10} />
          </a>
        )}
        {uc.modelExplanation && (
          <button title="AI Model Explanation"
            style={{ background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--accent-light)', padding: '2px 3px', lineHeight: 1,
              display: 'flex', alignItems: 'center', flexShrink: 0 }}
            onClick={e => { e.stopPropagation(); setShowExpl(true); }}>
            <MdAutoAwesome size={14} />
          </button>
        )}
        {onRefactor && (
          <button className="btn btn-sm btn-secondary" style={{ padding: '2px 8px', fontSize: 11 }}
            onClick={e => { e.stopPropagation(); onRefactor(uc); }}>
            Refactor
          </button>
        )}
        <span style={{ color: 'var(--text-muted)', fontSize: 11, flexShrink: 0 }}>{uc.testCases.length} TCs</span>
        {open ? <MdExpandLess size={16} /> : <MdExpandMore size={16} />}
      </div>
      {open && (
        <div className="tree-children">
          {/* Compliance tags */}
          {compliance.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5,
              padding: '6px 8px 10px', borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
              <span style={{ ...sectionLabel, marginBottom: 0, alignSelf: 'center', marginRight: 4 }}>
                Compliance:
              </span>
              {compliance.map((c, i) => <span key={i} style={complianceTag}>{c}</span>)}
            </div>
          )}
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
  const normalized = (epics ?? []).map(normalizeEpic);
  if (!normalized.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🌲</div>
        <div className="empty-state-title">No artifacts yet</div>
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {normalized.map(epic => <EpicRow key={epic.id} epic={epic} onRefactor={onRefactor} />)}
    </div>
  );
}
