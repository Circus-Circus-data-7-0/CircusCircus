from flask import Flask
from .auth_routes import auth_bp
from .post_routes import posts_bp
from .subforum import subforum_rt as subforums_bp

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(subforums_bp)
    # Set globals
    from .models import db
    db.init_app(app)
    
    with app.app_context():
        # Create tables on startup so the app can run against a fresh database.
        db.create_all()
        return app

