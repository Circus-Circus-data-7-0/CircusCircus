from flask import Blueprint, redirect, render_template, request
from flask_login import login_required, login_user, logout_user

from .models import User, db
from .user import email_taken, username_taken, valid_email, valid_password, valid_username


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
    user.add_permission("post:create")
    user.add_permission("comment:create")
    if user.username == "admin":
        user.admin = True
        user.add_permission("admin:all")
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect("/")


@auth_bp.route('/loginform')
def loginform():
    return render_template("login.html")
