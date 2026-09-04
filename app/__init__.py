from flask import Flask


def create_app():
    """Create and configure the GryphDeck API."""
    app = Flask(__name__)

    from app.routes import main

    app.register_blueprint(main)

    @app.after_request
    def add_cors_headers(response):
        """Allow the local Next.js frontend to call the development API."""
        response.headers["Access-Control-Allow-Origin"] = app.config.get(
            "FRONTEND_ORIGIN", "http://localhost:3000"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        return response

    return app
