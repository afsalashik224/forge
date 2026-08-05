import React from 'react';
import { FileCode2 } from 'lucide-react';

export default function AdrTracker() {
  const adrs = [
    {
      id: "ADR-001",
      title: "Primary Linux Development Environment",
      date: "2026-07-27",
      status: "ACCEPTED",
      decision: "Use WSL / Linux environment for local development and build pipelines.",
      reason: "Matches production Linux Docker containers, aligns with DevOps toolchains (Ansible, Terraform, Jenkins)."
    },
    {
      id: "ADR-002",
      title: "Externalize Application Configuration",
      date: "2026-07-27",
      status: "ACCEPTED",
      decision: "Application runtime settings will not be hardcoded in Python code.",
      reason: "Ensures portability across dev, staging, and production environments using python-dotenv and Settings objects."
    },
    {
      id: "ADR-003",
      title: "Single Responsibility & Repository Pattern",
      date: "2026-07-27",
      status: "ACCEPTED",
      decision: "Separate database queries (Repository), business logic (Service), and HTTP handlers (Blueprint API).",
      reason: "Allows testability, dependency injection, and clean layer separation."
    }
  ];

  return (
    <div style={{ padding: '28px', maxWidth: '950px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <FileCode2 size={22} color="var(--emerald-primary)" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Architecture Decision Records (ADRs)
            </h1>
            <span className="badge-copper">ROADMAP PREVIEW</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            System design decisions and architectural choices recorded in Forge repository log.
          </p>
        </div>
      </div>

      {/* ADR List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {adrs.map((adr) => (
          <div key={adr.id} className="matte-card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="badge-emerald font-mono">{adr.id}</span>
                <h3 style={{ fontSize: '0.975rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {adr.title}
                </h3>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {adr.date}
              </span>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-main)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '14px',
              marginBottom: '10px'
            }}>
              <div style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--emerald-primary)', marginBottom: '3px', letterSpacing: '0.04em' }}>
                DECISION
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                {adr.decision}
              </p>
            </div>

            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              <strong style={{ color: 'var(--text-secondary)' }}>Rationale:</strong> {adr.reason}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
