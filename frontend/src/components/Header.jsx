import React from 'react';
import { Search, Plus, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Header({ 
  activeTab, 
  onOpenCreateModal, 
  onOpenCommandPalette, 
  healthStatus 
}) {
  const getTabTitle = (tab) => {
    switch (tab) {
      case 'workspace': return 'Knowledge Workspace';
      case 'library': return 'Forge Library';
      case 'compass': return 'Forge Compass';
      case 'progress': return 'Repository Progress';
      case 'adrs': return 'Architecture Records';
      default: return 'Knowledge Workspace';
    }
  };

  const isHealthy = healthStatus?.status === 'healthy';
  const isMac = typeof window !== 'undefined' && window.navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  return (
    <header style={{
      height: '60px',
      backgroundColor: 'var(--surface-primary)',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 20
    }}>
      {/* Clean Breadcrumb & Page Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Forge /</span>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {getTabTitle(activeTab)}
        </h2>
      </div>

      {/* Action Bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Command Palette Trigger */}
        <button
          onClick={onOpenCommandPalette}
          style={{
            backgroundColor: 'var(--surface-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            padding: '6px 12px',
            color: 'var(--text-muted)',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            transition: 'border-color 0.15s ease'
          }}
          onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--border-hover)'}
          onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
          aria-label="Open Command Palette"
        >
          <Search size={14} color="var(--text-muted)" />
          <span className="search-text-label">Search commands...</span>
          <kbd style={{
            backgroundColor: 'var(--bg-main)',
            border: '1px solid var(--border-color)',
            borderRadius: '4px',
            padding: '1px 5px',
            fontSize: '0.675rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-secondary)'
          }}>
            {isMac ? '⌘K' : 'Ctrl+K'}
          </kbd>
        </button>

        {/* Backend Health Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 10px',
          borderRadius: '6px',
          backgroundColor: isHealthy ? 'var(--emerald-subtle)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${isHealthy ? 'var(--emerald-border)' : 'rgba(239, 68, 68, 0.3)'}`,
          fontSize: '0.725rem',
          fontFamily: 'var(--font-mono)'
        }}>
          {isHealthy ? (
            <>
              <CheckCircle2 size={12} color="var(--emerald-primary)" />
              <span style={{ color: 'var(--emerald-primary)' }}>API Online</span>
            </>
          ) : (
            <>
              <AlertCircle size={12} color="#EF4444" />
              <span style={{ color: '#EF4444' }}>API Offline</span>
            </>
          )}
        </div>

        {/* Create Concept CTA */}
        <button className="btn-emerald" onClick={onOpenCreateModal}>
          <Plus size={15} />
          <span className="btn-text-label">Forge Concept</span>
        </button>
      </div>
    </header>
  );
}
