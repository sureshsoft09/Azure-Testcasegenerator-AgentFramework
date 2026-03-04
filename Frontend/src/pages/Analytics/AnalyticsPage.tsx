import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { dashboardApi, analyticsApi } from '../../api/client';
import { Project, AnalyticsSummary } from '../../types';
import Spinner from '../../components/Spinner';

const COLORS = ['#ef4444', '#f59e0b', '#22c55e', '#6366f1', '#3b82f6', '#a855f7'];

export default function AnalyticsPage() {
  const [selectedProject, setSelectedProject] = useState('');

  const { data: projectsData, isLoading: loadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => dashboardApi.getProjects().then((r: any) => r.data.projects as Project[]),
  });

  const { data: summary, isLoading: loadingStats } = useQuery<AnalyticsSummary>({
    queryKey: ['analytics', selectedProject],
    queryFn: () => analyticsApi.getSummary(selectedProject).then((r: any) => r.data),
    enabled: !!selectedProject,
  });

  const projects = projectsData ?? [];

  // Prepare chart data
  const priorityData = summary
    ? Object.entries(summary.priorityBreakdown).map(([name, value]) => ({ name, value }))
    : [];

  const complianceData = summary
    ? Object.entries(summary.complianceMapping).slice(0, 10).map(([name, value]) => ({ name, value }))
    : [];

  const artifactData = summary
    ? [
        { name: 'Epics', count: summary.totalEpics },
        { name: 'Features', count: summary.totalFeatures },
        { name: 'Use Cases', count: summary.totalUseCases },
        { name: 'Test Cases', count: summary.totalTestCases },
      ]
    : [];

  const jiraData = summary
    ? [
        { name: 'Jira Linked', value: summary.jiraLinkedCount },
        { name: 'Not Linked', value: summary.jiraUnlinkedCount },
      ]
    : [];

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="page-title">Analytics</div>
          <div className="page-subtitle">Test artifact insights and compliance coverage</div>
        </div>
      </div>

      {/* Project selector */}
      <div className="card">
        <div className="form-group" style={{ maxWidth: 340 }}>
          <label className="form-label">Select Project</label>
          {loadingProjects ? <Spinner /> : (
            <select className="select" value={selectedProject} onChange={e => setSelectedProject(e.target.value)}>
              <option value="">— Choose a project —</option>
              {projects.map(p => (
                <option key={p.projectId} value={p.projectId}>{p.projectName} ({p.jiraProjectKey})</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {!selectedProject && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-title">Select a project to view analytics</div>
        </div>
      )}

      {loadingStats && <div className="flex items-center gap-3" style={{ padding: 30 }}><Spinner /> Loading analytics…</div>}

      {summary && !loadingStats && (
        <>
          {/* KPI cards */}
          <div className="grid-4">
            {[
              { label: 'Epics', value: summary.totalEpics, color: '#818cf8' },
              { label: 'Features', value: summary.totalFeatures, color: '#6366f1' },
              { label: 'Use Cases', value: summary.totalUseCases, color: '#22c55e' },
              { label: 'Test Cases', value: summary.totalTestCases, color: '#f59e0b' },
            ].map(s => (
              <div key={s.label} className="card">
                <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
                <div className="stat-label">{s.label}</div>
              </div>
            ))}
          </div>

          <div className="grid-2">
            {/* Priority Breakdown */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 16 }}>Priority Distribution</div>
              {priorityData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={priorityData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                      {priorityData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : <div className="empty-state" style={{ padding: 30 }}>No data</div>}
            </div>

            {/* Artifact counts */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 16 }}>Artifact Counts</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={artifactData}>
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                  <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
                  <Bar dataKey="count" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Jira Coverage */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 16 }}>Jira Coverage</div>
              {jiraData.some(d => d.value > 0) ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={jiraData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                      <Cell fill="#22c55e" />
                      <Cell fill="#64748b" />
                    </Pie>
                    <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state" style={{ padding: 30 }}>No Jira data</div>
              )}
            </div>

            {/* Compliance Mapping */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 16 }}>Compliance Coverage</div>
              {complianceData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={complianceData} layout="vertical">
                    <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
                    <YAxis type="category" dataKey="name" width={80} tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
                    <Bar dataKey="value" fill="#a855f7" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state" style={{ padding: 30 }}>
                  <div className="empty-state-icon" style={{ fontSize: 28 }}>📋</div>
                  <div className="empty-state-title">No compliance data yet</div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
