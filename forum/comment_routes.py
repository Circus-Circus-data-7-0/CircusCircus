import datetime

from flask import Blueprint, redirect, request
from flask_login import current_user, login_required

from .models import Comment, Post, db, error


comments_bp = Blueprint("comments", __name__, template_folder="templates")


@comments_bp.route('/action_comment', methods=['POST', 'GET'])
@login_required
def comment():
    post_id = int(request.args.get("post"))
    post = Post.query.filter(Post.id == post_id).first()
    if not post:
        return error("That post does not exist!")

    content = request.form['content']
    postdate = datetime.datetime.now()
    comment = Comment(content, postdate)
    current_user.comments.append(comment)
    post.comments.append(comment)
    db.session.commit()
    return redirect("/viewpost?post=" + str(post_id))
