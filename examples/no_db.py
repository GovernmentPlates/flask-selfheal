from flask import Flask
from flask_selfheal import SelfHeal
from flask_selfheal.resolvers import (
    AliasMappingResolver,
    FlaskRoutesResolver,
    FuzzyMappingResolver,
)

app = Flask(__name__)


@app.route("/")
def index():
    return """
    <h2>Welcome to the Self-Healing Flask App!</h2>
    <hr/>
    <p>This tests the <code>AliasMappingResolver</code>, <code>FlaskRoutesResolver</code>, and <code>FuzzyMappingResolver</code>.</p>
    <p>Try these links:</p>
    <ul>
        <li><a href="/hello-world">/hello-world</a> (exact match)</li>
        <li><a href="/hello-worl">/hello-worl (typo)</a></li>
        <li><a href="/world-hello">/world-hello (exact match)</a></li>
        <li><a href="/flask-basic">/flask-basic (flask-basic -> flask-basics)</a></li>
        <li><a href="/flask-basics">/flask-basics (exact match)</a></li>
        <li><a href="/flask-bascis">/flask-bascis (typo)</a></li>
        <li><a href="/not-found">/not-found (no match)</a></li>
    </ul>
    <p>Check out <code>examples/no_db.py</code> to see how it works!</p>
    """


@app.route("/hello-world")
def hello():
    return "Hello!"


@app.route("/world-hello")
def world_hello():
    return "World Hello!"


@app.route("/flask-basics")
def basics():
    return "Flask Basics"


# Resolvers: first check aliases, then Flask routes, then fuzzy match
resolvers = [
    AliasMappingResolver({"flask-basic": "flask-basics"}),
    FlaskRoutesResolver(),
    FuzzyMappingResolver(["hello-world", "flask-basics"]),
]

SelfHeal(app, resolvers=resolvers)

if __name__ == "__main__":
    app.run(debug=True)
