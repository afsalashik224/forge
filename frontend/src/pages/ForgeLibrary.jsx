import React, { useState, useMemo } from 'react';
import { Search, Plus, Grid, List, BookOpen, Edit3, Trash2, Hash, Layers, X, FolderGit2, GitBranch } from 'lucide-react';
import ConceptCard from '../components/ConceptCard';
import SkeletonCard from '../components/SkeletonCard';

const CATEGORIES = [
  { value: '', label: 'All Categories' },
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

export default function ForgeLibrary({ 
  concepts, 
  workspaces = [],
  repositories = [],
  onSelectConcept, 
  onOpenCreateModal, 
  onEditConcept, 
  onDeleteConcept, 
  loading, 
  error 
}) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [workspaceFilter, setWorkspaceFilter] = useState('');
  const [repositoryFilter, setRepositoryFilter] = useState('');
  const [viewMode, setViewMode] = useState('grid');

  // Collect all unique tags across concepts
  const allTags = useMemo(() => {
    const tagSet = new Set();
    concepts.forEach((c) => {
      const tags = Array.isArray(c.tags) ? c.tags : [];
      tags.forEach((t) => tagSet.add(t));
    });
    return Array.from(tagSet).sort();
  }, [concepts]);

  const filtered = concepts.filter((c) => {
    const q = search.toLowerCase();
    const cTags = Array.isArray(c.tags) ? c.tags : [];
    const cRepos = Array.isArray(c.repositories) ? c.repositories : [];
    const cWorkspaces = Array.isArray(c.workspaces) ? c.workspaces : [];

    const matchesSearch = 
      !q ||
      c.title.toLowerCase().includes(q) ||
      c.slug.toLowerCase().includes(q) ||
      (c.summary && c.summary.toLowerCase().includes(q)) ||
      (c.content && c.content.toLowerCase().includes(q)) ||
      cTags.some((t) => t.toLowerCase().includes(q)) ||
      cRepos.some((r) => r.name.toLowerCase().includes(q)) ||
      cWorkspaces.some((w) => w.name.toLowerCase().includes(q));

    const matchesStatus = 
      statusFilter === 'ALL' || 
      (c.status && c.status.toUpperCase() === statusFilter);

    const matchesCategory = 
      !categoryFilter || 
      (c.category || '') === categoryFilter;

    const matchesTag = 
      !tagFilter || 
      cTags.includes(tagFilter);

    const matchesWorkspace =
      !workspaceFilter ||
      cWorkspaces.some((w) => w.slug === workspaceFilter);

    const matchesRepository =
      !repositoryFilter ||
      cRepos.some((r) => r.slug === repositoryFilter);

    return matchesSearch && matchesStatus && matchesCategory && matchesTag && matchesWorkspace && matchesRepository;
  });

  const hasActiveFilters = categoryFilter || tagFilter || workspaceFilter || repositoryFilter || (statusFilter !== 'ALL');

  return (
    <div style={{ padding: '28px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '14px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Forge Library
            </h1>
            <span className="badge-emerald">{concepts.length} concepts</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Live engineering concept repository powered by SQL persistence.
          </p>
        </div>

        <button className="btn-emerald" onClick={onOpenCreateModal}>
          <Plus size={15} />
          <span>Forge Concept</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="matte-card" style={{
        padding: '14px 18px',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '14px'
      }}>
        {/* Search Input */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: 'var(--bg-main)',
          border: '1px solid var(--border-color)',
          borderRadius: '6px',
          padding: '7px 12px',
          width: '320px',
          maxWidth: '100%'
        }}>
          <Search size={15} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search titles, content, tags, repos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
              width: '100%'
            }}
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0', display: 'flex' }}
              aria-label="Clear search"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: 'var(--bg-main)', padding: '3px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            {['ALL', 'DRAFT', 'PUBLISHED'].map((filter) => (
              <button
                key={filter}
                onClick={() => setStatusFilter(filter)}
                style={{
                  padding: '4px 10px',
                  borderRadius: '4px',
                  border: 'none',
                  backgroundColor: statusFilter === filter ? 'var(--surface-secondary)' : 'transparent',
                  color: statusFilter === filter ? 'var(--emerald-primary)' : 'var(--text-muted)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {filter}
              </button>
            ))}
          </div>

          {/* View Toggle */}
          <div style={{ display: 'flex', gap: '2px', backgroundColor: 'var(--bg-main)', padding: '3px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            <button
              onClick={() => setViewMode('grid')}
              style={{
                padding: '5px',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: viewMode === 'grid' ? 'var(--surface-secondary)' : 'transparent',
                color: viewMode === 'grid' ? 'var(--emerald-primary)' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
              aria-label="Grid View"
            >
              <Grid size={15} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              style={{
                padding: '5px',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: viewMode === 'list' ? 'var(--surface-secondary)' : 'transparent',
                color: viewMode === 'list' ? 'var(--emerald-primary)' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
              aria-label="List View"
            >
              <List size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Category, Tag, Workspace & Repository Filters */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '24px',
        flexWrap: 'wrap',
        alignItems: 'center',
      }}>
        {/* Category Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Layers size={14} color="var(--text-muted)" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            aria-label="Filter by category"
            style={{
              backgroundColor: 'var(--surface-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-primary)',
              padding: '5px 10px',
              fontSize: '0.8rem',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        {/* Tag Filter */}
        {allTags.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Hash size={14} color="var(--text-muted)" />
            <select
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
              aria-label="Filter by tag"
              style={{
                backgroundColor: 'var(--surface-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                padding: '5px 10px',
                fontSize: '0.8rem',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="">All Tags</option>
              {allTags.map((tag) => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </select>
          </div>
        )}

        {/* Workspace Filter */}
        {workspaces.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <FolderGit2 size={14} color="var(--text-muted)" />
            <select
              value={workspaceFilter}
              onChange={(e) => setWorkspaceFilter(e.target.value)}
              aria-label="Filter by workspace"
              style={{
                backgroundColor: 'var(--surface-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                padding: '5px 10px',
                fontSize: '0.8rem',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="">All Workspaces</option>
              {workspaces.map((ws) => (
                <option key={ws.id} value={ws.slug}>{ws.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Repository Filter */}
        {repositories.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <GitBranch size={14} color="var(--text-muted)" />
            <select
              value={repositoryFilter}
              onChange={(e) => setRepositoryFilter(e.target.value)}
              aria-label="Filter by repository"
              style={{
                backgroundColor: 'var(--surface-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                padding: '5px 10px',
                fontSize: '0.8rem',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="">All Repositories</option>
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.slug}>{repo.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Clear Filters */}
        {hasActiveFilters && (
          <button
            onClick={() => {
              setStatusFilter('ALL');
              setCategoryFilter('');
              setTagFilter('');
              setWorkspaceFilter('');
              setRepositoryFilter('');
            }}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-muted)',
              padding: '4px 10px',
              fontSize: '0.75rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <X size={12} />
            Clear filters
          </button>
        )}

        {/* Result count */}
        {(search || hasActiveFilters) && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {filtered.length} of {concepts.length} concepts
          </span>
        )}
      </div>

      {/* Content Grid / List */}
      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : error ? (
        <div className="matte-card" style={{ padding: '36px', textAlign: 'center', color: '#F87171', fontSize: '0.875rem' }}>
          {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="matte-card" style={{ padding: '48px', textAlign: 'center' }}>
          <BookOpen size={32} color="var(--text-muted)" style={{ marginBottom: '10px' }} />
          <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
            No concepts match your criteria
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '18px' }}>
            {search ? `No results for "${search}"` : 'Your Forge Library is currently empty.'}
          </p>
          <button className="btn-emerald" onClick={onOpenCreateModal}>
            <Plus size={15} />
            <span>Forge First Concept</span>
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '20px'
        }}>
          {filtered.map((c) => (
            <ConceptCard 
              key={c.id} 
              concept={c} 
              onClick={() => onSelectConcept(c)} 
              onEdit={onEditConcept}
              onDelete={onDeleteConcept}
            />
          ))}
        </div>
      ) : (
        /* List View */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {filtered.map((c) => {
            const cTags = Array.isArray(c.tags) ? c.tags : [];
            return (
              <div
                key={c.id}
                className="matte-card matte-card-interactive"
                onClick={() => onSelectConcept(c)}
                style={{
                  padding: '14px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', flexShrink: 0 }}>
                    <span className="badge-emerald">{c.status || 'DRAFT'}</span>
                    {c.category && (
                      <span className="badge-slate" style={{ fontSize: '0.625rem', textTransform: 'capitalize' }}>
                        {c.category.replace(/-/g, ' ')}
                      </span>
                    )}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {c.title}
                    </h4>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--emerald-primary)', fontFamily: 'var(--font-mono)' }}>
                        slug: {c.slug}
                      </span>
                      {cTags.slice(0, 3).map((tag) => (
                        <span key={tag} style={{ fontSize: '0.65rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
                          <Hash size={9} />{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    ID #{c.id}
                  </div>
                  {onEditConcept && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditConcept(c);
                      }}
                      style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                      title="Edit concept"
                      aria-label="Edit concept"
                    >
                      <Edit3 size={14} />
                    </button>
                  )}
                  {onDeleteConcept && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConcept(c);
                      }}
                      style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#EF4444')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                      title="Delete concept"
                      aria-label="Delete concept"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
