import React, { useEffect, useState } from 'react';
import { Network, ArrowUpRight, BookOpen, FolderGit2, GitBranch, RefreshCw } from 'lucide-react';
import KnowledgeGraphCanvas from './KnowledgeGraphCanvas';
import { fetchKnowledgeGraph } from '../services/api';

export default function KnowledgeGraphWidget({
  refreshKey = 0,
  onOpenGraphExplorer,
  onNavigateFromNode,
  onOpenCreateModal,
}) {
  const [graph, setGraph] = useState({ nodes: [], edges: [], stats: null });
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    fetchKnowledgeGraph()
      .then((data) => {
        if (!active) return;
        setGraph(data || { nodes: [], edges: [], stats: null });
        setSelectedNode((prev) =>
          prev ? (data?.nodes || []).find((n) => n.id === prev.id) || null : null
        );
      })
      .catch((err) => {
        if (!active) return;
        setError(err.message || 'Unable to load knowledge graph.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshKey]);

  const nodes = graph.nodes || [];
  const edges = graph.edges || [];

  return (
    <div className="matte-card" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
      {/* Widget Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '6px',
            backgroundColor: 'var(--emerald-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Network size={18} color="var(--emerald-primary)" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Knowledge Graph Explorer
              </h3>
              <span className="badge-emerald">LIVE</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Real-time entity map of stored Workspaces, Repositories, and Concepts
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {nodes.length} nodes · {edges.length} edges
          </span>
          {onOpenGraphExplorer && (
            <button
              type="button"
              className="btn-secondary"
              onClick={onOpenGraphExplorer}
              style={{ padding: '5px 10px', fontSize: '0.75rem' }}
            >
              <span>Full Explorer</span>
              <ArrowUpRight size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Live Graph Canvas or Honest Empty State */}
      {loading ? (
        <div
          style={{
            height: '250px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            backgroundColor: 'var(--bg-main)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
          }}
        >
          <RefreshCw size={15} />
          <span>Loading live graph…</span>
        </div>
      ) : error ? (
        <div
          style={{
            height: '250px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'var(--bg-main)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px',
            color: '#F87171',
            fontSize: '0.85rem',
            padding: '16px',
            textAlign: 'center',
          }}
        >
          {error}
        </div>
      ) : nodes.length === 0 ? (
        <div
          style={{
            height: '220px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'var(--bg-main)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px',
            padding: '20px',
            textAlign: 'center',
          }}
        >
          <Network size={28} color="var(--text-muted)" style={{ marginBottom: '8px' }} />
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
            No graph entities exist yet. Forge a concept or add workspaces/repositories to populate the graph.
          </p>
          {onOpenCreateModal && (
            <button type="button" className="btn-emerald" onClick={onOpenCreateModal}>
              Forge First Concept
            </button>
          )}
        </div>
      ) : (
        <KnowledgeGraphCanvas
          nodes={nodes}
          edges={edges}
          selectedNodeId={selectedNode?.id || null}
          onSelectNode={setSelectedNode}
          onDoubleClickNode={(node) => onNavigateFromNode && onNavigateFromNode(node)}
          height={280}
          width={920}
          showEdgeLabels={false}
          interactive={true}
        />
      )}

      {/* Selected Node Footer */}
      <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', flexWrap: 'wrap', gap: '8px' }}>
        {selectedNode ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--emerald-primary)' }}>
              Selected ({selectedNode.entity_type}): <strong>{selectedNode.label}</strong>
            </span>
            {onNavigateFromNode && (
              <button
                type="button"
                onClick={() => onNavigateFromNode(selectedNode)}
                style={{
                  background: 'var(--surface-secondary)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-primary)',
                  borderRadius: '4px',
                  padding: '2px 8px',
                  fontSize: '0.725rem',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                {selectedNode.entity_type === 'concept' && <BookOpen size={11} />}
                {selectedNode.entity_type === 'repository' && <GitBranch size={11} />}
                {selectedNode.entity_type === 'workspace' && <FolderGit2 size={11} />}
                <span>
                  {selectedNode.entity_type === 'concept' ? 'Open Concept' : `View ${selectedNode.entity_type}`}
                </span>
              </button>
            )}
          </div>
        ) : (
          <span>Click a node to highlight connections · Double-click to open</span>
        )}
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
          Backed by SQLite Graph API
        </span>
      </div>
    </div>
  );
}
