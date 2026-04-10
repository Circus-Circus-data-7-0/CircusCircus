import hashlib
import hmac
import secrets
from typing import List, Optional


class User:
    def __init__(
        self,
        id: int,
        username: str,
        password: str,
        email: str,
        is_admin: bool = False,
        permissions: Optional[List[str]] = None,
        privacy: str = "public"
    ):
        # --- Core Fields ---
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = self._hash_password(password)

        # --- Admin / Settings ---
        self.is_admin = is_admin
        self.permissions = permissions or []
        self.privacy = privacy

        # --- Relationships ---
        self.post_fk: List[int] = []
        self.comments_fk: List[int] = []

    # -------------------------
    # Password Handling
    # -------------------------

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"{salt}${digest}"

    def check_password(self, password: str) -> bool:
        try:
            salt, stored_digest = self.password_hash.split("$", 1)
            digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
            return hmac.compare_digest(stored_digest, digest)
        except ValueError:
            return False

    def set_password(self, new_password: str):
        self.password_hash = self._hash_password(new_password)

    # -------------------------
    # Permissions & Privacy
    # -------------------------

    def add_permission(self, permission: str):
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: str):
        if permission in self.permissions:
            self.permissions.remove(permission)

    def is_allowed(self, permission: str) -> bool:
        return self.is_admin or permission in self.permissions

    def set_privacy(self, privacy: str):
        if privacy not in ["public", "private", "friends"]:
            raise ValueError("Invalid privacy setting")
        self.privacy = privacy

    # -------------------------
    # Relationships
    # -------------------------

    def add_post(self, post_id: int):
        if post_id not in self.post_fk:
            self.post_fk.append(post_id)

    def add_comment(self, comment_id: int):
        if comment_id not in self.comments_fk:
            self.comments_fk.append(comment_id)

    # -------------------------
    # Debugging / Logging
    # -------------------------

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"