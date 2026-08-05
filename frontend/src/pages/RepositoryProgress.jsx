import React from 'react';
import { TrendingUp } from 'lucide-react';

export default function RepositoryProgress({ conceptsCount }) {
  const milestoneCategories = [
    { name: "Backend Architecture & Design Principles", mastered: 2, total: 5, progress: 40 },
    { name: "Database & Data Access Layer", mastered: 1, total: 4, progress: 25 },
    { name: "DevOps & Infrastructure Pipelines", mastered: 2, total: 3, progress: 66 },
    { name: "System Scalability & Performance", mastered: 0, total: 6, progress: 0 },
  ];

  return (
    <div style={{ padding: '28px', maxWidth: '950px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <TrendingUp size={22} color="var(--emerald-primary)" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Repository Progress
            </h1>
            <span className="badge-copper">ROADMAP PREVIEW</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Track engineering concept retention schedules and structural mastery progress over time.
          </p>
        </div>
      </div>

      {/* Progress Card Overview */}
      <div className="matte-card" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
          <div>
            <span style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--emerald-primary)', letterSpacing: '0.04em' }}>
              OVERALL KNOWLEDGE RETENTION
            </span>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
              {conceptsCount > 0 ? 'Initial Repository Phase' : 'Repository Initializing'}
            </h2>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span className="badge-emerald" style={{ fontSize: '0.8rem' }}>
              {conceptsCount} Concepts Tracked
            </span>
          </div>
        </div>

        {/* Knowledge Domains Breakdown */}
        <h3 style={{ fontSize: '0.975rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>
          Engineering Domain Competencies
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {milestoneCategories.map((cat, idx) => (
            <div key={idx} style={{ backgroundColor: 'var(--bg-main)', padding: '14px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.85rem' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{cat.name}</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--emerald-primary)' }}>
                  {cat.mastered}/{cat.total} mastered ({cat.progress}%)
                </span>
              </div>

              {/* Progress Bar Container */}
              <div style={{ width: '100%', height: '5px', backgroundColor: 'var(--surface-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{
                  width: `${cat.progress}%`,
                  height: '100%',
                  backgroundColor: 'var(--emerald-primary)',
                  borderRadius: '3px',
                  transition: 'width 0.4s ease'
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
