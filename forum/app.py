
from flask import render_template
from flask_login import LoginManager
from .models import db, User
from .subforum import Subforum, db

from forum import create_app
# Build the Flask app using the package factory.
app = create_app()

# Simple metadata used by the templates and app config.
app.config['SITE_NAME'] = 'Schooner'
app.config['SITE_DESCRIPTION'] = 'a schooner forum'
app.config['FLASK_DEBUG'] = 1

def init_site():
	# Create the default forum structure on first run.
	print("creating initial subforums")
	admin = add_subforum("Forum", "Announcements, bug reports, and general discussion about the forum belongs here", protected=True)
	add_subforum("Announcements", "View forum announcements here", admin, protected=True)
	add_subforum("Bug Reports", "Report bugs with the forum here", admin, protected=True)
	add_subforum("General Discussion", "Use this subforum to post anything you want", protected=True)
	add_subforum("Other", "Discuss other things here", protected=True)

def add_subforum(title, description, parent=None, protected=False):
	# Avoid duplicate subforums at the same level.
	sub = Subforum(title, description)
	sub.protected = protected
	if parent:
		for subforum in parent.subforums:
			if subforum.title == title:
				return
		parent.subforums.append(sub)
	else:
		subforums = Subforum.query.filter(Subforum.parent_id == None).all()
		for subforum in subforums:
			if subforum.title == title:
				return
		db.session.add(sub)
	print("adding " + title)
	db.session.commit()
	return sub

# Flask-Login needs a loader so it can restore the current user from the session.
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
	# Look up the full User row for the stored session ID.
	return User.query.get(userid)

with app.app_context():
	# Create tables if needed, then seed the database the first time it runs.
	db.create_all()
	if not Subforum.query.all():
		init_site()

@app.route('/')
def index():
	# Show only top-level subforums on the home page.
	subforums = Subforum.query.filter(Subforum.parent_id == None).order_by(Subforum.id)
	return render_template("subforums.html", subforums=subforums)




