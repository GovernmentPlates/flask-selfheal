from flask_selfheal.resolvers import FuzzyMappingResolver


def test_fuzzy_resolver():
    resolver = FuzzyMappingResolver(["hello-world", "flask-basics"])
    assert resolver.resolve("flask-basic") == "flask-basics"
    assert resolver.resolve("not-found") is None
