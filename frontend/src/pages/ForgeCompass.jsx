import React, { useEffect, useState } from 'react';
import {
  Compass,
  CheckCircle2,
  XCircle,
  RotateCcw,
  RefreshCw,
  ArrowUpRight,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import {
  fetchCompassRecommendations,
  refreshCompassRecommendations,
  updateRecommendationStatus,
} from '../services/api';

const PRIORITY_STYLES = {
  HIGH: { color: '#F87171', bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.35)' },
  MEDIUM: { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.35)' },
  LOW: { color: '#94A3B8', bg: 'rgba(148, 163, 184, 0.12)', border: 'rgba(148, 163, 184, 0.3)' },
};

function formatEvidenceValue(val) {
  if (Array.isArray(val)) {
    return val
      .map((item) => (typeof item === 'object' && item !== null ? item.title || item.slug || JSON.stringify(item) : String(item)))
      .join(', ');
  }
  if (typeof val === 'object' && val !== null) {
    return Object.entries(val)
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ');
  }
  return String(val);
}

export default function ForgeCompass({
  refreshKey = 0,
  onCompassUpdated,
  onNavigateRecommendation,
  onOpenCreateConcept,
  onOpenWorkspaces,
  showToast,
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [activeGroup, setActiveGroup] = useState('active_pending'); // 'active_pending' | 'completed' | 'dismissed' | 'no_longer_relevant'
  const [priorityFilter, setPriorityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    fetchCompassRecommendations({
      priority: priorityFilter || undefined,
      category: categoryFilter || undefined,
    })
      .then((res) => {
        if (active) setData(res);
      })
      .catch((err) => {
        if (active) setError(err.message || 'Failed to load Forge Compass recommendations.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshKey, priorityFilter, categoryFilter]);

  const handleManualRefresh = async () => {
    setRefreshing(true);
    try {
      const res = await refreshCompassRecommendations();
      setData(res);
      if (onCompassUpdated) onCompassUpdated();
      if (showToast) showToast('Forge Compass recommendations refreshed.', 'success');
    } catch (err) {
      if (showToast) showToast(err.message || 'Failed to refresh recommendations.', 'error');
    } finally {
      setRefreshing(false);
    }
  };

  const handleStatusChange = async (recId, newStatus) => {
    try {
      await updateRecommendationStatus(recId, newStatus);
      const updated = await fetchCompassRecommendations({
        refresh: false,
        priority: priorityFilter || undefined,
        category: categoryFilter || undefined,
      });
      setData(updated);
      if (onCompassUpdated) onCompassUpdated();
      if (showToast) showToast(`Recommendation marked ${newStatus.toLowerCase()}.`, 'success');
    } catch (err) {
      if (showToast) showToast(err.message || 'Failed to update recommendation.', 'error');
    }
  };

  const groups = data?.groups || {
    active_pending: [],
    completed: [],
    dismissed: [],
    no_longer_relevant: [],
  };
  const counts = data?.counts || {};
  const overview = data?.overview || {};
  const visibleRecs = groups[activeGroup] || [];

  const tabItems = [
    { key: 'active_pending', label: `Active Queue (${counts.active_pending ?? groups.active_pending.length})` },
    { key: 'completed', label: `Completed (${counts.completed ?? groups.completed.length})` },
    { key: 'dismissed', label: `Dismissed (${counts.dismissed ?? groups.dismissed.length})` },
    { key: 'no_longer_relevant', label: `Resolved in Data (${counts.no_longer_relevant ?? groups.no_longer_relevant.length})` },
  ];

  return (
    <div style={{ padding: '28px', maxWidth: '1080px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <Compass size={22} color="var(--copper-primary)" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Forge Compass
            </h1>
            <span className="badge-emerald">LIVE ENGINE</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Actionable, evidence-backed next steps derived from real Forge repositories, concepts, and graph coverage.
          </p>
        </div>

        <button
          type="button"
          className="btn-secondary"
          onClick={handleManualRefresh}
          disabled={refreshing}
          style={{ fontSize: '0.8rem', padding: '7px 12px' }}
        >
          <RefreshCw size={14} />
          <span>{refreshing ? 'Analyzing...' : 'Refresh Insights'}</span>
        </button>
      </div>

      {/* Priority Summary Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '12px', marginBottom: '20px' }}>
        <div className="matte-card" style={{ padding: '14px 16px' }}>
          <span style={{ fontSize: '0.675rem', fontWeight: 700, color: '#F87171' }}>HIGH PRIORITY</span>
          <div style={{ fontSize: '1.45rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
            {counts.high_priority || 0}
          </div>
        </div>
        <div className="matte-card" style={{ padding: '14px 16px' }}>
          <span style={{ fontSize: '0.675rem', fontWeight: 700, color: '#F59E0B' }}>MEDIUM PRIORITY</span>
          <div style={{ fontSize: '1.45rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
            {counts.medium_priority || 0}
          </div>
        </div>
        <div className="matte-card" style={{ padding: '14px 16px' }}>
          <span style={{ fontSize: '0.675rem', fontWeight: 700, color: '#94A3B8' }}>LOW PRIORITY</span>
          <div style={{ fontSize: '1.45rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
            {counts.low_priority || 0}
          </div>
        </div>
        <div className="matte-card" style={{ padding: '14px 16px' }}>
          <span style={{ fontSize: '0.675rem', fontWeight: 700, color: 'var(--emerald-primary)' }}>COMPLETED ACTIONS</span>
          <div style={{ fontSize: '1.45rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
            {counts.completed || 0}
          </div>
        </div>
      </div>

      {/* Tabs and Filters */}
      <div className="matte-card" style={{ padding: '12px 16px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {tabItems.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setActiveGroup(t.key)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: activeGroup === t.key ? '1px solid var(--emerald-border)' : '1px solid transparent',
                backgroundColor: activeGroup === t.key ? 'var(--emerald-subtle)' : 'transparent',
                color: activeGroup === t.key ? 'var(--emerald-primary)' : 'var(--text-muted)',
                fontSize: '0.785rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            aria-label="Filter by priority"
            style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', padding: '5px 10px', fontSize: '0.775rem' }}
          >
            <option value="">All Priorities</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            aria-label="Filter by category"
            style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', padding: '5px 10px', fontSize: '0.775rem' }}
          >
            <option value="">All Categories</option>
            <option value="DOCUMENTATION_GAP">Documentation Gap</option>
            <option value="MISSING_RELATIONSHIPS">Missing Relationships</option>
            <option value="LOW_COVERAGE">Low Coverage</option>
            <option value="ORGANIZATION_ISSUE">Organization Issue</option>
            <option value="CATEGORY_BALANCE">Category Balance</option>
          </select>
        </div>
      </div>

      {/* Recommendations List */}
      {loading ? (
        <div className="matte-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Evaluating Progress Engine observations...
        </div>
      ) : error ? (
        <div className="matte-card" style={{ padding: '32px', textAlign: 'center', color: '#F87171', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      ) : (overview.total_repositories === 0 && overview.total_concepts === 0 && overview.total_workspaces === 0 && visibleRecs.length === 0) ? (
        <div className="matte-card" style={{ padding: '44px', textAlign: 'center' }}>
          <Sparkles size={30} color="var(--copper-primary)" style={{ marginBottom: '10px' }} />
          <h3 style={{ fontSize: '1.05rem', color: 'var(--text-primary)', marginBottom: '6px' }}>
            Waiting for Forge Knowledge Data
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '480px', margin: '0 auto 18px auto' }}>
            Forge Compass only generates recommendations grounded in real stored workspaces, repositories, concepts, and relationships. Create your first entities to receive tailored guidance.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
            {onOpenWorkspaces && (
              <button type="button" className="btn-secondary" onClick={onOpenWorkspaces}>
                Add Workspace / Repository
              </button>
            )}
            {onOpenCreateConcept && (
              <button type="button" className="btn-emerald" onClick={onOpenCreateConcept}>
                Forge Concept
              </button>
            )}
          </div>
        </div>
      ) : visibleRecs.length === 0 ? (
        <div className="matte-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          {activeGroup === 'active_pending'
            ? 'No active pending recommendations match your current filters.'
            : `No recommendations in "${tabItems.find((t) => t.key === activeGroup)?.label}".`}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {visibleRecs.map((rec) => {
            const pStyle = PRIORITY_STYLES[rec.priority] || PRIORITY_STYLES.MEDIUM;
            const evidenceEntries = Object.entries(rec.evidence || {});

            return (
              <div key={rec.id} className="matte-card" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '14px', flexWrap: 'wrap', marginBottom: '10px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '6px' }}>
                      <span
                        style={{
                          fontSize: '0.675rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          color: pStyle.color,
                          backgroundColor: pStyle.bg,
                          border: `1px solid ${pStyle.border}`,
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {rec.priority}
                      </span>
                      <span className="badge-slate" style={{ fontSize: '0.675rem' }}>
                        {rec.category.replace(/_/g, ' ')}
                      </span>
                      {rec.entity_label && (
                        <span className="badge-copper" style={{ fontSize: '0.675rem' }}>
                          {rec.entity_type}: {rec.entity_label}
                        </span>
                      )}
                      {!rec.is_active && rec.status === 'PENDING' && (
                        <span className="badge-emerald" style={{ fontSize: '0.675rem' }}>
                          CONDITION RESOLVED
                        </span>
                      )}
                    </div>
                    <h3 style={{ fontSize: '1.025rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {rec.title}
                    </h3>
                  </div>

                  <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    {rec.rule_code}
                  </span>
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.55', marginBottom: '10px' }}>
                  {rec.explanation}
                </p>

                <div style={{ fontSize: '0.8125rem', color: 'var(--emerald-primary)', marginBottom: '12px' }}>
                  <strong>Suggested action:</strong> {rec.suggested_action}
                </div>

                {/* Supporting Evidence */}
                {evidenceEntries.length > 0 && (
                  <div
                    style={{
                      backgroundColor: 'var(--bg-main)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '6px',
                      padding: '10px 12px',
                      marginBottom: '14px',
                    }}
                  >
                    <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '6px' }}>
                      SUPPORTING EVIDENCE
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 18px', fontSize: '0.75rem' }}>
                      {evidenceEntries.map(([k, v]) => (
                        <div key={k} style={{ color: 'var(--text-secondary)' }}>
                          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{k}: </span>
                          <span>{formatEvidenceValue(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Controls */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', paddingTop: '10px', borderTop: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {onNavigateRecommendation && (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => onNavigateRecommendation(rec)}
                        style={{ padding: '6px 12px', fontSize: '0.775rem' }}
                      >
                        <span>
                          {rec.action_target === 'graph'
                            ? 'Open Knowledge Graph'
                            : rec.action_target === 'workspaces'
                            ? 'Open Workspaces & Repos'
                            : rec.action_target === 'edit-concept'
                            ? 'Edit Concept'
                            : rec.action_target === 'create-concept'
                            ? 'Forge Concept'
                            : 'Explore in Library'}
                        </span>
                        <ArrowUpRight size={13} />
                      </button>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {rec.status === 'PENDING' ? (
                      <>
                        <button
                          type="button"
                          className="btn-emerald"
                          onClick={() => handleStatusChange(rec.id, 'COMPLETED')}
                          style={{ padding: '6px 12px', fontSize: '0.775rem' }}
                        >
                          <CheckCircle2 size={13} />
                          <span>Complete</span>
                        </button>
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => handleStatusChange(rec.id, 'DISMISSED')}
                          style={{ padding: '6px 12px', fontSize: '0.775rem' }}
                        >
                          <XCircle size={13} />
                          <span>Dismiss</span>
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => handleStatusChange(rec.id, 'PENDING')}
                        style={{ padding: '6px 12px', fontSize: '0.775rem' }}
                      >
                        <RotateCcw size={13} />
                        <span>Reopen</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
