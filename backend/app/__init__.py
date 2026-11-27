from flask import Flask, jsonify

from app.database.db import db
from app.config.settings import Settings
from app.api.concept_api import concept_api
from app.api.workspace_api import workspace_api
from app.api.repository_api import repository_api
from app.api.graph_api import graph_api


def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = Settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = Settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    app.register_blueprint(concept_api)
    app.register_blueprint(workspace_api)
    app.register_blueprint(repository_api)
    app.register_blueprint(graph_api)

    db.init_app(app)

    @app.get("/health")
    def health():
        return {
            "application": Settings.APP_NAME,
            "version": Settings.APP_VERSION,
            "environment": Settings.ENVIRONMENT,
            "status": "healthy",
        }

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": getattr(error, "description", "Bad request."),
            "message": getattr(error, "description", "Bad request.")
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": getattr(error, "description", "Resource not found."),
            "message": getattr(error, "description", "Resource not found.")
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "error": "Method not allowed.",
            "message": "Method not allowed."
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal server error.",
            "message": "Internal server error."
        }), 500

    return app
