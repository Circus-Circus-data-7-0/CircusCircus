from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from .models import db
import datetime
from .user import User

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    postdate = db.Column(db.DateTime)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    read = db.Column(db.Boolean, default=False)
    sender    = db.relationship('User', foreign_keys=[sender_id],    backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

rt_messages = Blueprint('rt_messages', __name__, template_folder='templates')

@rt_messages.route('/messages')
@login_required
def messages():
    sender_filter = request.args.get('sender')
    query = Messages.query.filter_by(recipient_id=current_user.id)
    if sender_filter:
        sender = User.query.filter_by(username=sender_filter).first()
        if sender:
            query = query.filter_by(sender_id=sender.id)
    msgs = query.order_by(Messages.id.desc()).all()
    senders = User.query.join(Messages, Messages.sender_id == User.id).filter(Messages.recipient_id == current_user.id).distinct().all()
    return render_template('messages.html', messages=msgs, senders=senders, current_sender=sender_filter)

@rt_messages.route('/action_message', methods=['POST'])
@login_required
def action_message():
    recipient = User.query.filter_by(username=request.form['recipient']).first()
    if not recipient:
        return render_template('messages.html', errors=["That username does not exist."], messages=Messages.query.filter_by(recipient_id=current_user.id).order_by(Messages.id.desc()).all(), senders=User.query.join(Messages, Messages.sender_id == User.id).filter(Messages.recipient_id == current_user.id).distinct().all(), current_sender=None)
    msg = Messages(content=request.form['content'], postdate=datetime.datetime.now(),
              sender_id=current_user.id, recipient_id=recipient.id)
    db.session.add(msg)
    db.session.commit()
    return redirect('/messages')

