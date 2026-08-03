from app.database.db import db
from app.models.concept import Concept


class ConceptRepository:

	def create(self, concept):
		db.session.add(concept)
		db.session.commit()
		return concept


	def get_by_id(self,concept_id):
		return db.session.get(Concept, concept_id)

	def get_by_slug(self, slug):
		return Concept.query.filter_by(slug=slug).first()
	def get_all(self):
		return Concept.query.all()
