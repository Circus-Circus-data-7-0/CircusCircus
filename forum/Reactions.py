#import post.py
from flask import request, redirect, Blueprint, request, redirect
from flask_login import current_user
from flask_login.utils import login_required
from .models import db

rt_react = Blueprint('rt_react', __name__)

class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10))  # 'up', 'down', 'heart'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

@rt_react.route('/action_react', methods=['POST'])
@login_required
def action_react():
    post_id = int(request.form['post_id'])
    kind = request.form['kind']
    if kind not in ('up', 'down', 'heart'):
        return redirect('/')
    existing = Reaction.query.filter_by(post_id=post_id, user_id=current_user.id, kind=kind).first()
    if existing:
        db.session.delete(existing)
    else:
        r = Reaction(kind=kind, user_id=current_user.id, post_id=post_id)
        db.session.add(r)
    db.session.commit()
    return redirect('/viewpost?post=' + str(post_id))
