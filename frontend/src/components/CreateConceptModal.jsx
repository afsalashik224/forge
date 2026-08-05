import React, { useState, useEffect } from 'react';
import { X, Plus, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import { createConcept } from '../services/api';

export default function CreateConceptModal({ isOpen, onClose, onCreated, showToast }) {
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [summary, setSummary] = useState('');
  const [autoSlug, setAutoSlug] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !submitting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, submitting, onClose]);

  if (!isOpen) return null;

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
      await createConcept({
        title: title.trim(),
        slug: slug.trim(),
        summary: summary.trim()
      });
      setTitle('');
      setSlug('');
      setSummary('');
      setSubmitting(false);
      
      if (showToast) showToast(`Concept "${title.trim()}" forged successfully!`, 'success');
      onCreated();
      onClose();
    } catch (err) {
      const errorMsg = err.message || "Failed to forge new concept.";
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
      aria-label="Forge New Concept"
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
              <Plus size={16} color="#ffffff" />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Forge New Concept
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Add an engineering concept to your repository knowledge base.
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
                  <span>Forging...</span>
                </>
              ) : (
                'Save & Publish Concept'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
