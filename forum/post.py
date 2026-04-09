import datetime
from .models import db

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
    private = db.Column(db.Boolean, default=False)
    replies = db.relationship("Post", backref=db.backref('parent_post', remote_side='Post.id'))

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
