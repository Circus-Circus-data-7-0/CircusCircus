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

