import React, { useState, useEffect, useRef } from 'react';
import { Search, BookOpen, Compass, TrendingUp, FileCode2, LayoutDashboard, X, ArrowRight } from 'lucide-react';

export default function CommandPalette({ isOpen, onClose, onOpen, concepts = [], setActiveTab, onSelectConcept }) {
  const [query, setQuery] = useState('');
  const inputRef = useRef(null);

  // Single global keyboard listener for Ctrl+K, Cmd+K, and Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      const isK = (e.key && e.key.toLowerCase() === 'k') || e.code === 'KeyK';
      const isCmdOrCtrl = e.ctrlKey || e.metaKey;

      if (isCmdOrCtrl && isK) {
        e.preventDefault();
        e.stopPropagation();
        if (isOpen) {
          onClose();
        } else if (onOpen) {
          onOpen();
        }
      } else if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onOpen]);

  // Automatic input focus and query reset when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const filteredConcepts = concepts.filter(c => 
    c.title.toLowerCase().includes(query.toLowerCase()) || 
    c.slug.toLowerCase().includes(query.toLowerCase()) ||
    (c.summary && c.summary.toLowerCase().includes(query.toLowerCase()))
  );

  const navCommands = [
    { id: 'workspace', label: 'Knowledge Workspace Overview', icon: LayoutDashboard },
    { id: 'library', label: 'Forge Library (Concepts Catalog)', icon: BookOpen },
    { id: 'compass', label: 'Forge Compass (Recommendations Preview)', icon: Compass },
    { id: 'progress', label: 'Repository Progress (Mastery Preview)', icon: TrendingUp },
    { id: 'adrs', label: 'Architecture Records (ADR Tracker)', icon: FileCode2 },
  ].filter(p => p.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <div 
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
    >
      <div 
        onClick={(e) => e.stopPropagation()}
        className="matte-card"
        style={{
          width: '600px',
          maxWidth: '92vw',
          backgroundColor: 'var(--surface-primary)',
          borderColor: 'var(--border-color)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
          overflow: 'hidden',
          marginTop: '-10vh'
        }}
      >
        {/* Search Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '14px 18px',
          borderBottom: '1px solid var(--border-color)'
        }}>
          <Search size={18} color="var(--emerald-primary)" />
          <input
            ref={inputRef}
            type="text"
            autoFocus
            placeholder="Type a command or search concepts..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.95rem',
              fontFamily: 'var(--font-sans)'
            }}
          />
          <button 
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            aria-label="Close Command Palette"
          >
            <X size={18} />
          </button>
        </div>

        {/* Results Body */}
        <div style={{ maxHeight: '340px', overflowY: 'auto', padding: '10px' }}>
          {/* Navigation Commands */}
          {navCommands.length > 0 && (
            <div style={{ marginBottom: '14px' }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', padding: '4px 8px' }}>
                NAVIGATION COMMANDS
              </div>
              {navCommands.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveTab(item.id);
                      onClose();
                    }}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '9px 12px',
                      borderRadius: '6px',
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      textAlign: 'left'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--surface-secondary)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Icon size={16} color="var(--emerald-primary)" />
                      <span>{item.label}</span>
                    </div>
                    <ArrowRight size={14} color="var(--text-muted)" />
                  </button>
                );
              })}
            </div>
          )}

          {/* Concepts Results */}
          {filteredConcepts.length > 0 && (
            <div>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', padding: '4px 8px' }}>
                LIVE FORGE CONCEPTS ({filteredConcepts.length})
              </div>
              {filteredConcepts.map((c) => (
                <button
                  key={c.id}
                  onClick={() => {
                    onSelectConcept(c);
                    onClose();
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '9px 12px',
                    borderRadius: '6px',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    textAlign: 'left'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--surface-secondary)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <div style={{ fontWeight: 500 }}>{c.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--emerald-primary)', fontFamily: 'var(--font-mono)' }}>
                      slug: {c.slug}
                    </div>
                  </div>
                  <span className="badge-emerald">{c.status}</span>
                </button>
              ))}
            </div>
          )}

          {navCommands.length === 0 && filteredConcepts.length === 0 && (
            <div style={{ padding: '28px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No matching commands or concepts found for "{query}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
