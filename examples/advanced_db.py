from flask import Flask, redirect, url_for
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
    return f"""
    <h1>{product.name}</h1>
    <p>Slug: {product.slug}</p>
    <p>Price: {product.price} CHF</p>
    <hr/>
    <p><i>Return back to the <a href="{url_for("search")}">frontpage</a>.</i></p>
    """
    # ^ Never ever do this in a real app - this is just for demo purposes
    # (look up "SSTI" if you are curious, and more importantly, use templates!)


@app.route("/search")
def search():
    products = Product.query.all()
    return f"""
    <h2>Advanced URL healing examples</h2>
    <hr/>
    <p>You can configure the <code>DatabaseResolver</code> with options to control the fuzzy threshold, typo 
    checks and more. As well as define custom logic in the <code>SelfHeal</code> subclass to extract slugs from complex paths.</p>
    <p>In this example, we handle paths like <code>/product/&lt;slug&gt;</code> and try to resolve <code>&lt;slug&gt;</code> 
    using various strategies.</p>
    <p>Check out <code>examples/advanced_db.py</code> to see how it works!</p>
    <p>In the meantime, try these links or test your own variations below:</p>
    <ul>
        <li><a href="/product/cool-product-SKU1234567">Exact match</a></li>
        <li><a href="/product/cool-pr0duct-SKU1234567">With typo (0 instead of o)</a></li>
        <li><a href="/product/cool-SKU1234567">Partial match I</a></li>
        <li><a href="/product/product-SKU1234567">Partial match II</a></li>
        <li><a href="/product/SKU1234567">Just the SKU</a></li>
        <li><a href="/product/cool-prodcut-SKU1234567">Transposed letters ('prodcut' instead of 'product')</a></li>
        <li><a href="/product/awesome-ABC987654">Different product</a></li>
        <li><a href="/product/phone-xyz123">Phone variation</a></li>
    </ul>
    <form method="GET" action="/product/">
        <input type="text" name="test" placeholder="Enter any product variation" style="width: 200px;"/>
        <button type="submit">Test Resolver</button>
    </form>
    <p>You can also see all the products in the demo database here:</p>
    <table>
        <thead>
            <tr><th>slug</th><th>name</th><th>price (CHF)</th></tr>
        </thead>
        <tbody>
            {"".join(f'<tr><td><a href="/product/{p.slug}">{p.slug}</a></td><td>{p.name}</td><td>{p.price}</td></tr>' for p in products)}
        </tbody>
    </table>
    """
    # ^ Also never do this in your real app - this is just for demo purposes and I'm lazy :)


@app.route("/")
def index():
    return redirect(url_for("search"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
