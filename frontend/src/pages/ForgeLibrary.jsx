import React, { useState } from 'react';
import { Search, Plus, Grid, List, BookOpen } from 'lucide-react';
import ConceptCard from '../components/ConceptCard';
import SkeletonCard from '../components/SkeletonCard';

export default function ForgeLibrary({ concepts, onSelectConcept, onOpenCreateModal, loading, error }) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [viewMode, setViewMode] = useState('grid');

  const filtered = concepts.filter((c) => {
    const matchesSearch = 
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.slug.toLowerCase().includes(search.toLowerCase()) ||
      (c.summary && c.summary.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = 
      statusFilter === 'ALL' || 
      (c.status && c.status.toUpperCase() === statusFilter);

    return matchesSearch && matchesStatus;
  });

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
        marginBottom: '24px',
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
          width: '300px',
          maxWidth: '100%'
        }}>
          <Search size={15} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search titles, slugs, or summaries..."
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
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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
            <ConceptCard key={c.id} concept={c} onClick={() => onSelectConcept(c)} />
          ))}
        </div>
      ) : (
        /* List View */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {filtered.map((c) => (
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <span className="badge-emerald">{c.status || 'DRAFT'}</span>
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {c.title}
                  </h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--emerald-primary)', fontFamily: 'var(--font-mono)' }}>
                    slug: {c.slug}
                  </span>
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                ID #{c.id}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
