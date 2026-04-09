
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
    username = db.Column(db.Text, unique=True)
    password_hash = db.Column(db.Text)
    email = db.Column(db.Text, unique=True)
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


# Post is defined in post.py and imported by routes directly.
# Subforum is defined in subforum.py.

def error(errormessage):
	return "<b style=\"color: red;\">" + errormessage + "</b>"

# def generateLinkPath(subforumid):
# 	links = []
# 	subforum = Subforum.query.filter(Subforum.id == subforumid).first()
# 	parent = Subforum.query.filter(Subforum.id == subforum.parent_id).first()
# 	links.append("<a href=\"/subforum?sub=" + str(subforum.id) + "\">" + subforum.title + "</a>")
# 	while parent is not None:
# 		links.append("<a href=\"/subforum?sub=" + str(parent.id) + "\">" + parent.title + "</a>")
# 		parent = Subforum.query.filter(Subforum.id == parent.parent_id).first()
# 	links.append("<a href=\"/\">Forum Index</a>")
# 	link = ""
# 	for l in reversed(links):
# 		link = link + " / " + l
# 	return link


# Post validation helpers
def valid_title(title):
	return len(title) > 4 and len(title) < 140

def valid_content(content):
	return len(content) > 10 and len(content) < 5000

