import React, { useEffect, useState } from 'react';
import { X, BookOpen, Tag, Layers, AlertCircle, Edit3, Trash2, GitBranch, Hash, FolderGit2 } from 'lucide-react';
import { fetchConceptBySlug } from '../services/api';
import MarkdownRenderer from './MarkdownRenderer';

export default function ConceptReaderModal({ concept, onClose, onEdit, onDelete }) {
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
    let isCurrent = true;
    if (concept?.slug) {
      setLoading(true);
      setError(null);
      setFullConcept(concept);
      fetchConceptBySlug(concept.slug)
        .then((data) => {
          if (!isCurrent) return;
          if (data) setFullConcept(data);
          else setFullConcept(concept);
          setLoading(false);
        })
        .catch((err) => {
          if (!isCurrent) return;
          console.warn("Reader modal error:", err);
          setError("Failed to fetch updated concept details. Displaying cached version.");
          setFullConcept(concept);
          setLoading(false);
        });
    } else {
      setFullConcept(null);
    }
    return () => {
      isCurrent = false;
    };
  }, [concept]);

  if (!concept) return null;

  const conceptTags = Array.isArray(fullConcept?.tags) ? fullConcept.tags : [];
  const conceptCategory = fullConcept?.category || '';

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
          width: '800px',
          maxWidth: '95vw',
          maxHeight: '90vh',
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
          justifyContent: 'space-between',
          flexShrink: 0,
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
                marginBottom: '16px',
                paddingBottom: '14px',
                borderBottom: '1px solid var(--border-color)',
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
                flexWrap: 'wrap',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)', color: 'var(--emerald-primary)' }}>
                  <Tag size={13} />
                  <span>{fullConcept?.slug}</span>
                </div>
                {conceptCategory && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Layers size={13} color="var(--text-muted)" />
                    <span style={{ textTransform: 'capitalize' }}>{conceptCategory.replace(/-/g, ' ')}</span>
                  </div>
                )}
              </div>

              {/* Tags */}
              {conceptTags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
                  {conceptTags.map((tag) => (
                    <span
                      key={tag}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '3px',
                        backgroundColor: 'var(--surface-secondary)',
                        color: 'var(--text-secondary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '4px',
                        padding: '2px 8px',
                        fontSize: '0.725rem',
                        fontWeight: 500,
                      }}
                    >
                      <Hash size={10} />
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Summary */}
              {fullConcept?.summary && (
                <div style={{
                  backgroundColor: 'var(--surface-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  padding: '14px 18px',
                  fontSize: '0.875rem',
                  lineHeight: '1.65',
                  color: 'var(--text-secondary)',
                  marginBottom: '16px',
                  fontStyle: 'italic',
                }}>
                  {fullConcept.summary}
                </div>
              )}

              {/* Markdown Content */}
              {fullConcept?.content ? (
                <div style={{
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  lineHeight: '1.65',
                  color: 'var(--text-secondary)',
                  marginBottom: '16px',
                }}>
                  <MarkdownRenderer content={fullConcept.content} />
                </div>
              ) : !fullConcept?.summary ? (
                <div style={{
                  backgroundColor: 'var(--surface-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  padding: '18px',
                  fontSize: '0.875rem',
                  color: 'var(--text-muted)',
                  fontStyle: 'italic',
                }}>
                  No content recorded for this concept.
                </div>
              ) : null}

              {/* Associated Workspaces & Repositories */}
              {((fullConcept?.workspaces && fullConcept.workspaces.length > 0) ||
                (fullConcept?.repositories && fullConcept.repositories.length > 0)) && (
                <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border-color)' }}>
                  {fullConcept?.workspaces && fullConcept.workspaces.length > 0 && (
                    <div style={{ marginBottom: '10px' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                        ASSOCIATED WORKSPACES ({fullConcept.workspaces.length})
                      </span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {fullConcept.workspaces.map(ws => (
                          <span
                            key={ws.id}
                            className="badge-copper"
                            style={{ fontSize: '0.725rem', display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 8px' }}
                          >
                            <FolderGit2 size={12} />
                            <span>{ws.name}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {fullConcept?.repositories && fullConcept.repositories.length > 0 && (
                    <div>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                        ASSOCIATED REPOSITORIES ({fullConcept.repositories.length})
                      </span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {fullConcept.repositories.map(repo => (
                          <span
                            key={repo.id}
                            className="badge-emerald"
                            style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '5px', padding: '4px 8px' }}
                          >
                            <GitBranch size={12} />
                            <span>{repo.name}</span>
                            {repo.primary_language && (
                              <span style={{ opacity: 0.8, fontSize: '0.7rem' }}>({repo.primary_language})</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
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
          color: 'var(--text-muted)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {onDelete && (
              <button
                type="button"
                onClick={() => onDelete(fullConcept || concept)}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  color: '#F87171',
                  borderRadius: '6px',
                  padding: '6px 12px',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease'
                }}
                title="Delete concept"
              >
                <Trash2 size={13} />
                <span>Delete</span>
              </button>
            )}
            {onEdit && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => onEdit(fullConcept || concept)}
                style={{ padding: '6px 12px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                title="Edit concept"
              >
                <Edit3 size={13} />
                <span>Edit</span>
              </button>
            )}
          </div>
          <button className="btn-secondary" onClick={onClose}>
            Close Reader
          </button>
        </div>
      </div>
    </div>
  );
}
