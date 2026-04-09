from flask import Flask
from .routes import rt
from .subforum_route import rt

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    # Register the main routes blueprint.
    app.register_blueprint(rt)
    # Set globals
    from .models import db
    db.init_app(app)
    
    with app.app_context():
        # Create tables on startup so the app can run against a fresh database.
        db.create_all()
        return app

