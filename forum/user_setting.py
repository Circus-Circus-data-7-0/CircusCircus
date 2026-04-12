class UserSettings(db.Model):
    # Store the per-user privacy and display preferences.
    __tablename__ = "user_settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    profile_visibility = db.Column(db.String(20), nullable=False, default="public")
    post_visibility = db.Column(db.String(20), nullable=False, default="public")
    show_email = db.Column(db.Boolean, nullable=False, default=False)
    allow_messages = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", back_populates="settings")

    def __init__(
        self,
        profile_visibility="public",
        post_visibility="public",
        show_email=False,
        allow_messages=True,
    ):
        self.profile_visibility = profile_visibility
        self.post_visibility = post_visibility
        self.show_email = show_email
        self.allow_messages = allow_messages