from sqlalchemy.exc import IntegrityError
from app.database.db import db
from app.models.concept import Concept

_UNSET = object()


class ConceptRepository:

	def create(self, concept):
		try:
			db.session.add(concept)
			db.session.commit()
			return concept
		except IntegrityError:
			db.session.rollback()
			raise

	def get_by_id(self, concept_id):
		return db.session.get(Concept, concept_id)

	def get_by_slug(self, slug):
		return Concept.query.filter_by(slug=slug).first()

	def get_all(self):
		return Concept.query.all()

	def update(self, concept, title=_UNSET, slug=_UNSET, summary=_UNSET, status=_UNSET, content=_UNSET, tags=_UNSET, category=_UNSET):
		try:
			if title is not _UNSET:
				concept.title = title
			if slug is not _UNSET:
				concept.slug = slug
			if summary is not _UNSET:
				concept.summary = summary
			if status is not _UNSET:
				concept.status = status
			if content is not _UNSET:
				concept.content = content
			if tags is not _UNSET:
				concept.tags = tags
			if category is not _UNSET:
				concept.category = category
			db.session.commit()
			return concept
		except IntegrityError:
			db.session.rollback()
			raise

	def delete(self, concept):
		try:
			db.session.delete(concept)
			db.session.commit()
			return True
		except Exception:
			db.session.rollback()
			raise

