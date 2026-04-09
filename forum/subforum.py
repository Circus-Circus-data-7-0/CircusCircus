from .models import db, valid_content, valid_title, error
from .post import Post

class Subforum(db.Model):
    # Represent a forum category and its optional child subforums.
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, unique=True)
    description = db.Column(db.Text)
    subforums = db.relationship("Subforum")
    parent_id = db.Column(db.Integer, db.ForeignKey('subforum.id'))
    posts = db.relationship("Post", backref="subforum")
    path = None
    hidden = db.Column(db.Boolean, default=False)
    protected = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    users = db.relationship("User", backref="subforum")

    def __init__(self, title, description):
        self.title = title
        self.description = description

def generateLinkPath(subforumid):
	links = []
	subforum = Subforum.query.filter(Subforum.id == subforumid).first()
	parent = Subforum.query.filter(Subforum.id == subforum.parent_id).first()
	links.append("<a href=\"/subforum?sub=" + str(subforum.id) + "\">" + subforum.title + "</a>")
	while parent is not None:
		links.append("<a href=\"/subforum?sub=" + str(parent.id) + "\">" + parent.title + "</a>")
		parent = Subforum.query.filter(Subforum.id == parent.parent_id).first()
	links.append("<a href=\"/\">Forum Index</a>")
	link = ""
	for l in reversed(links):
		link = link + " / " + l
	return link


# Post validation helpers
def valid_title(title):
	return len(title) > 4 and len(title) < 140

def valid_content(content):
	return len(content) > 10 and len(content) < 5000


#routes for subforum browsing and creation

from flask import Blueprint, render_template, request, redirect
from flask_login import current_user, login_required
from flask_login.utils import login_required
from .models import valid_content, valid_title
from .post import Post

# Route handlers for login, browsing, and content creation.
# The app is small enough to keep in one blueprint for now.

subforum_rt = Blueprint('subforum_routes', __name__, template_folder='templates')
@subforum_rt.route('/subforum')
def subforum():
	# Show one subforum, its posts, and its child subforums.
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return error("That subforum does not exist!")
	posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
	subforumpath = subforum.path or generateLinkPath(subforum.id)

	subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
	return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=subforumpath)

@login_required
@subforum_rt.route('/createsubforum', methods=['GET', 'POST'])
def create_subforum_page():
	# Only admins can create subforums.
	if not current_user.admin:
		return error("Only administrators can create subforums!")
	
	# Get the parent subforum if specified
	parent_id = request.args.get('parent') or request.form.get('parent_id')
	parent_subforum = None
	if parent_id:
		try:
			parent_id = int(parent_id)
			parent_subforum = Subforum.query.get(parent_id)
		except (ValueError, TypeError):
			pass
	
	if request.method == 'POST':
		title = request.form['title']
		description = request.form['description']
		
		# Validate input
		errors = []
		retry = False
		if not valid_title(title):
			errors.append("Title must be between 4 and 140 characters long!")
			retry = True
		if not valid_content(description):
			errors.append("Description must be between 10 and 5000 characters long!")
			retry = True
		
		if retry:
			subforums = Subforum.query.filter(Subforum.parent_id == None).all()
			return render_template("createsubforum.html", subforums=subforums, parent_subforum=parent_subforum, errors=errors)
		
		# Create the new subforum
		subforum = Subforum(title, description)
		
		# Add to parent if specified
		if parent_subforum:
			parent_subforum.subforums.append(subforum)
		
		db.session.add(subforum)
		db.session.commit()
		
		if parent_subforum:
			return redirect("/subforum?sub=" + str(parent_subforum.id))
		else:
			return redirect("/")
	
	# GET request - show the form
	subforums = Subforum.query.filter(Subforum.parent_id == None).all()
	return render_template("createsubforum.html", subforums=subforums, parent_subforum=parent_subforum)

@login_required
@subforum_rt.route('/deletesubforum', methods=['POST'])
def delete_subforum():
	# Only admins can delete subforums.
	if not current_user.admin:
		return Subforum.error("Only administrators can delete subforums!")
	
	subforum_id = int(request.form.get('subforum_id'))
	subforum = Subforum.query.get(subforum_id)
	
	if not subforum:
		return Subforum.error("That subforum does not exist!")
	
	# Prevent deletion of protected subforums
	if subforum.protected:
		return Subforum.error("This subforum is protected and cannot be deleted!")
	
	# Prevent deletion if subforum has child subforums or posts
	if subforum.subforums or subforum.posts:
		return Subforum.error("Cannot delete a subforum that contains child subforums or posts!")
	
	parent_id = subforum.parent_id
	db.session.delete(subforum)
	db.session.commit()
	
	# Redirect back to parent or home
	if parent_id:
		return redirect("/subforum?sub=" + str(parent_id))
	else:
		return redirect("/")

