import json
from collections import deque

from app.models.concept import Concept
from app.models.concept_relationship import (
    ALLOWED_RELATIONSHIP_TYPES,
    ConceptRelationship,
)
from app.repositories.graph_repository import GraphRepository


STRUCTURAL_RELATIONSHIP_TYPES = (
    "CONTAINS_REPO",
    "DOCUMENTS_CONCEPT",
)

ALL_EDGE_TYPES = STRUCTURAL_RELATIONSHIP_TYPES + ALLOWED_RELATIONSHIP_TYPES


class DuplicateRelationshipError(ValueError):
    """Raised when attempting to create a relationship edge that already exists."""


class GraphService:
    """Domain logic for Knowledge Graph construction, filtering, exploration, and edge CRUD."""

    def __init__(self, repository=None):
        self.repository = repository or GraphRepository()

    @staticmethod
    def _parse_tags(tags_raw):
        if not tags_raw:
            return []
        try:
            parsed = json.loads(tags_raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    @staticmethod
    def serialize_relationship(rel):
        return {
            "id": rel.id,
            "source_concept_id": rel.source_concept_id,
            "source_slug": rel.source_concept.slug if rel.source_concept else None,
            "source_title": rel.source_concept.title if rel.source_concept else None,
            "target_concept_id": rel.target_concept_id,
            "target_slug": rel.target_concept.slug if rel.target_concept else None,
            "target_title": rel.target_concept.title if rel.target_concept else None,
            "relationship_type": rel.relationship_type,
            "description": rel.description or "",
            "created_at": rel.created_at.isoformat() if rel.created_at else None,
            "updated_at": rel.updated_at.isoformat() if rel.updated_at else None,
        }

    def create_relationship(
        self,
        source_concept_id=None,
        target_concept_id=None,
        source_slug=None,
        target_slug=None,
        relationship_type=None,
        description=None,
    ):
        source = None
        if source_concept_id is not None:
            source = Concept.query.filter_by(id=source_concept_id).first()
        elif source_slug:
            source = Concept.query.filter_by(slug=source_slug).first()

        if not source:
            ident = source_slug or source_concept_id
            raise LookupError(f"Source concept '{ident}' not found.")

        target = None
        if target_concept_id is not None:
            target = Concept.query.filter_by(id=target_concept_id).first()
        elif target_slug:
            target = Concept.query.filter_by(slug=target_slug).first()

        if not target:
            ident = target_slug or target_concept_id
            raise LookupError(f"Target concept '{ident}' not found.")

        if source.id == target.id:
            raise ValueError("Self-referential relationships are not allowed.")

        if not relationship_type or not isinstance(relationship_type, str):
            raise ValueError(
                f"Field 'relationship_type' must be one of: {', '.join(ALLOWED_RELATIONSHIP_TYPES)}."
            )

        normalized_type = relationship_type.strip().upper()
        if normalized_type not in ALLOWED_RELATIONSHIP_TYPES:
            raise ValueError(
                f"Invalid relationship_type '{relationship_type}'. "
                f"Allowed values: {', '.join(ALLOWED_RELATIONSHIP_TYPES)}."
            )

        existing = self.repository.get_relationship(source.id, target.id, normalized_type)
        if existing:
            raise DuplicateRelationshipError(
                f"Relationship '{source.slug}' -[{normalized_type}]-> '{target.slug}' already exists."
            )

        rel = ConceptRelationship(
            source_concept_id=source.id,
            target_concept_id=target.id,
            relationship_type=normalized_type,
            description=description.strip() if isinstance(description, str) and description.strip() else None,
        )
        return self.repository.create_relationship(rel)

    def get_relationship_by_id(self, relationship_id):
        return self.repository.get_relationship_by_id(relationship_id)

    def list_relationships(self, concept_slug=None, relationship_type=None):
        concept_id = None
        if concept_slug:
            concept = Concept.query.filter_by(slug=concept_slug).first()
            if not concept:
                raise LookupError(f"Concept with slug '{concept_slug}' not found.")
            concept_id = concept.id

        normalized_type = None
        if relationship_type:
            normalized_type = relationship_type.strip().upper()
            if normalized_type not in ALLOWED_RELATIONSHIP_TYPES:
                raise ValueError(
                    f"Invalid relationship_type '{relationship_type}'. "
                    f"Allowed values: {', '.join(ALLOWED_RELATIONSHIP_TYPES)}."
                )

        return self.repository.get_all_relationships(
            concept_id=concept_id,
            relationship_type=normalized_type,
        )

    def delete_relationship(self, relationship_id):
        rel = self.repository.get_relationship_by_id(relationship_id)
        if not rel:
            raise LookupError(f"Relationship with id '{relationship_id}' not found.")

        payload = self.serialize_relationship(rel)
        self.repository.delete_relationship(rel)
        return payload

    def _build_full_graph(self):
        """Construct the complete node & edge maps from stored database entities."""
        entities = self.repository.load_graph_entities()
        nodes = {}
        edges = []

        for ws in entities["workspaces"]:
            node_id = f"workspace:{ws.id}"
            nodes[node_id] = {
                "id": node_id,
                "entity_type": "workspace",
                "entity_id": ws.id,
                "slug": ws.slug,
                "label": ws.name,
                "description": ws.description or "",
                "status": None,
                "category": None,
                "tags": [],
                "primary_language": None,
                "metadata": {
                    "repositories_count": len(ws.repositories),
                },
            }

        for repo in entities["repositories"]:
            node_id = f"repository:{repo.id}"
            nodes[node_id] = {
                "id": node_id,
                "entity_type": "repository",
                "entity_id": repo.id,
                "slug": repo.slug,
                "label": repo.name,
                "description": repo.description or "",
                "vcs_url": repo.vcs_url or "",
                "primary_language": repo.primary_language or "",
                "status": repo.status,
                "category": None,
                "tags": [],
                "metadata": {
                    "workspaces_count": len(repo.workspaces),
                    "concepts_count": len(repo.concepts),
                },
            }

        for concept in entities["concepts"]:
            node_id = f"concept:{concept.id}"
            nodes[node_id] = {
                "id": node_id,
                "entity_type": "concept",
                "entity_id": concept.id,
                "slug": concept.slug,
                "label": concept.title,
                "description": concept.summary or "",
                "status": concept.status,
                "category": concept.category or "",
                "tags": self._parse_tags(concept.tags),
                "primary_language": None,
                "metadata": {
                    "repositories_count": len(concept.repositories),
                    "has_content": bool(concept.content and concept.content.strip()),
                },
            }

        # Structural edges: Workspace -> Repository
        for ws in entities["workspaces"]:
            src_id = f"workspace:{ws.id}"
            for repo in ws.repositories:
                tgt_id = f"repository:{repo.id}"
                if tgt_id in nodes:
                    edges.append({
                        "id": f"ws-repo:{ws.id}:{repo.id}",
                        "source": src_id,
                        "target": tgt_id,
                        "relationship_type": "CONTAINS_REPO",
                        "origin": "structural",
                        "editable": True,
                        "description": None,
                        "relationship_id": None,
                    })

        # Structural edges: Repository -> Concept
        for repo in entities["repositories"]:
            src_id = f"repository:{repo.id}"
            for concept in repo.concepts:
                tgt_id = f"concept:{concept.id}"
                if tgt_id in nodes:
                    edges.append({
                        "id": f"repo-concept:{repo.id}:{concept.id}",
                        "source": src_id,
                        "target": tgt_id,
                        "relationship_type": "DOCUMENTS_CONCEPT",
                        "origin": "structural",
                        "editable": True,
                        "description": None,
                        "relationship_id": None,
                    })

        # Explicit Knowledge Graph edges: Concept -> Concept
        for rel in entities["relationships"]:
            src_id = f"concept:{rel.source_concept_id}"
            tgt_id = f"concept:{rel.target_concept_id}"
            if src_id in nodes and tgt_id in nodes:
                edges.append({
                    "id": f"rel:{rel.id}",
                    "relationship_id": rel.id,
                    "source": src_id,
                    "target": tgt_id,
                    "relationship_type": rel.relationship_type,
                    "origin": "explicit",
                    "editable": True,
                    "description": rel.description or "",
                })

        return nodes, edges, entities

    def build_graph(
        self,
        entity_types=None,
        relationship_types=None,
        workspace_slug=None,
        repository_slug=None,
        category=None,
        status=None,
        query=None,
        focus_node_id=None,
        depth=1,
        include_neighbors=False,
    ):
        nodes, edges, entities = self._build_full_graph()

        # Resolve focus_node_id first if provided (accepts 'concept:3' or 'concept:my-slug')
        resolved_focus = None
        if focus_node_id:
            if focus_node_id in nodes:
                resolved_focus = focus_node_id
            elif ":" in focus_node_id:
                etype, ident = focus_node_id.split(":", 1)
                for nid, n in nodes.items():
                    if n["entity_type"] == etype and n["slug"] == ident:
                        resolved_focus = nid
                        break
            if not resolved_focus:
                raise LookupError(f"Graph node '{focus_node_id}' not found.")

        allowed_ids = set(nodes.keys())

        # Workspace scope filter: keep workspace + its repos + concepts linked to those repos
        if workspace_slug:
            ws = next((w for w in entities["workspaces"] if w.slug == workspace_slug), None)
            if not ws:
                raise LookupError(f"Workspace with slug '{workspace_slug}' not found.")
            scoped = {f"workspace:{ws.id}"}
            for repo in ws.repositories:
                scoped.add(f"repository:{repo.id}")
                for concept in repo.concepts:
                    scoped.add(f"concept:{concept.id}")
            allowed_ids &= scoped

        # Repository scope filter: keep repo + its workspaces + its concepts
        if repository_slug:
            repo = next((r for r in entities["repositories"] if r.slug == repository_slug), None)
            if not repo:
                raise LookupError(f"Repository with slug '{repository_slug}' not found.")
            scoped = {f"repository:{repo.id}"}
            for ws in repo.workspaces:
                scoped.add(f"workspace:{ws.id}")
            for concept in repo.concepts:
                scoped.add(f"concept:{concept.id}")
            allowed_ids &= scoped

        # Category filter (applies to concept nodes; keeps non-concept nodes unless filtered out)
        if category:
            allowed_ids = {
                nid for nid in allowed_ids
                if nodes[nid]["entity_type"] != "concept" or nodes[nid]["category"] == category
            }

        # Status filter (applies to concept and repository nodes)
        if status:
            normalized_status = status.strip().upper()
            allowed_ids = {
                nid for nid in allowed_ids
                if nodes[nid]["entity_type"] == "workspace"
                or (nodes[nid]["status"] or "").upper() == normalized_status
            }

        # Entity type filter
        if entity_types:
            valid_types = {"workspace", "repository", "concept"}
            requested_types = {t.strip().lower() for t in entity_types if t.strip().lower() in valid_types}
            if requested_types:
                allowed_ids = {
                    nid for nid in allowed_ids
                    if nodes[nid]["entity_type"] in requested_types
                }

        # Relationship type filter
        allowed_rel_types = None
        if relationship_types:
            allowed_rel_types = {rt.strip().upper() for rt in relationship_types if rt.strip()}

        # Active edges before query/focus
        candidate_edges = [
            e for e in edges
            if e["source"] in allowed_ids
            and e["target"] in allowed_ids
            and (allowed_rel_types is None or e["relationship_type"] in allowed_rel_types)
        ]

        # Query text filter
        if query:
            q = query.strip().lower()
            matched_ids = set()
            for nid in allowed_ids:
                n = nodes[nid]
                searchable = " ".join([
                    n["label"] or "",
                    n["slug"] or "",
                    n["description"] or "",
                    n["category"] or "",
                    n["primary_language"] or "",
                    " ".join(n["tags"] or []),
                ]).lower()
                if q in searchable:
                    matched_ids.add(nid)

            if include_neighbors:
                neighbor_ids = set(matched_ids)
                for e in candidate_edges:
                    if e["source"] in matched_ids:
                        neighbor_ids.add(e["target"])
                    if e["target"] in matched_ids:
                        neighbor_ids.add(e["source"])
                allowed_ids = neighbor_ids
            else:
                allowed_ids = matched_ids

        # Focus BFS neighborhood filter
        if resolved_focus:
            if resolved_focus not in allowed_ids:
                # Ensure focus node itself stays anchored when exploring its neighborhood
                allowed_ids.add(resolved_focus)
                candidate_edges = [
                    e for e in edges
                    if e["source"] in allowed_ids
                    and e["target"] in allowed_ids
                    and (allowed_rel_types is None or e["relationship_type"] in allowed_rel_types)
                ]

            hop_limit = max(1, min(int(depth or 1), 3))
            adj = {nid: set() for nid in allowed_ids}
            for e in candidate_edges:
                adj[e["source"]].add(e["target"])
                adj[e["target"]].add(e["source"])

            visited = {resolved_focus}
            queue = deque([(resolved_focus, 0)])
            while queue:
                curr, dist = queue.popleft()
                if dist >= hop_limit:
                    continue
                for nxt in adj.get(curr, ()):
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, dist + 1))
            allowed_ids = visited

        final_edges = [
            e for e in edges
            if e["source"] in allowed_ids
            and e["target"] in allowed_ids
            and (allowed_rel_types is None or e["relationship_type"] in allowed_rel_types)
        ]

        # Compute degree within the returned graph
        degree_map = {nid: 0 for nid in allowed_ids}
        counts_by_rel = {}
        for e in final_edges:
            degree_map[e["source"]] += 1
            degree_map[e["target"]] += 1
            rt = e["relationship_type"]
            counts_by_rel[rt] = counts_by_rel.get(rt, 0) + 1

        final_nodes = []
        counts_by_entity = {"workspace": 0, "repository": 0, "concept": 0}
        for nid in sorted(allowed_ids):
            node_data = dict(nodes[nid])
            node_data["degree"] = degree_map[nid]
            final_nodes.append(node_data)
            counts_by_entity[node_data["entity_type"]] += 1

        return {
            "nodes": final_nodes,
            "edges": final_edges,
            "stats": {
                "total_nodes": len(final_nodes),
                "total_edges": len(final_edges),
                "counts_by_entity": counts_by_entity,
                "counts_by_relationship": counts_by_rel,
            },
            "relationship_types": list(ALLOWED_RELATIONSHIP_TYPES),
            "all_edge_types": list(ALL_EDGE_TYPES),
            "focus_node_id": resolved_focus,
        }

    def explore_node(self, entity_type, identifier, depth=1):
        """Return a node and its connected neighbors and incident edges."""
        nodes, edges, _ = self._build_full_graph()

        target_id = None
        candidate_by_id = f"{entity_type}:{identifier}"
        if candidate_by_id in nodes:
            target_id = candidate_by_id
        else:
            for nid, n in nodes.items():
                if n["entity_type"] == entity_type and n["slug"] == identifier:
                    target_id = nid
                    break

        if not target_id:
            raise LookupError(f"{entity_type.capitalize()} '{identifier}' not found in graph.")

        subgraph = self.build_graph(focus_node_id=target_id, depth=depth)
        direct_edges = [e for e in edges if e["source"] == target_id or e["target"] == target_id]

        outgoing = []
        incoming = []
        for e in direct_edges:
            if e["source"] == target_id:
                outgoing.append({**e, "neighbor": nodes[e["target"]]})
            else:
                incoming.append({**e, "neighbor": nodes[e["source"]]})

        return {
            "node": nodes[target_id],
            "outgoing": outgoing,
            "incoming": incoming,
            "subgraph": subgraph,
        }
