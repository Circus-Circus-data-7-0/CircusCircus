from typing import Optional, Tuple
from models.user import User
from utils.validators import valid_username, valid_password, valid_email


# -------------------------
# Database Checks
# -------------------------

def username_taken(db_session, username: str) -> bool:
    return db_session.query(User).filter(User.username == username).first() is not None


def email_taken(db_session, email: str) -> bool:
    return db_session.query(User).filter(User.email == email).first() is not None


# -------------------------
# User Registration Service
# -------------------------

def register_user(
    db_session,
    user_id: int,
    username: str,
    password: str,
    email: str,
    privacy: str = "public"
) -> Tuple[Optional[User], Optional[str]]:
    """
    Creates a new user with validation and DB checks.

    Returns:
        (User, None) on success
        (None, error_message) on failure
    """

    # --- Validation ---
    if not valid_username(username):
        return None, "Invalid username"

    if not valid_password(password):
        return None, "Invalid password"

    if not valid_email(email):
        return None, "Invalid email"

    if privacy not in ["public", "private", "friends"]:
        return None, "Invalid privacy setting"

    # --- Uniqueness Checks ---
    if username_taken(db_session, username):
        return None, "Username already taken"

    if email_taken(db_session, email):
        return None, "Email already in use"

    # --- Create User ---
    new_user = User(
        id=user_id,
        username=username,
        password=password,
        email=email,
        privacy=privacy
    )

    # --- Default Permissions ---
    new_user.add_permission("post:create")
    new_user.add_permission("comment:create")

    # --- Persist to DB ---
    db_session.add(new_user)
    db_session.commit()

    return new_user, None