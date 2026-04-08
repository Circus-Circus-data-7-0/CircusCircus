import re
from user.models.user import User

# -------------------------
# Regex Validation Rules
# -------------------------

password_regex = re.compile(r"^[a-zA-Z0-9!@#%&]{6,40}$")
username_regex = re.compile(r"^[a-zA-Z0-9!@#%&]{4,40}$")
email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# -------------------------
# Validation Functions
# -------------------------

def valid_username(username):
    return bool(username_regex.match(username))


def valid_password(password):
    return bool(password_regex.match(password))


def valid_email(email):
    return bool(email_regex.match(email))


# -------------------------
# Account Creation
# -------------------------

def register_user(user_id, username, password, email, privacy="public"):
    if not valid_username(username):
        return "Invalid username"

    if not valid_password(password):
        return "Invalid password"

    if not valid_email(email):
        return "Invalid email"

    if privacy not in ["public", "private"]:
        return "Invalid privacy setting"

    # Create user object
    new_user = User(
        id=user_id,
        username=username,
        password=password,
        email=email,
        privacy=privacy
    )

    new_user.add_permission("post:create")
    new_user.add_permission("comment:create")

    return new_user