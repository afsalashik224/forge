import React from 'react';
import { BookOpen, ExternalLink, Tag } from 'lucide-react';

export default function ConceptCard({ concept, onClick }) {
  return (
    <div 
      className="matte-card matte-card-interactive"
      onClick={onClick}
      style={{
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        height: '100%',
        minHeight: '175px'
      }}
    >
      <div>
        {/* Header Row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span className="badge-emerald">{concept.status || 'DRAFT'}</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            #{concept.id}
          </span>
        </div>

        {/* Title */}
        <h3 style={{ 
          fontSize: '1rem', 
          fontWeight: 600, 
          color: 'var(--text-primary)', 
          marginBottom: '6px',
          lineHeight: '1.4'
        }}>
          {concept.title}
        </h3>

        {/* Slug */}
        <div style={{ 
          fontSize: '0.75rem', 
          color: 'var(--emerald-primary)', 
          fontFamily: 'var(--font-mono)',
          marginBottom: '10px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <Tag size={12} />
          <span>{concept.slug}</span>
        </div>

        {/* Summary Text */}
        <p style={{
          fontSize: '0.85rem',
          color: 'var(--text-secondary)',
          lineHeight: '1.5',
          display: '-webkit-box',
          WebkitLineClamp: 3,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden'
        }}>
          {concept.summary || 'No summary provided for this concept.'}
        </p>
      </div>

      {/* Card Footer */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        marginTop: '16px',
        paddingTop: '10px',
        borderTop: '1px solid var(--border-color)',
        fontSize: '0.75rem',
        color: 'var(--text-muted)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <BookOpen size={13} color="var(--emerald-primary)" />
          <span>Read concept</span>
        </div>
        <ExternalLink size={13} color="var(--text-muted)" />
      </div>
    </div>
  );
}
