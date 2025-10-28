from flask import Flask, abort, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_selfheal import SelfHeal
from flask_selfheal.resolvers import DatabaseResolver, AliasMappingResolver

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String, unique=True)


with app.app_context():
    db.create_all()
    db.session.add(Article(slug="self-healing-urls"))
    db.session.add(Article(slug="flask-basics"))
    db.session.add(Article(slug="cool-product-SKU1234567"))
    db.session.add(Article(slug="super-phone-XYZ123"))
    db.session.commit()


@app.route("/")
def index():
    return render_template("simple_db/index.html")


@app.route("/articles/<slug>")
def by_slug(slug):
    article = Article.query.filter_by(slug=slug).first()
    if article:
        return render_template("simple_db/article.html", slug=article.slug)
    abort(404)


# Resolvers: first check aliases, then DB
resolvers = [
    AliasMappingResolver({"flask-basic": "flask-basics"}),
    DatabaseResolver(
        Article,
        min_word_length=4,  # Require 4+ chars to prevent "123" matches
    ),
]

SelfHeal(app, resolvers=resolvers, redirect_pattern="/articles/{slug}")

if __name__ == "__main__":
    app.run(debug=True)
