import React, { useState, useEffect } from 'react';
import { X, Edit3, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import { updateConcept } from '../services/api';

export default function EditConceptModal({ isOpen, concept, onClose, onUpdated, showToast }) {
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [summary, setSummary] = useState('');
  const [status, setStatus] = useState('DRAFT');
  const [autoSlug, setAutoSlug] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (concept) {
      setTitle(concept.title || '');
      setSlug(concept.slug || '');
      setSummary(concept.summary || '');
      setStatus(concept.status || 'DRAFT');
      setAutoSlug(false);
      setError(null);
    }
  }, [concept, isOpen]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !submitting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, submitting, onClose]);

  if (!isOpen || !concept) return null;

  const handleTitleChange = (e) => {
    const val = e.target.value;
    setTitle(val);
    if (autoSlug) {
      const generated = val
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-');
      setSlug(generated);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!title.trim() || !slug.trim()) {
      setError("Title and slug are required fields.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await updateConcept(concept.slug, {
        title: title.trim(),
        slug: slug.trim(),
        summary: summary.trim(),
        status: status
      });

      setSubmitting(false);
      if (showToast) {
        showToast(`Concept "${title.trim()}" updated successfully!`, 'success');
      }
      if (onUpdated) {
        onUpdated(response.data);
      }
      onClose();
    } catch (err) {
      const errorMsg = err.message || "Failed to update concept.";
      setError(errorMsg);
      if (showToast) showToast(errorMsg, 'error');
      setSubmitting(false);
    }
  };

  return (
    <div 
      className="modal-backdrop"
      onClick={() => {
        if (!submitting) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Edit Concept"
    >
      <div 
        onClick={(e) => e.stopPropagation()}
        className="matte-card"
        style={{
          width: '580px',
          maxWidth: '92vw',
          backgroundColor: 'var(--surface-primary)',
          borderColor: 'var(--border-color)',
          overflow: 'hidden',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)'
        }}
      >
        {/* Modal Header */}
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
              backgroundColor: 'var(--emerald-hover)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Edit3 size={16} color="#ffffff" />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Edit Concept #{concept.id}
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Modify metadata, summary, and lifecycle state.
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            disabled={submitting}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '22px' }}>
          {error && (
            <div style={{
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              padding: '10px 14px',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.8125rem',
              color: '#F87171'
            }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Title Input */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              CONCEPT TITLE *
            </label>
            <input
              type="text"
              className="input-matte"
              placeholder="e.g. Distributed Caching Strategies"
              value={title}
              onChange={handleTitleChange}
              required
              disabled={submitting}
            />
          </div>

          {/* Slug Input */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                URL SLUG *
              </label>
              <button
                type="button"
                onClick={() => setAutoSlug(!autoSlug)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: autoSlug ? 'var(--emerald-primary)' : 'var(--text-muted)',
                  fontSize: '0.725rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Sparkles size={12} />
                <span>{autoSlug ? 'Auto-generating' : 'Manual mode'}</span>
              </button>
            </div>
            <input
              type="text"
              className="input-matte font-mono"
              placeholder="e.g. distributed-caching-strategies"
              value={slug}
              onChange={(e) => {
                setAutoSlug(false);
                setSlug(e.target.value);
              }}
              required
              disabled={submitting}
            />
          </div>

          {/* Status Select */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              LIFECYCLE STATUS
            </label>
            <select
              className="input-matte"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              disabled={submitting}
              style={{ width: '100%', cursor: 'pointer' }}
            >
              <option value="DRAFT">DRAFT</option>
              <option value="PUBLISHED">PUBLISHED</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>
          </div>

          {/* Summary Textarea */}
          <div style={{ marginBottom: '22px' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              CONCEPT SUMMARY / UNDERSTANDING
            </label>
            <textarea
              className="input-matte"
              rows={4}
              placeholder="Explain the architectural pattern, tradeoffs, or key engineering understanding..."
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              disabled={submitting}
            />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn-emerald" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 size={14} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
                  <span>Updating...</span>
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
