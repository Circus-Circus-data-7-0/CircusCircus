from flask import Blueprint, render_template, request, redirect
from flask_login import current_user, login_required

from .models import db


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


def _request_bool(name, default=False):
    # Read a checkbox/boolean field from the submitted form.
    value = request.form.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def _ensure_user_settings(user):
    # Lazily create a UserSettings row if one does not already exist.
    if user.settings is None:
        user_settings = UserSettings()
        user.settings = user_settings
        db.session.add(user_settings)
        return user_settings, True
    return user.settings, False


settings_bp = Blueprint("settings", __name__, template_folder="templates")


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    # Show or update the current user's privacy preferences.
    user_settings, created = _ensure_user_settings(current_user)
    if created:
        db.session.commit()

    if request.method == "POST":
        profile_visibility = request.form.get("profile_visibility", "public")
        post_visibility = request.form.get("post_visibility", "public")
        user_settings.profile_visibility = (
            profile_visibility if profile_visibility in ("public", "private") else "public"
        )
        user_settings.post_visibility = (
            post_visibility if post_visibility in ("public", "private") else "public"
        )
        user_settings.show_email = _request_bool("show_email")
        user_settings.allow_messages = _request_bool("allow_messages", True)
        db.session.commit()
        return redirect("/settings")

    return render_template("settings.html", settings=user_settings)
