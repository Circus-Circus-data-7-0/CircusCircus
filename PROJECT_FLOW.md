# CircusCircus Project Flow

This document explains how the current project fits together at two levels:
- quick overview for orientation
- deeper walkthrough of the runtime logic and data flow

It is written so someone new to Flask can follow the project without reading all source files first.

## Quick Overview

- Tech stack: Flask + Flask-Login + Flask-SQLAlchemy + Jinja templates.
- Entry point: `forum/app.py` creates the running app and root route.
- App factory: `forum/__init__.py` builds and configures the Flask app.
- Configuration: `config.py` provides secret key and SQLAlchemy settings.
- Data models: `forum/models.py` defines User, Post, Subforum, Comment.
- Request handlers: `forum/routes.py` handles auth, browsing, posting, comments.
- Account helpers: `forum/user.py` contains username/password utility checks.
- Templates: `forum/templates/` render pages for index, subforums, posts, login.
- Startup script: `run.sh` runs the app using Flask.

## How Startup Works

1. Flask starts with module `forum.app` (configured by `FLASK_APP`).
2. `forum/app.py` calls `create_app()` from `forum/__init__.py`.
3. `create_app()`:
   - creates Flask app
   - loads `Config` from `config.py`
   - registers blueprint `rt` from `forum/routes.py`
   - initializes SQLAlchemy via `db.init_app(app)`
   - creates DB tables with `db.create_all()` inside app context
4. Back in `forum/app.py`:
   - Flask-Login is configured
   - `user_loader` is registered to restore users from session IDs
   - tables are ensured again and initial subforums are seeded if empty

Note: table creation happens in both `forum/__init__.py` and `forum/app.py`. That is safe, but redundant.

## Beginner Map: What You Are Looking At

If you open this project and feel lost, use this sequence:

1. Open `config.py` to see app-wide settings.
2. Open `forum/__init__.py` to see how Flask is created and wired.
3. Open `forum/app.py` to see login setup, seed data setup, and the home route.
4. Open `forum/routes.py` to see the main user actions (login, browse, post, comment).
5. Open `forum/models.py` to understand what data is stored and how tables connect.
6. Open `forum/templates/` to see what each route renders.

This order moves from "how app starts" to "what app does" to "how page looks".

## URL and Request Flow

### Root and browsing

- `GET /` in `forum/app.py`:
  - fetches top-level subforums (`parent_id is None`)
  - renders `subforums.html`

- `GET /subforum?sub=<id>` in `forum/routes.py`:
  - loads the target subforum
  - loads recent posts for that subforum (up to 50, newest first)
  - loads child subforums
  - builds breadcrumb HTML path with `generateLinkPath()`
  - renders `subforum.html`

- `GET /viewpost?post=<id>` in `forum/routes.py`:
  - loads post and comments (newest comments first)
  - builds breadcrumb path from post's subforum
  - renders `viewpost.html`

### Authentication

- `POST /action_login`:
  - reads username/password from form
  - finds user by username
  - verifies hash with `user.check_password()`
  - logs in with Flask-Login or returns login page with errors

- `GET /action_logout` (login required):
  - logs current user out
  - redirects to root

- `POST /action_createaccount`:
  - validates username format and uniqueness
  - validates email uniqueness
  - creates `User` (password stored as hash)
  - auto-logs in and redirects to root

### Content creation

- `GET /addpost?sub=<id>` (login required):
  - verifies subforum exists
  - renders `createpost.html`

- `POST /action_post?sub=<id>` (login required):
  - validates title/content length
  - creates `Post`
  - links post to current user and subforum
  - commits and redirects to `viewpost`

- `POST/GET /action_comment?post=<id>` (login required):
  - verifies post exists
  - creates `Comment`
  - links comment to current user and post
  - commits and redirects to `viewpost`

## Deep Logic Walkthrough

This section explains how the system behaves internally, not just which files exist.

### 1. App factory and global objects

- `db` is created once in `forum/models.py` as a global SQLAlchemy object.
- `create_app()` in `forum/__init__.py` binds that `db` object to the Flask app instance.
- Route registration happens by attaching the routes blueprint (`rt`) to the app.
- Flask-Login setup happens in `forum/app.py`, where `LoginManager` is attached to the app.

Result: every route can use `db`, model queries, and `current_user` with one shared app context.

### 2. Database initialization and seed logic

- On startup, tables are created if missing.
- Then the app checks whether any `Subforum` rows exist.
- If none exist, `init_site()` seeds a default category tree.
- `add_subforum()` avoids duplicate titles at the same tree level.

Result: first run creates a usable forum structure automatically.

### 3. Authentication lifecycle

- Account creation stores a hashed password only.
- Login route checks plain password against hash.
- On success, Flask-Login stores user identity in session.
- On later requests, `load_user(userid)` converts session ID back into a `User` row.
- Logout clears that session identity.

Result: auth state is cookie/session based, with DB lookup per request as needed.

### 4. Read flow for forum pages

- Forum index route reads top-level subforums.
- Subforum route reads:
  - one subforum by ID
  - posts under that subforum
  - direct child subforums
  - breadcrumb path text
