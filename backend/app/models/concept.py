from app.database.db import db

class Concept(db.Model):

	__tablename__ = "concepts"

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	slug = db.Column(db.String(200), unique=True, nullable=False)
	summary = db.Column(db.Text)

	status = db.Column(
		db.String(20),
		nullable=False,
		default="DRAFT",

	)

	created_at = db.Column(
		db.DateTime,
		server_default=db.func.now(),
		onupdate=db.func.now(),
	)
	
	def __repr__(self):
		return f"<Concept {self.title}>"
