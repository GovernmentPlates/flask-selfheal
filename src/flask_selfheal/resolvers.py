from difflib import get_close_matches
from sqlalchemy import or_
import re


class BaseResolver:
    """Base class for all resolvers"""

    def resolve(self, path: str) -> str | None:
        raise NotImplementedError


class AliasMappingResolver(BaseResolver):
    """Basic 1:1 alias mapping resolver

    Resolves old slugs to new slugs based on a provided mapping. This is
    useful for handling renamed or moved resources where the old slug should
    redirect to the new slug.

    :param alias_map: Dict mapping old_slug -> new_slug
    """

    def __init__(self, alias_map: dict[str, str]):
        self.alias_map = alias_map

    def resolve(self, path: str) -> str | None:
        return self.alias_map.get(path)


class FuzzyMappingResolver(BaseResolver):
    """Fuzzy-like matching resolver

    Similar to the :class:`AliasMappingResolver`, but uses fuzzy-like matching to
    find the closest match from a list of candidates.

    :param candidates: List of valid slugs or routes
    :param fuzzy_cutoff: Similarity threshold (0 to 1) for a match to be considered valid
    """

    def __init__(self, candidates: list[str], fuzzy_cutoff=0.6):
        self.candidates = candidates
        self.fuzzy_cutoff = fuzzy_cutoff

    def resolve(self, path: str) -> str | None:
        close = get_close_matches(path, self.candidates, n=1, cutoff=self.fuzzy_cutoff)
        return close[0] if close else None


