from flask_selfheal.resolvers import AliasMappingResolver


def test_alias_resolver():
    resolver = AliasMappingResolver({"old-slug": "new-slug"})
    assert resolver.resolve("old-slug") == "new-slug"
    assert resolver.resolve("missing") is None
