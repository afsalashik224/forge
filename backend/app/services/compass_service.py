import json
from datetime import datetime, timezone

from app.models.compass_recommendation import (
    CompassRecommendation,
    RECOMMENDATION_PRIORITIES,
    RECOMMENDATION_STATUSES,
)
from app.repositories.compass_repository import CompassRepository
from app.services.progress_service import ProgressService, CORE_ENGINEERING_PILLARS


PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


class CompassService:
    """
    Forge Compass Recommendation Engine.

    Generates deterministic, evidence-backed recommendations from ProgressService metrics,
    persists recommendation decisions (PENDING / COMPLETED / DISMISSED), and avoids
    overwriting user decisions or duplicating active items during refresh.
    """

    def __init__(self, compass_repo=None, progress_service=None):
        self.compass_repo = compass_repo or CompassRepository()
        self.progress_service = progress_service or ProgressService()

    @staticmethod
    def _parse_evidence(evidence_json):
        if not evidence_json:
            return {}
        try:
            parsed = json.loads(evidence_json)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @classmethod
    def serialize_recommendation(cls, rec):
        return {
            "id": rec.id,
            "dedupe_key": rec.dedupe_key,
            "rule_code": rec.rule_code,
            "title": rec.title,
            "explanation": rec.explanation,
            "category": rec.category,
            "priority": rec.priority,
            "entity_type": rec.entity_type,
            "entity_id": rec.entity_id,
            "entity_slug": rec.entity_slug,
            "entity_label": rec.entity_label,
            "evidence": cls._parse_evidence(rec.evidence_json),
            "suggested_action": rec.suggested_action,
            "action_target": rec.action_target,
            "status": rec.status,
            "is_active": bool(rec.is_active),
            "resolved_at": rec.resolved_at.isoformat() if rec.resolved_at else None,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
            "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
        }

    def _build_candidates(self, report):
        """Evaluate transparent rule-based conditions against the Progress Engine report."""
        candidates = []
        snapshot = report["_raw_snapshot"]
        repositories = report["repositories"]
        concepts = snapshot["concepts"]
        workspaces = snapshot["workspaces"]
        category_dist = report["category_distribution"]
        health = report["knowledge_health"]

        # 1. Repository-level rules
        for repo in repositories:
            counts = repo["counts"]
            concept_count = counts["concepts"]
            repo_slug = repo["slug"]
            repo_name = repo["name"]

            # Rule 1a: Repository has zero concepts
            if concept_count == 0:
                candidates.append({
                    "dedupe_key": f"repo_no_concepts:repository:{repo['id']}",
                    "rule_code": "REPO_NO_CONCEPTS",
                    "title": f"Document core concepts for {repo_name}",
                    "explanation": (
                        f"Repository '{repo_name}' currently has 0 linked knowledge concepts "
                        "(0% knowledge coverage)."
                    ),
                    "category": "DOCUMENTATION_GAP",
                    "priority": "HIGH",
                    "entity_type": "repository",
                    "entity_id": repo["id"],
                    "entity_slug": repo_slug,
                    "entity_label": repo_name,
                    "evidence": {
                        "repository_slug": repo_slug,
                        "concept_count": 0,
                        "knowledge_coverage": repo["dimensions"]["knowledge_coverage"]["score"],
                        "primary_language": repo["primary_language"] or "unspecified",
                    },
                    "suggested_action": (
                        f"Create at least 1–3 architectural or technology concepts for '{repo_name}' "
                        "and associate them with this repository."
                    ),
                    "action_target": "create-concept",
                })

            # Rule 1b: Repository has minimal concept coverage (1-2 concepts)
            elif 1 <= concept_count <= 2:
                candidates.append({
                    "dedupe_key": f"repo_low_coverage:repository:{repo['id']}",
                    "rule_code": "REPO_LOW_COVERAGE",
                    "title": f"Expand knowledge coverage for {repo_name}",
                    "explanation": (
                        f"Repository '{repo_name}' only has {concept_count} linked concept(s) "
                        f"({repo['dimensions']['knowledge_coverage']['score']}% of the 5-concept baseline)."
                    ),
                    "category": "LOW_COVERAGE",
                    "priority": "MEDIUM",
                    "entity_type": "repository",
                    "entity_id": repo["id"],
                    "entity_slug": repo_slug,
                    "entity_label": repo_name,
                    "evidence": {
                        "repository_slug": repo_slug,
                        "concept_count": concept_count,
                        "target_concepts": 5,
                        "knowledge_coverage": repo["dimensions"]["knowledge_coverage"]["score"],
                    },
                    "suggested_action": (
                        f"Document additional patterns, deployment setup, or design decisions for '{repo_name}'."
                    ),
                    "action_target": "create-concept",
                })

            # Rule 2: Repository has >= 2 concepts with missing graph relationships
            if concept_count >= 2 and counts["unconnected_concepts"] > 0:
                unconnected = [
                    {"slug": c["slug"], "title": c["title"]}
                    for c in repo["concepts"]
                    if c["relationships_count"] == 0
                ]
                candidates.append({
                    "dedupe_key": f"repo_unconnected_concepts:repository:{repo['id']}",
                    "rule_code": "REPO_UNCONNECTED_CONCEPTS",
                    "title": f"Connect related concepts in {repo_name}",
                    "explanation": (
                        f"{counts['unconnected_concepts']} of {concept_count} concepts linked to "
                        f"'{repo_name}' have no Knowledge Graph relationships."
                    ),
                    "category": "MISSING_RELATIONSHIPS",
                    "priority": "HIGH" if concept_count >= 3 else "MEDIUM",
                    "entity_type": "repository",
                    "entity_id": repo["id"],
                    "entity_slug": repo_slug,
                    "entity_label": repo_name,
                    "evidence": {
                        "repository_slug": repo_slug,
                        "concept_count": concept_count,
                        "connected_concepts": counts["connected_concepts"],
                        "unconnected_concepts": unconnected,
                        "internal_edges": counts["internal_edges"],
                    },
                    "suggested_action": (
                        "Open the Knowledge Graph and link concepts using DEPENDS_ON, IMPLEMENTS, or RELATES_TO edges."
                    ),
                    "action_target": "graph",
                })

            # Rule 3: Repository has concepts missing Markdown content or tags
            incomplete = [
                {"slug": c["slug"], "title": c["title"], "missing": c["missing"]}
                for c in repo["concepts"]
                if not c["has_content"] or not c["has_tags"]
            ]
            if incomplete:
                missing_body_cnt = sum(1 for c in repo["concepts"] if not c["has_content"])
                candidates.append({
                    "dedupe_key": f"repo_incomplete_docs:repository:{repo['id']}",
                    "rule_code": "REPO_INCOMPLETE_DOCS",
                    "title": f"Complete documentation details for {repo_name}",
                    "explanation": (
                        f"{len(incomplete)} concept(s) in '{repo_name}' are missing substantive Markdown "
                        f"content ({missing_body_cnt}) or classification tags."
                    ),
                    "category": "DOCUMENTATION_GAP",
                    "priority": "HIGH" if missing_body_cnt > 0 else "LOW",
                    "entity_type": "repository",
                    "entity_id": repo["id"],
                    "entity_slug": repo_slug,
                    "entity_label": repo_name,
                    "evidence": {
                        "repository_slug": repo_slug,
                        "incomplete_concepts_count": len(incomplete),
                        "incomplete_concepts": incomplete,
                        "documentation_completeness": repo["dimensions"]["documentation_completeness"]["score"],
                    },
                    "suggested_action": (
                        "Open the incomplete concept(s) and add Markdown sections, code examples, and tags."
                    ),
                    "action_target": "library",
                })

            # Rule 4: Repository has no Workspace assignment
            if counts["workspaces"] == 0:
                candidates.append({
                    "dedupe_key": f"repo_no_workspace:repository:{repo['id']}",
                    "rule_code": "REPO_NO_WORKSPACE",
                    "title": f"Assign {repo_name} to a Workspace",
                    "explanation": (
                        f"Repository '{repo_name}' is not grouped under any Workspace, reducing architectural visibility."
                    ),
                    "category": "ORGANIZATION_ISSUE",
                    "priority": "MEDIUM",
                    "entity_type": "repository",
                    "entity_id": repo["id"],
                    "entity_slug": repo_slug,
                    "entity_label": repo_name,
                    "evidence": {
                        "repository_slug": repo_slug,
                        "workspaces_count": 0,
                    },
                    "suggested_action": (
                        f"Assign '{repo_name}' to an existing or new Workspace in Workspaces & Repositories."
                    ),
                    "action_target": "workspaces",
                })

            # Rule 5: Repository metadata incomplete (>= 2 missing of description, language, vcs_url)
            missing_meta = [
                f for f in repo["dimensions"]["organization_quality"]["missing_fields"]
                if f != "workspace"
            ]
            if len(missing_meta) >= 2:
                candidates.append({
                    "dedupe_key": f"repo_missing_metadata:repository:{repo['id']}",
                    "rule_code": "REPO_MISSING_METADATA",
                    "title": f"Enrich repository metadata for {repo_name}",
                    "explanation": (
                        f"Repository '{repo_name}' is missing {len(missing_meta)} metadata fields: "
                        f"{', '.join(missing_meta)}."
                    ),
                    "category": "ORGANIZATION_ISSUE",
                    "priority": "LOW",
                    "entity_type": "repository",
                    "entity_id": repo["id"],
                    "entity_slug": repo_slug,
                    "entity_label": repo_name,
                    "evidence": {
                        "repository_slug": repo_slug,
                        "missing_fields": missing_meta,
                        "organization_quality": repo["dimensions"]["organization_quality"]["score"],
                    },
                    "suggested_action": (
                        "Edit the repository record to add description, primary language, and source VCS URL."
                    ),
                    "action_target": "workspaces",
                })

        # 2. Concept-level rules (isolated orphan concepts not attached to any repo & 0 graph edges)
        for orphan in health["orphan_concepts"]:
            if len(concepts) >= 2 or len(repositories) >= 1:
                candidates.append({
                    "dedupe_key": f"concept_orphan:concept:{orphan['id']}",
                    "rule_code": "CONCEPT_ISOLATED_ORPHAN",
                    "title": f"Integrate isolated concept '{orphan['title']}'",
                    "explanation": (
                        f"Concept '{orphan['title']}' is neither linked to any repository nor connected "
                        "to any other concept in the Knowledge Graph."
                    ),
                    "category": "MISSING_RELATIONSHIPS",
                    "priority": "MEDIUM",
                    "entity_type": "concept",
                    "entity_id": orphan["id"],
                    "entity_slug": orphan["slug"],
                    "entity_label": orphan["title"],
                    "evidence": {
                        "concept_slug": orphan["slug"],
                        "repositories_count": 0,
                        "relationships_count": 0,
                    },
                    "suggested_action": (
                        "Associate this concept with a repository or connect it to a related concept in the Knowledge Graph."
                    ),
                    "action_target": "graph",
                })

        # Standalone concepts missing Markdown body (skip those already covered by repo_incomplete_docs)
        repo_concept_ids = {c["id"] for r in repositories for c in r["concepts"]}
        for stub in health["concepts_missing_content"]:
            if stub["id"] not in repo_concept_ids:
                candidates.append({
                    "dedupe_key": f"concept_missing_content:concept:{stub['id']}",
                    "rule_code": "CONCEPT_MISSING_CONTENT",
                    "title": f"Author Markdown content for '{stub['title']}'",
                    "explanation": (
                        f"Concept '{stub['title']}' currently lacks substantive Markdown documentation "
                        "(< 50 characters)."
                    ),
                    "category": "DOCUMENTATION_GAP",
                    "priority": "MEDIUM",
                    "entity_type": "concept",
                    "entity_id": stub["id"],
                    "entity_slug": stub["slug"],
                    "entity_label": stub["title"],
                    "evidence": {
                        "concept_slug": stub["slug"],
                        "linked_to_repository": False,
                    },
                    "suggested_action": (
                        "Edit the concept and add structured Markdown explanation, tradeoffs, or code examples."
                    ),
                    "action_target": "edit-concept",
                })

        # 3. Workspace-level rule: Workspace with 0 repositories
        for ws in workspaces:
            if len(ws.repositories or []) == 0:
                candidates.append({
                    "dedupe_key": f"workspace_empty:workspace:{ws.id}",
                    "rule_code": "WORKSPACE_EMPTY",
                    "title": f"Add repositories to workspace '{ws.name}'",
                    "explanation": (
                        f"Workspace '{ws.name}' has 0 associated repositories."
                    ),
                    "category": "ORGANIZATION_ISSUE",
                    "priority": "LOW",
                    "entity_type": "workspace",
                    "entity_id": ws.id,
                    "entity_slug": ws.slug,
                    "entity_label": ws.name,
                    "evidence": {
                        "workspace_slug": ws.slug,
                        "repositories_count": 0,
                    },
                    "suggested_action": (
                        f"Link or create repositories inside '{ws.name}' to organize your codebase."
                    ),
                    "action_target": "workspaces",
                })

        # 4. Platform-level category balance rule (only when meaningful data exists >= 4 concepts)
        if len(concepts) >= 4:
            missing_pillars = [p for p in CORE_ENGINEERING_PILLARS if category_dist.get(p, 0) == 0]
            if missing_pillars:
                candidates.append({
                    "dedupe_key": "platform_underrepresented_pillars:global",
                    "rule_code": "UNDERREPRESENTED_CATEGORY",
                    "title": "Balance underrepresented core engineering categories",
                    "explanation": (
                        f"Your knowledge base has {len(concepts)} concepts, but no documented entries in: "
                        f"{', '.join(missing_pillars)}."
                    ),
                    "category": "CATEGORY_BALANCE",
                    "priority": "LOW",
                    "entity_type": "global",
                    "entity_id": None,
                    "entity_slug": None,
                    "entity_label": "Platform Knowledge Base",
                    "evidence": {
                        "total_concepts": len(concepts),
                        "present_categories": category_dist,
                        "missing_core_pillars": missing_pillars,
                    },
                    "suggested_action": (
                        f"Consider documenting concepts covering {', '.join(missing_pillars)} "
                        "to broaden architectural coverage."
                    ),
                    "action_target": "create-concept",
                })

        return candidates

    def sync_recommendations(self):
        """
        Idempotently synchronize persisted recommendations with current Progress Engine state.

        - Creates new PENDING rows for newly detected conditions.
        - Updates explanation/evidence/priority for active conditions WITHOUT altering user status.
        - Marks PENDING items whose condition no longer holds (or whose target entity was deleted)
          as is_active=False ('no longer relevant') without falsely marking them COMPLETED.
        """
        report = self.progress_service.compute_full_report()
        snapshot = report["_raw_snapshot"]
        valid_entities = {
            ("repository", r.id) for r in snapshot["repositories"]
        } | {
            ("workspace", w.id) for w in snapshot["workspaces"]
        } | {
            ("concept", c.id) for c in snapshot["concepts"]
        }

        candidates = self._build_candidates(report)
        candidate_map = {c["dedupe_key"]: c for c in candidates}
        existing_all = self.compass_repo.get_all(include_inactive=True)
        existing_map = {rec.dedupe_key: rec for rec in existing_all}

        # Upsert triggered candidates
        for dedupe_key, cand in candidate_map.items():
            evidence_str = json.dumps(cand["evidence"], sort_keys=True)
            existing = existing_map.get(dedupe_key)
            if existing is None:
                rec = CompassRecommendation(
                    dedupe_key=dedupe_key,
                    rule_code=cand["rule_code"],
                    title=cand["title"],
                    explanation=cand["explanation"],
                    category=cand["category"],
                    priority=cand["priority"],
                    entity_type=cand["entity_type"],
                    entity_id=cand["entity_id"],
                    entity_slug=cand["entity_slug"],
                    entity_label=cand["entity_label"],
                    evidence_json=evidence_str,
                    suggested_action=cand["suggested_action"],
                    action_target=cand["action_target"],
                    status="PENDING",
                    is_active=True,
                )
                self.compass_repo.add(rec)
            else:
                # Preserve existing.status (PENDING / COMPLETED / DISMISSED)!
                existing.title = cand["title"]
                existing.explanation = cand["explanation"]
                existing.category = cand["category"]
                existing.priority = cand["priority"]
                existing.entity_slug = cand["entity_slug"]
                existing.entity_label = cand["entity_label"]
                existing.evidence_json = evidence_str
                existing.suggested_action = cand["suggested_action"]
                existing.action_target = cand["action_target"]
                existing.is_active = True

        # Reconcile previously persisted items whose condition no longer triggers
        for rec in existing_all:
            if rec.dedupe_key not in candidate_map:
                rec.is_active = False
            # Clean stale references if underlying entity was deleted
            if rec.entity_type in ("repository", "workspace", "concept") and rec.entity_id is not None:
                if (rec.entity_type, rec.entity_id) not in valid_entities:
                    rec.is_active = False
                    rec.entity_id = None
                    rec.entity_slug = None

        self.compass_repo.commit()
        return report

    def get_recommendations(
        self,
        refresh=True,
        status=None,
        priority=None,
        category=None,
        repository_slug=None,
    ):
        report = None
        if refresh:
            report = self.sync_recommendations()
        else:
            report = self.progress_service.compute_full_report()

        all_recs = self.compass_repo.get_all(include_inactive=True)
        serialized = [self.serialize_recommendation(r) for r in all_recs]

        # Optional filters
        filtered = serialized
        if status:
            norm_status = status.strip().upper()
            if norm_status not in RECOMMENDATION_STATUSES:
                raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(RECOMMENDATION_STATUSES)}.")
            filtered = [r for r in filtered if r["status"] == norm_status]

        if priority:
            norm_priority = priority.strip().upper()
            if norm_priority not in RECOMMENDATION_PRIORITIES:
                raise ValueError(f"Invalid priority '{priority}'. Must be one of: {', '.join(RECOMMENDATION_PRIORITIES)}.")
            filtered = [r for r in filtered if r["priority"] == norm_priority]

        if category:
            norm_cat = category.strip().upper()
            filtered = [r for r in filtered if r["category"] == norm_cat]

        if repository_slug:
            filtered = [
                r for r in filtered
                if (r["entity_type"] == "repository" and r["entity_slug"] == repository_slug)
                or r["evidence"].get("repository_slug") == repository_slug
            ]

        filtered.sort(key=lambda r: (PRIORITY_ORDER.get(r["priority"], 9), r["id"]))

        active_pending = [r for r in filtered if r["status"] == "PENDING" and r["is_active"]]
        no_longer_relevant = [r for r in filtered if r["status"] == "PENDING" and not r["is_active"]]
        completed = [r for r in filtered if r["status"] == "COMPLETED"]
        dismissed = [r for r in filtered if r["status"] == "DISMISSED"]

        # Summary counts across all persisted recommendations (unfiltered)
        all_pending_active = [r for r in serialized if r["status"] == "PENDING" and r["is_active"]]
        counts = {
            "active_pending": len(all_pending_active),
            "high_priority": sum(1 for r in all_pending_active if r["priority"] == "HIGH"),
            "medium_priority": sum(1 for r in all_pending_active if r["priority"] == "MEDIUM"),
            "low_priority": sum(1 for r in all_pending_active if r["priority"] == "LOW"),
            "completed": sum(1 for r in serialized if r["status"] == "COMPLETED"),
            "dismissed": sum(1 for r in serialized if r["status"] == "DISMISSED"),
            "no_longer_relevant": sum(1 for r in serialized if r["status"] == "PENDING" and not r["is_active"]),
        }

        return {
            "recommendations": filtered,
            "groups": {
                "active_pending": active_pending,
                "completed": completed,
                "dismissed": dismissed,
                "no_longer_relevant": no_longer_relevant,
            },
            "counts": counts,
            "overview": report["overview"],
        }

    def update_recommendation_status(self, rec_id, status):
        if not status or not isinstance(status, str):
            raise ValueError(f"Field 'status' must be one of: {', '.join(RECOMMENDATION_STATUSES)}.")

        norm_status = status.strip().upper()
        if norm_status not in RECOMMENDATION_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(RECOMMENDATION_STATUSES)}.")

        rec = self.compass_repo.get_by_id(rec_id)
        if not rec:
            raise LookupError(f"Recommendation with id '{rec_id}' not found.")

        rec.status = norm_status
        if norm_status in ("COMPLETED", "DISMISSED"):
            rec.resolved_at = datetime.now(timezone.utc)
        else:
            rec.resolved_at = None

        self.compass_repo.commit()
        return self.serialize_recommendation(rec)
