# MySQL Migration and Startup Guide

This guide explains what we changed to move the app to MySQL, why the changes were needed, and how the app starts now. It is written for a team handoff, so it gives a quick summary first and then the deeper details.

## Quick Overview

- The app used to depend on SQLite-style assumptions.
- We moved the database config to MySQL and added PyMySQL support.
- We changed the launcher so the app starts with sensible defaults instead of stopping on missing environment variables.
- We fixed the schema so MySQL can create the tables cleanly.
- We added startup checks so the app can create the database and app user when MySQL access is available.

In short: the app now starts, connects to MySQL, creates its tables, and seeds the default forum structure without the user having to understand the setup details first.

## What We Changed

### 1. Database configuration moved to MySQL

The core database settings live in `config.py`. That file now builds a MySQL connection string using:

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`

If those environment variables are not provided, the app uses defaults that match the project setup:

- user: `zipchat_app`
- password: `password`
- host: `127.0.0.1`
- port: `3306`
- database: `ZipChat`

This means a teammate can clone the repo and run the launcher without having to edit config files first.

### 2. The launcher no longer hard-stops on missing password input

`run.sh` used to exit when `DB_PASSWORD` was missing. That made startup brittle because the app could not even get to its own error handling.

Now `run.sh`:

- creates the virtual environment if needed
- installs requirements
- sets MySQL environment defaults
- provides a default DB password if one is not exported
- starts Flask

That makes the startup path more forgiving for new users and for team members running the app locally.

### 3. The schema was adjusted for MySQL rules

MySQL does not allow unique indexes on plain `TEXT` columns without a key length. That is why `db.create_all()` originally failed on the `User` table.

We changed the model fields that need uniqueness or fixed sizes:

- `User.username` became a bounded string
- `User.email` became a bounded string
- `User.password_hash` became a bounded string
- `Post.title` became a bounded string
- `Subforum.title` became a bounded string

That was the key schema fix that allowed MySQL table creation to succeed.

### 4. Startup now tries to prepare MySQL automatically

`config.py` now includes startup helpers that:

- try to connect to MySQL as an admin user on the local machine
- create the `ZipChat` database if it is missing
- create the `zipchat_app` user if it is missing
- grant that user access to the database
- verify that the app credentials can connect

This is a best-effort bootstrap. If MySQL admin access is unavailable on a specific machine, the code prints clear instructions instead of failing silently.

### 5. MySQL driver support was added

The app uses PyMySQL to talk to MySQL, and MySQL 9 can use `caching_sha2_password` authentication. That means the Python environment also needs the `cryptography` package.

Without `cryptography`, the connection can fail during authentication even if the database settings are otherwise correct.

## How Startup Works Now

The current startup sequence is:

1. `bash ./run.sh` is executed.
2. The script creates or reuses `.venv`.
3. Dependencies are installed.
4. Environment defaults are set for the app.
5. Flask starts with `forum.app`.
6. `forum/app.py` imports the Flask app factory.
7. `config.py` runs the MySQL setup checks.
8. MySQL admin access is attempted.
9. The database and app user are created if possible.
10. The app connects as `zipchat_app`.
11. `db.create_all()` creates tables.
12. The default subforums are seeded if needed.
13. The site starts listening on the configured port.

That flow is why the app now feels more like a single command startup instead of a manual setup checklist.

## Why Each Change Was Necessary

### MySQL needed more explicit setup than SQLite

SQLite is very forgiving because it stores data in a local file and usually does not require credentials. MySQL is stricter because it expects:

- a running server
- a database name
- a user account
- a password or admin path
- permissions on the target database

That is why a SQLite-style setup can work in development but fail once the backend is switched to MySQL.

### The app needed a real default path

Before the cleanup, startup depended on the user remembering environment variables and database details. That is brittle for a team workflow.

The new defaults mean the repo itself now contains the expected values, and environment variables are only needed for overrides.

### The models needed to match MySQL rules

The ORM models are not just app code. They define the actual SQL table structure. If a field is too open-ended for a unique constraint, MySQL rejects the table creation.

Changing `TEXT` to bounded `String` fields made the schema portable and allowed table creation to work consistently.

## What A New Teammate Should Know

- Start the app with `bash ./run.sh` from the project root.
- The app now carries sane defaults for the MySQL connection.
- The first startup may print MySQL setup warnings if local admin access is not available.
- If the database already exists, startup should proceed directly to table creation and app launch.
- If you want to override credentials, export the environment variables before running the launcher.

## Important Files

- `run.sh`: launch script and runtime defaults
- `config.py`: MySQL setup logic and SQLAlchemy configuration
- `forum/models.py`: database schema definitions
- `forum/app.py`: app startup, table creation, and seed data
- `requirements.txt`: Python dependencies, including PyMySQL and cryptography

## Final Result

The app now has a simpler onboarding story:

- run one command
- get a MySQL-backed Flask app
- have the database schema created automatically
- use a predictable app user and database name

That is the version of the project you can hand to a teammate without asking them to understand the whole migration history first.
