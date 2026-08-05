import React, { useState } from 'react';
import { Network } from 'lucide-react';

export default function KnowledgeGraphWidget({ concepts }) {
  const [selectedNode, setSelectedNode] = useState(null);

  const defaultNodes = [
    { id: 'node-1', name: 'Software Architecture', level: 1, x: 20, y: 35, connections: ['node-2', 'node-3'] },
    { id: 'node-2', name: 'REST APIs & Protocols', level: 2, x: 50, y: 20, connections: ['node-4'] },
    { id: 'node-3', name: 'Database Persistence', level: 2, x: 50, y: 65, connections: ['node-5'] },
    { id: 'node-4', name: 'Single Responsibility (SRP)', level: 3, x: 80, y: 25, connections: [] },
    { id: 'node-5', name: 'Repository Pattern', level: 3, x: 80, y: 70, connections: [] },
  ];

  return (
    <div className="matte-card" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
      {/* Widget Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
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
                Knowledge Graph Visualizer
              </h3>
              <span className="badge-copper">PREVIEW</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Interactive dependency map of software engineering concepts
            </p>
          </div>
        </div>
      </div>

      {/* Visual Canvas Area */}
      <div style={{
        height: '220px',
        backgroundColor: 'var(--bg-main)',
        border: '1px solid var(--border-color)',
        borderRadius: '10px',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        backgroundImage: 'radial-gradient(var(--surface-secondary) 1px, transparent 1px)',
        backgroundSize: '20px 20px'
      }}>
        {/* SVG connection lines */}
        <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          <line x1="20%" y1="35%" x2="50%" y2="20%" stroke="var(--emerald-hover)" strokeWidth="2" strokeDasharray="4 4" opacity="0.8" />
          <line x1="20%" y1="35%" x2="50%" y2="65%" stroke="var(--emerald-hover)" strokeWidth="2" strokeDasharray="4 4" opacity="0.8" />
          <line x1="50%" y1="20%" x2="80%" y2="25%" stroke="var(--border-color)" strokeWidth="1.5" />
          <line x1="50%" y1="65%" x2="80%" y2="70%" stroke="var(--border-color)" strokeWidth="1.5" />
        </svg>

        {/* Graph Nodes */}
        {defaultNodes.map((node) => {
          const isSelected = selectedNode?.id === node.id;
          return (
            <div
              key={node.id}
              onClick={() => setSelectedNode(node)}
              style={{
                position: 'absolute',
                left: `${node.x}%`,
                top: `${node.y}%`,
                transform: 'translate(-50%, -50%)',
                backgroundColor: isSelected ? 'var(--emerald-hover)' : 'var(--surface-primary)',
                border: `1px solid ${isSelected ? 'var(--emerald-primary)' : 'var(--emerald-border)'}`,
                color: isSelected ? '#ffffff' : 'var(--text-primary)',
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                zIndex: 5
              }}
            >
              {node.name}
            </div>
          );
        })}
      </div>

      {/* Selected Node Details or hint */}
      <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        {selectedNode ? (
          <span style={{ color: 'var(--emerald-primary)' }}>Selected: <strong>{selectedNode.name}</strong></span>
        ) : (
          <span>Click any concept node to highlight knowledge dependencies</span>
        )}
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>Graph Engine v1.0 Roadmap</span>
      </div>
    </div>
  );
}
