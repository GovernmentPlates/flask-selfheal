import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_selfheal.resolvers import DatabaseResolver


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    return app


def test_database_resolver(app):
    db = SQLAlchemy(app)

    class Article(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        slug = db.Column(db.String, unique=True)

    with app.app_context():
        db.create_all()
        db.session.add(Article(slug="flask-basics"))
        db.session.commit()

        resolver = DatabaseResolver(Article)
        assert resolver.resolve("flask-basic") == "flask-basics"
        assert resolver.resolve("not-found") is None
