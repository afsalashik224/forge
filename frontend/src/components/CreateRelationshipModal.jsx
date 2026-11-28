import React, { useState, useEffect } from 'react';
import { X, Link2, AlertCircle, Loader2 } from 'lucide-react';
import { createRelationship } from '../services/api';

const RELATIONSHIP_OPTIONS = [
  { value: 'DEPENDS_ON', label: 'DEPENDS_ON — Source requires Target' },
  { value: 'RELATES_TO', label: 'RELATES_TO — Topically connected' },
  { value: 'IMPLEMENTS', label: 'IMPLEMENTS — Concrete realization of Target' },
  { value: 'EXTENDS', label: 'EXTENDS — Builds upon Target' },
  { value: 'ALTERNATIVE_TO', label: 'ALTERNATIVE_TO — Competing or alternate approach' },
  { value: 'SUPERSEDES', label: 'SUPERSEDES — Replaces older concept' },
  { value: 'PART_OF', label: 'PART_OF — Belongs to broader concept' },
];

export default function CreateRelationshipModal({
  isOpen,
  onClose,
  concepts = [],
  initialSourceId = '',
  onCreated,
  showToast,
}) {
  const [sourceId, setSourceId] = useState('');
  const [targetId, setTargetId] = useState('');
  const [relationshipType, setRelationshipType] = useState('RELATES_TO');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setSourceId(initialSourceId ? String(initialSourceId) : (concepts[0]?.id ? String(concepts[0].id) : ''));
      const fallbackTarget = concepts.find((c) => String(c.id) !== String(initialSourceId || concepts[0]?.id));
      setTargetId(fallbackTarget ? String(fallbackTarget.id) : '');
      setRelationshipType('RELATES_TO');
      setDescription('');
      setError(null);
    }
  }, [isOpen, initialSourceId, concepts]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!sourceId || !targetId) {
      setError('Select both a source concept and a target concept.');
      return;
    }
    if (sourceId === targetId) {
      setError('Source and target concepts must be different.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await createRelationship({
        source_concept_id: Number(sourceId),
        target_concept_id: Number(targetId),
        relationship_type: relationshipType,
        description: description.trim() || null,
      });
      if (showToast) showToast('Knowledge relationship created.', 'success');
      if (onCreated) onCreated(res.data);
      onClose();
    } catch (err) {
      const msg = err.message || 'Failed to create relationship.';
      setError(msg);
      if (showToast) showToast(msg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="modal-backdrop"
      onClick={() => !submitting && onClose()}
      role="dialog"
      aria-modal="true"
      aria-label="Link Concepts"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="matte-card"
        style={{
          width: '540px',
          maxWidth: '94vw',
          backgroundColor: 'var(--surface-primary)',
          borderColor: 'var(--border-color)',
          overflow: 'hidden',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
        }}
      >
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Link2 size={18} color="var(--emerald-primary)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Create Knowledge Relationship
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '20px' }}>
          {error && (
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '6px',
                padding: '10px 12px',
                marginBottom: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.8125rem',
                color: '#F87171',
              }}
            >
              <AlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          {concepts.length < 2 ? (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Create at least two concepts in Forge Library before linking concepts together.
            </div>
          ) : (
            <>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  SOURCE CONCEPT *
                </label>
                <select
                  className="input-matte"
                  value={sourceId}
                  onChange={(e) => setSourceId(e.target.value)}
                  disabled={submitting}
                >
                  {concepts.map((c) => (
                    <option key={c.id} value={String(c.id)}>
                      {c.title} ({c.slug})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  RELATIONSHIP TYPE *
                </label>
                <select
                  className="input-matte"
                  value={relationshipType}
                  onChange={(e) => setRelationshipType(e.target.value)}
                  disabled={submitting}
                >
                  {RELATIONSHIP_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  TARGET CONCEPT *
                </label>
                <select
                  className="input-matte"
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  disabled={submitting}
                >
                  <option value="">Select target concept…</option>
                  {concepts.map((c) => (
                    <option key={c.id} value={String(c.id)}>
                      {c.title} ({c.slug})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  RATIONALE / CONTEXT (OPTIONAL)
                </label>
                <input
                  type="text"
                  className="input-matte"
                  placeholder="e.g. Uses token buckets implemented by Redis cache"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={submitting}
                />
              </div>
            </>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-emerald"
              disabled={submitting || concepts.length < 2}
            >
              {submitting ? (
                <>
                  <Loader2 size={14} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
                  <span>Linking...</span>
                </>
              ) : (
                'Create Relationship'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
