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
