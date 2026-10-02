"""CyberShield 360 - Application Configuration"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration for Flask application."""

    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "cybershield360-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cybershield360-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb://localhost:27017/cybershield360"
    )
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "cybershield360")

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), "reports")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    RATE_LIMIT_DEFAULT = "200 per hour"
    RATE_LIMIT_AUTH = "20 per minute"

    # ML model paths
    ML_MODELS_PATH = os.path.join(os.path.dirname(__file__), "ml_models")
    URL_MODEL_PATH = os.path.join(ML_MODELS_PATH, "url_rf_model.pkl")

    # Frontend path
    FRONTEND_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