- View-post route reads:
  - one post by ID
  - comments for that post
  - breadcrumb path from that post's subforum

Result: each page query is focused and template-driven.

### 5. Write flow for posts and comments

- Create-post route validates title/content length.
- If invalid, template is re-rendered with error messages.
- If valid, a `Post` is created and attached to:
  - current user
  - selected subforum
- Create-comment route does the same pattern for `Comment`:
  - verify post exists
  - create comment
  - attach to current user and post
- Each write ends with `db.session.commit()` and redirect.

Result: writes are simple transaction-style operations with immediate redirect.

### 6. Why relationships are used heavily

- Instead of manually assigning every foreign key field, code often appends objects to relationships.
- Example pattern:
  - `user.posts.append(post)`
  - `subforum.posts.append(post)`
- SQLAlchemy fills key IDs and persists links on commit.

Result: route code stays short and object-oriented.

## End-to-End Request Trace Examples

These traces show exactly what happens in common user actions.

### Trace A: User signs up, then lands on home page

1. Browser submits signup form to `POST /action_createaccount`.
2. Route reads username, email, password from `request.form`.
3. Helper checks run:
   - username format
   - username uniqueness
   - email uniqueness
4. If any check fails:
   - route renders login template with error list
   - DB is unchanged
5. If checks pass:
   - `User` object created (password hashed)
   - user row committed
   - user logged in with Flask-Login
   - redirect to `/`
6. `GET /` loads top-level subforums and renders index template.

### Trace B: Logged-in user creates a post

1. User opens `GET /addpost?sub=<id>`.
2. Route confirms target subforum exists.
3. Create-post form renders.
4. User submits form to `POST /action_post?sub=<id>`.
5. Route validates title/content length.
6. If invalid, route re-renders form with validation messages.
7. If valid:
   - `Post` object is created
   - post attached to selected subforum and current user
   - session commit persists post row and foreign keys
   - redirect to `GET /viewpost?post=<new_id>`
8. Post detail page queries post/comments and renders.

### Trace C: Logged-in user comments on a post

1. User submits comment form to `POST /action_comment?post=<id>`.
2. Route verifies post exists.
3. Route creates `Comment` with content and current timestamp.
4. Comment is linked to current user and target post.
5. Commit persists comment row and keys.
6. Redirect goes back to `GET /viewpost?post=<id>`.
7. Page reload now includes the new comment at top (newest first).

## How to Read Logic Quickly During Maintenance

When trying to understand a behavior, follow this mini-checklist:

1. Identify route function handling the URL.
2. List which model queries it runs.
3. Check which helper validators it calls.
4. Check what template it renders or redirect it returns.
5. Confirm where commit happens for data writes.

Using this method keeps debugging predictable across the whole codebase.

## Data Model and Relationships

Defined in `forum/models.py`:

- `User`
  - fields: id, username, password_hash, email, admin
  - relationships: one-to-many with Post and Comment
  - methods: `check_password()`

- `Subforum`
  - fields: id, title, description, parent_id, hidden
  - relationships:
    - self-referential child subforums via `subforums`
    - one-to-many with Post

- `Post`
  - fields: id, title, content, user_id, subforum_id, postdate
  - relationships: one-to-many with Comment
  - helper: `get_time_string()` for relative-time labels

- `Comment`
  - fields: id, content, postdate, user_id, post_id
  - helper: `get_time_string()` for relative-time labels

## Validation and Utility Logic

From `forum/user.py` and `forum/models.py`:

- Username regex allows 4-40 characters from `[a-zA-Z0-9!@#%&]`.
- Password regex allows 6-40 characters from same set.
- `username_taken()` and `email_taken()` query existing users.
- `valid_title()` and `valid_content()` enforce post size bounds.
- `error()` returns a simple red HTML error string.
- `generateLinkPath()` builds breadcrumb HTML by walking up parent subforums.

## Session and Login State

- Flask-Login tracks authenticated users in session cookies.
- `load_user(userid)` in `forum/app.py` maps session user IDs to `User` rows.
- Routes requiring auth use `@login_required`.

## Templates and Rendering Role

- `subforums.html`: forum index page
- `subforum.html`: single subforum view + child subforums + post list
- `viewpost.html`: post detail + comments
- `createpost.html`: post creation form
- `login.html`: login/signup form
- `layout.html` and `header.html`: shared structure and navigation

## Important Notes About Current Logic

- Redundant DB initialization: `db.create_all()` is called in two places.
- Error responses are plain HTML snippets, not dedicated error templates.
- Some routes trust query parameters exist and are valid integers.
- Relative-time cache fields (`lastcheck`, `savedresponce`) are in-memory only and reset per process.

## Practical Mental Model

Think of the app as four layers:

1. Config layer (`config.py`): constants for app and database.
2. App wiring (`forum/__init__.py`, `forum/app.py`): create app, attach DB/login, seed initial data.
3. Domain layer (`forum/models.py`, `forum/user.py`): schema, validation helpers, utility functions.
4. Delivery layer (`forum/routes.py` + templates): map HTTP requests to queries, updates, and rendered HTML.

When debugging, start at the route, then trace into model queries and helper functions, then verify template rendering inputs.
