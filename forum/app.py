import os
import sys

if __package__ in (None, ""):
	# Allow running this file directly with `python forum/app.py`.
	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import render_template
from flask_login import LoginManager
from sqlalchemy import inspect, text
from .models import db, User, UserSettings
from .subforum import Subforum

from forum import create_app
# Build the Flask app using the package factory.
app = create_app()

# Simple metadata used by the templates and app config.
app.config['SITE_NAME'] = 'Schooner'
app.config['SITE_DESCRIPTION'] = 'a schooner forum'
app.config['FLASK_DEBUG'] = 1

def init_site():
	# Create the default forum structure on first run.
	print("creating initial subforums")
	admin = add_subforum("Forum", "Announcements, bug reports, and general discussion about the forum belongs here", protected=True)
	add_subforum("Announcements", "View forum announcements here", admin, protected=True)
	add_subforum("Bug Reports", "Report bugs with the forum here", admin, protected=True)
	add_subforum("General Discussion", "Use this subforum to post anything you want", protected=True)
	add_subforum("Other", "Discuss other things here", protected=True)

def add_subforum(title, description, parent=None, protected=False):
	# Avoid duplicate subforums at the same level.
	sub = Subforum(title, description)
	sub.protected = protected
	if parent:
		for subforum in parent.subforums:
			if subforum.title == title:
				return
		parent.subforums.append(sub)
	else:
		subforums = Subforum.query.filter(Subforum.parent_id == None).all()
		for subforum in subforums:
			if subforum.title == title:
				return
		db.session.add(sub)
	print("adding " + title)
	db.session.commit()
	return sub


def _sql_literal(value):
	# Convert Python default values into SQL literals for ALTER TABLE statements.
	if value is None:
		return "NULL"
	if isinstance(value, bool):
		return "1" if value else "0"
	if isinstance(value, (int, float)):
		return str(value)
	escaped = str(value).replace("'", "''")
	return f"'{escaped}'"


def _coerce_visibility(value, default="public"):
	if value is None:
		return default
	text_value = str(value).strip().lower()
	if text_value in ("private", "hidden", "off", "false", "0"):
		return "private"
	if text_value in ("public", "open", "on", "true", "1"):
		return "public"
	return default


def _coerce_bool(value, default=False):
	if value is None:
		return default
	if isinstance(value, bool):
		return value
	text_value = str(value).strip().lower()
	if text_value in ("1", "true", "yes", "on"):
		return True
	if text_value in ("0", "false", "no", "off"):
		return False
	return default


def ensure_model_schema_compatibility():
	# Keep existing MySQL tables compatible with current and future model columns.
	inspector = inspect(db.engine)
	existing_tables = set(inspector.get_table_names())

	with db.engine.begin() as conn:
		for mapper in db.Model.registry.mappers:
			table = mapper.local_table
			table_name = table.name
			if table_name not in existing_tables:
				continue

			existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
			for column in table.columns:
				if column.name in existing_columns:
					continue
				if column.primary_key:
					continue

				column_type = column.type.compile(dialect=db.engine.dialect)
				nullability = "NULL" if column.nullable else "NOT NULL"

				default_sql = ""
				if column.default is not None and getattr(column.default, "is_scalar", False):
					default_sql = f" DEFAULT {_sql_literal(column.default.arg)}"

				sql = (
					f"ALTER TABLE `{table_name}` "
					f"ADD COLUMN `{column.name}` {column_type} {nullability}{default_sql}"
				)
				conn.execute(text(sql))


def migrate_legacy_user_settings():
	# Copy any old privacy-related columns into the new one-row-per-user settings table.
	inspector = inspect(db.engine)
	existing_tables = set(inspector.get_table_names())
	if "user" not in existing_tables or "user_settings" not in existing_tables:
		return

	user_columns = {column["name"] for column in inspector.get_columns("user")}
	legacy_visibility_columns = (
		"profile_visibility",
		"privacy",
		"privacy_level",
		"profile_privacy",
		"private_profile",
	)
	legacy_post_visibility_columns = (
		"post_visibility",
		"posts_visibility",
		"private_posts",
		"posts_private",
		"public_posts",
	)
	legacy_email_columns = (
		"show_email",
		"email_public",
		"public_email",
	)
	legacy_messages_columns = (
		"allow_messages",
		"messages_enabled",
		"dm_enabled",
		"allow_dm",
	)

	for user in User.query.all():
		if user.settings is not None:
			continue

		values = {column: getattr(user, column) for column in user_columns if hasattr(user, column)}
		profile_visibility = _coerce_visibility(
			next((values[column] for column in legacy_visibility_columns if column in values), None)
		)
		post_visibility = _coerce_visibility(
			next((values[column] for column in legacy_post_visibility_columns if column in values), None)
		)
		show_email = _coerce_bool(
			next((values[column] for column in legacy_email_columns if column in values), None)
		)
		allow_messages = _coerce_bool(
			next((values[column] for column in legacy_messages_columns if column in values), None),
			True,
		)

		user.settings = UserSettings(
			profile_visibility=profile_visibility,
			post_visibility=post_visibility,
			show_email=show_email,
			allow_messages=allow_messages,
		)

	db.session.commit()

# Flask-Login needs a loader so it can restore the current user from the session.
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
	# Look up the full User row for the stored session ID.
	return User.query.get(userid)

with app.app_context():
	# Create tables if needed, then seed the database the first time it runs.
	db.create_all()
	ensure_model_schema_compatibility()
	migrate_legacy_user_settings()
	if not Subforum.query.all():
		init_site()

@app.route('/')
def index():
	# Show only top-level subforums on the home page.
	subforums = Subforum.query.filter(Subforum.parent_id == None).order_by(Subforum.id)
	return render_template("subforums.html", subforums=subforums)


if __name__ == "__main__":
	app.run(debug=True, port=8000)




