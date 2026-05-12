"""Утилитарные функции и декораторы для веб-слоя."""
import os
import secrets
from functools import wraps
from pathlib import Path
from typing import Iterable

from flask import abort, flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename

from config import Config


def is_allowed_image(filename: str) -> bool:
    """Проверяет, что расширение файла входит в разрешённые."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def save_uploaded_image(file_storage, subfolder: str) -> str:
    """Сохраняет файл в папку загрузок и возвращает относительный путь.

    Возвращает строку вида ``uploads/<subfolder>/<random>.jpg`` —
    её можно передавать в ``url_for('static', filename=...)``.
    """
    if file_storage is None or not file_storage.filename:
        return ""

    original = secure_filename(file_storage.filename)
    if not is_allowed_image(original):
        return ""

    ext = original.rsplit(".", 1)[1].lower()
    new_name = f"{secrets.token_hex(16)}.{ext}"

    target_dir = Path(Config.UPLOAD_FOLDER) / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    full_path = target_dir / new_name
    file_storage.save(str(full_path))

    return f"uploads/{subfolder}/{new_name}"


def remove_static_file(relative_path: str) -> None:
    """Удаляет файл из static-папки, если он существует."""
    if not relative_path:
        return
    full_path = Path(Config.UPLOAD_FOLDER).parent / relative_path
    try:
        if full_path.is_file():
            os.remove(full_path)
    except OSError:
        pass


def owner_required(loader):
    """Декоратор: разрешает доступ только владельцу объекта.

    ``loader`` принимает kwargs view-функции и возвращает (obj, owner_field).
    Поле ``owner_field`` — имя атрибута, в котором лежит ``user_id``.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Сначала войдите в аккаунт.", "warning")
                return redirect(url_for("login"))
            obj, owner_field = loader(**kwargs)
            if obj is None:
                abort(404)
            if getattr(obj, owner_field) != current_user.id:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def chunked(items: Iterable, size: int):
    """Делит итерируемое на куски заданного размера."""
    chunk = []
    for item in items:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def paginate(query, page: int, per_page: int):
    """Простая ручная пагинация SQLAlchemy-запроса.

    Возвращает (items, total_pages, page).
    """
    page = max(1, page)
    per_page = max(1, per_page)
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total_pages, page
