from flask import Flask


from app.database.db import db
from app.config.settings import Settings
from app.api.concept_api import concept_api

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = Settings.SECRET_KEY

    app.config["SQLALCHEMY_DATABASE_URI"] = Settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.register_blueprint(concept_api)

    db.init_app(app)

    @app.get("/health")
    def health():
        return {
            "application": Settings.APP_NAME,
            "version": Settings.APP_VERSION,
            "environment": Settings.ENVIRONMENT,
            "status": "healthy",
        }

    return app
