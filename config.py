"""Flask configuration and MySQL bootstrap helpers."""

from os import environ, path

basedir = path.abspath(path.dirname(__file__))


class Config:
    """Configuration values consumed by Flask and Flask-SQLAlchemy."""

    SECRET_KEY = environ.get("SECRET_KEY", "kristofer")
    FLASK_APP = "forum.app"
    UPLOAD_FOLDER = path.join(basedir, "forum", "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "webm"}

    DB_USER = environ.get("DB_USER", "zipchat_app")
    DB_PASSWORD = environ.get("DB_PASSWORD", "password")
    DB_HOST = environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = environ.get("DB_PORT", "3306")
    DB_NAME = environ.get("DB_NAME", "ZipChat")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False