# Phase 4 — Knowledge Graph

## Overview

Phase 4 replaces the static preview graph widget with a live, database-backed **Knowledge Graph** built directly on top of Forge's relational models (`Workspace`, `Repository`, and `Concept`) in SQLite.

Every displayed node and edge corresponds to stored records:
- **Entity Nodes**: `workspace`, `repository`, and `concept` records.
- **Structural Edges**:
  - `CONTAINS_REPO` (`Workspace -> Repository` via `workspace_repositories`)
  - `DOCUMENTS_CONCEPT` (`Repository -> Concept` via `repository_concepts`)
- **Explicit Knowledge Relationships**:
  - Typed directed edges between concepts (`concept_relationships` table):
    `DEPENDS_ON`, `RELATES_TO`, `IMPLEMENTS`, `EXTENDS`, `ALTERNATIVE_TO`, `SUPERSEDES`, `PART_OF`.

## Database & Migration

- **Model**: `backend/app/models/concept_relationship.py` (`ConceptRelationship`)
  - Enforces foreign keys to `concepts.id` (`ON DELETE CASCADE`).
  - Enforces `CHECK (source_concept_id != target_concept_id)` (no self-loops).
  - Enforces `UNIQUE (source_concept_id, target_concept_id, relationship_type)`.
- **Migration**: `backend/migrations/004_add_concept_relationships.py` (`run_migration_004`)
  - Idempotent table and index creation (`ix_concept_rel_source`, `ix_concept_rel_target`, `uq_concept_rel_edge`).

## Graph REST API (`/api/graph`)

- `GET /api/graph/`
  - Query parameters:
    - `entity_types`: comma-separated `workspace,repository,concept`
    - `relationship_types`: comma-separated edge types
    - `workspace`: workspace slug scope
    - `repository`: repository slug scope
    - `category`: concept category filter
    - `status`: entity status filter
    - `q`: text search (`include_neighbors=true` retains 1-hop neighbors)
    - `focus` + `depth` (`1`–`3`): BFS connected neighborhood subgraph around a node (`<entity_type>:<id_or_slug>`)
- `GET /api/graph/nodes/<entity_type>/<identifier>/neighbors`
  - Returns the focus node, direct incoming/outgoing edges, and neighborhood subgraph.
- `GET /api/graph/relationships`
  - Lists explicit concept relationships (filterable by `concept` slug and `relationship_type`).
- `POST /api/graph/relationships`
  - Validates entities (`404`), self-loops and relationship types (`400`), and duplicate directed edges (`409`), returning `201 Created`.
- `DELETE /api/graph/relationships/<id>`
  - Removes an explicit relationship (`200 OK` or `404`).

## Concept Detail Integration

- `GET /api/concepts/<slug>` returns `relationships.outgoing` and `relationships.incoming` so concepts can be navigated directly from `ConceptReaderModal`.

## Frontend Visualization & Navigation

- **Shared Interactive Canvas**: `frontend/src/components/KnowledgeGraphCanvas.jsx` + deterministic force-refined tier layout in `frontend/src/utils/graphLayout.js` (drag nodes, pan, zoom, edge highlighting, arrowheads).
- **Dashboard Live Widget**: `frontend/src/components/KnowledgeGraphWidget.jsx` displays real nodes/edges and links to the full explorer.
- **Full Knowledge Graph Explorer**: `frontend/src/pages/KnowledgeGraphPage.jsx` provides filtering, 1–3 hop connected-node exploration, edge creation/removal (`CreateRelationshipModal.jsx`), and direct navigation to `ConceptReaderModal`, `EditConceptModal`, `WorkspaceManager`, and `ForgeLibrary`.

## Verification Summary

### Automated Checks
- **Backend (`pytest tests/ -v`)**: 127 / 127 tests passed (`test_graph.py`, `test_migration_004.py`, plus all Phase 0–3 tests).
- **Frontend Lint & Build**: `oxlint` passed with 0 warnings / 0 errors; `vite build` succeeded cleanly.

### End-to-End Browser Smoke Test (`http://localhost:3000/`, isolated SQLite DB)
Executed against live Vite + Flask servers in Chrome with all 7 verification steps passing (0 console errors, 112/112 HTTP requests returning `200`/`201`/`304`):
1. **App Load & Health**: Verified `SYSTEM ACTIVE` and `API HEALTH STATUS: Healthy` (`Forge v0.1.0`).
2. **Empty Graph State**: Confirmed `Knowledge Graph Explorer` widget displayed `0 nodes · 0 edges` with empty-state guidance (no static placeholder nodes).
3. **Workspace & Repository Creation**: Created workspace `Core Platform` (`core-platform`) and repository `Auth Gateway` (`auth-gateway`), linking them (`201 Created`).
4. **Concept Authoring & Live Preview**: Created `Zero Trust Security` (`#mtls`) and `JWT Tokens` (`#jwt`) linked to `Auth Gateway`, verifying live split-screen Markdown heading, bold formatting, and Python syntax-highlighted code block preview before saving (`201 Created`).
5. **Live Dashboard Graph Widget**: Confirmed widget updated automatically to `4 nodes · 3 edges` and navigated via `Full Explorer` to the `Knowledge Graph` page.
6. **Knowledge Graph Interactions & Navigation**:
   - Created `Zero Trust Security -[DEPENDS_ON]-> JWT Tokens` (`4 nodes · 4 edges`, `201 Created`).
   - Verified Node Inspector metadata, tags, and `CONNECTED RELATIONSHIPS (2)`.
   - Verified `Focus Neighbors`: `1-hop` isolated 3 nodes / 3 edges (`Auth Gateway`, `Zero Trust Security`, `JWT Tokens`); `2-hop` expanded to 4 nodes / 4 edges (including `Core Platform`).
   - Verified entity-type toggle filtering, `DEPENDS_ON` relationship filter, and `Reset Filters`.
   - Navigated from node to `ConceptReaderModal` (rendering Markdown, `#mtls`, workspace `CORE PLATFORM`, repo `Auth Gateway`, and clickable `CONNECTED CONCEPTS` chip jumping directly to `JWT Tokens`).
   - Navigated from `Auth Gateway` node to `Workspaces & Repositories` (`Repositories` sub-tab filtered to `auth-gateway`).
   - Deleted the `DEPENDS_ON` relationship from the Inspector (`DELETE /api/graph/relationships/1` -> `200`), restoring edge count to `3 edges`.
7. **Observed Minor Non-Blocking Items**:
   - Two `DOCUMENTS_CONCEPT` edge labels on adjacent edges can overlap horizontally at default zoom (`Hide Labels` toggle available).
   - Fixed `Header.jsx` breadcrumb titles for `workspaces` and `graph` tabs and added `aria-label="Forge Concept"` for narrow viewports after the smoke test.

