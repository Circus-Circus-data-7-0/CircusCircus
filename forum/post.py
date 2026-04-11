import datetime
import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app, send_from_directory
from flask_login import current_user
from flask_login.utils import login_required
from werkzeug.utils import secure_filename
from .models import db, valid_content, valid_title, error
from .user import User

post_rt = Blueprint('post_routes', __name__, template_folder='templates')


class Post(db.Model):
    # Store a forum post or a reply. Top-level posts have parent_id=None;
    # replies point to their parent via parent_id.
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=True)
    upload_file = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text)
    private = db.Column(db.Boolean, default=False)
    postdate = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subforum_id = db.Column(db.Integer, db.ForeignKey('subforum.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    replies = db.relationship("Post", backref=db.backref('parent_post', remote_side='Post.id'))
    reactions = db.relationship('Reaction', backref='post')
    
    # Simple in-memory cache for human-readable time labels.
    lastcheck = None
    savedresponse = None

    def __init__(self, title=None, content=None, postdate=None, upload_file=None, private=False):
        self.title = title
        self.content = content
        self.postdate = postdate
        self.upload_file = upload_file
        self.private = private

    def get_time_string(self):
        # Recalculate every 30 seconds to avoid inaccurate time labels
        now = datetime.datetime.now()
        if self.lastcheck is None or (now - self.lastcheck).total_seconds() > 30:
            self.lastcheck = now
        else:
            return self.savedresponse

        diff = now - self.postdate
        seconds = diff.total_seconds()
        if seconds / (60 * 60 * 24 * 30) > 1:
            self.savedresponse = " " + str(int(seconds / (60 * 60 * 24 * 30))) + " months ago"
        elif seconds / (60 * 60 * 24) > 1:
            self.savedresponse = " " + str(int(seconds / (60 * 60 * 24))) + " days ago"
        elif seconds / (60 * 60) > 1:
            self.savedresponse = " " + str(int(seconds / (60 * 60))) + " hours ago"
        elif seconds / (60) > 1:
            self.savedresponse = " " + str(int(seconds / 60)) + " minutes ago"
        else:
            self.savedresponse = "Just a moment ago!"
        return self.savedresponse


# Routes are defined below after Post so they can reference it directly.
# Import Subforum here (after Post is defined) to avoid circular imports.
from .subforum import Subforum, generateLinkPath  # noqa: E402


@post_rt.route('/uploads/<filename>')
def uploaded_file(filename):
	return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@post_rt.route('/addpost')
@login_required
def addpost():
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return error("That subforum does not exist!")
	return render_template("createpost.html", subforum=subforum)

@post_rt.route('/viewpost')
def viewpost():
	postid = int(request.args.get("post"))
	post = Post.query.filter(Post.id == postid).first()
	if not post:
		return error("That post does not exist!")
	if post.private and (not current_user.is_authenticated or post.user_id != current_user.id):
		return error("This post is private.")
	subforumpath = post.subforum.path or generateLinkPath(post.subforum.id)
	comments = Post.query.filter(Post.parent_id == postid).order_by(Post.id.desc())
	return render_template("viewpost.html", post=post, path=subforumpath, comments=comments)

@post_rt.route('/action_comment', methods=['POST', 'GET'])
@login_required
def comment():
	post_id = int(request.args.get("post"))
	post = Post.query.filter(Post.id == post_id).first()
	if not post:
		return error("That post does not exist!")
	content = request.form['content']
	reply = Post(content=content, postdate=datetime.datetime.now())
	reply.parent_id = post_id
	current_user.posts.append(reply)
	db.session.commit()
	return redirect("/viewpost?post=" + str(post_id))

@post_rt.route('/action_post', methods=['POST'])
@login_required
def action_post():
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return redirect(url_for("routes.index"))

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
		return render_template("createpost.html", subforum=subforum, errors=errors)
	private = 'private' in request.form
	file = request.files.get('upload_file')
	filename = None
	if file and file.filename:
		filename = secure_filename(file.filename)
		upload_folder = current_app.config['UPLOAD_FOLDER']
		os.makedirs(upload_folder, exist_ok=True)
		file.save(os.path.join(upload_folder, filename))
	post = Post(title=title, content=content, postdate=datetime.datetime.now(), upload_file=filename, private=private)
	subforum.posts.append(post)
	user.posts.append(post)
	db.session.commit()
	return redirect("/viewpost?post=" + str(post.id))

@post_rt.route('/action_delete_post', methods=['POST'])
@login_required
def action_delete_post():
    post_id = int(request.args.get("post"))
    post = Post.query.filter(Post.id == post_id).first()
    if not post:
        return error("That post does not exist!")
    if post.user_id != current_user.id and not current_user.admin:
        return error("You do not have permission to delete this post.")
    Post.query.filter(Post.parent_id == post_id).delete()
	db.session.delete(post)
	db.session.commit()
    return redirect("/subforum?sub=" + str(post.subforum_id))