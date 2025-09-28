from flask import Flask, abort
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
    return """
    <h2>Examples with Alias Mapping & (Simple) Database Resolver</h2>
    <hr/>
    <p>Try these links:</p>
    <ul>
        <li><a href="/articles/self-healing-urls">Exact match</a></li>
        <li><a href="/articles/self-healing-url">Close match (missing 's')</a></li>
        <li><a href="/articles/flask-basic">Alias (flask-basic -> flask-basics)</a></li>
        <li><a href="/articles/flask-basics">Direct link</a></li>
        <li><a href="/articles/cool-product">Partial match</a></li>
        <li><a href="/articles/phone-xyz123">Phone match</a></li>
        <li><a href="/articles/super-phone">Partial phone match</a></li>
    </ul>
    <p>Check out <code>examples/simple_db.py</code> to see how it works!</p>
    """


@app.route("/articles/<slug>")
def by_slug(slug):
    article = Article.query.filter_by(slug=slug).first()
    if article:
        return f"Article: {article.slug}"
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
