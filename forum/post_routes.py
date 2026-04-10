import datetime

from flask import Blueprint, redirect, render_template, request
from flask_login import current_user, login_required

from .models import Comment, Post, Subforum, db, error, generateLinkPath, valid_content, valid_title


posts_bp = Blueprint("posts", __name__, template_folder="templates")


@posts_bp.route('/addpost')
@login_required
def addpost():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return error("That subforum does not exist!")

    return render_template("createpost.html", subforum=subforum)


@posts_bp.route('/viewpost')
def viewpost():
    postid = int(request.args.get("post"))
    post = Post.query.filter(Post.id == postid).first()
    if not post:
        return error("That post does not exist!")

    subforumpath = post.subforum.path if post.subforum.path else generateLinkPath(post.subforum.id)
    comments = Comment.query.filter(Comment.post_id == postid).order_by(Comment.id.desc())
    return render_template("viewpost.html", post=post, path=subforumpath, comments=comments)


@posts_bp.route('/action_post', methods=['POST'])
@login_required
def action_post():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return redirect("/")

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

    post = Post(title, content, datetime.datetime.now())
    subforum.posts.append(post)
    current_user.posts.append(post)
    db.session.commit()
    return redirect("/viewpost?post=" + str(post.id))
