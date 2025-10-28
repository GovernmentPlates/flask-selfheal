from flask import Flask, render_template
from flask_selfheal import SelfHeal
from flask_selfheal.resolvers import (
    AliasMappingResolver,
    FlaskRoutesResolver,
    FuzzyMappingResolver,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("no_db/index.html")


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
