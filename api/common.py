"""Общие утилиты REST API.

Здесь собраны функции, которыми пользуются разные ресурсы:
проверка переданных полей, обработка ошибок, единый формат ответа.
"""
from typing import Iterable

from flask import jsonify, make_response


def abort_with(status: int, message: str):
    """Возвращает JSON-ответ с ошибкой и заданным HTTP-статусом."""
    response = jsonify({"success": False, "error": message})
    response.status_code = status
    return response


def ok(payload: dict | None = None, status: int = 200):
    """Стандартизованный успешный ответ API."""
    body = {"success": True}
    if payload:
        body.update(payload)
    response = jsonify(body)
    response.status_code = status
    return response


def check_required_fields(data: dict | None, fields: Iterable[str]):
    """Возвращает ответ с ошибкой, если хотя бы одно поле отсутствует."""
    if data is None:
        return abort_with(400, "Ожидается JSON-тело запроса.")
    missing = [field for field in fields if field not in data]
    if missing:
        return abort_with(
            400,
            f"Отсутствуют обязательные поля: {', '.join(missing)}.",
        )
    return None


def not_found(entity: str):
    return abort_with(404, f"{entity} не найден(а).")


def forbidden():
    return abort_with(403, "Недостаточно прав для этого действия.")


def make_error_handler(status: int, message: str):
    """Фабрика обработчиков HTTP-ошибок для Flask."""
    def handler(_exc):
        return make_response(
            jsonify({"success": False, "error": message}),
            status,
        )
    return handler
