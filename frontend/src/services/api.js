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

export async function fetchConcepts() {
  try {
    const res = await fetch('/api/concepts/');
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
