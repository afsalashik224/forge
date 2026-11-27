import React, { useState } from 'react';
import { X, Link2, AlertCircle, Check } from 'lucide-react';
import { linkConceptToRepository, unlinkConceptFromRepository } from '../services/api';

export default function AssociateConceptModal({
  isOpen,
  onClose,
  repository,
  availableConcepts = [],
  onAssociationChanged
}) {
  const [loadingSlug, setLoadingSlug] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen || !repository) return null;

  const currentConceptSlugs = (repository.concepts || []).map(c => c.slug);

  const handleToggle = async (concept) => {
    setLoadingSlug(concept.slug);
    setError(null);
    const isLinked = currentConceptSlugs.includes(concept.slug);
    try {
      if (isLinked) {
        await unlinkConceptFromRepository(repository.slug, concept.slug);
      } else {
        await linkConceptToRepository(repository.slug, concept.slug);
      }
      onAssociationChanged();
    } catch (err) {
      setError(err.message || 'Failed to update concept association.');
    } finally {
      setLoadingSlug(null);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 50,
      backdropFilter: 'blur(3px)'
    }}>
      <div className="matte-card" style={{
        width: '100%',
        maxWidth: '500px',
        padding: '24px',
        position: 'relative',
        maxHeight: '85vh',
        overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Link2 size={20} color="var(--emerald-primary)" />
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Concept Associations
              </h2>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Repo: <code style={{ color: 'var(--emerald-primary)' }}>{repository.name}</code>
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 14px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--ruby-danger)',
            borderRadius: '6px',
            color: 'var(--ruby-danger)',
            fontSize: '0.85rem',
            marginBottom: '16px'
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          Link software engineering concepts that are implemented or applied in this repository:
        </p>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          maxHeight: '360px',
          overflowY: 'auto',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '8px',
          backgroundColor: 'var(--bg-main)'
        }}>
          {availableConcepts.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', padding: '16px' }}>
              No concepts available. Create concepts in the Forge Library first.
            </p>
          ) : (
            availableConcepts.map((concept) => {
              const isLinked = currentConceptSlugs.includes(concept.slug);
              const isActing = loadingSlug === concept.slug;
              return (
                <div
                  key={concept.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    backgroundColor: isLinked ? 'var(--surface-primary)' : 'transparent',
                    border: '1px solid',
                    borderColor: isLinked ? 'var(--emerald-primary)' : 'var(--border-color)',
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)', display: 'block' }}>
                      {concept.title}
                    </span>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {concept.slug}
                    </span>
                  </div>

                  <button
                    onClick={() => handleToggle(concept)}
                    disabled={isActing}
                    className={isLinked ? 'btn-secondary' : 'btn-primary'}
                    style={{
                      fontSize: '0.75rem',
                      padding: '4px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    {isActing ? (
                      '...'
                    ) : isLinked ? (
                      <>
                        <Check size={14} color="var(--emerald-primary)" />
                        Linked
                      </>
                    ) : (
                      'Link'
                    )}
                  </button>
                </div>
              );
            })
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
