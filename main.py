from forum import create_app
from user.services.auth import register_user

app = create_app()

with app.app_context():
    user = register_user(
        username="Bianca123",
        password="Pass123!",
        email="bianca@email.com"
    )

    print(user)
