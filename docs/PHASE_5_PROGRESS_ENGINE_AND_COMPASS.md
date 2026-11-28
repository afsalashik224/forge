# Phase 5 — Progress Engine & Forge Compass

## 1. Product Objectives

Phase 5 unifies Forge's stored Workspaces, Repositories, Knowledge Concepts, Tags, Categories, and Knowledge Graph relationships into an explainable measurement and guidance system:

- **Repository Progress**: Quantifies documentation coverage, concept completeness, taxonomy diversity, graph connectivity, and metadata organization for every stored repository.
- **Progress Engine**: Centralized rule and metric calculation service backed strictly by persisted SQLite records (no fabricated metrics, no AI/ML hallucinations, no N+1 query loops).
- **Forge Compass**: Persistent, evidence-backed recommendation engine that translates Progress Engine observations into prioritized, actionable next steps with durable `PENDING`, `COMPLETED`, and `DISMISSED` workflows.

---

## 2. Architecture & Data Model

```text
React Frontend (RepositoryProgress, ForgeCompass, KnowledgeWorkspace)
    ↓
Flask REST Blueprints (/api/progress, /api/compass)
    ↓
Service Layer (ProgressService, CompassService)
    ↓
Repository Layer (ProgressRepository with selectinload, CompassRepository)
    ↓
SQLAlchemy Models (Workspace, Repository, Concept, ConceptRelationship, CompassRecommendation)
    ↓
SQLite
```

### Schema & Migration (`005_add_compass_recommendations.py`)

- **Table**: `compass_recommendations` (`CompassRecommendation` in `backend/app/models/compass_recommendation.py`)
- **Columns**:
  - `id` (`INTEGER PK`), `dedupe_key` (`VARCHAR(200) UNIQUE NOT NULL`), `rule_code` (`VARCHAR(64) NOT NULL`)
  - `title`, `explanation`, `category`, `priority` (`HIGH` | `MEDIUM` | `LOW`)
  - `entity_type`, `entity_id`, `entity_slug`, `entity_label`
  - `evidence_json` (`TEXT`), `suggested_action` (`TEXT`), `action_target` (`VARCHAR(50)`)
  - `status` (`PENDING` | `COMPLETED` | `DISMISSED`), `is_active` (`BOOLEAN`), `resolved_at`, `created_at`, `updated_at`
- **Indexes**: `uq_compass_dedupe_key`, `ix_compass_status`, `ix_compass_priority`, `ix_compass_entity`.

---

## 3. Progress Metrics & Exact Formulas

All metrics measure **documentation coverage, organization, and knowledge graph connectivity** — never source-code completion or production readiness.

1. **Knowledge Coverage** (weight `25%`):
   - Formula: `min(concept_count / 5, 1.0) * 100`
2. **Documentation Completeness** (weight `30%`):
   - Per linked concept, 4 quality checks (`1` point each):
     - `summary` non-empty (`>= 15` chars)
     - `content` non-empty (`>= 50` chars)
     - `tags` list non-empty (`>= 1` tag)
     - `status == 'PUBLISHED'`
   - Formula: `0.0` if `concept_count == 0`, else `(sum(points) / (concept_count * 4)) * 100`
3. **Concept Diversity** (weight `15%`):
   - Targets: `3` distinct non-empty categories, `4` distinct tags.
   - Formula: `0.0` if `concept_count == 0`, else `(0.6 * min(distinct_categories / 3, 1.0) + 0.4 * min(distinct_tags / 4, 1.0)) * 100`
4. **Relationship Coverage** (weight `15%`):
   - Measures how many concepts attached to the repository participate in at least one explicit `ConceptRelationship` edge.
   - Formula: `0.0` if `concept_count == 0`, else `(connected_concepts / concept_count) * 100`
5. **Organization Quality** (weight `15%`):
   - 4 metadata checks (`1` point each): assigned to `>= 1` workspace, `description >= 10` chars, `primary_language` set, `vcs_url` set.
   - Formula: `(checks_passed / 4) * 100`
6. **Overall Repository Documentation Score**:
   - `round(0.25 * knowledge_coverage + 0.30 * documentation_completeness + 0.15 * concept_diversity + 0.15 * relationship_coverage + 0.15 * organization_quality, 1)`
   - **Data Sufficiency Classification**: `NO_CONCEPTS` (`0`), `MINIMAL_DATA` (`1`), `WELL_DOCUMENTED` (`>= 3` concepts & score `>= 70%`), otherwise `PARTIAL`.

