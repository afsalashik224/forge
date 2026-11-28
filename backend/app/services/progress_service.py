import json

from app.repositories.progress_repository import ProgressRepository


TARGET_CONCEPTS_PER_REPO = 5
TARGET_DISTINCT_CATEGORIES = 3
TARGET_DISTINCT_TAGS = 4
MIN_SUMMARY_LEN = 15
MIN_CONTENT_LEN = 50
MIN_REPO_DESC_LEN = 10

METRIC_DEFINITIONS = [
    {
        "key": "knowledge_coverage",
        "label": "Knowledge Coverage",
        "weight": 0.25,
        "formula": "min(concept_count / 5, 1.0) * 100",
        "description": "Measures documented knowledge concepts linked to the repository against a 5-concept baseline.",
    },
    {
        "key": "documentation_completeness",
        "label": "Documentation Completeness",
        "weight": 0.30,
        "formula": "(sum of per-concept checks [summary >= 15 chars, content >= 50 chars, tags >= 1, status == PUBLISHED] / (concept_count * 4)) * 100",
        "description": "Measures substantive documentation quality across concepts associated with the repository.",
    },
    {
        "key": "concept_diversity",
        "label": "Concept Diversity",
        "weight": 0.15,
        "formula": "(0.6 * min(distinct_categories / 3, 1.0) + 0.4 * min(distinct_tags / 4, 1.0)) * 100",
        "description": "Measures breadth across distinct technical categories (3 target) and tags (4 target).",
    },
    {
        "key": "relationship_coverage",
        "label": "Relationship Coverage",
        "weight": 0.15,
        "formula": "(connected_concepts / concept_count) * 100",
        "description": "Measures how many repository concepts participate in explicit Knowledge Graph relationships.",
    },
    {
        "key": "organization_quality",
        "label": "Organization Quality",
        "weight": 0.15,
        "formula": "(passed metadata checks [has >= 1 workspace, description >= 10 chars, primary_language set, vcs_url set] / 4) * 100",
        "description": "Measures repository workspace alignment and structural metadata completeness.",
    },
]

CORE_ENGINEERING_PILLARS = ("architecture", "security", "testing", "devops")


