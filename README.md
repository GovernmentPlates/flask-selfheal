# flask-selfheal 🔗

Automatically fix broken URLs in your Flask app using intelligent resolvers.

![PyPI - Version](https://img.shields.io/pypi/v/flask-selfheal)
![PyPI - License](https://img.shields.io/pypi/l/flask-selfheal)

## Features
- **Multiple Matching Strategies**: Choose from 1:1 exact matching, fuzzy matching, and even hybrid database-backed approaches to find the best matching URL.
- **Configurable**: Fine-tune matching strategies, thresholds, and normalization rules to suit your needs.
- **Chainable Resolvers**: Combine multiple resolvers to create a robust URL healing strategy.
- **Easy Integration**: Plug into any Flask app with minimal setup.
- **Performant**: Optimized to try fast methods first and only use expensive ones as a last resort.


## Installation

```bash
uv pip install flask-selfheal
```

## Usage

### Fuzzy Flask Routes Resolver

This example demonstrates how to use the `FlaskRoutesResolver` to automatically correct common typos in your Flask routes using fuzzy matching (using `difflib` under the hood).

```python
from flask import Flask
from flask_selfheal import SelfHeal
from flask_selfheal.resolvers import FlaskRoutesResolver

app = Flask(__name__)

@app.route("/home")
def home():
    return "Welcome Home!"

@app.route("/about")
def about():
    return "About Us"

@app.route("/contact")
def contact():
    return "Contact Us"

# Configure SelfHeal with fuzzy matching
SelfHeal(app, resolvers=[FlaskRoutesResolver()])

if __name__ == "__main__":
    app.run(debug=True)
```

```
https://example.com/hme    --> Redirects to /home
https://example.com/abot   --> Redirects to /about
https://example.com/contat --> Redirects to /contact
```

### Chaining Multiple Resolvers

You can combine multiple resolvers to create a more robust URL healing strategy. In this example, we use both `AliasMappingResolver` and `FuzzyMappingResolver` to handle obsolete URLs and common typos.

```python
from flask import Flask
from flask_selfheal import SelfHeal
from flask_selfheal.resolvers import AliasMappingResolver, FuzzyMappingResolver

app = Flask(__name__)

@app.route("/home")
def home():
    return "Welcome Home!"

@app.route("/new-path")
def new_path():
    return "This is the new path!"

# Define resolvers - will be tried in order defined
resolvers = [
    AliasMappingResolver(
        {"old-path": "new-path"}  # Handle obsolete URLs
    ),
    FuzzyMappingResolver(
        ["home", "new-path"]  # Handle typos
    )
]

SelfHeal(app, resolvers=resolvers)

if __name__ == "__main__":
    app.run(debug=True)
```

```
https://example.com/old-path  --> Redirects to /new-path
https://example.com/hme       --> Redirects to /home
https://example.com/new-pth   --> Redirects to /new-path
```

### Database-Backed Resolver

The `DatabaseResolver` allows you to resolve URLs based on the slug in your database (using SQLAlchemy).

Ensure that you have a model with a slug field in your database (example below).

```python
class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False) # <--
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
```

```python
from flask import Flask
from app.models import Articles  # Your SQLAlchemy model
from flask_selfheal import SelfHeal
from flask_selfheal.resolvers import DatabaseResolver

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///yourdatabase.db"
db.init_app(app)

@app.route("/articles/<slug>")
def article_detail(slug):
    article = Articles.query.filter_by(slug=slug).first_or_404()
    return f"Article: {article.title}"

# Configure the DatabaseResolver
db_resolver = [
    DatabaseResolver(
        Articles,
        slug_field='slug',
    )
]

SelfHeal(app, resolvers=db_resolver, redirect_pattern="/articles/{slug}")

if __name__ == "__main__":
    app.run(debug=True)
```

```
https://example.com/articles/1234         --> Redirects to /articles/hello-world-1234567
https://example.com/articles/hello-world  --> Redirects to /articles/hello-world-1234567
https://example.com/articles/hell-wrl     --> Redirects to /articles/hello-world-1234567
https://example.com/articles/world        --> Redirects to /articles/hello-world-1234567
```

The `DatabaseResolver` follows these strategies in order when trying to find a matching slug:
1. **Exact match:** Fastest, direct database lookup
2. **SQL `LIKE` matching:** Handle simple variations using SQL `LIKE` wildcards
3. **Normalized matching:** Handle common typos (`0 -> o`, `1 -> l`, etc.)
4. **Word-based matching:** Match individual significant words
5. **Partial matching:** Match meaningful substrings
6. **Fuzzy matching:** Handle more complex typos by fuzzy matching


### Fine-tuning the Database Resolver

The `DatabaseResolver` can be customized with various parameters to adjust its behavior:

```python
resolver = DatabaseResolver(
    model=Product,
    slug_field='slug',
    use_fuzzy=True,                # Enable/disable last resort fuzzy matching
    fuzzy_cutoff=0.7,              # Similarity threshold (0-1)
    enable_word_matching=True,     # Match individual words
    enable_partial_matching=True,  # Match partial strings
    min_word_length=3,             # Minimum word length to consider
    custom_normalizers={           # Custom normalizer mappings (0 -> o, ph -> f, etc.)
        '0': 'o', 'ph': 'f'
    }
)
```

You can take a look at more examples in the `examples/` directory


## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request on GitHub.
