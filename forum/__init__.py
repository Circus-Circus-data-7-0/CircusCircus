from flask import Flask
from .auth_routes import auth_bp
from .comment_routes import comments_bp
from .post_routes import posts_bp
from .subforum_routes import subforums_bp

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    app.register_blueprint(auth_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(subforums_bp)
    # Set globals
    from .models import db
    db.init_app(app)
    
    with app.app_context():
        # Add some routes
        db.create_all()
        return app

