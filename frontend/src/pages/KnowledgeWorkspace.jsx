import React from 'react';
import { BookOpen, Activity, Clock, Plus, Compass, ArrowUpRight, TrendingUp, Target } from 'lucide-react';
import ConceptCard from '../components/ConceptCard';
import KnowledgeGraphWidget from '../components/KnowledgeGraphWidget';
import SkeletonCard from '../components/SkeletonCard';

export default function KnowledgeWorkspace({ 
  concepts, 
  healthStatus, 
  progressOverview = null,
  compassSummary = null,
  onSelectConcept, 
  onOpenCreateModal, 
  onEditConcept,
  onDeleteConcept,
  setActiveTab,
  onNavigateFromGraphNode,
  onNavigateRecommendation,
  graphVersion = 0,
  loading
}) {
  const recentConcepts = concepts.slice(-3).reverse();
  const overview = progressOverview?.overview || {};
  const compassCounts = compassSummary?.counts || {};
  const topRecommendations = (compassSummary?.groups?.active_pending || []).slice(0, 3);

  return (
    <div style={{ padding: '28px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Hero Welcome Banner */}
      <div className="matte-card" style={{
        padding: '28px',
        marginBottom: '24px',
        backgroundColor: 'var(--surface-primary)',
        borderColor: 'var(--border-color)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span className="badge-emerald">SYSTEM ACTIVE</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            ENVIRONMENT: {healthStatus?.environment || 'development'}
          </span>
        </div>

        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', letterSpacing: '-0.02em' }}>
          Software Engineering Knowledge Platform
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', maxWidth: '650px', lineHeight: '1.6' }}>
          Organize, discover, connect, and progressively master engineering knowledge. Built with a clean repository architecture and live Flask REST APIs.
        </p>

        <div style={{ display: 'flex', gap: '10px', marginTop: '18px' }}>
          <button className="btn-emerald" onClick={onOpenCreateModal}>
            <Plus size={15} />
            <span>Forge New Concept</span>
          </button>
          <button className="btn-secondary" onClick={() => setActiveTab('library')}>
            <BookOpen size={15} />
            <span>Explore Library ({concepts.length})</span>
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '18px',
        marginBottom: '24px'
      }}>
        {/* Metric 1 */}
        <div className="matte-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
              FORGE LIBRARY CONCEPTS
            </span>
            <BookOpen size={16} color="var(--emerald-primary)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
            {concepts.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--emerald-primary)', marginTop: '4px' }}>
            Live SQL persistence
          </div>
        </div>

        {/* Metric 2 */}
        <div className="matte-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
              API HEALTH STATUS
            </span>
            <Activity size={16} color="var(--emerald-primary)" />
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
            {healthStatus?.status || 'Healthy'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>
            {healthStatus?.application || 'Forge'} v{healthStatus?.version || '0.1.0'}
          </div>
        </div>

        {/* Metric 3: Live Documentation Coverage */}
        <div
          className="matte-card matte-card-interactive"
          onClick={() => setActiveTab('progress')}
          style={{ padding: '18px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
              REPO DOC COVERAGE
            </span>
            <TrendingUp size={16} color="var(--emerald-primary)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: overview.average_documentation_score !== null && overview.average_documentation_score !== undefined ? 'var(--emerald-primary)' : 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {overview.average_documentation_score !== null && overview.average_documentation_score !== undefined
              ? `${overview.average_documentation_score}%`
              : 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            {overview.total_repositories || 0} repos · {overview.well_documented_repositories || 0} well documented
          </div>
        </div>

        {/* Metric 4: Live Forge Compass */}
        <div
          className="matte-card matte-card-interactive"
          onClick={() => setActiveTab('compass')}
          style={{ padding: '18px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
              FORGE COMPASS
            </span>
            <Compass size={16} color="var(--copper-primary)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
            {compassCounts.active_pending ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: compassCounts.high_priority > 0 ? '#F87171' : 'var(--copper-primary)', marginTop: '4px' }}>
            {compassCounts.high_priority || 0} high priority action(s)
          </div>
        </div>
      </div>

      {/* Main Grid: Top Compass Actions + Knowledge Graph Widget + Recently Forged */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
        {topRecommendations.length > 0 && (
          <div className="matte-card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Target size={16} color="var(--copper-primary)" />
                <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Forge Compass — Priority Next Actions
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setActiveTab('compass')}
                style={{ background: 'transparent', border: 'none', color: 'var(--copper-primary)', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                <span>Open Compass ({compassCounts.active_pending || 0})</span>
                <ArrowUpRight size={14} />
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
              {topRecommendations.map((rec) => (
                <div
                  key={rec.id}
                  onClick={() => onNavigateRecommendation ? onNavigateRecommendation(rec) : setActiveTab('compass')}
                  className="matte-card-interactive"
                  style={{
                    backgroundColor: 'var(--bg-main)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span className={rec.priority === 'HIGH' ? 'badge-copper' : 'badge-slate'} style={{ fontSize: '0.65rem' }}>
                      {rec.priority}
                    </span>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {rec.entity_label || rec.category}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    {rec.title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.45' }}>
                    {rec.explanation}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <KnowledgeGraphWidget
          refreshKey={graphVersion}
          onOpenGraphExplorer={() => setActiveTab('graph')}
          onNavigateFromNode={onNavigateFromGraphNode}
          onOpenCreateModal={onOpenCreateModal}
        />

        {/* Recently Forged Section */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={16} color="var(--emerald-primary)" />
              <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Recently Forged
              </h2>
            </div>

            <button 
              onClick={() => setActiveTab('library')}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--emerald-primary)',
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <span>View All ({concepts.length})</span>
              <ArrowUpRight size={14} />
            </button>
          </div>

          {loading ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '18px' }}>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : recentConcepts.length > 0 ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '18px'
            }}>
              {recentConcepts.map((c) => (
                <ConceptCard 
                  key={c.id} 
                  concept={c} 
                  onClick={() => onSelectConcept(c)} 
                  onEdit={onEditConcept}
                  onDelete={onDeleteConcept}
                />
              ))}
            </div>
          ) : (
            <div className="matte-card" style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              No concepts forged yet. Click <strong>Forge New Concept</strong> to create your first entry.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
