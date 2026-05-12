"""Управление подключением к базе данных и фабрика сессий SQLAlchemy.

Используется паттерн, рекомендованный курсом: глобальная инициализация
один раз при старте приложения, после чего любой модуль может получить
новую сессию через ``create_session``.
"""
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.orm import DeclarativeBase, Session


class SqlAlchemyBase(DeclarativeBase):
    """Базовый класс для всех декларативных моделей."""


__factory: orm.sessionmaker | None = None


def global_init(db_url: str) -> None:
    """Инициализирует подключение к базе и создаёт таблицы.

    Повторный вызов с уже инициализированной фабрикой игнорируется,
    чтобы случайно не пересоздать sessionmaker.
    """
    global __factory

    if __factory is not None:
        return

    if not db_url or not db_url.strip():
        raise ValueError("Не задан адрес базы данных.")

    engine = sqlalchemy.create_engine(db_url, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    # Импорт нужен здесь, чтобы все модели зарегистрировались
    # в metadata до вызова create_all.
    from . import __all_models  # noqa: F401

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    """Возвращает новую сессию работы с БД."""
    if __factory is None:
        raise RuntimeError(
            "База данных не инициализирована. Вызовите global_init() при старте."
        )
    return __factory()
