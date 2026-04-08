import hashlib
import hmac
import secrets


class User:
    def __init__(self, id, username, password, email,
                 is_admin=False, permissions=None, privacy="public"):

        # --- Core Fields ---
        self.id = id                    # Primary Key
        self.username = username
        self.password_hash = self._hash_password(password)
        self.email = email

        # --- Admin / Settings ---
        self.is_admin = is_admin
        self.permissions = permissions if permissions else []
        self.privacy = privacy

        # --- Relationships (instead of FK fields) ---
        self.post_fk = []        # list of post IDs
        self.comments_fk = []    # list of comment IDs

    # -------------------------
    # Helper Methods
    # -------------------------

    @staticmethod
    def _hash_password(password):
        salt = secrets.token_hex(16)
        digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"{salt}${digest}"

    def check_password(self, password):
        salt, stored_digest = self.password_hash.split("$", 1)
        digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(stored_digest, digest)

    def add_post(self, post_id):
        self.post_fk.append(post_id)

    def add_comment(self, comment_id):
        self.comments_fk.append(comment_id)

    def set_privacy(self, privacy):
        self.privacy = privacy

    def add_permission(self, permission):
        if permission not in self.permissions:
            self.permissions.append(permission)

    def is_allowed(self, permission):
        return self.is_admin or permission in self.permissions

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"