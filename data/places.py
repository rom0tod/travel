"""Модель точки маршрута.

Точка — это конкретное место (достопримечательность, отель, кафе),
привязанное к одному из дней поездки. Хранит координаты для отрисовки
на карте Leaflet.
"""
from typing import Optional

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


PLACE_KINDS = (
    "sight",
    "hotel",
    "food",
    "transport",
    "activity",
    "other",
)


class Place(SqlAlchemyBase, SerializerMixin):
    """Точка интереса внутри поездки."""

    __tablename__ = "places"

    serialize_only = (
        "id", "trip_id", "name", "address", "notes", "kind",
        "latitude", "longitude", "day", "order_index",
    )

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True,
    )
    trip_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("trips.id"),
        nullable=False,
        index=True,
    )

    name = sqlalchemy.Column(sqlalchemy.String(120), nullable=False)
    address = sqlalchemy.Column(sqlalchemy.String(255), default="")
    notes = sqlalchemy.Column(sqlalchemy.Text, default="")
    kind = sqlalchemy.Column(sqlalchemy.String(20), default="sight")

    latitude = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    longitude = sqlalchemy.Column(sqlalchemy.Float, nullable=True)

    day = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    order_index = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    trip: orm.Mapped["Trip"] = orm.relationship(  # noqa: F821
        "Trip", back_populates="places",
    )

    @property
    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def coordinates(self) -> Optional[tuple]:
        """Возвращает кортеж (lat, lng) или None, если координат нет."""
        if not self.has_coordinates:
            return None
        return (self.latitude, self.longitude)

    @staticmethod
    def is_valid_kind(value: str) -> bool:
        return value in PLACE_KINDS

    def __repr__(self) -> str:
        return f"<Place id={self.id} name={self.name!r} day={self.day}>"
