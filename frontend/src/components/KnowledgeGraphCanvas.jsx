import React, { useMemo, useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { computeGraphLayout } from '../utils/graphLayout';

const EDGE_COLORS = {
  CONTAINS_REPO: '#C8872F',
  DOCUMENTS_CONCEPT: '#38BDF8',
  DEPENDS_ON: '#10B981',
  RELATES_TO: '#94A3B8',
  IMPLEMENTS: '#A78BFA',
  EXTENDS: '#34D399',
  ALTERNATIVE_TO: '#FBBF24',
  SUPERSEDES: '#F87171',
  PART_OF: '#60A5FA',
};

function getNodeColors(node, isSelected, isNeighbor, dimmed) {
  if (node.entity_type === 'workspace') {
    return {
      bg: isSelected ? '#9A5B13' : '#1E1B16',
      border: isSelected || isNeighbor ? '#F59E0B' : '#C8872F',
      badgeBg: 'rgba(200, 135, 47, 0.2)',
      badgeText: '#FBBF24',
      text: '#F8FAFC',
      opacity: dimmed ? 0.28 : 1,
    };
  }
  if (node.entity_type === 'repository') {
    return {
      bg: isSelected ? '#0C4A6E' : '#102030',
      border: isSelected || isNeighbor ? '#38BDF8' : '#0284C7',
      badgeBg: 'rgba(56, 189, 248, 0.16)',
      badgeText: '#38BDF8',
      text: '#F8FAFC',
      opacity: dimmed ? 0.28 : 1,
    };
  }
  // Concept node
  const published = node.status === 'PUBLISHED';
  return {
    bg: isSelected ? '#065F46' : '#111827',
    border: isSelected || isNeighbor ? '#10B981' : (published ? '#059669' : '#475569'),
    badgeBg: published ? 'rgba(16, 185, 129, 0.18)' : 'rgba(148, 163, 184, 0.15)',
    badgeText: published ? '#10B981' : '#94A3B8',
    text: '#F8FAFC',
    opacity: dimmed ? 0.28 : 1,
  };
}

export default function KnowledgeGraphCanvas({
  nodes = [],
  edges = [],
  selectedNodeId = null,
  onSelectNode,
  onDoubleClickNode,
  height = 520,
  width = 960,
  showEdgeLabels = true,
  interactive = true,
}) {
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [dragOverrides, setDragOverrides] = useState({});
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [draggingState, setDraggingState] = useState(null);
  const svgRef = useRef(null);

  const basePositions = useMemo(
    () => computeGraphLayout(nodes, edges, width, height),
    [nodes, edges, width, height]
  );

  // Drop stale drag overrides when node set changes
  useEffect(() => {
    const validIds = new Set(nodes.map((n) => n.id));
    setDragOverrides((prev) => {
      const next = {};
      Object.keys(prev).forEach((k) => {
        if (validIds.has(k)) next[k] = prev[k];
      });
      return next;
    });
  }, [nodes]);

  const positions = useMemo(() => {
    const merged = {};
    nodes.forEach((n) => {
      merged[n.id] = dragOverrides[n.id] || basePositions[n.id] || { x: width / 2, y: height / 2 };
    });
    return merged;
  }, [nodes, basePositions, dragOverrides, width, height]);

  const activeNodeId = hoveredNodeId || selectedNodeId;
  const connectedIds = useMemo(() => {
    if (!activeNodeId) return new Set();
    const set = new Set([activeNodeId]);
    edges.forEach((e) => {
      if (e.source === activeNodeId) set.add(e.target);
      if (e.target === activeNodeId) set.add(e.source);
    });
    return set;
  }, [activeNodeId, edges]);

  const getSvgCoords = (clientX, clientY) => {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const rect = svg.getBoundingClientRect();
    const scaleX = width / rect.width;
    const scaleY = height / rect.height;
    const rawX = (clientX - rect.left) * scaleX;
    const rawY = (clientY - rect.top) * scaleY;
    return {
      x: (rawX - pan.x) / zoom,
      y: (rawY - pan.y) / zoom,
      rawX,
      rawY,
    };
  };

  const handleMouseDownCanvas = (e) => {
    if (!interactive) return;
    if (e.target === svgRef.current || e.target.dataset.canvasBg === 'true') {
      const pt = getSvgCoords(e.clientX, e.clientY);
      setDraggingState({
        type: 'pan',
        startRawX: pt.rawX,
        startRawY: pt.rawY,
        origPanX: pan.x,
        origPanY: pan.y,
      });
    }
  };

  const handleMouseDownNode = (e, nodeId) => {
    e.stopPropagation();
    if (onSelectNode) onSelectNode(nodes.find((n) => n.id === nodeId) || null);
    if (!interactive) return;
    const pt = getSvgCoords(e.clientX, e.clientY);
    const pos = positions[nodeId];
    setDraggingState({
      type: 'node',
      nodeId,
      offsetX: pos.x - pt.x,
      offsetY: pos.y - pt.y,
    });
  };

  const handleMouseMove = (e) => {
    if (!draggingState || !interactive) return;
    const pt = getSvgCoords(e.clientX, e.clientY);
    if (draggingState.type === 'pan') {
      setPan({
        x: draggingState.origPanX + (pt.rawX - draggingState.startRawX),
        y: draggingState.origPanY + (pt.rawY - draggingState.startRawY),
      });
    } else if (draggingState.type === 'node') {
      setDragOverrides((prev) => ({
        ...prev,
        [draggingState.nodeId]: {
          x: Math.max(60, Math.min(width - 60, pt.x + draggingState.offsetX)),
          y: Math.max(32, Math.min(height - 32, pt.y + draggingState.offsetY)),
        },
      }));
    }
  };

  const handleMouseUp = () => {
    setDraggingState(null);
  };

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setDragOverrides({});
  };

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: `${height}px`,
        backgroundColor: 'var(--bg-main)',
        border: '1px solid var(--border-color)',
        borderRadius: '10px',
        overflow: 'hidden',
        backgroundImage: 'radial-gradient(var(--surface-secondary) 1px, transparent 1px)',
        backgroundSize: '22px 22px',
        userSelect: 'none',
      }}
    >
      {/* Zoom & Reset Controls */}
      {interactive && (
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            zIndex: 10,
            display: 'flex',
            gap: '4px',
            backgroundColor: 'var(--surface-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            padding: '4px',
          }}
        >
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(2.2, +(z + 0.2).toFixed(2)))}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px', display: 'flex' }}
            title="Zoom in"
            aria-label="Zoom in"
          >
            <ZoomIn size={15} />
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.2).toFixed(2)))}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px', display: 'flex' }}
            title="Zoom out"
            aria-label="Zoom out"
          >
            <ZoomOut size={15} />
          </button>
          <button
            type="button"
            onClick={handleResetView}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px', display: 'flex' }}
            title="Reset graph view"
            aria-label="Reset graph view"
          >
            <RotateCcw size={15} />
          </button>
        </div>
      )}

      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        style={{
          width: '100%',
          height: '100%',
          cursor: draggingState?.type === 'pan' ? 'grabbing' : (interactive ? 'grab' : 'default'),
        }}
        onMouseDown={handleMouseDownCanvas}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          {Object.entries(EDGE_COLORS).map(([type, color]) => (
            <marker
              key={type}
              id={`arrow-${type}`}
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill={color} />
            </marker>
          ))}
        </defs>

        <rect
          x="0"
          y="0"
          width={width}
          height={height}
          fill="transparent"
          data-canvas-bg="true"
        />

        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {/* Edges */}
          {edges.map((edge) => {
            const p1 = positions[edge.source];
            const p2 = positions[edge.target];
            if (!p1 || !p2) return null;

            const isIncident =
              activeNodeId && (edge.source === activeNodeId || edge.target === activeNodeId);
            const dimmed = activeNodeId && !isIncident;

            // Compute offset endpoints so arrowheads stop nicely near node boundaries
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const dist = Math.hypot(dx, dy) || 1;
            const ux = dx / dist;
            const uy = dy / dist;
            const padStart = 42;
            const padEnd = 52;
            const x1 = dist > padStart + padEnd ? p1.x + ux * padStart : p1.x;
            const y1 = dist > padStart + padEnd ? p1.y + uy * (padStart * 0.45) : p1.y;
            const x2 = dist > padStart + padEnd ? p2.x - ux * padEnd : p2.x;
            const y2 = dist > padStart + padEnd ? p2.y - uy * (padEnd * 0.45) : p2.y;

            const color = EDGE_COLORS[edge.relationship_type] || '#64748B';
            const isStructural = edge.origin === 'structural';
            const midX = (x1 + x2) / 2;
            const midY = (y1 + y2) / 2;

            return (
              <g key={edge.id} style={{ opacity: dimmed ? 0.16 : isIncident ? 1 : 0.72, transition: 'opacity 0.15s ease' }}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={color}
                  strokeWidth={isIncident ? 2.4 : 1.5}
                  strokeDasharray={isStructural ? '5 4' : undefined}
                  markerEnd={`url(#arrow-${edge.relationship_type})`}
                />
                {(showEdgeLabels || isIncident) && (
                  <g transform={`translate(${midX}, ${midY})`}>
                    <rect
                      x="-44"
                      y="-9"
                      width="88"
                      height="18"
                      rx="4"
                      fill="#0B1220"
                      stroke={color}
                      strokeOpacity="0.45"
                      strokeWidth="0.75"
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="central"
                      fill={color}
                      fontSize="8.5"
                      fontFamily="var(--font-mono)"
                      fontWeight="600"
                    >
                      {edge.relationship_type}
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = positions[node.id];
            if (!pos) return null;
            const isSelected = selectedNodeId === node.id;
            const isNeighbor = activeNodeId && connectedIds.has(node.id);
            const dimmed = activeNodeId && !isNeighbor;
            const palette = getNodeColors(node, isSelected, isNeighbor, dimmed);
            const displayLabel =
              node.label.length > 22 ? `${node.label.slice(0, 20)}…` : node.label;
            const tagLabel =
              node.entity_type === 'workspace'
                ? 'WS'
                : node.entity_type === 'repository'
                ? 'REPO'
                : 'CONCEPT';
            const boxWidth = Math.max(122, Math.min(188, displayLabel.length * 7.2 + 48));
            const boxHeight = 36;

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                style={{
                  cursor: interactive ? 'pointer' : 'pointer',
                  opacity: palette.opacity,
                  transition: 'opacity 0.15s ease',
                }}
                onMouseDown={(e) => handleMouseDownNode(e, node.id)}
                onMouseEnter={() => setHoveredNodeId(node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
                onDoubleClick={(e) => {
                  e.stopPropagation();
                  if (onDoubleClickNode) onDoubleClickNode(node);
                }}
              >
                <rect
                  x={-boxWidth / 2}
                  y={-boxHeight / 2}
                  width={boxWidth}
                  height={boxHeight}
                  rx={node.entity_type === 'concept' ? 18 : 8}
                  fill={palette.bg}
                  stroke={palette.border}
                  strokeWidth={isSelected ? 2.2 : 1.3}
                />
                {/* Entity type pill */}
                <rect
                  x={-boxWidth / 2 + 7}
                  y={-9}
                  width={tagLabel === 'CONCEPT' ? 44 : 32}
                  height={18}
                  rx="4"
                  fill={palette.badgeBg}
                />
                <text
                  x={-boxWidth / 2 + 7 + (tagLabel === 'CONCEPT' ? 22 : 16)}
                  y="0"
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={palette.badgeText}
                  fontSize="8"
                  fontWeight="700"
                  fontFamily="var(--font-mono)"
                >
                  {tagLabel}
                </text>
                {/* Node title */}
                <text
                  x={-boxWidth / 2 + (tagLabel === 'CONCEPT' ? 58 : 45)}
                  y="0"
                  dominantBaseline="central"
                  fill={palette.text}
                  fontSize="11"
                  fontWeight={isSelected ? '600' : '500'}
                  fontFamily="var(--font-sans)"
                >
                  {displayLabel}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}
