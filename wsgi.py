"""WSGI-точка входа для продакшен-серверов (gunicorn, uwsgi).

Локально продолжаем запускать через ``python main.py``, а на хостинге
сервер запускается командой вида:

    gunicorn wsgi:app --bind 0.0.0.0:$PORT
"""
from main import create_app


app = create_app()
