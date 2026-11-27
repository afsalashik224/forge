import React, { useState, useEffect } from 'react';
import { X, Edit3, Sparkles, AlertCircle, Loader2, GitBranch } from 'lucide-react';
import { fetchConceptBySlug, updateConcept } from '../services/api';
import MarkdownEditor from './MarkdownEditor';
import TagInput from './TagInput';

const CATEGORIES = [
  { value: '', label: 'No category' },
  { value: 'architecture', label: 'Architecture' },
  { value: 'design-patterns', label: 'Design Patterns' },
  { value: 'devops', label: 'DevOps' },
  { value: 'security', label: 'Security' },
  { value: 'performance', label: 'Performance' },
  { value: 'testing', label: 'Testing' },
  { value: 'languages', label: 'Languages' },
  { value: 'frameworks', label: 'Frameworks' },
  { value: 'infrastructure', label: 'Infrastructure' },
  { value: 'data', label: 'Data' },
  { value: 'networking', label: 'Networking' },
  { value: 'other', label: 'Other' },
];

export default function EditConceptModal({
  isOpen,
  concept,
  onClose,
  onUpdated,
  showToast,
  availableRepositories = [],
}) {
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState([]);
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('DRAFT');
  const [selectedRepoIds, setSelectedRepoIds] = useState([]);
  const [autoSlug, setAutoSlug] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isCurrent = true;
    if (isOpen && concept) {
      setTitle(concept.title || '');
      setSlug(concept.slug || '');
      setSummary(concept.summary || '');
      setContent(concept.content || '');
      setTags(Array.isArray(concept.tags) ? concept.tags : []);
      setCategory(concept.category || '');
      setStatus(concept.status || 'DRAFT');
      setSelectedRepoIds(
        Array.isArray(concept.repositories) ? concept.repositories.map((r) => r.id) : []
      );
      setAutoSlug(false);
      setError(null);

      // Hydrate latest details from API so markdown content and links are never stale
      if (concept.slug) {
        setLoadingDetails(true);
        fetchConceptBySlug(concept.slug)
          .then((full) => {
            if (!isCurrent || !full) return;
            setTitle(full.title || '');
            setSlug(full.slug || '');
            setSummary(full.summary || '');
            setContent(full.content || '');
            setTags(Array.isArray(full.tags) ? full.tags : []);
            setCategory(full.category || '');
            setStatus(full.status || 'DRAFT');
            setSelectedRepoIds(
              Array.isArray(full.repositories) ? full.repositories.map((r) => r.id) : []
            );
          })
          .catch(() => {
            // Keep cached props on transient failure
          })
          .finally(() => {
            if (isCurrent) setLoadingDetails(false);
          });
      }
    }
    return () => {
      isCurrent = false;
    };
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

  const toggleRepoSelection = (repoId) => {
    setSelectedRepoIds((prev) =>
      prev.includes(repoId) ? prev.filter((id) => id !== repoId) : [...prev, repoId]
    );
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
        status: status,
        content: content,
        tags: tags,
        category: category,
        repository_ids: selectedRepoIds,
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
          width: '900px',
          maxWidth: '95vw',
          maxHeight: '90vh',
          backgroundColor: 'var(--surface-primary)',
          borderColor: 'var(--border-color)',
          overflow: 'hidden',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Modal Header */}
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
                Modify content, metadata, tags, repo associations, and lifecycle state.
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

        {/* Form Body - Scrollable */}
        <form onSubmit={handleSubmit} style={{ padding: '22px', overflowY: 'auto', flex: 1 }}>
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

          {loadingDetails ? (
            <div style={{ padding: '28px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Loading full concept content...
            </div>
          ) : (
            <>
              {/* Title and Slug Row */}
              <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
                <div style={{ flex: 1 }}>
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

                <div style={{ flex: 1 }}>
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
                      <span>{autoSlug ? 'Auto' : 'Manual'}</span>
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
              </div>

              {/* Category, Status, Summary Row */}
              <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
                <div style={{ width: '170px', flexShrink: 0 }}>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    CATEGORY
                  </label>
                  <select
                    className="input-matte"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    disabled={submitting}
                    style={{ width: '100%', cursor: 'pointer' }}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>

                <div style={{ width: '140px', flexShrink: 0 }}>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    STATUS
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

                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    SUMMARY
                  </label>
                  <input
                    type="text"
                    className="input-matte"
                    placeholder="Brief one-line description"
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    disabled={submitting}
                  />
                </div>
              </div>

              {/* Tags Input */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  TAGS
                </label>
                <TagInput
                  tags={tags}
                  onChange={setTags}
                  disabled={submitting}
                  placeholder="Type a tag and press Enter…"
                />
              </div>

              {/* Associate Repositories */}
              {availableRepositories.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    <GitBranch size={13} color="var(--emerald-primary)" />
                    <span>ASSOCIATE REPOSITORIES</span>
                  </label>
                  <div style={{
                    maxHeight: '110px',
                    overflowY: 'auto',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    padding: '8px 10px',
                    backgroundColor: 'var(--bg-main)',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '8px 16px'
                  }}>
                    {availableRepositories.map((repo) => (
                      <label key={repo.id} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={selectedRepoIds.includes(repo.id)}
                          onChange={() => toggleRepoSelection(repo.id)}
                          disabled={submitting}
                        />
                        <span>{repo.name}</span>
                        {repo.workspaces && repo.workspaces.length > 0 && (
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            ({repo.workspaces.map((w) => w.name).join(', ')})
                          </span>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Markdown Editor */}
              <div style={{ marginBottom: '22px' }}>
                <MarkdownEditor
                  value={content}
                  onChange={setContent}
                  disabled={submitting}
                />
              </div>
            </>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn-emerald" disabled={submitting || loadingDetails}>
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
