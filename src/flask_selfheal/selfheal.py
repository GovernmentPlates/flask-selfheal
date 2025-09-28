from flask import request, redirect, url_for


class SelfHeal:
    """
    Self-healing URL middleware for Flask.

    This middleware attempts to resolve 404 errors by redirecting to
    a "close enough" URL based on the provided resolving strategies.

    :param resolvers: list of resolver instances
    :param redirect_pattern: pattern for redirect URL (e.g., "/product/{slug}", "/{slug}")
    :param endpoint: Flask endpoint name to use with url_for instead of redirect
    """

    def __init__(
        self, app=None, resolvers=None, redirect_pattern="/{slug}", endpoint=None
    ):
        self.app = app
        self.resolvers = resolvers or []
        self.redirect_pattern = redirect_pattern
        self.endpoint = endpoint

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.register_error_handler(404, self.handle_404)

    def handle_404(self, e):
        path = request.path.strip("/")

        for resolver in self.resolvers:
            target = resolver.resolve(path)
            if target:
                if self.endpoint:
                    # Use Flask url_for with the specified endpoint
                    return redirect(url_for(self.endpoint, slug=target), code=301)
                else:
                    # Use the redirect pattern (default: "/{slug}")
                    redirect_url = self.redirect_pattern.format(slug=target)
                    return redirect(redirect_url, code=301)

        return f"404 Not Found: {path}", 404 # Maybe make this configurable (custom page)?
