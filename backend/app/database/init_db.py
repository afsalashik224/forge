from app import create_app
from app.database.db import db
import app.models

app = create_app()

with app.app_context():
	db.create_all()
	print("Database initialized successfully!")
