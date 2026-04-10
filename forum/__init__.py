from flask import Flask
from .routes import rt
from .post import post_rt
from .subforum import subforum_rt
from .Reactions import rt_react

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    #I think more blueprints might be used to break routes up into things like
    # post_routes
    # subforum_routes
    # etc
    # Register the main routes blueprint.
    app.register_blueprint(rt)
    app.register_blueprint(post_rt)
    app.register_blueprint(subforum_rt)
    app.register_blueprint(rt_react)
    # Set globals
    from .models import db
    db.init_app(app)
    
    with app.app_context():
        # Create tables on startup so the app can run against a fresh database.
        db.create_all()
        return app

