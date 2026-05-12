"""Конфигурация Flask-приложения TripPlanner.

Все параметры собраны в одном месте, чтобы не размазывать константы
по разным модулям и упростить переключение между окружениями.
"""
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"


class Config:
    """Общие настройки приложения."""

    SECRET_KEY = os.environ.get("TRIPPLANNER_SECRET", "tripplanner-dev-secret")

    DATABASE_URL = f"sqlite:///{(DB_DIR / 'tripplanner.sqlite').as_posix()}"

    UPLOAD_FOLDER = str(UPLOAD_DIR)
    ALLOWED_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "gif", "webp"})
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    ITEMS_PER_PAGE = 9

    GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
    GEOCODER_USER_AGENT = "TripPlanner/1.0 (educational project)"
    GEOCODER_TIMEOUT = 5

    EXPENSE_CATEGORIES = (
        "transport",
        "accommodation",
        "food",
        "activities",
        "souvenirs",
        "other",
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
