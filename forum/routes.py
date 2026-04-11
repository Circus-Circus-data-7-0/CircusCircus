from flask import render_template, request, redirect, url_for
from flask_login import current_user, login_user, logout_user
from flask_login.utils import login_required
import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from .models import User, UserSettings, Post, Comment, valid_content, valid_title, db, error
from .user import username_taken, email_taken, valid_username
from .subforum import Subforum, db, generateLinkPath

# Route handlers for login, browsing, and content creation.
# The app is small enough to keep in one blueprint for now.

rt = Blueprint('routes', __name__, template_folder='templates')


def _request_bool(name, default=False):
	value = request.form.get(name)
	if value is None:
		return default
	return value.lower() in ("1", "true", "yes", "on")


def _ensure_user_settings(user):
	created = False
	settings = user.settings
	if settings is None:
		settings = UserSettings()
		user.settings = settings
		db.session.add(settings)
		created = True
	return settings, created

@rt.route('/action_login', methods=['POST'])
def action_login():
	# Read login form values and authenticate the user.
	username = request.form['username']
	password = request.form['password']
	user = User.query.filter(User.username == username).first()
	if user and user.check_password(password):
		login_user(user)
	else:
		errors = []
		errors.append("Username or password is incorrect!")
		return render_template("login.html", errors=errors)
	return redirect("/")

@login_required
@rt.route('/action_logout')
def action_logout():
	# End the current session and send the user back home.
	logout_user()
	return redirect("/")

@rt.route('/action_createaccount', methods=['POST'])
def action_createaccount():
	# Validate signup data, create the user, then log them in.
	username = request.form['username']
	password = request.form['password']
	email = request.form['email']
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
	# if not valid_password(password):
	# 	errors.append("Password is not valid!")
	# 	retry = True
	if retry:
		return render_template("login.html", errors=errors)
	user = User(email, username, password)
	if user.username == "admin":
		user.admin = True
	user.settings = UserSettings()
	db.session.add(user)
	db.session.commit()
	login_user(user)
	return redirect("/")


@login_required
@rt.route('/settings', methods=['GET', 'POST'])
def settings():
	# Show or update the current user's privacy preferences.
	settings, created = _ensure_user_settings(current_user)
	if created and request.method == 'GET':
		db.session.commit()
	if request.method == 'POST':
		profile_visibility = request.form.get('profile_visibility', 'public')
		post_visibility = request.form.get('post_visibility', 'public')
		settings.profile_visibility = profile_visibility if profile_visibility in ('public', 'private') else 'public'
		settings.post_visibility = post_visibility if post_visibility in ('public', 'private') else 'public'
		settings.show_email = _request_bool('show_email')
		settings.allow_messages = _request_bool('allow_messages', True)
		db.session.commit()
		return redirect('/settings')

	return render_template('settings.html', settings=settings)


# @rt.route('/subforum')
# def subforum():
# 	# Show one subforum, its posts, and its child subforums.
# 	subforum_id = int(request.args.get("sub"))
# 	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
# 	if not subforum:
# 		return error("That subforum does not exist!")
# 	posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
# 	subforumpath = subforum.path or generateLinkPath(subforum.id)

# 	subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
# 	return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=subforumpath)

@rt.route('/loginform')
def loginform():
	# Render the shared login and signup page.
	return render_template("login.html")


# @login_required
# @rt.route('/addpost')
# def addpost():
# 	# Show the new post form for the selected subforum.
# 	subforum_id = int(request.args.get("sub"))
# 	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
# 	if not subforum:
# 		return error("That subforum does not exist!")

# 	return render_template("createpost.html", subforum=subforum)

# @rt.route('/viewpost')
# def viewpost():
# 	# Show one post and its comments.
# 	postid = int(request.args.get("post"))
# 	post = Post.query.filter(Post.id == postid).first()
# 	if not post:
# 		return error("That post does not exist!")
# 	subforumpath = post.subforum.path or generateLinkPath(post.subforum.id)
# 	# Newest replies appear first for easier reading.
# 	comments = Post.query.filter(Post.parent_id == postid).order_by(Post.id.desc())
# 	return render_template("viewpost.html", post=post, path=subforumpath, comments=comments)

# @login_required
# @rt.route('/action_comment', methods=['POST', 'GET'])
# def comment():
# 	# Create a comment, attach it to the user and post, then save it.
# 	post_id = int(request.args.get("post"))
# 	post = Post.query.filter(Post.id == post_id).first()
# 	if not post:
# 		return error("That post does not exist!")
# 	content = request.form['content']
# 	postdate = datetime.datetime.now()
# 	reply = Post(content, postdate)
# 	reply.parent_id = post_id
# 	current_user.posts.append(reply)
# 	db.session.commit()
# 	return redirect("/viewpost?post=" + str(post_id))

# @login_required
# @rt.route('/action_post', methods=['POST'])
# def action_post():
# 	# Validate a new post before saving it.
# 	subforum_id = int(request.args.get("sub"))
# 	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
# 	if not subforum:
# 		return redirect(url_for("index"))

# 	user = current_user
# 	title = request.form['title']
# 	content = request.form['content']
# 	# Collect validation errors first so the form can be shown again if needed.
# 	errors = []
# 	retry = False
# 	if not valid_title(title):
# 		errors.append("Title must be between 4 and 140 characters long!")
# 		retry = True
# 	if not valid_content(content):
# 		errors.append("Post must be between 10 and 5000 characters long!")
# 		retry = True
# 	if retry:
# 		return render_template("createpost.html", subforum=subforum, errors=errors)
# 	post = Post(content, datetime.datetime.now(), title=title)
# 	subforum.posts.append(post)
# 	user.posts.append(post)
# 	db.session.commit()
# 	return redirect("/viewpost?post=" + str(post.id))

# @login_required
# @rt.route('/createsubforum', methods=['GET', 'POST'])
# def create_subforum_page():
# 	# Only admins can create subforums.
# 	if not current_user.admin:
# 		return error("Only administrators can create subforums!")
	
# 	# Get the parent subforum if specified
# 	parent_id = request.args.get('parent') or request.form.get('parent_id')
# 	parent_subforum = None
# 	if parent_id:
# 		try:
# 			parent_id = int(parent_id)
# 			parent_subforum = Subforum.query.get(parent_id)
# 		except (ValueError, TypeError):
# 			pass
	
# 	if request.method == 'POST':
# 		title = request.form['title']
# 		description = request.form['description']
		
# 		# Validate input
# 		errors = []
# 		retry = False
# 		if not valid_title(title):
# 			errors.append("Title must be between 4 and 140 characters long!")
# 			retry = True
# 		if not valid_content(description):
# 			errors.append("Description must be between 10 and 5000 characters long!")
# 			retry = True
		
# 		if retry:
# 			subforums = Subforum.query.filter(Subforum.parent_id == None).all()
# 			return render_template("createsubforum.html", subforums=subforums, parent_subforum=parent_subforum, errors=errors)
		
# 		# Create the new subforum
# 		subforum = Subforum(title, description)
		
# 		# Add to parent if specified
# 		if parent_subforum:
# 			parent_subforum.subforums.append(subforum)
		
# 		db.session.add(subforum)
# 		db.session.commit()
		
# 		if parent_subforum:
# 			return redirect("/subforum?sub=" + str(parent_subforum.id))
# 		else:
# 			return redirect("/")
	
# 	# GET request - show the form
# 	subforums = Subforum.query.filter(Subforum.parent_id == None).all()
# 	return render_template("createsubforum.html", subforums=subforums, parent_subforum=parent_subforum)

