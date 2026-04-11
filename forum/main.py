import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from forum import create_app
from forum.user.services.auth import register_user

app = create_app()

with app.app_context():
    user = register_user(
        username="Bianca123",
        password="Pass123!",
        email="bianca@email.com"
    )

    print(user)