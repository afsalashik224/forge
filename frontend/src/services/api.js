/**
 * Centralized API Client Service for Forge Backend
 */

export async function fetchHealthStatus() {
  try {
    const res = await fetch('/health');
    if (!res.ok) {
      return {
        status: "unreachable",
        application: "Forge",
        version: "0.1.0",
        environment: "offline"
      };
    }
    return await res.json();
  } catch (error) {
    console.warn("Backend health endpoint check failed:", error);
    return {
      status: "unreachable",
      application: "Forge",
      version: "0.1.0",
      environment: "offline"
    };
  }
}

// -----------------------------------------------------------------------------
// Concepts API
// -----------------------------------------------------------------------------

export async function fetchConcepts(params = {}) {
  try {
    const query = new URLSearchParams();
    if (params.q) query.set('q', params.q);
    if (params.tags) query.set('tags', Array.isArray(params.tags) ? params.tags.join(',') : params.tags);
    if (params.category) query.set('category', params.category);
    if (params.status) query.set('status', params.status);
    if (params.repository) query.set('repository', params.repository);
    if (params.workspace) query.set('workspace', params.workspace);

    const qs = query.toString();
    const url = qs ? `/api/concepts/?${qs}` : '/api/concepts/';
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Server returned HTTP status ${res.status}`);
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error("Failed to fetch concepts:", error);
    throw new Error("Unable to connect to Forge concept service. Please verify backend state.");
  }
}

export async function searchConcepts(params = {}) {
  return fetchConcepts(params);
}

export async function fetchConceptBySlug(slug) {
  if (!slug) return null;
  try {
    const res = await fetch(`/api/concepts/${encodeURIComponent(slug)}`);
    if (res.status === 404) return null;
    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch concept '${slug}':`, error);
    throw new Error(`Could not load details for concept '${slug}'.`);
  }
}

