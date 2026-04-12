from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime
from .models import db
from .user_setting import UserSettings
# Shared SQLAlchemy object used by the app factory and all models.
from flask_sqlalchemy import SQLAlchemy

#db = SQLAlchemy()

class User(UserMixin, db.Model):
    # Store account information and ownership of posts/comments.
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    admin = db.Column(db.Boolean, default=False)
    privacy = db.Column(db.String(20), default="public")
    posts = db.relationship("Post", backref="user")
    settings = db.relationship("UserSettings", uselist=False, back_populates="user")

    def __init__(self, email, username, password, privacy="public", admin=False):
        # Save the hashed password instead of the plain text password.
        self.email = email
        self.username = username
        self.set_password(password)
        self.privacy = privacy
        self.admin = admin

    @property
    def password(self):
        # Passwords are write-only and stored as a hash.
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, password):
        self.set_password(password)

    @property
    def is_admin(self):
        return self.admin

    @is_admin.setter
    def is_admin(self, value):
        self.admin = value


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Compare a password guess against the stored hash.
        return check_password_hash(self.password_hash, password)


    def set_privacy(self, privacy):
        if privacy not in ["public", "private"]:
            raise ValueError("Privacy must be 'public' or 'private'")
        self.privacy = privacy


# from .models import User

import re

##
# Some utility routines.
##

password_regex = re.compile("^[a-zA-Z0-9!@#%&]{6,40}$")
username_regex = re.compile("^[a-zA-Z0-9!@#%&]{4,40}$")
email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
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
def valid_email(email):
	return bool(email_regex.match(email))

#########################################################################

from flask import Blueprint, redirect, render_template, request
from flask_login import login_required, login_user, logout_user


#from .user import email_taken, username_taken, valid_email, valid_password, valid_username


auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route('/action_login', methods=['POST'])
def action_login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter(User.username == username).first()
    if user and user.check_password(password):
        login_user(user)
    else:
        return render_template("login.html", errors=["Username or password is incorrect!"])
    return redirect("/")


@auth_bp.route('/action_logout')
@login_required
def action_logout():
    logout_user()
    return redirect("/")


@auth_bp.route('/action_createaccount', methods=['POST'])
def action_createaccount():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    privacy = request.form.get('privacy', 'public')
    errors = []
    retry = False

    if username_taken(username):
        errors.append("Username is already taken!")
        retry = True
    if email_taken(email):
        errors.append("An account already exists with this email!")
        retry = True
    if not valid_username(username):
        errors.append("Username is not valid!")
        retry = True
    if not valid_password(password):
        errors.append("Password must be 6-40 characters and contain only letters, numbers, and !@#%&")
        retry = True
    if not valid_email(email):
        errors.append("Email is not valid!")
        retry = True
    if privacy not in ["public", "private"]:
        errors.append("Privacy must be either public or private")
        retry = True

    if retry:
        return render_template("login.html", errors=errors)

    user = User(email, username, password, privacy=privacy)
    user.settings = UserSettings(profile_visibility=privacy)
    if user.username == "admin":
        user.admin = True
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect("/")


@auth_bp.route('/loginform')
def loginform():
    return render_template("login.html")