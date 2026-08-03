from app import create_app
import app.models 

from app.models.concept import Concept
from app.repositories.concept_repository import ConceptRepository

app = create_app()

with app.app_context():

	repository = ConceptRepository()

	concept = Concept(
		title="Git Branches",
		slug="git-branches",
		summary= "An independent line of development."
	)

	repository.create(concept)

	print(repository.get_all())
