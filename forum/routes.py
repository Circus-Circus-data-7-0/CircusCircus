"""Legacy import shim for split route modules.

Route handlers were moved into:
- auth_routes.py
- comment_routes.py
- post_routes.py
- subforum_routes.py
"""

from .auth_routes import auth_bp
from .comment_routes import comments_bp
from .post_routes import posts_bp
from .subforum_routes import subforums_bp


