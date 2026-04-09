from flask import Flask
from forum.routes import rt
from forum.models import db


def create_app():
    """Construct the Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    app.register_blueprint(rt)
    db.init_app(app)
    return app