export async function createConcept(payload) {
  try {
    const res = await fetch('/api/concepts/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || `Server returned error status ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to create concept:", error);
    throw error;
  }
}

export async function updateConcept(slug, payload) {
  try {
    const res = await fetch(`/api/concepts/${encodeURIComponent(slug)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server returned error status ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to update concept '${slug}':`, error);
    throw error;
  }
}

export async function deleteConcept(slug) {
  try {
    const res = await fetch(`/api/concepts/${encodeURIComponent(slug)}`, {
      method: 'DELETE',
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server returned error status ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to delete concept '${slug}':`, error);
    throw error;
  }
}

// -----------------------------------------------------------------------------
// Workspaces API
// -----------------------------------------------------------------------------

export async function fetchWorkspaces() {
  try {
    const res = await fetch('/api/workspaces/');
    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error("Failed to fetch workspaces:", error);
    throw error;
  }
}

export async function fetchWorkspaceBySlug(slug) {
  if (!slug) return null;
  try {
    const res = await fetch(`/api/workspaces/${encodeURIComponent(slug)}`);
    if (res.status === 404) return null;
    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch workspace '${slug}':`, error);
    throw error;
  }
}

export async function createWorkspace(payload) {
  try {
    const res = await fetch('/api/workspaces/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to create workspace:", error);
    throw error;
  }
}

export async function updateWorkspace(slug, payload) {
  try {
    const res = await fetch(`/api/workspaces/${encodeURIComponent(slug)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to update workspace '${slug}':`, error);
    throw error;
  }
}

export async function deleteWorkspace(slug) {
  try {
    const res = await fetch(`/api/workspaces/${encodeURIComponent(slug)}`, {
      method: 'DELETE',
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to delete workspace '${slug}':`, error);
    throw error;
  }
}

export async function linkRepositoryToWorkspace(workspaceSlug, repoSlug) {
  try {
    const res = await fetch(`/api/workspaces/${encodeURIComponent(workspaceSlug)}/repositories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repository_slug: repoSlug }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to link repository to workspace:", error);
    throw error;
  }
}

export async function unlinkRepositoryFromWorkspace(workspaceSlug, repoSlug) {
  try {
    const res = await fetch(`/api/workspaces/${encodeURIComponent(workspaceSlug)}/repositories/${encodeURIComponent(repoSlug)}`, {
      method: 'DELETE',
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to unlink repository from workspace:", error);
    throw error;
  }
}

// -----------------------------------------------------------------------------
// Repositories API
// -----------------------------------------------------------------------------

export async function fetchRepositories() {
  try {
    const res = await fetch('/api/repositories/');
    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error("Failed to fetch repositories:", error);
    throw error;
  }
}

export async function fetchRepositoryBySlug(slug) {
  if (!slug) return null;
  try {
    const res = await fetch(`/api/repositories/${encodeURIComponent(slug)}`);
    if (res.status === 404) return null;
    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch repository '${slug}':`, error);
    throw error;
  }
}

export async function createRepository(payload) {
  try {
    const res = await fetch('/api/repositories/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to create repository:", error);
    throw error;
  }
}

export async function updateRepository(slug, payload) {
  try {
    const res = await fetch(`/api/repositories/${encodeURIComponent(slug)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to update repository '${slug}':`, error);
    throw error;
  }
}

export async function deleteRepository(slug) {
  try {
    const res = await fetch(`/api/repositories/${encodeURIComponent(slug)}`, {
      method: 'DELETE',
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to delete repository '${slug}':`, error);
    throw error;
  }
}

export async function linkConceptToRepository(repoSlug, conceptSlug) {
  try {
    const res = await fetch(`/api/repositories/${encodeURIComponent(repoSlug)}/concepts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ concept_slug: conceptSlug }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to link concept to repository:", error);
    throw error;
  }
}

export async function unlinkConceptFromRepository(repoSlug, conceptSlug) {
  try {
    const res = await fetch(`/api/repositories/${encodeURIComponent(repoSlug)}/concepts/${encodeURIComponent(conceptSlug)}`, {
      method: 'DELETE',
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to unlink concept from repository:", error);
    throw error;
  }
}

// -----------------------------------------------------------------------------
// Knowledge Graph API
// -----------------------------------------------------------------------------

export async function fetchKnowledgeGraph(params = {}) {
  try {
    const query = new URLSearchParams();
    if (params.entity_types && params.entity_types.length > 0) {
      query.set('entity_types', Array.isArray(params.entity_types) ? params.entity_types.join(',') : params.entity_types);
    }
    if (params.relationship_types && params.relationship_types.length > 0) {
      query.set('relationship_types', Array.isArray(params.relationship_types) ? params.relationship_types.join(',') : params.relationship_types);
    }
    if (params.workspace) query.set('workspace', params.workspace);
    if (params.repository) query.set('repository', params.repository);
    if (params.category) query.set('category', params.category);
    if (params.status) query.set('status', params.status);
    if (params.q) query.set('q', params.q);
    if (params.focus) query.set('focus', params.focus);
    if (params.depth) query.set('depth', String(params.depth));
    if (params.include_neighbors) query.set('include_neighbors', 'true');

    const qs = query.toString();
    const url = qs ? `/api/graph/?${qs}` : '/api/graph/';
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to fetch knowledge graph:", error);
    throw error;
  }
}

export async function fetchNodeNeighbors(entityType, identifier, depth = 1) {
  try {
    const res = await fetch(`/api/graph/nodes/${encodeURIComponent(entityType)}/${encodeURIComponent(identifier)}/neighbors?depth=${depth}`);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to fetch node neighbors:", error);
    throw error;
  }
}

export async function fetchRelationships(params = {}) {
  try {
    const query = new URLSearchParams();
    if (params.concept) query.set('concept', params.concept);
    if (params.relationship_type) query.set('relationship_type', params.relationship_type);
    const qs = query.toString();
    const res = await fetch(qs ? `/api/graph/relationships?${qs}` : '/api/graph/relationships');
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to fetch relationships:", error);
    throw error;
  }
}

export async function createRelationship(payload) {
  try {
    const res = await fetch('/api/graph/relationships', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to create relationship:", error);
    throw error;
  }
}

export async function deleteRelationship(relationshipId) {
  try {
    const res = await fetch(`/api/graph/relationships/${encodeURIComponent(relationshipId)}`, {
      method: 'DELETE',
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to delete relationship ${relationshipId}:`, error);
    throw error;
  }
}

// -----------------------------------------------------------------------------
// Progress Engine & Forge Compass API (Phase 5)
// -----------------------------------------------------------------------------

export async function fetchProgressOverview() {
  try {
    const res = await fetch('/api/progress/');
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to fetch progress overview:", error);
    throw error;
  }
}

export async function fetchRepositoryProgress(slug) {
  try {
    const res = await fetch(`/api/progress/repositories/${encodeURIComponent(slug)}`);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to fetch progress for repository '${slug}':`, error);
    throw error;
  }
}

export async function fetchCompassRecommendations(params = {}) {
  try {
    const query = new URLSearchParams();
    if (params.refresh === false) query.set('refresh', 'false');
    if (params.status) query.set('status', params.status);
    if (params.priority) query.set('priority', params.priority);
    if (params.category) query.set('category', params.category);
    if (params.repository) query.set('repository', params.repository);

    const qs = query.toString();
    const url = qs ? `/api/compass/?${qs}` : '/api/compass/';
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to fetch Forge Compass recommendations:", error);
    throw error;
  }
}

export async function refreshCompassRecommendations() {
  try {
    const res = await fetch('/api/compass/refresh', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error("Failed to refresh Compass recommendations:", error);
    throw error;
  }
}

export async function updateRecommendationStatus(recId, status) {
  try {
    const res = await fetch(`/api/compass/recommendations/${encodeURIComponent(recId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Server error ${res.status}`);
    }
    return data;
  } catch (error) {
    console.error(`Failed to update recommendation ${recId}:`, error);
    throw error;
  }
}
