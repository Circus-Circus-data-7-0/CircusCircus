import os
import sys

if __package__ in (None, ""):
	# Allow running this file directly with `python forum/app.py`.
	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import render_template
from flask_login import LoginManager
from sqlalchemy import inspect, text
from .models import db
from .subforum import Subforum
from .user import User

from forum import create_app
# Build the Flask app using the package factory.
app = create_app()

# Simple metadata used by the templates and app config.
app.config['SITE_NAME'] = 'ZipChat'
app.config['SITE_DESCRIPTION'] = 'a Zip Code Wilmington forum'
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
	if not Subforum.query.all():
		init_site()

@app.route('/')
def index():
	# Show only top-level subforums on the home page.
	subforums = Subforum.query.filter(Subforum.parent_id == None).order_by(Subforum.id)
	return render_template("subforums.html", subforums=subforums)


if __name__ == "__main__":
	app.run(debug=True, port=8000)




