"""Forum-side compatibility package for user validation/query helpers."""

import re

from forum.models import User

password_regex = re.compile(r"^[a-zA-Z0-9!@#%&]{6,40}$")
username_regex = re.compile(r"^[a-zA-Z0-9!@#%&]{4,40}$")
email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_username(username):
	return bool(username_regex.match(username))


def valid_password(password):
	return bool(password_regex.match(password))


def valid_email(email):
	return bool(email_regex.match(email))


def username_taken(username):
	return User.query.filter(User.username == username).first()


def email_taken(email):
	return User.query.filter(User.email == email).first()


__all__ = [
	"email_taken",
	"username_taken",
	"valid_email",
	"valid_password",
	"valid_username",
]