---

## 4. Recommendation Rules & Lifecycle

Rules fire strictly from stored evidence in `CompassService`:
- `REPO_NO_CONCEPTS` (`HIGH`, `DOCUMENTATION_GAP`): Repository has 0 linked concepts.
- `REPO_LOW_COVERAGE` (`MEDIUM`, `LOW_COVERAGE`): Repository has 1–2 linked concepts.
- `REPO_UNCONNECTED_CONCEPTS` (`HIGH` if `>= 3` concepts else `MEDIUM`, `MISSING_RELATIONSHIPS`): Repository has `>= 2` concepts with at least one lacking Knowledge Graph edges.
- `REPO_INCOMPLETE_DOCS` (`HIGH` if missing Markdown body else `LOW`, `DOCUMENTATION_GAP`): Linked concepts lack Markdown content or tags.
- `REPO_NO_WORKSPACE` (`MEDIUM`, `ORGANIZATION_ISSUE`): Repository is not assigned to a Workspace.
- `REPO_MISSING_METADATA` (`LOW`, `ORGANIZATION_ISSUE`): Repository misses `>= 2` of `description`, `primary_language`, `vcs_url`.
- `CONCEPT_ISOLATED_ORPHAN` (`MEDIUM`, `MISSING_RELATIONSHIPS`): Concept has 0 linked repositories and 0 graph relationships.
- `CONCEPT_MISSING_CONTENT` (`MEDIUM`, `DOCUMENTATION_GAP`): Unlinked concept lacks substantive Markdown content (`< 50` chars).
- `WORKSPACE_EMPTY` (`LOW`, `ORGANIZATION_ISSUE`): Workspace has 0 associated repositories.
- `UNDERREPRESENTED_CATEGORY` (`LOW`, `CATEGORY_BALANCE`): Platform has `>= 4` concepts while core categories (`architecture`, `security`, `testing`, `devops`) have 0 entries.

### Persistence & Non-Overwrite Semantics
- Recommendations are deduplicated by unique `dedupe_key`.
- Refreshing updates `explanation`, `evidence_json`, `priority`, and `is_active` **without overwriting** user `COMPLETED` or `DISMISSED` status decisions.
- If a condition resolves in underlying data while still `PENDING`, `is_active` becomes `False` (`Resolved in Data`) rather than falsely marking user `COMPLETED`.
- Deleted referenced entities automatically mark stale recommendations inactive and clear invalid entity IDs/slugs.

---

## 5. REST API Endpoints

### Progress API (`/api/progress`)
- `GET /api/progress/` — Overall platform metrics, repository progress breakdowns, category distribution, knowledge health signals, and `metric_definitions`.
- `GET /api/progress/repositories/<slug>` — Detailed progress breakdown and gaps for a single repository (`200` or `404`).

### Compass API (`/api/compass`)
- `GET /api/compass/` (alias `GET /api/compass/recommendations`) — Synchronizes recommendations (unless `?refresh=false`) and returns grouped recommendations (`active_pending`, `completed`, `dismissed`, `no_longer_relevant`) and priority counts (`?status=`, `?priority=`, `?category=`, `?repository=`).
- `POST /api/compass/refresh` — Explicitly runs idempotent synchronization and returns updated payload.
- `PATCH /api/compass/recommendations/<id>` (alias `POST .../status`) — Updates status to `PENDING`, `COMPLETED`, or `DISMISSED` (`200`, `400`, `404`).

---

## 6. Frontend Integration

- **`RepositoryProgress.jsx`**: Displays live average score, collapsible formula explanations, honest empty states, per-repository 5-dimension cards, clickable linked concepts, gap summaries, category distribution, and knowledge health signals.
- **`ForgeCompass.jsx`**: Displays priority counts, `Active Queue` / `Completed` / `Dismissed` / `Resolved in Data` tabs, priority/category filters, supporting evidence blocks, entity navigation buttons, and persistent `Complete` / `Dismiss` / `Reopen` controls.
- **`KnowledgeWorkspace.jsx` & `Sidebar.jsx`**: Live Repo Doc Coverage and Forge Compass KPI cards, top-3 priority actions strip, and live Compass badge count in navigation.

---

## 7. Verification Summary

