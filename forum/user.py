from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime

# Shared SQLAlchemy object used by the app factory and all models.
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Database models
class User(UserMixin, db.Model):
    # Store account information and ownership of posts/comments.
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    admin = db.Column(db.Boolean, default=False)
    posts = db.relationship("Post", backref="user")

    def __init__(self, email, username, password):
        # Save the hashed password instead of the plain text password.
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Compare a password guess against the stored hash.
        return check_password_hash(self.password_hash, password)


from .models import User

import re

##
# Some utility routines.
##

password_regex = re.compile("^[a-zA-Z0-9!@#%&]{6,40}$")
username_regex = re.compile("^[a-zA-Z0-9!@#%&]{4,40}$")
#Account checks
def valid_username(username):
	if not username_regex.match(username):
		#username does not meet password reqirements
		return False
	#username is not taken and does meet the password requirements
	return True
def valid_password(password):
	return password_regex.match(password)

def username_taken(username):
	return User.query.filter(User.username == username).first()
def email_taken(email):
	return User.query.filter(User.email == email).first()


##########################################################################
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
