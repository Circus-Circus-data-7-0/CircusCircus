from user.services.auth import register_user

# Simulate user input
user = register_user(
    user_id=1,
    username="Bianca123",
    password="Pass123!",
    email="bianca@email.com"
)

print(user)