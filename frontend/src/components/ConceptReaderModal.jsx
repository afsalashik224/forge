import React, { useEffect, useState } from 'react';
import { X, BookOpen, Tag, Layers, AlertCircle } from 'lucide-react';
import { fetchConceptBySlug } from '../services/api';

export default function ConceptReaderModal({ concept, onClose }) {
  const [fullConcept, setFullConcept] = useState(concept);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && concept) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [concept, onClose]);

  useEffect(() => {
    if (concept?.slug) {
      setLoading(true);
      setError(null);
      fetchConceptBySlug(concept.slug)
        .then((data) => {
          if (data) setFullConcept(data);
          else setFullConcept(concept);
          setLoading(false);
        })
        .catch((err) => {
          console.warn("Reader modal error:", err);
          setError("Failed to fetch updated concept details. Displaying cached version.");
          setFullConcept(concept);
          setLoading(false);
        });
    }
  }, [concept]);

  if (!concept) return null;

  return (
    <div 
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Concept Reader"
    >
      <div 
        onClick={(e) => e.stopPropagation()}
        className="matte-card"
        style={{
          width: '700px',
          maxWidth: '92vw',
          maxHeight: '85vh',
          backgroundColor: 'var(--surface-primary)',
          borderColor: 'var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5)'
        }}
      >
        {/* Header */}
        <div style={{
          padding: '18px 22px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '30px',
              height: '30px',
              borderRadius: '6px',
              backgroundColor: 'var(--emerald-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <BookOpen size={16} color="var(--emerald-primary)" />
            </div>
            <div>
              <span className="badge-emerald" style={{ marginBottom: '2px' }}>
                {fullConcept?.status || 'DRAFT'}
              </span>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                CONCEPT ID #{fullConcept?.id}
              </div>
            </div>
          </div>

          <button 
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '4px'
            }}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '24px', flex: 1, overflowY: 'auto' }}>
          {loading ? (
            <div>
              <div className="skeleton" style={{ width: '70%', height: '32px', marginBottom: '16px' }} />
              <div className="skeleton" style={{ width: '40%', height: '18px', marginBottom: '24px' }} />
              <div className="skeleton" style={{ width: '100%', height: '120px' }} />
            </div>
          ) : (
            <>
              {error && (
                <div style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '0.8125rem',
                  color: '#F87171'
                }}>
                  <AlertCircle size={14} />
                  <span>{error}</span>
                </div>
              )}

              <h1 style={{ 
                fontSize: '1.5rem', 
                fontWeight: 700, 
                color: 'var(--text-primary)',
                marginBottom: '8px',
                lineHeight: '1.3'
              }}>
                {fullConcept?.title}
              </h1>

              {/* Metadata Bar */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                marginBottom: '20px',
                paddingBottom: '14px',
                borderBottom: '1px solid var(--border-color)',
                fontSize: '0.75rem',
                color: 'var(--text-secondary)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)', color: 'var(--emerald-primary)' }}>
                  <Tag size={13} />
                  <span>{fullConcept?.slug}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Layers size={13} color="var(--text-muted)" />
                  <span>Forge Repository</span>
                </div>
              </div>

              {/* Concept Summary Text */}
              <div style={{
                backgroundColor: 'var(--surface-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                padding: '18px',
                fontSize: '0.875rem',
                lineHeight: '1.65',
                color: 'var(--text-secondary)',
                whiteSpace: 'pre-wrap'
              }}>
                {fullConcept?.summary || 'No summary text recorded for this concept.'}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 22px',
          borderTop: '1px solid var(--border-color)',
          backgroundColor: 'var(--bg-main)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.75rem',
          color: 'var(--text-muted)'
        }}>
          <span>Forge Knowledge Reader</span>
          <button className="btn-secondary" onClick={onClose}>
            Close Reader
          </button>
        </div>
      </div>
    </div>
  );
}
