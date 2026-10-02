"""CyberShield 360 - Main Flask Application."""
import os
import sys

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from routes.content_routes import content_bp
from routes.dashboard_routes import dashboard_bp
from routes.notify_routes import notify_bp
from routes.reports_routes import reports_bp
from routes.scanner_routes import scanner_bp
from utils.database import init_db


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)

    if app.config["APP_ENV"] == "production":
        required_env = ("SECRET_KEY", "JWT_SECRET_KEY", "MONGO_URI", "ADMIN_EMAIL", "ADMIN_PASSWORD")
        missing_env = [key for key in required_env if not os.getenv(key)]
        if missing_env:
            raise RuntimeError(f"Missing required production environment variables: {', '.join(missing_env)}")

    # Initialize extensions
    cors_origins = [
        origin.strip().rstrip("/")
        for origin in app.config["CORS_ORIGINS"].split(",")
        if origin.strip()
    ]
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        expose_headers=["Content-Type", "Authorization"],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )

    JWTManager(app)

    # Initialize database
    try:
        database = init_db(
            app.config["MONGO_URI"],
            app.config["MONGO_DB_NAME"]
        )
        if database is None and app.config["APP_ENV"] == "production":
            raise RuntimeError("MongoDB is required in production; verify the Atlas URI and network access list.")
        app.config["DB_CONNECTED"] = database is not None

    except Exception as e:
        if app.config["APP_ENV"] == "production":
            raise RuntimeError(f"Production database initialization failed: {e}") from e
        app.config["DB_CONNECTED"] = False

        print(
            f"Warning: MongoDB connection failed: {e}"
        )

        print(
            "App will run with limited functionality. "
            "Configure MONGO_URI in .env"
        )

    # Create upload/report directories
    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    os.makedirs(
        app.config["REPORTS_FOLDER"],
        exist_ok=True
    )

    os.makedirs(
        app.config["ML_MODELS_PATH"],
        exist_ok=True
    )

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(scanner_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(notify_bp)
    app.register_blueprint(admin_bp)

    # Seed base app data once the app is initialized.
    if app.config.get("DB_CONNECTED") or app.config["APP_ENV"] != "production":
        try:
            from seed_data import seed_database
            seed_database()
        except Exception as e:
            print(f"Seed warning: {e}")

    # Serve frontend static files
    frontend_path = app.config["FRONTEND_FOLDER"]

    @app.route("/")
    def index():
        return send_from_directory(
            frontend_path,
            "index.html"
        )

    @app.route("/<path:path>")
    def serve_frontend(path):
        """Serve frontend files and clean page routes."""

        if path.startswith("api/"):
            return {
                "error": "API route not found"
            }, 404

        # Exact match under frontend
        file_path = os.path.join(
            frontend_path,
            path
        )

        if os.path.isfile(file_path):
            return send_from_directory(
                frontend_path,
                path
            )

        # Normalize relative page path
        rel_path = (
            path[6:]
            if path.startswith("pages/")
            else path
        )

        # Candidate paths
        candidates = [
            rel_path,
            f"{rel_path}.html",
            f"{path}.html"
        ]

        for cand in candidates:

            page_full = os.path.join(
                frontend_path,
                "pages",
                cand
            )

            if os.path.isfile(page_full):

                return send_from_directory(
                    os.path.join(
                        frontend_path,
                        "pages"
                    ),
                    cand
                )

        # Fallback
        return send_from_directory(
            frontend_path,
            "index.html"
        )

    @app.route(
        "/api/health",
        methods=["GET"]
    )
    def health():

        return {
            "status": "healthy",
            "app": "CyberShield 360",
            "version": "1.0.0",
            "database": app.config.get(
                "DB_CONNECTED",
                False
            )
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":

    # Seed database on first run
    if app.config.get("DB_CONNECTED"):

        try:

            from seed_data import seed_database

            seed_database()

        except Exception as e:

            print(
                f"Seed warning: {e}"
            )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )