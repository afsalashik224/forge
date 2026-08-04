import os

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Settings:
    """Application configuration."""

    APP_NAME = os.getenv("APP_NAME", "Forge")
    APP_VERSION = os.getenv("APP_VERSION", "0.1.1")

    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))

    DATABASE_URL = os.getenv("DATABASE_URL")

    SECRET_KEY = os.getenv("SECRET_KEY")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
