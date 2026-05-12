"""Модель пользователя.

Хранит учётные данные путешественника. Хэш пароля считается через
``werkzeug.security`` — в открытом виде пароль в БД не попадает.
"""
import datetime
from typing import List

import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    """Учётная запись путешественника."""

    __tablename__ = "users"

    serialize_only = (
        "id", "username", "email", "about", "avatar",
        "created_at", "trips_count",
    )

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True,
    )
    username = sqlalchemy.Column(
        sqlalchemy.String(40), unique=True, nullable=False, index=True,
    )
    email = sqlalchemy.Column(
        sqlalchemy.String(120), unique=True, nullable=False, index=True,
    )
    password_hash = sqlalchemy.Column(
        sqlalchemy.String(255), nullable=False,
    )
    about = sqlalchemy.Column(sqlalchemy.Text, default="")
    avatar = sqlalchemy.Column(sqlalchemy.String(255), default="")
    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.utcnow,
    )

    trips: orm.Mapped[List["Trip"]] = orm.relationship(  # noqa: F821
        "Trip", back_populates="owner", cascade="all, delete-orphan",
    )
    comments: orm.Mapped[List["Comment"]] = orm.relationship(  # noqa: F821
        "Comment", back_populates="author", cascade="all, delete-orphan",
    )
    likes: orm.Mapped[List["Like"]] = orm.relationship(  # noqa: F821
        "Like", back_populates="user", cascade="all, delete-orphan",
    )

    def set_password(self, raw_password: str) -> None:
        """Сохраняет хэш переданного пароля."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Проверяет совпадение пароля с сохранённым хэшем."""
        return check_password_hash(self.password_hash, raw_password)

    @property
    def trips_count(self) -> int:
        """Количество поездок, созданных пользователем."""
        return len(self.trips)

    def public_trips(self) -> List["Trip"]:  # noqa: F821
        """Возвращает только публичные поездки пользователя."""
        return [trip for trip in self.trips if trip.is_public]

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
