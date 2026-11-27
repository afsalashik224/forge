from app.database.db import db

class Concept(db.Model):

	__tablename__ = "concepts"

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	slug = db.Column(db.String(200), unique=True, nullable=False)
	summary = db.Column(db.Text)
	content = db.Column(db.Text)
	tags = db.Column(db.Text, default="[]")
	category = db.Column(db.String(50), default="")

	status = db.Column(
		db.String(20),
		nullable=False,
		default="DRAFT",

	)

	created_at = db.Column(
		db.DateTime,
		server_default=db.func.now(),
		nullable=False,
	)

	updated_at = db.Column(
		db.DateTime,
		server_default=db.func.now(),
		onupdate=db.func.now(),
		nullable=True,
	)

	repositories = db.relationship(
		"Repository",
		secondary="repository_concepts",
		back_populates="concepts",
		lazy="select",
	)
	
	def __repr__(self):
		return f"<Concept {self.title}>"
