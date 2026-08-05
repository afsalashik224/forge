import React from 'react';
import { Compass, Sparkles, Target } from 'lucide-react';

export default function ForgeCompass() {
  const recommendations = [
    {
      title: "Distributed Caching & Redis Eviction",
      reason: "Recommended based on your recent 'REST API' & persistence entries",
      difficulty: "Intermediate",
      category: "System Architecture"
    },
    {
      title: "Asynchronous Message Brokers & Queues",
      reason: "Identified gap in backend event-driven pattern mastery",
      difficulty: "Advanced",
      category: "Backend Systems"
    },
    {
      title: "Database Indexing & B-Tree Mechanics",
      reason: "Prerequisite concept for scaling SQLAlchemy persistence layer",
      difficulty: "Foundational",
      category: "Data Systems"
    }
  ];

  return (
    <div style={{ padding: '28px', maxWidth: '950px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Compass size={22} color="var(--copper-primary)" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Forge Compass
            </h1>
            <span className="badge-copper">ROADMAP PREVIEW</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Forge's upcoming intelligent recommendation system designed to guide engineering mastery pathways.
          </p>
        </div>
      </div>

      {/* Vision Card */}
      <div className="matte-card" style={{
        padding: '24px',
        marginBottom: '24px',
        borderColor: 'var(--copper-border)',
        backgroundColor: 'var(--surface-primary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Sparkles size={16} color="var(--copper-primary)" />
          <span style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--copper-primary)', letterSpacing: '0.04em' }}>
            RECOMMENDATION ENGINE PARADIGM
          </span>
        </div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
          Forge Compass analyzes your repository concepts, identifies engineering knowledge gaps, and dynamically generates personalized learning trajectories to turn memorization into structural understanding.
        </p>
      </div>

      {/* Suggested Pathways Preview */}
      <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '14px' }}>
        Algorithmic Learning Recommendations (Preview)
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {recommendations.map((rec, idx) => (
          <div key={idx} className="matte-card" style={{ padding: '18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <div style={{
                width: '32px', height: '32px', borderRadius: '6px',
                backgroundColor: 'var(--copper-subtle)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0
              }}>
                <Target size={16} color="var(--copper-primary)" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <h3 style={{ fontSize: '0.975rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {rec.title}
                  </h3>
                  <span className="badge-slate">{rec.difficulty}</span>
                </div>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  {rec.reason}
                </p>
                <span style={{ fontSize: '0.75rem', color: 'var(--emerald-primary)', fontFamily: 'var(--font-mono)' }}>
                  Category: {rec.category}
                </span>
              </div>
            </div>

            <span className="badge-copper">PLANNED MODULE</span>
          </div>
        ))}
      </div>
    </div>
  );
}