class ProgressService:
    """Centralized, deterministic Progress Engine grounded strictly in stored Forge entities."""

    def __init__(self, repository=None):
        self.repository = repository or ProgressRepository()

    @staticmethod
    def _parse_tags(tags_raw):
        if not tags_raw:
            return []
        try:
            parsed = json.loads(tags_raw)
            return [t for t in parsed if isinstance(t, str) and t.strip()] if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    @classmethod
    def _evaluate_concept_completeness(cls, concept, rel_count_map):
        summary_text = (concept.summary or "").strip()
        content_text = (concept.content or "").strip()
        tags = cls._parse_tags(concept.tags)
        category = (concept.category or "").strip()
        status = (concept.status or "DRAFT").upper()

        has_summary = len(summary_text) >= MIN_SUMMARY_LEN
        has_content = len(content_text) >= MIN_CONTENT_LEN
        has_tags = len(tags) >= 1
        is_published = status == "PUBLISHED"

        passed = sum([has_summary, has_content, has_tags, is_published])
        missing = []
        if not has_summary:
            missing.append("summary")
        if not has_content:
            missing.append("markdown_content")
        if not has_tags:
            missing.append("tags")
        if not is_published:
            missing.append("published_status")

        return {
            "id": concept.id,
            "title": concept.title,
            "slug": concept.slug,
            "status": status,
            "category": category,
            "tags": tags,
            "has_summary": has_summary,
            "has_content": has_content,
            "has_tags": has_tags,
            "is_published": is_published,
            "checks_passed": passed,
            "checks_total": 4,
            "completeness_score": round((passed / 4) * 100, 1),
            "relationships_count": rel_count_map.get(concept.id, 0),
            "missing": missing,
        }

    def _evaluate_repository(self, repo, rel_count_map, relationships):
        concepts = list(repo.concepts or [])
        workspaces = list(repo.workspaces or [])
        concept_count = len(concepts)
        concept_ids = {c.id for c in concepts}

        # 1. Knowledge coverage
        knowledge_coverage = round(min(concept_count / TARGET_CONCEPTS_PER_REPO, 1.0) * 100, 1)
        published_count = sum(1 for c in concepts if (c.status or "").upper() == "PUBLISHED")
        draft_count = sum(1 for c in concepts if (c.status or "").upper() == "DRAFT")

        # 2. Documentation completeness
        concept_details = [self._evaluate_concept_completeness(c, rel_count_map) for c in concepts]
        if concept_count == 0:
            doc_completeness = 0.0
            total_doc_checks_passed = 0
            total_doc_checks_possible = 0
        else:
            total_doc_checks_passed = sum(d["checks_passed"] for d in concept_details)
            total_doc_checks_possible = concept_count * 4
            doc_completeness = round((total_doc_checks_passed / total_doc_checks_possible) * 100, 1)

        # 3. Concept diversity
        distinct_categories = sorted({d["category"] for d in concept_details if d["category"]})
        distinct_tags = sorted({tag for d in concept_details for tag in d["tags"]})
        if concept_count == 0:
            concept_diversity = 0.0
        else:
            cat_ratio = min(len(distinct_categories) / TARGET_DISTINCT_CATEGORIES, 1.0)
            tag_ratio = min(len(distinct_tags) / TARGET_DISTINCT_TAGS, 1.0)
            concept_diversity = round((0.6 * cat_ratio + 0.4 * tag_ratio) * 100, 1)

        # 4. Relationship coverage
        connected_concepts = [d for d in concept_details if d["relationships_count"] > 0]
        unconnected_concepts = [d for d in concept_details if d["relationships_count"] == 0]
        internal_edges_count = sum(
            1 for r in relationships
            if r.source_concept_id in concept_ids and r.target_concept_id in concept_ids
        )
        cross_repo_edges_count = sum(
            1 for r in relationships
            if (r.source_concept_id in concept_ids) ^ (r.target_concept_id in concept_ids)
        )
        if concept_count == 0:
            relationship_coverage = 0.0
        else:
            relationship_coverage = round((len(connected_concepts) / concept_count) * 100, 1)

        # 5. Organization quality
        has_workspace = len(workspaces) >= 1
        has_description = len((repo.description or "").strip()) >= MIN_REPO_DESC_LEN
        has_language = bool((repo.primary_language or "").strip())
        has_vcs_url = bool((repo.vcs_url or "").strip())
        org_passed = sum([has_workspace, has_description, has_language, has_vcs_url])
        organization_quality = round((org_passed / 4) * 100, 1)

        missing_metadata = []
        if not has_workspace:
            missing_metadata.append("workspace")
        if not has_description:
            missing_metadata.append("description")
        if not has_language:
            missing_metadata.append("primary_language")
        if not has_vcs_url:
            missing_metadata.append("vcs_url")

        # Overall weighted score (documentation & graph maturity, NOT code completeness)
        documentation_score = round(
            0.25 * knowledge_coverage
            + 0.30 * doc_completeness
            + 0.15 * concept_diversity
            + 0.15 * relationship_coverage
            + 0.15 * organization_quality,
            1,
        )

        if concept_count == 0:
            data_sufficiency = "NO_CONCEPTS"
        elif concept_count == 1:
            data_sufficiency = "MINIMAL_DATA"
        elif concept_count >= 3 and documentation_score >= 70.0:
            data_sufficiency = "WELL_DOCUMENTED"
        else:
            data_sufficiency = "PARTIAL"

        # Structured gap list
        gaps = []
        if concept_count == 0:
            gaps.append("No knowledge concepts linked to this repository.")
        elif concept_count < 3:
            gaps.append(
                f"Low concept coverage ({concept_count}/{TARGET_CONCEPTS_PER_REPO} target concepts)."
            )
        if not has_workspace:
            gaps.append("Repository is not assigned to any Workspace.")
        if any(not d["has_content"] for d in concept_details):
            missing_body_count = sum(1 for d in concept_details if not d["has_content"])
            gaps.append(f"{missing_body_count} linked concept(s) lack substantive Markdown content.")
        if any(not d["has_tags"] for d in concept_details):
            missing_tags_count = sum(1 for d in concept_details if not d["has_tags"])
            gaps.append(f"{missing_tags_count} linked concept(s) have no tags.")
        if concept_count >= 2 and len(unconnected_concepts) > 0:
            gaps.append(
                f"{len(unconnected_concepts)} of {concept_count} concept(s) have no Knowledge Graph relationships."
            )
        if missing_metadata:
            gaps.append(f"Missing repository metadata: {', '.join(missing_metadata)}.")

        return {
            "id": repo.id,
            "name": repo.name,
            "slug": repo.slug,
            "description": repo.description or "",
            "vcs_url": repo.vcs_url or "",
            "primary_language": repo.primary_language or "",
            "status": repo.status,
            "workspaces": [{"id": w.id, "name": w.name, "slug": w.slug} for w in workspaces],
            "documentation_score": documentation_score,
            "data_sufficiency": data_sufficiency,
            "counts": {
                "concepts": concept_count,
                "published_concepts": published_count,
                "draft_concepts": draft_count,
                "workspaces": len(workspaces),
                "distinct_categories": len(distinct_categories),
                "distinct_tags": len(distinct_tags),
                "connected_concepts": len(connected_concepts),
                "unconnected_concepts": len(unconnected_concepts),
                "internal_edges": internal_edges_count,
                "cross_repo_edges": cross_repo_edges_count,
            },
            "dimensions": {
                "knowledge_coverage": {
                    "score": knowledge_coverage,
                    "weight": 0.25,
                    "numerator": min(concept_count, TARGET_CONCEPTS_PER_REPO),
                    "denominator": TARGET_CONCEPTS_PER_REPO,
                    "evidence": f"{concept_count} linked concept(s) vs {TARGET_CONCEPTS_PER_REPO} baseline",
                },
                "documentation_completeness": {
                    "score": doc_completeness,
                    "weight": 0.30,
                    "numerator": total_doc_checks_passed,
                    "denominator": total_doc_checks_possible,
                    "evidence": (
                        "No concepts linked yet"
                        if concept_count == 0
                        else f"{total_doc_checks_passed}/{total_doc_checks_possible} concept quality checks passed"
                    ),
                },
                "concept_diversity": {
                    "score": concept_diversity,
                    "weight": 0.15,
                    "categories": distinct_categories,
                    "tags": distinct_tags,
                    "evidence": f"{len(distinct_categories)} category(ies), {len(distinct_tags)} unique tag(s)",
                },
                "relationship_coverage": {
                    "score": relationship_coverage,
                    "weight": 0.15,
                    "numerator": len(connected_concepts),
                    "denominator": concept_count,
                    "evidence": (
                        "No concepts linked yet"
                        if concept_count == 0
                        else f"{len(connected_concepts)}/{concept_count} concepts connected ({internal_edges_count} intra-repo, {cross_repo_edges_count} cross-repo edges)"
                    ),
                },
                "organization_quality": {
                    "score": organization_quality,
                    "weight": 0.15,
                    "numerator": org_passed,
                    "denominator": 4,
                    "missing_fields": missing_metadata,
                    "evidence": f"{org_passed}/4 metadata checks passed",
                },
            },
            "concepts": concept_details,
            "gaps": gaps,
        }

    def compute_full_report(self):
        """Compute repository progress metrics, platform overview, and knowledge health."""
        snapshot = self.repository.load_snapshot()
        workspaces = snapshot["workspaces"]
        repositories = snapshot["repositories"]
        concepts = snapshot["concepts"]
        relationships = snapshot["relationships"]

        # Count explicit graph relationships per concept
        rel_count_map = {}
        for rel in relationships:
            rel_count_map[rel.source_concept_id] = rel_count_map.get(rel.source_concept_id, 0) + 1
            rel_count_map[rel.target_concept_id] = rel_count_map.get(rel.target_concept_id, 0) + 1

        repo_reports = [
            self._evaluate_repository(repo, rel_count_map, relationships)
            for repo in repositories
        ]

        # Platform-level concept health & category distribution
        concept_health_details = [
            self._evaluate_concept_completeness(c, rel_count_map) for c in concepts
        ]
        category_distribution = {}
        uncategorized_count = 0
        status_breakdown = {"DRAFT": 0, "PUBLISHED": 0, "ARCHIVED": 0}
        orphan_concepts = []
        concepts_missing_content = []
        concepts_missing_tags = []

        for c, c_detail in zip(concepts, concept_health_details):
            cat = c_detail["category"]
            if cat:
                category_distribution[cat] = category_distribution.get(cat, 0) + 1
            else:
                uncategorized_count += 1

            st = c_detail["status"]
            status_breakdown[st] = status_breakdown.get(st, 0) + 1

            repo_links = len(c.repositories or [])
            if repo_links == 0 and c_detail["relationships_count"] == 0:
                orphan_concepts.append({"id": c.id, "slug": c.slug, "title": c.title})
            if not c_detail["has_content"]:
                concepts_missing_content.append({"id": c.id, "slug": c.slug, "title": c.title})
            if not c_detail["has_tags"]:
                concepts_missing_tags.append({"id": c.id, "slug": c.slug, "title": c.title})

        empty_workspaces = [
            {"id": w.id, "slug": w.slug, "name": w.name}
            for w in workspaces
            if len(w.repositories or []) == 0
        ]

        repo_count = len(repo_reports)
        avg_score = (
            round(sum(r["documentation_score"] for r in repo_reports) / repo_count, 1)
            if repo_count > 0
            else None
        )
        well_documented_count = sum(
            1 for r in repo_reports if r["data_sufficiency"] == "WELL_DOCUMENTED"
        )
        insufficient_data_repos = sum(
            1 for r in repo_reports if r["data_sufficiency"] in ("NO_CONCEPTS", "MINIMAL_DATA")
        )

        return {
            "overview": {
                "total_workspaces": len(workspaces),
                "total_repositories": repo_count,
                "total_concepts": len(concepts),
                "total_relationships": len(relationships),
                "average_documentation_score": avg_score,
                "well_documented_repositories": well_documented_count,
                "insufficient_data_repositories": insufficient_data_repos,
                "has_sufficient_data": repo_count > 0 and len(concepts) > 0,
                "disclaimer": (
                    "Scores measure documentation coverage, structural completeness, and Knowledge Graph connectivity "
                    "from stored Forge data — not source-code completion or production readiness."
                ),
            },
            "repositories": repo_reports,
            "category_distribution": category_distribution,
            "uncategorized_concepts_count": uncategorized_count,
            "concept_status_breakdown": status_breakdown,
            "knowledge_health": {
                "orphan_concepts_count": len(orphan_concepts),
                "orphan_concepts": orphan_concepts,
                "concepts_missing_content_count": len(concepts_missing_content),
                "concepts_missing_content": concepts_missing_content,
                "concepts_missing_tags_count": len(concepts_missing_tags),
                "empty_workspaces_count": len(empty_workspaces),
                "empty_workspaces": empty_workspaces,
            },
            "metric_definitions": METRIC_DEFINITIONS,
            "_raw_snapshot": snapshot,
        }

    def get_progress_overview(self):
        """Public progress overview payload (strips internal raw ORM objects)."""
        report = self.compute_full_report()
        report.pop("_raw_snapshot", None)
        return report

    def get_repository_progress(self, slug):
        """Compute detailed progress report for a single repository by slug."""
        report = self.compute_full_report()
        repo = next((r for r in report["repositories"] if r["slug"] == slug), None)
        if not repo:
            raise LookupError(f"Repository with slug '{slug}' not found.")
        return {
            "repository": repo,
            "metric_definitions": METRIC_DEFINITIONS,
            "disclaimer": report["overview"]["disclaimer"],
        }
