import os
import sys

if __package__ in (None, ""):
	# Allow running this file directly with `python forum/app.py`.
	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import render_template
from flask_login import LoginManager

from . import create_app
from .models import User, db
from .post import Post
from .subforum import Subforum
# Build the Flask app using the package factory.
app = create_app()

# Simple metadata used by the templates and app config.
app.config['SITE_NAME'] = 'ZIPCHAT'
app.config['SITE_DESCRIPTION'] = 'a ZIPCHAT forum'
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


@app.context_processor
def inject_channel_links():
	"""Expose helper values for channel links and real dashboard stats."""
	def channel_url(title):
		sub = Subforum.query.filter(Subforum.title == title).first()
		if sub:
			return f"/subforum?sub={sub.id}"
		return "/"

	stats = {
		"members": User.query.count(),
		"posts": Post.query.filter(Post.parent_id == None).count(),
		"subforums": Subforum.query.count(),
		# No realtime presence tracking exists yet, so show the true known value.
		"online": 0,
	}

	recent_users = User.query.order_by(User.id.desc()).limit(5).all()
	top_subforums = Subforum.query.filter(Subforum.parent_id == None).order_by(Subforum.id).all()

	return {
		"channel_url": channel_url,
		"stats": stats,
		"recent_users": recent_users,
		"top_subforums": top_subforums,
	}

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


if __name__ == "__main__":
	app.run(debug=True, port=8000)




