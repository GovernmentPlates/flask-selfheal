from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_selfheal import SelfHeal
from flask_selfheal.resolvers import DatabaseResolver

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db = SQLAlchemy(app)


# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()
    db.session.add_all(
        [
            Product(slug="cool-product-SKU1234567", name="Cool Product", price=199.99),
            Product(
                slug="awesome-gadget-ABC987654", name="Awesome Gadget", price=149.99
            ),
            Product(slug="super-phone-XYZ123", name="Super Phone", price=599.99),
            Product(slug="gaming-mouse-GHI321654", name="Gaming Mouse", price=79.99),
            Product(slug="laptop-model-DEF456789", name="Laptop Model", price=1299.99),
        ]
    )
    db.session.commit()

# Configure the DatabaseResolver
product_resolver = DatabaseResolver(
    model=Product,
    slug_field="slug",
    use_fuzzy=True,  # Enable fuzzy matching for typos
    fuzzy_cutoff=0.7,  # Higher threshold for better matches
    enable_word_matching=True,  # Match individual words like "SKU1234567"
    enable_partial_matching=True,  # Match partial strings like "cool-SKU1234567"
    min_word_length=4,  # Only consider words 4+ chars for matching
    custom_normalizers={  # Domain-specific typo corrections (for the demo)
        "0": "o",  # 0 -> o
        "1": "l",  # 1 -> l
        "pr0duct": "product",  # Common product typo
    },
)


# Custom SelfHeal class that extracts slug from /product/<slug> paths
class ProductSelfHeal(SelfHeal):
    def handle_404(self, e):
        from flask import request, redirect, url_for

        path = request.path.strip("/")

        # Extract slug from /product/<slug> paths
        if path.startswith("product/"):
            slug_part = path[8:]  # Remove "product/" prefix
        else:
            slug_part = path

        for resolver in self.resolvers:
            target = resolver.resolve(slug_part)
            if target:
                redirect_url = url_for("product_detail", slug=target)
                return redirect(redirect_url, code=301)

        return f"404 Not Found: {path}", 404


# Initialize SelfHeal with custom handler
selfheal = ProductSelfHeal(app, resolvers=[product_resolver])


@app.route("/product/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    return render_template("advanced_db/product.html", product=product)


@app.route("/products")
def products():
    products = Product.query.all()
    return render_template("advanced_db/search.html", products=products)


@app.route("/")
def index():
    return redirect(url_for("products"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