class DatabaseResolver(BaseResolver):
    """Database-backed resolver with fuzzy-like matching

    Resolves slugs by querying a SQLAlchemy model. This will try multiple
    strategies in the following order: exact match, `LIKE` wildcards
    (via :func:`.contains()`), word-based matching, partial matching,
    and finally fuzzy matching.

    You will need to ensure that the model and `slug_field` are correctly set up
    to match your database schema.

    For example:
    ```
    class Article(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        slug = db.Column(db.String, unique=True)
    ```

    :param model: SQLAlchemy model
    :param slug_field: column name to use
    :param use_fuzzy: whether to use fuzzy matching as a last resort
    :param fuzzy_cutoff: similarity threshold for fuzzy matching (0 to 1)
    :param enable_word_matching: whether to match individual words from the path
    :param enable_partial_matching: whether to try partial matches of the path
    :param min_word_length: minimum length for words to be considered in matching
    :param custom_normalizers: dict of custom character normalizations
    """

    def __init__(
        self,
        model,
        slug_field="slug",
        use_fuzzy=True,
        fuzzy_cutoff=0.6,
        enable_word_matching=True,
        enable_partial_matching=True,
        min_word_length=3,
        custom_normalizers=None,
    ):
        self.model = model
        self.slug_field = slug_field
        self.use_fuzzy = use_fuzzy
        self.fuzzy_cutoff = fuzzy_cutoff
        self.enable_word_matching = enable_word_matching
        self.enable_partial_matching = enable_partial_matching
        self.min_word_length = min_word_length
        self.custom_normalizers = custom_normalizers or {}

    def resolve(self, path: str) -> str | None:
        # Handle empty or very short paths
        if not path or len(path.strip()) < 2:
            return None

        session = self.model.query.session
        slug_column = getattr(self.model, self.slug_field)

        # First try exact match (fastest)
        exact_match = session.query(slug_column).filter(slug_column == path).scalar()
        if exact_match:
            return exact_match

        # Try contains match (covers startswith and endswith cases)
        contains_match = (
            session.query(slug_column)
            .filter(slug_column.contains(path, autoescape=True))
            .first()
        )
        if contains_match:
            return contains_match[0]

        # Try normalized version for common typos
        normalized_path = self._normalize_path(path)
        if normalized_path != path:
            # Try exact match first
            exact_norm_match = (
                session.query(slug_column)
                .filter(slug_column == normalized_path)
                .first()
            )
            if exact_norm_match:
                return exact_norm_match[0]

            contains_norm_match = (
                session.query(slug_column)
                .filter(slug_column.contains(normalized_path, autoescape=True))
                .first()
            )
            if contains_norm_match:
                return contains_norm_match[0]

        # Try word-based matching
        if self.enable_word_matching:
            word_match = self._try_word_matching(session, slug_column, path)
            if word_match:
                return word_match

        # Try partial matching for significant parts
        if self.enable_partial_matching:
            partial_match = self._try_partial_matching(session, slug_column, path)
            if partial_match:
                return partial_match

        # Finally, fall back to fuzzy matching for typos (slower but comprehensive)
        if self.use_fuzzy:
            slugs = [row[0] for row in session.query(slug_column).all()]
            close = get_close_matches(path, slugs, n=1, cutoff=self.fuzzy_cutoff)
            return close[0] if close else None

        return None

    def _normalize_path(self, path: str) -> str:
        """Normalize path for common typos and character substitutions"""
        # Default normalizations (I find these are generally useful in my testing)
        normalizations = {
            "0": "o",
            "1": "l",
            "3": "e",
            "5": "s",
            "@": "a",
            "ph": "f",
            "ck": "k",
            "qu": "kw",
        }

        # Override with custom normalizations if provided
        if self.custom_normalizers:
            normalizations = self.custom_normalizers

        normalized = path.lower()
        for typo, correct in normalizations.items():
            normalized = normalized.replace(typo, correct)

        return normalized

    def _try_word_matching(self, session, slug_column, path: str) -> str | None:
        """Try matching based on individual words in the path"""
        # Extract meaningful words (alphanumeric sequences)
        words = re.findall(r"[a-zA-Z0-9]+", path)
        significant_words = [w for w in words if len(w) >= self.min_word_length]

        if not significant_words:
            return None

        patterns = []

        for word in significant_words:
            patterns.append(slug_column.contains(word, autoescape=True))

        # Add word combinations (max 2 words)
        if len(significant_words) > 1:
            for i in range(len(significant_words)):
                for j in range(i + 1, min(i + 3, len(significant_words) + 1)):
                    combo = "-".join(significant_words[i:j])
                    patterns.append(slug_column.contains(combo, autoescape=True))

        word_match = session.query(slug_column).filter(or_(*patterns)).first()
        if word_match:
            return word_match[0]

        return None

    def _try_partial_matching(self, session, slug_column, path: str) -> str | None:
        """Try matching significant parts of the path"""
        # Remove common separators and split
        clean_path = re.sub(r"[-_\s]+", "", path)

        if len(clean_path) < 4:
            return None

        # Try different substring lengths, starting with longer ones
        for length in range(max(4, len(clean_path) // 2), len(clean_path)):
            for start in range(len(clean_path) - length + 1):
                substring = clean_path[start : start + length]
                if len(substring) >= 4:  # Only try meaningful substrings
                    partial_match = (
                        session.query(slug_column)
                        .filter(slug_column.contains(substring, autoescape=True))
                        .first()
                    )
                    if partial_match:
                        return partial_match[0]

        return None


class FlaskRoutesResolver(BaseResolver):
    """Fuzzy-like resolver based on existing Flask routes

    Similar to the :class:`FuzzyMappingResolver`, but uses the current
    Flask app's registered routes as candidates.

    :param fuzzy_cutoff: Similarity threshold (0 to 1) for a match to be considered valid
    """

    def __init__(self, fuzzy_cutoff=0.6):
        self.fuzzy_cutoff = fuzzy_cutoff

    def resolve(self, path: str) -> str | None:
        from flask import current_app

        routes = [
            r.rule.strip("/")
            for r in current_app.url_map.iter_rules()
            if "<" not in r.rule  # Skip dynamic routes
        ]
        # Filter out empty strings (root route - '/') to avoid redirect loops
        routes = [route for route in routes if route]
        close = get_close_matches(path, routes, n=1, cutoff=self.fuzzy_cutoff)
        return close[0] if close else None
