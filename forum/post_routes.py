from flask import Blueprint, render_template, request, redirect, url_for, current_app, send_from_directory
from flask_login import current_user, login_user, logout_user
from flask_login.utils import login_required
import datetime
from .models import User, Post, Subforum, valid_content, valid_title, db, generateLinkPath, error
from .user import username_taken, email_taken, valid_username
from .routes import rt
import os
from werkzeug.utils import secure_filename


@rt.route('/uploads/<filename>')
def uploaded_file(filename):
	return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@rt.route('/addpost')
@login_required
def addpost():
	# Show the new post form for the selected subforum.
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return error("That subforum does not exist!")
	default_visibility = "public"
	if getattr(current_user, "is_authenticated", False) and getattr(current_user, "settings", None):
		default_visibility = current_user.settings.post_visibility or "public"
	return render_template("createpost.html", subforum=subforum, default_visibility=default_visibility)

@rt.route('/viewpost')
def viewpost():
	# Show one post and its comments.
	postid = int(request.args.get("post"))
	post = Post.query.filter(Post.id == postid).first()
	if not post:
		return error("That post does not exist!")
	if post.visibility == "private" and not current_user.is_authenticated:
		return redirect("/loginform")
	subforumpath = post.subforum.path or generateLinkPath(post.subforum.id)
	# Newest replies appear first for easier reading.
	comments = Post.query.filter(Post.parent_id == postid).order_by(Post.id.desc())
	return render_template("viewpost.html", post=post, path=subforumpath, comments=comments)

@rt.route('/action_comment', methods=['POST', 'GET'])
@login_required
def comment():
	# Create a comment, attach it to the user and post, then save it.
	post_id = int(request.args.get("post"))
	post = Post.query.filter(Post.id == post_id).first()
	if not post:
		return error("That post does not exist!")
	content = request.form['content']
	postdate = datetime.datetime.now()
	reply = Post(content=content, postdate=postdate)
	reply.parent_id = post_id
	current_user.posts.append(reply)
	db.session.commit()
	return redirect("/viewpost?post=" + str(post_id))

@rt.route('/action_post', methods=['POST'])
@login_required
def action_post():
	# Validate a new post before saving it.
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return redirect(url_for("index"))

	user = current_user
	title = request.form['title']
	content = request.form['content']
	errors = []
	retry = False
	if not valid_title(title):
		errors.append("Title must be between 4 and 140 characters long!")
		retry = True
	if not valid_content(content):
		errors.append("Post must be between 10 and 5000 characters long!")
		retry = True
	if retry:
		return render_template("createpost.html", subforum=subforum, errors=errors, default_visibility=request.form.get("visibility", "public"))
	visibility = request.form.get("visibility", "public")
	if visibility not in ("public", "private"):
		visibility = "public"
	file = request.files.get('upload_file')
	filename = None
	if file and file.filename:
		filename = secure_filename(file.filename)
		file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
	post = Post(title=title, content=content, postdate=datetime.datetime.now(), upload_file=filename, visibility=visibility)
	subforum.posts.append(post)
	user.posts.append(post)
	db.session.commit()
	return redirect("/viewpost?post=" + str(post.id))
