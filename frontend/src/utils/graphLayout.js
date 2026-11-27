/**
 * Deterministic hierarchical + force-refined layout for Forge Knowledge Graph.
 * Positions Workspace, Repository, and Concept nodes without overlapping.
 */

export function computeGraphLayout(nodes, edges, width = 960, height = 560) {
  const positions = {};
  if (!nodes || nodes.length === 0) return positions;

  const byType = {
    workspace: [],
    repository: [],
    concept: [],
  };

  nodes.forEach((n) => {
    if (byType[n.entity_type]) {
      byType[n.entity_type].push(n);
    } else {
      byType.concept.push(n);
    }
  });

  // Assign initial vertical tiers based on entity types present
  const activeTiers = ['workspace', 'repository', 'concept'].filter((t) => byType[t].length > 0);
  const tierCount = activeTiers.length || 1;
  const paddingX = 95;
  const paddingY = 70;
  const usableW = Math.max(200, width - paddingX * 2);
  const usableH = Math.max(160, height - paddingY * 2);

  activeTiers.forEach((tierType, tierIdx) => {
    const group = byType[tierType];
    const baseY =
      tierCount === 1
        ? height / 2
        : paddingY + (tierIdx / (tierCount - 1)) * usableH;

    group.forEach((node, idx) => {
      const cols = Math.min(group.length, tierType === 'concept' ? 5 : 4);
      const row = Math.floor(idx / cols);
      const col = idx % cols;
      const itemsInRow = Math.min(cols, group.length - row * cols);
      const x =
        itemsInRow === 1
          ? width / 2
          : paddingX + (col / (itemsInRow - 1)) * usableW;
      // Stagger rows slightly within the tier if there are many items
      const totalRows = Math.ceil(group.length / cols);
      const rowOffset = totalRows > 1 ? (row - (totalRows - 1) / 2) * 58 : 0;
      positions[node.id] = {
        x,
        y: Math.max(46, Math.min(height - 46, baseY + rowOffset)),
      };
    });
  });

  // Gentle force-directed refinement so connected nodes attract horizontally
  // and close nodes repel cleanly without leaving bounds
  if (nodes.length > 1) {
    const iterations = 65;
    const minDistX = 135;
    const minDistY = 62;

    for (let iter = 0; iter < iterations; iter++) {
      const forces = {};
      nodes.forEach((n) => {
        forces[n.id] = { fx: 0, fy: 0 };
      });

      // Repulsion between all pairs
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const pa = positions[a.id];
          const pb = positions[b.id];
          const dx = pb.x - pa.x;
          const dy = pb.y - pa.y;
          const normDx = dx / minDistX;
          const normDy = dy / minDistY;
          const distSq = normDx * normDx + normDy * normDy;

          if (distSq < 1.15) {
            const dist = Math.sqrt(Math.max(distSq, 0.01));
            const strength = (1.15 - dist) * 14;
            const ux = dx === 0 && dy === 0 ? ((i % 2 === 0 ? 1 : -1) * 0.7) : normDx / dist;
            const uy = dx === 0 && dy === 0 ? ((j % 2 === 0 ? 1 : -1) * 0.4) : normDy / dist;
            forces[a.id].fx -= ux * strength;
            forces[a.id].fy -= uy * strength * 0.55;
            forces[b.id].fx += ux * strength;
            forces[b.id].fy += uy * strength * 0.55;
          }
        }
      }

      // Attraction along edges (mainly horizontal alignment to preserve tier readability)
      edges.forEach((e) => {
        const pa = positions[e.source];
        const pb = positions[e.target];
        if (!pa || !pb) return;
        const dx = pb.x - pa.x;
        const dy = pb.y - pa.y;
        const sameTier =
          nodes.find((n) => n.id === e.source)?.entity_type ===
          nodes.find((n) => n.id === e.target)?.entity_type;

        forces[e.source].fx += dx * 0.035;
        forces[e.target].fx -= dx * 0.035;
        if (sameTier) {
          forces[e.source].fy += dy * 0.025;
          forces[e.target].fy -= dy * 0.025;
        }
      });

      // Center gravity
      nodes.forEach((n) => {
        const p = positions[n.id];
        forces[n.id].fx += (width / 2 - p.x) * 0.008;
        p.x = Math.max(85, Math.min(width - 85, p.x + forces[n.id].fx));
        p.y = Math.max(46, Math.min(height - 46, p.y + forces[n.id].fy));
      });
    }
  }

  return positions;
}
