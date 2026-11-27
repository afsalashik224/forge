import React, { useState } from 'react';
import { Edit3, Eye, Columns } from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';

export default function MarkdownEditor({ value, onChange, disabled, placeholder }) {
  const [mode, setMode] = useState('split');

  const modes = [
    { key: 'edit', icon: Edit3, label: 'Edit' },
    { key: 'split', icon: Columns, label: 'Split' },
    { key: 'preview', icon: Eye, label: 'Preview' },
  ];

  return (
    <div style={{
      border: '1px solid var(--border-color)',
      borderRadius: '6px',
      overflow: 'hidden',
      backgroundColor: 'var(--surface-secondary)',
    }}>
      {/* Toolbar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '6px 10px',
        borderBottom: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-main)',
      }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Markdown Content
        </span>
        <div style={{ display: 'flex', gap: '2px', backgroundColor: 'var(--surface-secondary)', padding: '2px', borderRadius: '5px', border: '1px solid var(--border-color)' }}>
          {modes.map(({ key, icon: Icon, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => setMode(key)}
              style={{
                padding: '3px 8px',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: mode === key ? 'var(--bg-main)' : 'transparent',
                color: mode === key ? 'var(--emerald-primary)' : 'var(--text-muted)',
                fontSize: '0.7rem',
                fontWeight: 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
              title={label}
            >
              <Icon size={12} />
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Editor / Preview */}
      <div style={{
        display: 'flex',
        minHeight: '280px',
        maxHeight: '400px',
      }}>
        {/* Editor Pane */}
        {(mode === 'edit' || mode === 'split') && (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            borderRight: mode === 'split' ? '1px solid var(--border-color)' : 'none',
          }}>
            <textarea
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              disabled={disabled}
              placeholder={placeholder || "Write your knowledge content in Markdown...\n\n## Example\n- Use **bold** and *italic*\n- Create `code blocks`\n- Add tables and task lists"}
              style={{
                flex: 1,
                width: '100%',
                padding: '14px',
                backgroundColor: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.825rem',
                lineHeight: '1.6',
                resize: 'none',
                minHeight: '280px',
              }}
            />
          </div>
        )}

        {/* Preview Pane */}
        {(mode === 'preview' || mode === 'split') && (
          <div style={{
            flex: 1,
            padding: '14px',
            overflowY: 'auto',
            maxHeight: '400px',
          }}>
            {value ? (
              <MarkdownRenderer content={value} />
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>
                Preview will appear here as you type…
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
