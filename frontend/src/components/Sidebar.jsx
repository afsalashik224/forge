import React from 'react';
import { 
  LayoutDashboard, 
  BookOpen, 
  Compass, 
  TrendingUp, 
  FileCode2, 
  Zap, 
  Terminal,
  X
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, conceptCount, isMobileOpen, onCloseMobile }) {
  const navSections = [
    {
      group: "KNOWLEDGE WORKSPACE",
      items: [
        { id: 'workspace', label: 'Workspace Overview', icon: LayoutDashboard, live: true },
        { id: 'library', label: 'Forge Library', icon: BookOpen, live: true, count: conceptCount },
      ]
    },
    {
      group: "LEARNING JOURNEY & ROADMAP",
      items: [
        { id: 'compass', label: 'Forge Compass', icon: Compass, preview: 'PREVIEW' },
        { id: 'progress', label: 'Repository Progress', icon: TrendingUp, preview: 'PREVIEW' },
        { id: 'adrs', label: 'Architecture Records', icon: FileCode2, preview: 'SOON' },
      ]
    }
  ];

  const sidebarContent = (
    <aside 
      style={{
        width: '260px',
        backgroundColor: 'var(--surface-primary)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
        zIndex: 30,
        flexShrink: 0
      }}
    >
      {/* Brand Header */}
      <div style={{ padding: '20px 18px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            backgroundColor: 'var(--emerald-hover)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Zap size={18} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              FORGE
            </h1>
            <span style={{ fontSize: '0.685rem', color: 'var(--emerald-primary)', fontWeight: 500 }}>
              Engineering Knowledge Platform
            </span>
          </div>
        </div>

        {/* Close button for mobile drawer */}
        {isMobileOpen && (
          <button 
            onClick={onCloseMobile}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            aria-label="Close sidebar navigation"
          >
            <X size={20} />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <nav style={{ padding: '16px 10px', flex: 1, overflowY: 'auto' }}>
        {navSections.map((section, idx) => (
          <div key={idx} style={{ marginBottom: '24px' }}>
            <div style={{ 
              fontSize: '0.65rem', 
              fontWeight: 700, 
              color: 'var(--text-muted)', 
              letterSpacing: '0.08em', 
              padding: '0 8px 8px 8px' 
            }}>
              {section.group}
            </div>
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    if (onCloseMobile) onCloseMobile();
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: 'none',
                    backgroundColor: isActive ? 'var(--surface-secondary)' : 'transparent',
                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: isActive ? 600 : 400,
                    marginBottom: '2px',
                    transition: 'background-color 0.15s ease, color 0.15s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.backgroundColor = 'rgba(22, 32, 50, 0.6)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Icon size={16} color={isActive ? 'var(--emerald-primary)' : 'var(--text-muted)'} />
                    <span>{item.label}</span>
                  </div>

                  {item.live && item.count !== undefined && (
                    <span className="badge-emerald">{item.count}</span>
                  )}

                  {item.preview && (
                    <span className="badge-copper">{item.preview}</span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Terminal / Version Footer */}
      <div style={{
        padding: '14px 18px',
        borderTop: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-main)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '0.725rem',
        color: 'var(--text-muted)'
      }}>
        <Terminal size={14} color="var(--emerald-primary)" />
        <span className="font-mono">v0.1.0 · dev-wsl</span>
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar (hidden on mobile <=768px via media styles) */}
      <div className="desktop-sidebar-container">
        {sidebarContent}
      </div>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div 
          onClick={onCloseMobile}
          style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(11, 18, 32, 0.8)',
            zIndex: 90
          }}
        >
          <div onClick={(e) => e.stopPropagation()} style={{ width: '260px', height: '100%' }}>
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
