from flask import render_template, request, redirect, url_for
from flask_login import current_user, login_user, logout_user
from flask_login.utils import login_required
import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from .models import User, Post, Comment, valid_content, valid_title, db, error, generateLinkPath, Subforum

# Route handlers for login, browsing, and content creation.
# The app is small enough to keep in one blueprint for now.

from .routes import rt

@rt.route('/subforum')
def subforum():
	# Show one subforum, its posts, and its child subforums.
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return error("That subforum does not exist!")
	posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
	subforumpath = subforum.path or generateLinkPath(subforum.id)

	subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
	return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=subforumpath)

#@login_required
@rt.route('/createsubforum', methods=['GET', 'POST'])
def create_subforum_page():
	# Only admins can create subforums.
	if not current_user.admin:
		return error("Only administrators can create subforums!")
	
	# Get the parent subforum if specified
	parent_id = request.args.get('parent') or request.form.get('parent_id')
	parent_subforum = None
	if parent_id:
		try:
			parent_id = int(parent_id)
			parent_subforum = Subforum.query.get(parent_id)
		except (ValueError, TypeError):
			pass
	
	if request.method == 'POST':
		title = request.form['title']
		description = request.form['description']
		
		# Validate input
		errors = []
		retry = False
		if not valid_title(title):
			errors.append("Title must be between 4 and 140 characters long!")
			retry = True
		if not valid_content(description):
			errors.append("Description must be between 10 and 5000 characters long!")
			retry = True
		
		if retry:
			subforums = Subforum.query.filter(Subforum.parent_id == None).all()
			return render_template("createsubforum.html", subforums=subforums, parent_subforum=parent_subforum, errors=errors)
		
		# Create the new subforum
		subforum = Subforum(title, description)
		
		# Add to parent if specified
		if parent_subforum:
			parent_subforum.subforums.append(subforum)
		
		db.session.add(subforum)
		db.session.commit()
		
		if parent_subforum:
			return redirect("/subforum?sub=" + str(parent_subforum.id))
		else:
			return redirect("/")
	
	# GET request - show the form
	subforums = Subforum.query.filter(Subforum.parent_id == None).all()
	return render_template("createsubforum.html", subforums=subforums, parent_subforum=parent_subforum)

