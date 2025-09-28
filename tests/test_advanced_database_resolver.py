import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_selfheal.resolvers import DatabaseResolver


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    return app


@pytest.fixture
def db_with_products(app):
    db = SQLAlchemy(app)

    class Product(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        slug = db.Column(db.String, unique=True)

    with app.app_context():
        db.create_all()

        # Add test products with various slug patterns
        test_slugs = [
            "cool-product-SKU1234567",
            "awesome-gadget-ABC987654",
            "super-phone-XYZ123",
            "laptop-model-DEF456789",
            "gaming-mouse-GHI321654",
        ]

        for slug in test_slugs:
            db.session.add(Product(slug=slug))

        db.session.commit()

        return db, Product


def test_exact_match(app, db_with_products):
    db, Product = db_with_products
    resolver = DatabaseResolver(Product)

    with app.app_context():
        # Should find exact matches
        assert resolver.resolve("cool-product-SKU1234567") == "cool-product-SKU1234567"
        assert resolver.resolve("gaming-mouse-GHI321654") == "gaming-mouse-GHI321654"


def test_typo_normalization(app, db_with_products):
    db, Product = db_with_products
    resolver = DatabaseResolver(Product)

    with app.app_context():
        # Should handle common typos
        assert (
            resolver.resolve("c00l-product-SKU1234567") == "cool-product-SKU1234567"
        )  # 0 -> o
        assert (
            resolver.resolve("cool-pr0duct-SKU1234567") == "cool-product-SKU1234567"
        )  # 0 -> o


def test_word_matching(app, db_with_products):
    db, Product = db_with_products
    resolver = DatabaseResolver(Product)

    with app.app_context():
        # Should match based on significant words
        assert resolver.resolve("SKU1234567") == "cool-product-SKU1234567"
        assert resolver.resolve("ABC987654") == "awesome-gadget-ABC987654"
        assert resolver.resolve("product-SKU1234567") == "cool-product-SKU1234567"


def test_partial_matching(app, db_with_products):
    db, Product = db_with_products
    resolver = DatabaseResolver(Product)

    with app.app_context():
        # Should match partial strings
        assert resolver.resolve("cool-SKU1234567") == "cool-product-SKU1234567"
        assert resolver.resolve("awesome-ABC987654") == "awesome-gadget-ABC987654"


def test_fuzzy_matching(app, db_with_products):
    db, Product = db_with_products
    resolver = DatabaseResolver(Product, fuzzy_cutoff=0.7)

    with app.app_context():
        # Should handle more complex typos via fuzzy matching
        assert (
            resolver.resolve("cool-prodcut-SKU1234567") == "cool-product-SKU1234567"
        )  # transposed letters
        assert (
            resolver.resolve("awsome-gadget-ABC987654") == "awesome-gadget-ABC987654"
        )  # missing letter


def test_custom_normalizers(app, db_with_products):
    db, Product = db_with_products

    # Custom normalizers for domain-specific typos
    custom_normalizers = {
        "ph": "f",  # phone -> fone
        "sku": "SKU",  # case normalization
    }

    resolver = DatabaseResolver(Product, custom_normalizers=custom_normalizers)

    with app.app_context():
        # Test with custom normalizations
        assert resolver.resolve("super-fone-XYZ123") == "super-phone-XYZ123"


def test_configurable_matching(app, db_with_products):
    db, Product = db_with_products

    with app.app_context():
        # Test with word matching disabled
        resolver_no_words = DatabaseResolver(Product, enable_word_matching=False)
        # Should still find via LIKE patterns even with word matching disabled
        # (SKU1234567 matches via %SKU1234567% LIKE pattern)
        assert resolver_no_words.resolve("SKU1234567") == "cool-product-SKU1234567"

        # Test with partial matching disabled
        resolver_no_partial = DatabaseResolver(Product, enable_partial_matching=False)
        # Should still work for exact matches but not partial ones
        assert (
            resolver_no_partial.resolve("cool-product-SKU1234567")
            == "cool-product-SKU1234567"
        )

        # Test with different min word length
        resolver_long_words = DatabaseResolver(Product, min_word_length=6)
        # Should still find long words like SKU1234567
        assert resolver_long_words.resolve("SKU1234567") == "cool-product-SKU1234567"


def test_no_match_cases(app, db_with_products):
    db, Product = db_with_products
    resolver = DatabaseResolver(Product)

    with app.app_context():
        # Should return None for completely unrelated paths
        assert resolver.resolve("totally-different-thing") is None
        assert resolver.resolve("unrelated") is None
        assert resolver.resolve("") is None


def test_performance_order(app, db_with_products):
    """Test that matching strategies are tried in performance order"""
    db, Product = db_with_products
    resolver = DatabaseResolver(Product)

    with app.app_context():
        # Exact match should be fastest (and found first)
        result = resolver.resolve("cool-product-SKU1234567")
        assert result == "cool-product-SKU1234567"

        # Test that LIKE patterns work
        result = resolver.resolve("product-SKU")  # Should match via LIKE %product-SKU%
        assert result == "cool-product-SKU1234567"
