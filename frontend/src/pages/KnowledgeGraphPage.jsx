import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  Network,
  Search,
  Link2,
  RefreshCw,
  Trash2,
  BookOpen,
  GitBranch,
  FolderGit2,
  Compass,
  Edit3,
  X,
  Crosshair,
  Eye,
  EyeOff,
} from 'lucide-react';
import KnowledgeGraphCanvas from '../components/KnowledgeGraphCanvas';
import CreateRelationshipModal from '../components/CreateRelationshipModal';
import {
  fetchKnowledgeGraph,
  deleteRelationship,
  unlinkConceptFromRepository,
  unlinkRepositoryFromWorkspace,
} from '../services/api';

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

export default function KnowledgeGraphPage({
  concepts = [],
  workspaces = [],
  refreshKey = 0,
  onGraphMutated,
  onSelectConceptBySlug,
  onEditConceptBySlug,
  onNavigateToWorkspace,
  onNavigateToRepository,
  onFilterLibraryByRepo,
  showToast,
}) {
  const [graphData, setGraphData] = useState({
    nodes: [],
    edges: [],
    stats: { total_nodes: 0, total_edges: 0, counts_by_entity: {}, counts_by_relationship: {} },
    all_edge_types: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Exploration State
  const [search, setSearch] = useState('');
  const [includeNeighbors, setIncludeNeighbors] = useState(true);
  const [entityTypes, setEntityTypes] = useState(['workspace', 'repository', 'concept']);
  const [relTypeFilter, setRelTypeFilter] = useState('');
  const [workspaceFilter, setWorkspaceFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [focusNodeId, setFocusNodeId] = useState('');
  const [focusDepth, setFocusDepth] = useState(1);
  const [showEdgeLabels, setShowEdgeLabels] = useState(true);

  const [selectedNode, setSelectedNode] = useState(null);
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchKnowledgeGraph({
        entity_types: entityTypes,
        relationship_types: relTypeFilter ? [relTypeFilter] : undefined,
        workspace: workspaceFilter || undefined,
        category: categoryFilter || undefined,
        q: search.trim() || undefined,
        include_neighbors: search.trim() ? includeNeighbors : false,
        focus: focusNodeId || undefined,
        depth: focusNodeId ? focusDepth : undefined,
      });
      setGraphData(data);
      setSelectedNode((prev) => {
        if (!prev) return null;
        return (data.nodes || []).find((n) => n.id === prev.id) || null;
      });
    } catch (err) {
      setError(err.message || 'Failed to load knowledge graph.');
    } finally {
      setLoading(false);
    }
  }, [
    entityTypes,
    relTypeFilter,
    workspaceFilter,
    categoryFilter,
    search,
    includeNeighbors,
    focusNodeId,
    focusDepth,
  ]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph, refreshKey]);

  const toggleEntityType = (etype) => {
    setEntityTypes((prev) => {
      if (prev.includes(etype)) {
        if (prev.length === 1) return prev; // keep at least one active
        return prev.filter((t) => t !== etype);
      }
      return [...prev, etype];
    });
  };

  const resetFilters = () => {
    setSearch('');
    setEntityTypes(['workspace', 'repository', 'concept']);
    setRelTypeFilter('');
    setWorkspaceFilter('');
    setCategoryFilter('');
    setFocusNodeId('');
    setFocusDepth(1);
  };

  const nodes = useMemo(() => graphData.nodes || [], [graphData.nodes]);
  const edges = useMemo(() => graphData.edges || [], [graphData.edges]);
  const nodeMap = useMemo(() => {
    const map = {};
    nodes.forEach((n) => {
      map[n.id] = n;
    });
    return map;
  }, [nodes]);

  const selectedConnections = useMemo(() => {
    if (!selectedNode) return { outgoing: [], incoming: [] };
    const outgoing = [];
    const incoming = [];
    edges.forEach((e) => {
      if (e.source === selectedNode.id && nodeMap[e.target]) {
        outgoing.push({ edge: e, neighbor: nodeMap[e.target] });
      }
      if (e.target === selectedNode.id && nodeMap[e.source]) {
        incoming.push({ edge: e, neighbor: nodeMap[e.source] });
      }
    });
    return { outgoing, incoming };
  }, [selectedNode, edges, nodeMap]);

  const handleDeleteEdge = async (edge) => {
    try {
      if (edge.origin === 'explicit' && edge.relationship_id) {
        await deleteRelationship(edge.relationship_id);
        if (showToast) showToast('Relationship removed.', 'success');
      } else if (edge.relationship_type === 'DOCUMENTS_CONCEPT') {
        const repo = nodeMap[edge.source];
        const concept = nodeMap[edge.target];
        if (repo && concept) {
          await unlinkConceptFromRepository(repo.slug, concept.slug);
          if (showToast) showToast('Concept unlinked from repository.', 'success');
        }
      } else if (edge.relationship_type === 'CONTAINS_REPO') {
        const ws = nodeMap[edge.source];
        const repo = nodeMap[edge.target];
        if (ws && repo) {
          await unlinkRepositoryFromWorkspace(ws.slug, repo.slug);
          if (showToast) showToast('Repository removed from workspace.', 'success');
        }
      }
      if (onGraphMutated) onGraphMutated();
      await loadGraph();
    } catch (err) {
      if (showToast) showToast(err.message || 'Failed to remove relationship.', 'error');
    }
  };

  const handleNavigateNode = (node) => {
    if (!node) return;
    if (node.entity_type === 'concept' && onSelectConceptBySlug) {
      onSelectConceptBySlug(node.slug);
    } else if (node.entity_type === 'repository' && onNavigateToRepository) {
      onNavigateToRepository(node.slug);
    } else if (node.entity_type === 'workspace' && onNavigateToWorkspace) {
      onNavigateToWorkspace(node.slug);
    }
  };

  const counts = graphData.stats?.counts_by_entity || {};

  return (
    <div style={{ padding: '24px 28px', maxWidth: '1320px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Network size={22} color="var(--emerald-primary)" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Knowledge Graph
            </h1>
            <span className="badge-emerald">{graphData.stats?.total_nodes || 0} nodes</span>
            <span className="badge-slate">{graphData.stats?.total_edges || 0} edges</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Explore real engineering relationships across Workspaces, Repositories, and Concepts.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setShowEdgeLabels((v) => !v)}
            style={{ padding: '7px 12px', fontSize: '0.8rem' }}
          >
            {showEdgeLabels ? <EyeOff size={14} /> : <Eye size={14} />}
            <span>{showEdgeLabels ? 'Hide Labels' : 'Show Labels'}</span>
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={loadGraph}
            style={{ padding: '7px 12px', fontSize: '0.8rem' }}
          >
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
          <button
            type="button"
            className="btn-emerald"
            onClick={() => setIsLinkModalOpen(true)}
          >
            <Link2 size={15} />
            <span>Link Concepts</span>
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="matte-card" style={{ padding: '14px 16px', marginBottom: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          {/* Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'var(--bg-main)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '6px 10px',
              width: '260px',
            }}>
              <Search size={14} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search nodes, tags, slugs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ background: 'transparent', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: '0.825rem', width: '100%' }}
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch('')}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex' }}
                  aria-label="Clear search"
                >
                  <X size={13} />
                </button>
              )}
            </div>

            {search && (
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={includeNeighbors}
                  onChange={(e) => setIncludeNeighbors(e.target.checked)}
                />
                <span>Include neighbors</span>
              </label>
            )}
          </div>

          {/* Entity Type Filter Toggles */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { id: 'workspace', label: `Workspaces (${counts.workspace || 0})`, color: '#F59E0B' },
              { id: 'repository', label: `Repositories (${counts.repository || 0})`, color: '#38BDF8' },
              { id: 'concept', label: `Concepts (${counts.concept || 0})`, color: '#10B981' },
            ].map((item) => {
              const active = entityTypes.includes(item.id);
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => toggleEntityType(item.id)}
                  style={{
                    padding: '5px 10px',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    border: `1px solid ${active ? item.color : 'var(--border-color)'}`,
                    backgroundColor: active ? 'var(--surface-secondary)' : 'transparent',
                    color: active ? item.color : 'var(--text-muted)',
                  }}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Secondary Filter Row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <select
            value={relTypeFilter}
            onChange={(e) => setRelTypeFilter(e.target.value)}
            aria-label="Filter by relationship type"
            style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', padding: '5px 10px', fontSize: '0.775rem' }}
          >
            <option value="">All Relationship Types</option>
            {(graphData.all_edge_types || []).map((rt) => (
              <option key={rt} value={rt}>{rt}</option>
            ))}
          </select>

          {workspaces.length > 0 && (
            <select
              value={workspaceFilter}
              onChange={(e) => setWorkspaceFilter(e.target.value)}
              aria-label="Filter by workspace"
              style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', padding: '5px 10px', fontSize: '0.775rem' }}
            >
              <option value="">All Workspaces</option>
              {workspaces.map((ws) => (
                <option key={ws.id} value={ws.slug}>{ws.name}</option>
              ))}
            </select>
          )}

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            aria-label="Filter by concept category"
            style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', padding: '5px 10px', fontSize: '0.775rem' }}
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>

          {focusNodeId && (
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'var(--emerald-subtle)', border: '1px solid var(--emerald-border)', borderRadius: '6px', padding: '4px 10px', fontSize: '0.75rem', color: 'var(--emerald-primary)' }}>
              <Crosshair size={13} />
              <span>Focus: {nodeMap[focusNodeId]?.label || focusNodeId}</span>
              <select
                value={focusDepth}
                onChange={(e) => setFocusDepth(Number(e.target.value))}
                style={{ backgroundColor: 'var(--bg-main)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '4px', padding: '1px 5px', fontSize: '0.725rem' }}
              >
                <option value={1}>1-hop</option>
                <option value={2}>2-hop</option>
                <option value={3}>3-hop</option>
              </select>
              <button
                type="button"
                onClick={() => setFocusNodeId('')}
                style={{ background: 'transparent', border: 'none', color: 'var(--emerald-primary)', cursor: 'pointer', display: 'flex' }}
                aria-label="Clear focus"
              >
                <X size={13} />
              </button>
            </div>
          )}

          {(search || relTypeFilter || workspaceFilter || categoryFilter || focusNodeId || entityTypes.length < 3) && (
            <button
              type="button"
              onClick={resetFilters}
              style={{ background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-muted)', padding: '4px 10px', fontSize: '0.75rem', cursor: 'pointer' }}
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Main Layout: Canvas + Inspector Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '18px', alignItems: 'start' }}>
        {/* Graph Canvas Pane */}
        <div className="matte-card" style={{ padding: '14px' }}>
          {loading ? (
            <div style={{ height: '540px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Building graph from stored records...
            </div>
          ) : error ? (
            <div style={{ height: '540px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#F87171', fontSize: '0.9rem' }}>
              {error}
            </div>
          ) : nodes.length === 0 ? (
            <div style={{ height: '540px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', padding: '24px' }}>
              <Network size={34} style={{ marginBottom: '10px', opacity: 0.7 }} />
              <h3 style={{ color: 'var(--text-primary)', marginBottom: '6px' }}>No matching graph nodes</h3>
              <p style={{ fontSize: '0.85rem', maxWidth: '420px', marginBottom: '14px' }}>
                Only real Workspaces, Repositories, and Concepts from SQLite are displayed here. Adjust your filters or add new entities.
              </p>
              <button type="button" className="btn-secondary" onClick={resetFilters}>
                Reset Filters
              </button>
            </div>
          ) : (
            <KnowledgeGraphCanvas
              nodes={nodes}
              edges={edges}
              selectedNodeId={selectedNode?.id || null}
              onSelectNode={setSelectedNode}
              onDoubleClickNode={handleNavigateNode}
              height={540}
              width={960}
              showEdgeLabels={showEdgeLabels}
              interactive={true}
            />
          )}

          {/* Legend */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border-color)', fontSize: '0.725rem', color: 'var(--text-muted)', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: '#C8872F' }} />
                Workspace
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: '#38BDF8' }} />
                Repository
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10B981' }} />
                Concept
              </span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>--- structural link · ─── explicit relationship</span>
            </div>
            <span>Drag nodes to arrange · Double-click to open</span>
          </div>
        </div>

        {/* Side Inspector Panel */}
        <div className="matte-card" style={{ padding: '18px', minHeight: '586px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {selectedNode ? (
            <>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                    <span className={selectedNode.entity_type === 'workspace' ? 'badge-copper' : 'badge-emerald'}>
                      {selectedNode.entity_type.toUpperCase()}
                    </span>
                    {selectedNode.status && <span className="badge-slate">{selectedNode.status}</span>}
                    {selectedNode.primary_language && <span className="badge-slate">{selectedNode.primary_language}</span>}
                  </div>
                  <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {selectedNode.label}
                  </h2>
                  <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--emerald-primary)', marginTop: '2px' }}>
                    {selectedNode.slug}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedNode(null)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  aria-label="Deselect node"
                >
                  <X size={16} />
                </button>
              </div>

              {selectedNode.description && (
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  {selectedNode.description}
                </p>
              )}

              {selectedNode.tags && selectedNode.tags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {selectedNode.tags.map((t) => (
                    <span key={t} className="badge-slate" style={{ fontSize: '0.675rem' }}>#{t}</span>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <button
                  type="button"
                  className="btn-emerald"
                  onClick={() => handleNavigateNode(selectedNode)}
                  style={{ justifyContent: 'center' }}
                >
                  {selectedNode.entity_type === 'concept' && <BookOpen size={14} />}
                  {selectedNode.entity_type === 'repository' && <GitBranch size={14} />}
                  {selectedNode.entity_type === 'workspace' && <FolderGit2 size={14} />}
                  <span>
                    {selectedNode.entity_type === 'concept'
                      ? 'Open Concept Reader'
                      : selectedNode.entity_type === 'repository'
                      ? 'Open Repository Details'
                      : 'Open Workspace Details'}
                  </span>
                </button>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setFocusNodeId(focusNodeId === selectedNode.id ? '' : selectedNode.id)}
                    style={{ flex: 1, justifyContent: 'center', fontSize: '0.775rem', padding: '6px 10px' }}
                  >
                    <Compass size={13} />
                    <span>{focusNodeId === selectedNode.id ? 'Exit Focus' : 'Focus Neighbors'}</span>
                  </button>

                  {selectedNode.entity_type === 'concept' && onEditConceptBySlug && (
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => onEditConceptBySlug(selectedNode.slug)}
                      style={{ fontSize: '0.775rem', padding: '6px 10px' }}
                    >
                      <Edit3 size={13} />
                      <span>Edit</span>
                    </button>
                  )}

                  {selectedNode.entity_type === 'repository' && onFilterLibraryByRepo && (
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => onFilterLibraryByRepo(selectedNode.slug)}
                      style={{ fontSize: '0.775rem', padding: '6px 10px' }}
                    >
                      <BookOpen size={13} />
                      <span>Concepts</span>
                    </button>
                  )}
                </div>

                {selectedNode.entity_type === 'concept' && (
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setIsLinkModalOpen(true)}
                    style={{ justifyContent: 'center', fontSize: '0.775rem', padding: '6px 10px' }}
                  >
                    <Link2 size={13} />
                    <span>Add Relationship from Here</span>
                  </button>
                )}
              </div>

              {/* Connected Relationships */}
              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px', flex: 1, overflowY: 'auto' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '8px' }}>
                  CONNECTED RELATIONSHIPS ({selectedConnections.outgoing.length + selectedConnections.incoming.length})
                </div>

                {selectedConnections.outgoing.length === 0 && selectedConnections.incoming.length === 0 ? (
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No visible connections for this node under current filters.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {selectedConnections.outgoing.map(({ edge, neighbor }) => (
                      <div
                        key={edge.id}
                        style={{
                          padding: '8px 10px',
                          backgroundColor: 'var(--surface-secondary)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '8px',
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => setSelectedNode(neighbor)}
                          style={{ background: 'transparent', border: 'none', textAlign: 'left', cursor: 'pointer', flex: 1, minWidth: 0 }}
                        >
                          <div style={{ fontSize: '0.675rem', fontFamily: 'var(--font-mono)', color: 'var(--emerald-primary)' }}>
                            → {edge.relationship_type}
                          </div>
                          <div style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {neighbor.label}
                          </div>
                          {edge.description && (
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{edge.description}</div>
                          )}
                        </button>
                        {edge.editable && (
                          <button
                            type="button"
                            onClick={() => handleDeleteEdge(edge)}
                            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
                            title="Remove relationship"
                            aria-label="Remove relationship"
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </div>
                    ))}

                    {selectedConnections.incoming.map(({ edge, neighbor }) => (
                      <div
                        key={edge.id}
                        style={{
                          padding: '8px 10px',
                          backgroundColor: 'var(--surface-secondary)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '8px',
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => setSelectedNode(neighbor)}
                          style={{ background: 'transparent', border: 'none', textAlign: 'left', cursor: 'pointer', flex: 1, minWidth: 0 }}
                        >
                          <div style={{ fontSize: '0.675rem', fontFamily: 'var(--font-mono)', color: 'var(--copper-primary)' }}>
                            ← {edge.relationship_type}
                          </div>
                          <div style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {neighbor.label}
                          </div>
                          {edge.description && (
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{edge.description}</div>
                          )}
                        </button>
                        {edge.editable && (
                          <button
                            type="button"
                            onClick={() => handleDeleteEdge(edge)}
                            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
                            title="Remove relationship"
                            aria-label="Remove relationship"
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                Node Inspector
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: '1.5', marginBottom: '16px' }}>
                Select any Workspace, Repository, or Concept node on the canvas to inspect metadata, explore 1–3 hop neighbors, manage relationships, or navigate directly to the item.
              </p>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '8px' }}>
                  EDGE BREAKDOWN
                </div>
                {Object.keys(graphData.stats?.counts_by_relationship || {}).length === 0 ? (
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No edges recorded yet. Use "Link Concepts" or associate concepts with repositories.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {Object.entries(graphData.stats?.counts_by_relationship || {}).map(([rtype, count]) => (
                      <div key={rtype} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.775rem' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{rtype}</span>
                        <span className="badge-slate">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Concept Relationship Modal */}
      <CreateRelationshipModal
        isOpen={isLinkModalOpen}
        onClose={() => setIsLinkModalOpen(false)}
        concepts={concepts}
        initialSourceId={selectedNode?.entity_type === 'concept' ? selectedNode.entity_id : ''}
        onCreated={() => {
          if (onGraphMutated) onGraphMutated();
          loadGraph();
        }}
        showToast={showToast}
      />
    </div>
  );
}
