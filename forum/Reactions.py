#Add to Posts.py eventually

class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10))  # 'up', 'down', 'heart'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

@rt.route('/action_react', methods=['POST'])
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

# Add to Post model so that post.reactions works
reactions = db.relationship('Reaction', backref='post')

#Add in viewpost.html inside {% block body%} below the </div> of actual post, eventually
<form method="POST" action="/action_react" style="display:inline">
  <input type="hidden" name="post_id" value="{{ post.id }}">
  {% for emoji, kind in [('👍', 'up'), ('👎', 'down'), ('❤️', 'heart')] %}
    {% set count = post.reactions | selectattr('kind', 'eq', kind) | list | length %}
    {% set reacted = current_user.is_authenticated and post.reactions | selectattr('kind','eq',kind) | selectattr('user_id','eq',current_user.id) | list %}
    <button name="kind" value="{{ kind }}" style="background:{{ '#eee' if reacted else 'none' }};border:1px solid #ccc;border-radius:4px;padding:4px 10px;cursor:pointer;font-size:14pt;">
      {{ emoji }} {{ count }}
    </button>
  {% endfor %}
</form>