### Automated Tests & Checks
- **Backend (`pytest tests/ -v`)**: **138 / 138 passed in 3.43s**, covering Phases 0–4 regression plus [test_migration_005.py](file:///d:/forge/backend/tests/test_migration_005.py), [test_progress_engine.py](file:///d:/forge/backend/tests/test_progress_engine.py), and [test_compass.py](file:///d:/forge/backend/tests/test_compass.py).
- **Frontend Lint (`oxlint`)**: **0 warnings and 0 errors** across 33 files.
- **Frontend Production Build (`vite build`)**: Built cleanly.

### End-to-End Browser Verification (`http://localhost:3000/`, isolated SQLite DB)
Executed against live Vite + Flask servers in Chrome with zero uncaught console errors and zero failed HTTP requests (`138` requests before reload + `70` requests after reload returning `200`/`201`/`304`):
1. **Honest Empty States**: Dashboard showed `REPO DOC COVERAGE: N/A` (`0 repos`) and `FORGE COMPASS: 0`; `Repository Progress` showed `Insufficient Data — No Repositories Yet` and expandable `Metric Formulas`; `Forge Compass` showed `Waiting for Forge Knowledge Data`.
2. **Workspace & Repository Tracking**: Created `Cloud Core` and `Orders Service` (`201`). `Repository Progress` updated live to `DOC SCORE: 15%` (`NO CONCEPTS`, `Knowledge Coverage: 0%`, `Organization Quality: 100%`).
3. **Concepts, Progress & Gaps**: Linked `Event-Driven Orders` (Markdown body + tag `kafka`) and `Idempotency Keys` (tag `api`, initially empty body). `Repository Progress` updated to `52.8%` (`Knowledge Coverage: 40%`, `Documentation Completeness: 62.5%`, `Concept Diversity: 60%`, `Relationship Coverage: 0%`, `Organization Quality: 100%`) with 3 identified gaps.
4. **Forge Compass Recommendations & Navigation**: Verified 3 evidence-backed pending items (`REPO_INCOMPLETE_DOCS`, `REPO_LOW_COVERAGE`, `REPO_UNCONNECTED_CONCEPTS`) and navigated via `Open Knowledge Graph`.
5. **Graph Link & Concept Update**: Linked `Event-Driven Orders -[RELATES_TO]-> Idempotency Keys` (`201`) and published `Idempotency Keys` (`200`). `Repository Progress` updated `Relationship Coverage` from `0%` to `100%`, `Documentation Completeness` from `62.5%` to `75%`, and overall `DOC SCORE` from `52.8%` to `71.5%`. Dashboard cards and top-actions strip updated in sync.
   - **Follow-Up `EditConceptModal` Content Verification (`Check Repo` + `Draft Entry`)**: Confirmed the prior `Idempotency Keys` edit left `content` empty because Chrome DevTools `fill_form` wrote `.value` without firing React `onChange`. Typing into `Markdown Content` (`aria-label="Markdown Content"`) triggered live preview immediately, persisted `"content"` via `PUT /api/concepts/draft-entry` (`200`), raised `Documentation Completeness` from `50%` (`2/4`) to `100%` (`4/4`) and `DOC SCORE` from `21.5%` to `36.5%`, and cleared `Concepts missing substantive Markdown body` (`1` → `0`).
6. **Resolution vs. User Decisions & Reload Persistence**: `REPO_UNCONNECTED_CONCEPTS`, `REPO_NO_CONCEPTS`, and `WORKSPACE_EMPTY` moved cleanly to `Resolved in Data (3)` (`CONDITION RESOLVED`, not auto-completed). Marked `Complete` and `Dismiss` on the remaining 2 active recommendations (`PATCH` → `200`), reloaded the browser page, and confirmed `Completed (1)`, `Dismissed (1)`, and `Resolved in Data (3)` persisted from SQLite.

---

## 8. Known Limitations

- **Documentation vs. Source Code**: Scores reflect documentation coverage, concept completeness, and Knowledge Graph linkage inside Forge rather than static analysis of repository source code, test coverage, or CI pass rates.
- **Scale Assumption**: `ProgressRepository` eager-loads all workspaces, repositories, concepts, and relationships in memory per request; this avoids N+1 queries and is fast for hundreds/low thousands of entities, though multi-tenant or very large catalogs would eventually benefit from SQL-level materialized views or paginated scoring.
- **Single-User Decision State**: Recommendation `status` (`COMPLETED`/`DISMISSED`) is global per installation (no multi-user authentication layer yet).
