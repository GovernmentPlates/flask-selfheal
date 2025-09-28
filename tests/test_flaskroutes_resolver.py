from flask import Flask
from flask_selfheal.resolvers import FlaskRoutesResolver


def test_flaskroutes_resolver():
    app = Flask(__name__)

    @app.route("/hello-world")
    def hello():
        return "hi"

    with app.app_context():
        resolver = FlaskRoutesResolver()
        assert resolver.resolve("hello-worl") == "hello-world"
        assert resolver.resolve("not-found") is None
