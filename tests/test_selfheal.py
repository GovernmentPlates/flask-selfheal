from flask import Flask, abort
from flask_selfheal import SelfHeal, AliasMappingResolver


def test_selfheal_client_redirect():
    app = Flask(__name__)

    @app.route("/<slug>")
    def by_slug(slug):
        # Simulate DB lookup: only "new" exists
        if slug == "new":
            return f"Slug: {slug}"
        abort(404)

    SelfHeal(app, resolvers=[AliasMappingResolver({"old": "new"})])
    client = app.test_client()

    # Request a slug that doesn't exist
    response = client.get("/old", follow_redirects=False)

    # Check that the redirect happened
    assert response.status_code == 301
    assert response.headers["Location"].endswith("/new")

    # Follow the redirect and check we are on the right page
    final = client.get("/old", follow_redirects=True)
    assert final.status_code == 200
    assert b"Slug: new" in final.data
