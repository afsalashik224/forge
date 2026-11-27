import React, { useState } from 'react';
import { X, Folder, AlertCircle } from 'lucide-react';
import { createWorkspace } from '../services/api';

export default function CreateWorkspaceModal({ isOpen, onClose, onWorkspaceCreated, availableRepositories = [] }) {
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [selectedRepoIds, setSelectedRepoIds] = useState([]);
  const [isAutoSlug, setIsAutoSlug] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleNameChange = (e) => {
    const val = e.target.value;
    setName(val);
    if (isAutoSlug) {
      setSlug(val.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
    }
  };

  const toggleRepoSelection = (repoId) => {
    setSelectedRepoIds(prev =>
      prev.includes(repoId) ? prev.filter(id => id !== repoId) : [...prev, repoId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Workspace name is required.');
      return;
    }
    if (!slug.trim()) {
      setError('Slug identifier is required.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await createWorkspace({
        name: name.trim(),
        slug: slug.trim(),
        description: description.trim(),
        repository_ids: selectedRepoIds,
      });
      onWorkspaceCreated(res.data);
      onClose();
      setName('');
      setSlug('');
      setDescription('');
      setSelectedRepoIds([]);
    } catch (err) {
      setError(err.message || 'Failed to create workspace.');
    } finally {
      setLoading(false);
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
        maxWidth: '520px',
        padding: '24px',
        position: 'relative',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Folder size={20} color="var(--emerald-primary)" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Create Workspace
            </h2>
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

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
              Workspace Name *
            </label>
            <input
              type="text"
              placeholder="e.g. Core Infrastructure"
              value={name}
              onChange={handleNameChange}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-main)',
                color: 'var(--text-primary)',
                fontSize: '0.9rem'
              }}
              required
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Slug Identifier *
              </label>
              <button
                type="button"
                onClick={() => setIsAutoSlug(!isAutoSlug)}
                style={{ background: 'none', border: 'none', fontSize: '0.75rem', color: 'var(--emerald-primary)', cursor: 'pointer' }}
              >
                {isAutoSlug ? 'Custom Slug' : 'Auto-Generate'}
              </button>
            </div>
            <input
              type="text"
              value={slug}
              onChange={(e) => {
                setIsAutoSlug(false);
                setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-'));
              }}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-main)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem'
              }}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
              Description
            </label>
            <textarea
              rows={3}
              placeholder="Workspace purpose and engineering scope..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-main)',
                color: 'var(--text-primary)',
                fontSize: '0.875rem',
                resize: 'vertical'
              }}
            />
          </div>

          {availableRepositories.length > 0 && (
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Associate Repositories
              </label>
              <div style={{
                maxHeight: '120px',
                overflowY: 'auto',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                padding: '6px',
                backgroundColor: 'var(--bg-main)',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px'
              }}>
                {availableRepositories.map(repo => (
                  <label key={repo.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.825rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={selectedRepoIds.includes(repo.id)}
                      onChange={() => toggleRepoSelection(repo.id)}
                    />
                    <span>{repo.name}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({repo.primary_language || 'No lang'})</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
            >
              {loading ? 'Creating...' : 'Create Workspace'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
