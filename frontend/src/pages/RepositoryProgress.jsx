import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  Info,
  AlertTriangle,
  BookOpen,
  Network,
  FolderGit2,
  GitBranch,
  Plus,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react';
import { fetchProgressOverview } from '../services/api';

const SUFFICIENCY_BADGES = {
  NO_CONCEPTS: { label: 'NO CONCEPTS', color: '#F87171', bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.35)' },
  MINIMAL_DATA: { label: 'MINIMAL DATA', color: '#FBBF24', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.35)' },
  PARTIAL: { label: 'PARTIAL COVERAGE', color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56, 189, 248, 0.35)' },
  WELL_DOCUMENTED: { label: 'WELL DOCUMENTED', color: '#10B981', bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.35)' },
};

const DIMENSION_LABELS = {
  knowledge_coverage: 'Knowledge Coverage',
  documentation_completeness: 'Documentation Completeness',
  concept_diversity: 'Concept Diversity',
  relationship_coverage: 'Relationship Coverage',
  organization_quality: 'Organization Quality',
};

export default function RepositoryProgress({
  refreshKey = 0,
  onOpenCreateConcept,
  onSelectConceptBySlug,
  onOpenGraph,
  onNavigateToRepository,
  onNavigateToWorkspaces,
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showMethodology, setShowMethodology] = useState(false);

  const loadProgress = () => {
    setLoading(true);
    setError(null);
    fetchProgressOverview()
      .then((res) => setData(res))
      .catch((err) => setError(err.message || 'Failed to load repository progress.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    fetchProgressOverview()
      .then((res) => {
        if (active) setData(res);
      })
      .catch((err) => {
        if (active) setError(err.message || 'Failed to load repository progress.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshKey]);

  const overview = data?.overview || {};
  const repositories = data?.repositories || [];
  const categoryDist = data?.category_distribution || {};
  const health = data?.knowledge_health || {};
  const metricDefs = data?.metric_definitions || [];

  return (
    <div style={{ padding: '28px', maxWidth: '1160px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <TrendingUp size={22} color="var(--emerald-primary)" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Repository Progress
            </h1>
            <span className="badge-emerald">LIVE METRICS</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Evidence-based documentation coverage, concept completeness, and Knowledge Graph connectivity per repository.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setShowMethodology((v) => !v)}
            style={{ fontSize: '0.8rem', padding: '7px 12px' }}
          >
            <Info size={14} />
            <span>Metric Formulas</span>
            {showMethodology ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={loadProgress}
            style={{ fontSize: '0.8rem', padding: '7px 12px' }}
          >
            <RefreshCw size={14} />
            <span>Recalculate</span>
          </button>
        </div>
      </div>

      {/* Transparency Disclaimer */}
      <div
        className="matte-card"
        style={{
          padding: '12px 16px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backgroundColor: 'var(--surface-secondary)',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
        }}
      >
        <Info size={15} color="var(--emerald-primary)" style={{ flexShrink: 0 }} />
        <span>
          {overview.disclaimer ||
            'Scores measure documentation coverage, structural completeness, and Knowledge Graph connectivity from stored Forge data — not source-code completion or production readiness.'}
        </span>
      </div>

      {/* Expandable Metric Methodology */}
      {showMethodology && metricDefs.length > 0 && (
        <div className="matte-card" style={{ padding: '18px 20px', marginBottom: '22px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px' }}>
            Transparent Metric Calculations (Weighted Score = 100%)
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
            {metricDefs.map((m) => (
              <div
                key={m.key}
                style={{
                  padding: '12px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--bg-main)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.825rem', color: 'var(--text-primary)' }}>{m.label}</span>
                  <span className="badge-emerald">{Math.round(m.weight * 100)}% weight</span>
                </div>
                <div style={{ fontSize: '0.725rem', fontFamily: 'var(--font-mono)', color: 'var(--emerald-primary)', marginBottom: '4px' }}>
                  {m.formula}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <div className="matte-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Calculating repository progress metrics...
        </div>
      ) : error ? (
        <div className="matte-card" style={{ padding: '36px', textAlign: 'center', color: '#F87171' }}>
          {error}
        </div>
      ) : (
        <>
          {/* Overview Stats Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '14px', marginBottom: '24px' }}>
            <div className="matte-card" style={{ padding: '16px' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
                AVG DOCUMENTATION SCORE
              </span>
              <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: overview.average_documentation_score !== null ? 'var(--emerald-primary)' : 'var(--text-muted)', marginTop: '4px' }}>
                {overview.average_documentation_score !== null && overview.average_documentation_score !== undefined
                  ? `${overview.average_documentation_score}%`
                  : 'N/A'}
              </div>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {overview.total_repositories === 0
                  ? 'No repositories tracked'
                  : `${overview.well_documented_repositories || 0} well documented`}
              </div>
            </div>

            <div className="matte-card" style={{ padding: '16px' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
                REPOSITORIES TRACKED
              </span>
              <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', marginTop: '4px' }}>
                {overview.total_repositories || 0}
              </div>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Across {overview.total_workspaces || 0} workspace(s)
              </div>
            </div>

            <div className="matte-card" style={{ padding: '16px' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
                DOCUMENTED CONCEPTS
              </span>
              <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', marginTop: '4px' }}>
                {overview.total_concepts || 0}
              </div>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {health.orphan_concepts_count || 0} isolated orphan(s)
              </div>
            </div>

            <div className="matte-card" style={{ padding: '16px' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
                GRAPH RELATIONSHIPS
              </span>
              <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', marginTop: '4px' }}>
                {overview.total_relationships || 0}
              </div>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Explicit concept links
              </div>
            </div>
          </div>

          {/* Repository Progress Cards or Honest Empty State */}
          {repositories.length === 0 ? (
            <div className="matte-card" style={{ padding: '44px', textAlign: 'center', marginBottom: '24px' }}>
              <GitBranch size={32} color="var(--text-muted)" style={{ marginBottom: '10px' }} />
              <h3 style={{ fontSize: '1.05rem', color: 'var(--text-primary)', marginBottom: '6px' }}>
                Insufficient Data — No Repositories Yet
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '480px', margin: '0 auto 18px auto' }}>
                Progress metrics are computed strictly from real repositories and linked knowledge concepts. Add a repository in Workspaces & Repositories to begin tracking documentation coverage.
              </p>
              <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
                {onNavigateToWorkspaces && (
                  <button type="button" className="btn-emerald" onClick={onNavigateToWorkspaces}>
                    <FolderGit2 size={15} />
                    <span>Go to Workspaces & Repos</span>
                  </button>
                )}
                {onOpenCreateConcept && (
                  <button type="button" className="btn-secondary" onClick={onOpenCreateConcept}>
                    <Plus size={15} />
                    <span>Forge Concept</span>
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', marginBottom: '24px' }}>
              {repositories.map((repo) => {
                const suff = SUFFICIENCY_BADGES[repo.data_sufficiency] || SUFFICIENCY_BADGES.PARTIAL;
                return (
                  <div key={repo.id} className="matte-card" style={{ padding: '22px' }}>
                    {/* Repo Card Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '16px', paddingBottom: '14px', borderBottom: '1px solid var(--border-color)' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '4px' }}>
                          <GitBranch size={17} color="var(--emerald-primary)" />
                          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {repo.name}
                          </h2>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: '6px',
                              color: suff.color,
                              backgroundColor: suff.bg,
                              border: `1px solid ${suff.border}`,
                              fontFamily: 'var(--font-mono)',
                            }}
                          >
                            {suff.label}
                          </span>
                          {repo.primary_language && <span className="badge-slate">{repo.primary_language}</span>}
                          {repo.workspaces.map((w) => (
                            <span key={w.id} className="badge-copper" style={{ fontSize: '0.675rem' }}>
                              {w.name}
                            </span>
                          ))}
                        </div>
                        <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                          slug: {repo.slug} · {repo.counts.concepts} concept(s) · {repo.counts.published_concepts} published
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 700 }}>DOC SCORE</div>
                          <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: repo.documentation_score >= 70 ? 'var(--emerald-primary)' : repo.documentation_score >= 40 ? '#38BDF8' : '#FBBF24' }}>
                            {repo.documentation_score}%
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 5 Dimensions Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px', marginBottom: '16px' }}>
                      {Object.entries(repo.dimensions).map(([key, dim]) => (
                        <div key={key} style={{ backgroundColor: 'var(--bg-main)', padding: '12px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.775rem', marginBottom: '6px' }}>
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{DIMENSION_LABELS[key] || key}</span>
                            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--emerald-primary)', fontWeight: 600 }}>
                              {dim.score}%
                            </span>
                          </div>
                          <div style={{ width: '100%', height: '5px', backgroundColor: 'var(--surface-secondary)', borderRadius: '3px', overflow: 'hidden', marginBottom: '6px' }}>
                            <div
                              style={{
                                width: `${dim.score}%`,
                                height: '100%',
                                backgroundColor: dim.score >= 70 ? 'var(--emerald-primary)' : dim.score >= 40 ? '#38BDF8' : '#F59E0B',
                                borderRadius: '3px',
                                transition: 'width 0.35s ease',
                              }}
                            />
                          </div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{dim.evidence}</div>
                        </div>
                      ))}
                    </div>

                    {/* Linked Concepts & Gaps */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginBottom: '14px' }}>
                      {/* Linked Concepts */}
                      <div style={{ backgroundColor: 'var(--surface-secondary)', padding: '12px 14px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px' }}>
                          LINKED KNOWLEDGE ({repo.concepts.length})
                        </div>
                        {repo.concepts.length === 0 ? (
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            No concepts associated yet.
                          </div>
                        ) : (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {repo.concepts.map((c) => (
                              <button
                                key={c.id}
                                type="button"
                                onClick={() => onSelectConceptBySlug && onSelectConceptBySlug(c.slug)}
                                className="btn-secondary"
                                style={{ padding: '4px 9px', fontSize: '0.75rem' }}
                              >
                                <BookOpen size={12} color="var(--emerald-primary)" />
                                <span>{c.title}</span>
                                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: c.completeness_score >= 75 ? 'var(--emerald-primary)' : '#FBBF24' }}>
                                  {Math.round(c.completeness_score)}%
                                </span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Identified Gaps */}
                      <div style={{ backgroundColor: 'var(--surface-secondary)', padding: '12px 14px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px' }}>
                          IDENTIFIED GAPS ({repo.gaps.length})
                        </div>
                        {repo.gaps.length === 0 ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--emerald-primary)' }}>
                            <CheckCircle2 size={14} />
                            <span>All coverage and metadata checks look healthy.</span>
                          </div>
                        ) : (
                          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.785rem', color: 'var(--text-secondary)' }}>
                            {repo.gaps.map((g, idx) => (
                              <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                                <AlertTriangle size={13} color="#F59E0B" style={{ flexShrink: 0, marginTop: '2px' }} />
                                <span>{g}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>

                    {/* Navigation Actions */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {onOpenCreateConcept && (
                        <button type="button" className="btn-emerald" onClick={onOpenCreateConcept} style={{ fontSize: '0.775rem', padding: '6px 12px' }}>
                          <Plus size={13} />
                          <span>Document Concept</span>
                        </button>
                      )}
                      {onOpenGraph && (
                        <button type="button" className="btn-secondary" onClick={() => onOpenGraph(repo.slug)} style={{ fontSize: '0.775rem', padding: '6px 12px' }}>
                          <Network size={13} />
                          <span>Inspect in Graph</span>
                        </button>
                      )}
                      {onNavigateToRepository && (
                        <button type="button" className="btn-secondary" onClick={() => onNavigateToRepository(repo.slug)} style={{ fontSize: '0.775rem', padding: '6px 12px' }}>
                          <GitBranch size={13} />
                          <span>Manage Repository</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Category Distribution & Platform Knowledge Health */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
            <div className="matte-card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '0.975rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px' }}>
                Knowledge Category Coverage
              </h3>
              {Object.keys(categoryDist).length === 0 && (data?.uncategorized_concepts_count || 0) === 0 ? (
                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  No concepts created yet.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(categoryDist).map(([cat, count]) => (
                    <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.825rem' }}>
                      <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{cat.replace(/-/g, ' ')}</span>
                      <span className="badge-emerald">{count}</span>
                    </div>
                  ))}
                  {(data?.uncategorized_concepts_count || 0) > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.825rem' }}>
                      <span style={{ color: '#FBBF24' }}>Uncategorized</span>
                      <span className="badge-copper">{data.uncategorized_concepts_count}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="matte-card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '0.975rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px' }}>
                Platform Knowledge Health Signals
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Isolated orphan concepts (no repo & no graph edges)</span>
                  <span className="badge-slate">{health.orphan_concepts_count || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Concepts missing substantive Markdown body</span>
                  <span className="badge-slate">{health.concepts_missing_content_count || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Concepts missing tags</span>
                  <span className="badge-slate">{health.concepts_missing_tags_count || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Empty workspaces (0 repositories)</span>
                  <span className="badge-slate">{health.empty_workspaces_count || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
