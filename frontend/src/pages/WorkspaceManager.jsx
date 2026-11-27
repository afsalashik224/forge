import React, { useState } from 'react';
import { 
  Folder, 
  GitBranch, 
  Plus, 
  Edit3, 
  Trash2, 
  ExternalLink, 
  Link2, 
  Layers, 
  BookOpen, 
  Search
} from 'lucide-react';

export default function WorkspaceManager({
  workspaces = [],
  repositories = [],
  concepts = [],
  onOpenCreateWorkspace,
  onOpenEditWorkspace,
  onDeleteWorkspace,
  onOpenCreateRepository,
  onOpenEditRepository,
  onDeleteRepository,
  onOpenAssociateConcept,
  onSelectConcept,
  loading = false,
}) {
  const [activeSubTab, setActiveSubTab] = useState('workspaces'); // 'workspaces' | 'repositories'
  const [searchQuery, setSearchQuery] = useState('');

  const filteredWorkspaces = workspaces.filter(w => 
    w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    w.slug.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (w.description && w.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const filteredRepositories = repositories.filter(r =>
    r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.slug.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (r.primary_language && r.primary_language.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (r.description && r.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const totalLinkedConcepts = new Set(
    repositories.flatMap(r => (r.concepts || []).map(c => c.slug))
  ).size;

  return (
    <div style={{ padding: '28px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Layers size={22} color="var(--emerald-primary)" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Workspaces & Repositories
            </h1>
            <span className="badge-emerald font-mono">PHASE 2</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Organize engineering repositories into workspaces and connect them with core knowledge concepts.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {activeSubTab === 'workspaces' ? (
            <button
              onClick={onOpenCreateWorkspace}
              className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Plus size={16} />
              <span>New Workspace</span>
            </button>
          ) : (
            <button
              onClick={onOpenCreateRepository}
              className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Plus size={16} />
              <span>Add Repository</span>
            </button>
          )}
        </div>
      </div>

      {/* Top Stats Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div className="matte-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--emerald-primary)', letterSpacing: '0.04em' }}>
            ACTIVE WORKSPACES
          </span>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
            {workspaces.length}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Logical project groupings
          </p>
        </div>

        <div className="matte-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--copper-primary)', letterSpacing: '0.04em' }}>
            TRACKED REPOSITORIES
          </span>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
            {repositories.length}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Codebases under management
          </p>
        </div>

        <div className="matte-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--text-secondary)', letterSpacing: '0.04em' }}>
            ASSOCIATED CONCEPTS
          </span>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
            {totalLinkedConcepts} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>/ {concepts.length}</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Knowledge linked to implementations
          </p>
        </div>
      </div>

      {/* Search & Tabs Toolbar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', backgroundColor: 'var(--surface-primary)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <button
            onClick={() => setActiveSubTab('workspaces')}
            style={{
              padding: '6px 16px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: activeSubTab === 'workspaces' ? 'var(--emerald-hover)' : 'transparent',
              color: activeSubTab === 'workspaces' ? '#ffffff' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Folder size={15} />
            <span>Workspaces ({workspaces.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab('repositories')}
            style={{
              padding: '6px 16px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: activeSubTab === 'repositories' ? 'var(--emerald-hover)' : 'transparent',
              color: activeSubTab === 'repositories' ? '#ffffff' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <GitBranch size={15} />
            <span>Repositories ({repositories.length})</span>
          </button>
        </div>

        {/* Search Input */}
        <div style={{ position: 'relative', width: '280px' }}>
          <Search size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder={activeSubTab === 'workspaces' ? 'Search workspaces...' : 'Search repositories...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 12px 6px 32px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              backgroundColor: 'var(--surface-primary)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem'
            }}
          />
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
          Loading organization data...
        </div>
      ) : activeSubTab === 'workspaces' ? (
        /* Workspaces Grid */
        filteredWorkspaces.length === 0 ? (
          <div className="matte-card" style={{ padding: '48px', textAlign: 'center' }}>
            <Folder size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
              No workspaces found
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Create your first workspace to organize related engineering repositories.
            </p>
            <button onClick={onOpenCreateWorkspace} className="btn-primary">
              Create Workspace
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '18px' }}>
            {filteredWorkspaces.map(ws => (
              <div key={ws.id} className="matte-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Folder size={18} color="var(--emerald-primary)" />
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {ws.name}
                      </h3>
                    </div>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {ws.slug}
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button
                      onClick={() => onOpenEditWorkspace(ws)}
                      title="Edit Workspace"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '4px' }}
                    >
                      <Edit3 size={15} />
                    </button>
                    <button
                      onClick={() => onDeleteWorkspace(ws)}
                      title="Delete Workspace"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ruby-danger)', padding: '4px' }}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '16px', flex: 1 }}>
                  {ws.description || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No description provided.</span>}
                </p>

                {/* Member Repositories */}
                <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                      MEMBER REPOSITORIES ({ws.repositories ? ws.repositories.length : 0})
                    </span>
                  </div>

                  {ws.repositories && ws.repositories.length > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {ws.repositories.map(r => (
                        <span
                          key={r.id}
                          className="badge-emerald"
                          style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                        >
                          <GitBranch size={12} />
                          {r.name}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      No repositories linked yet.
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        /* Repositories Grid */
        filteredRepositories.length === 0 ? (
          <div className="matte-card" style={{ padding: '48px', textAlign: 'center' }}>
            <GitBranch size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
              No repositories found
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Add a repository to begin associating knowledge concepts with production code.
            </p>
            <button onClick={onOpenCreateRepository} className="btn-primary">
              Add Repository
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '18px' }}>
            {filteredRepositories.map(repo => (
              <div key={repo.id} className="matte-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <GitBranch size={18} color="var(--copper-primary)" />
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {repo.name}
                      </h3>
                      <span className={repo.status === 'ACTIVE' ? 'badge-emerald' : 'badge-copper'} style={{ fontSize: '0.7rem' }}>
                        {repo.status}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {repo.slug}
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button
                      onClick={() => onOpenEditRepository(repo)}
                      title="Edit Repository"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '4px' }}
                    >
                      <Edit3 size={15} />
                    </button>
                    <button
                      onClick={() => onDeleteRepository(repo)}
                      title="Delete Repository"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ruby-danger)', padding: '4px' }}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '12px', flex: 1 }}>
                  {repo.description || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No description provided.</span>}
                </p>

                {/* Metadata row */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '14px', flexWrap: 'wrap' }}>
                  {repo.primary_language && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--emerald-primary)' }} />
                      {repo.primary_language}
                    </span>
                  )}
                  {repo.vcs_url && (
                    <a
                      href={repo.vcs_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: 'var(--emerald-primary)', display: 'flex', alignItems: 'center', gap: '3px', textDecoration: 'none' }}
                    >
                      <ExternalLink size={12} />
                      VCS Source
                    </a>
                  )}
                  {repo.workspaces && repo.workspaces.length > 0 && (
                    <span style={{ color: 'var(--text-muted)' }}>
                      Workspace: {repo.workspaces.map(w => w.name).join(', ')}
                    </span>
                  )}
                </div>

                {/* Associated Concepts */}
                <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                      ASSOCIATED CONCEPTS ({repo.concepts ? repo.concepts.length : 0})
                    </span>
                    <button
                      onClick={() => onOpenAssociateConcept(repo)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--emerald-primary)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '3px'
                      }}
                    >
                      <Link2 size={13} />
                      <span>Manage</span>
                    </button>
                  </div>

                  {repo.concepts && repo.concepts.length > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {repo.concepts.map(c => (
                        <button
                          key={c.id}
                          onClick={() => onSelectConcept && onSelectConcept(c)}
                          style={{
                            background: 'none',
                            border: '1px solid var(--border-color)',
                            borderRadius: '4px',
                            padding: '2px 8px',
                            fontSize: '0.75rem',
                            color: 'var(--text-primary)',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          <BookOpen size={11} color="var(--emerald-primary)" />
                          <span>{c.title}</span>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      No concepts associated. Click Manage to link concepts.
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}
