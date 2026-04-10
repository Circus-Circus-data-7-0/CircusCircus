from flask import Blueprint, render_template, request

from .models import Post, Subforum, error, generateLinkPath


subforums_bp = Blueprint("subforums", __name__, template_folder="templates")


@subforums_bp.route('/subforum')
def subforum():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return error("That subforum does not exist!")

    posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
    subforumpath = subforum.path if subforum.path else generateLinkPath(subforum.id)
    subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()

    return render_template(
        "subforum.html",
        subforum=subforum,
        posts=posts,
        subforums=subforums,
        path=subforumpath,
    )
