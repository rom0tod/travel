"""Геокодер на основе публичного API OpenStreetMap (Nominatim).

Используется библиотека ``requests``. Ключи не нужны, но Nominatim
требует осмысленный User-Agent — он берётся из конфига.
"""
from typing import Optional

import requests

from config import Config


class GeocodingError(Exception):
    """Ошибка обращения к сервису геокодирования."""


def geocode(address: str) -> Optional[dict]:
    """Возвращает координаты адреса или None, если ничего не найдено.

    Результат: словарь ``{"latitude", "longitude", "display_name"}``.
    Сетевые ошибки заворачиваются в GeocodingError.
    """
    cleaned = (address or "").strip()
    if not cleaned:
        return None

    params = {
        "q": cleaned,
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": Config.GEOCODER_USER_AGENT}

    try:
        response = requests.get(
            Config.GEOCODER_URL,
            params=params,
            headers=headers,
            timeout=Config.GEOCODER_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise GeocodingError(f"Сеть недоступна: {exc}") from exc

    if response.status_code != 200:
        raise GeocodingError(
            f"Сервис вернул статус {response.status_code}."
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise GeocodingError("Некорректный ответ геокодера.") from exc

    if not data:
        return None

    item = data[0]
    try:
        return {
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"]),
            "display_name": item.get("display_name", cleaned),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise GeocodingError("Ответ геокодера не содержит координат.") from exc
