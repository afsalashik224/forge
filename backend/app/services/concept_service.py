import json

from app.database.db import db
from app.models.concept import Concept
from app.models.repository import Repository
from app.repositories.concept_repository import ConceptRepository, _UNSET


VALID_CATEGORIES = {
    "", "architecture", "design-patterns", "devops", "security",
    "performance", "testing", "languages", "frameworks",
    "infrastructure", "data", "networking", "other",
}


class ConceptService:

    def __init__(self, repository=None):
        self.repository = repository or ConceptRepository()

    def create_concept(
        self,
        title,
        slug,
        summary,
        content=None,
        tags=None,
        category=None,
        repository_ids=None,
    ):
        existing = self.repository.get_by_slug(slug)

        if existing:
            raise ValueError(
                f"Concept with slug '{slug}' already exists."
            )

        tags_json = json.dumps(tags if tags else [])

        concept = Concept(
            title=title,
            slug=slug,
            summary=summary,
            content=content or "",
            tags=tags_json,
            category=category or "",
        )

        if repository_ids:
            for repo_id in repository_ids:
                repo = db.session.get(Repository, repo_id)
                if repo and repo not in concept.repositories:
                    concept.repositories.append(repo)

        return self.repository.create(concept)

    def get_all_concepts(self):
        return self.repository.get_all()

    def get_concept_by_slug(self, slug):
        return self.repository.get_by_slug(slug)

    def search_concepts(
        self,
        query=None,
        tags=None,
        category=None,
        status=None,
        repository_slug=None,
        workspace_slug=None,
    ):
        """Search concepts by text query, tags, category, status, repository, and workspace."""
        concepts = self.repository.get_all()
        results = []

        for concept in concepts:
            # Status filter
            if status and concept.status != status:
                continue

            # Category filter
            if category and (concept.category or "") != category:
                continue

            # Repository filter
            if repository_slug:
                repo_slugs = {r.slug for r in getattr(concept, "repositories", [])}
                if repository_slug not in repo_slugs:
                    continue

            # Workspace filter (via linked repositories)
            if workspace_slug:
                ws_slugs = {
                    w.slug
                    for r in getattr(concept, "repositories", [])
                    for w in getattr(r, "workspaces", [])
                }
                if workspace_slug not in ws_slugs:
                    continue

            # Tags filter — concept must have ALL requested tags
            if tags:
                concept_tags = self._parse_tags(concept.tags)
                concept_tags_lower = {t.lower() for t in concept_tags}
                if not all(t.lower() in concept_tags_lower for t in tags):
                    continue

            # Text search across title, slug, summary, content, tags
            if query:
                q = query.lower()
                searchable = " ".join([
                    concept.title or "",
                    concept.slug or "",
                    concept.summary or "",
                    concept.content or "",
                    " ".join(self._parse_tags(concept.tags)),
                ]).lower()
                if q not in searchable:
                    continue

            results.append(concept)

        return results

    def update_concept(
        self,
        current_slug,
        title=_UNSET,
        slug=_UNSET,
        summary=_UNSET,
        status=_UNSET,
        content=_UNSET,
        tags=_UNSET,
        category=_UNSET,
        repository_ids=_UNSET,
    ):
        concept = self.repository.get_by_slug(current_slug)
        if not concept:
            raise LookupError(f"Concept with slug '{current_slug}' not found.")

        if slug is not _UNSET and slug != current_slug:
            existing = self.repository.get_by_slug(slug)
            if existing:
                raise ValueError(f"Concept with slug '{slug}' already exists.")

        # Serialize tags to JSON if provided as a list
        if tags is not _UNSET and tags is not None:
            if isinstance(tags, list):
                tags = json.dumps(tags)

        # Sync associated repositories if provided
        if repository_ids is not _UNSET and repository_ids is not None:
            target_repos = []
            seen_ids = set()
            for repo_id in repository_ids:
                if repo_id in seen_ids:
                    continue
                repo = db.session.get(Repository, repo_id)
                if repo:
                    target_repos.append(repo)
                    seen_ids.add(repo_id)
            concept.repositories = target_repos

        return self.repository.update(
            concept,
            title=title,
            slug=slug,
            summary=summary,
            status=status,
            content=content,
            tags=tags,
            category=category,
        )

    def delete_concept(self, slug):
        concept = self.repository.get_by_slug(slug)
        if not concept:
            raise LookupError(f"Concept with slug '{slug}' not found.")

        concept_id = concept.id
        self.repository.delete(concept)
        return {"id": concept_id, "slug": slug, "title": concept.title}

    @staticmethod
    def _parse_tags(tags_raw):
        """Parse tags from JSON string or return empty list."""
        if not tags_raw:
            return []
        try:
            parsed = json.loads(tags_raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
