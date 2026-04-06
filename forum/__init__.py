from flask import Flask
from forum.routes import rt

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    # Register the main routes blueprint.
    app.register_blueprint(rt)

    # Initialize the shared database object on this app.
    from forum.models import db
    db.init_app(app)
    
    with app.app_context():
        # Create tables on startup so the app can run against a fresh database.
        db.create_all()
        return app

