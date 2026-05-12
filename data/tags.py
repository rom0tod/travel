"""Модель тегов поездок.

Теги позволяют группировать поездки по типу отдыха (горы, море, городской
туризм и т.д.) и используются в поиске по explore-странице.
"""
from typing import List

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase
from .trips import trip_tags_table


class Tag(SqlAlchemyBase, SerializerMixin):
    """Произвольный тег, который можно повесить на поездку."""

    __tablename__ = "tags"

    serialize_only = ("id", "name", "slug")

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True,
    )
    name = sqlalchemy.Column(sqlalchemy.String(40), unique=True, nullable=False)
    slug = sqlalchemy.Column(sqlalchemy.String(40), unique=True, nullable=False)

    trips: orm.Mapped[List["Trip"]] = orm.relationship(  # noqa: F821
        "Trip", secondary=trip_tags_table, back_populates="tags",
    )

    @staticmethod
    def normalize(raw_name: str) -> tuple:
        """Возвращает корректную пару (name, slug) для нового тега."""
        cleaned = (raw_name or "").strip().lower()
        slug = "".join(
            ch if ch.isalnum() else "-"
            for ch in cleaned
        ).strip("-")
        return cleaned, slug

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"
