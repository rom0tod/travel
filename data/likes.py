"""Модель лайков пользовательских поездок."""
import datetime

import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Like(SqlAlchemyBase):
    """Связь «пользователь поставил лайк поездке»."""

    __tablename__ = "likes"
    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            "user_id", "trip_id", name="uq_like_user_trip",
        ),
    )

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True,
    )
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("users.id"),
        nullable=False, index=True,
    )
    trip_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("trips.id"),
        nullable=False, index=True,
    )
    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.utcnow,
    )

    user: orm.Mapped["User"] = orm.relationship(  # noqa: F821
        "User", back_populates="likes",
    )
    trip: orm.Mapped["Trip"] = orm.relationship(  # noqa: F821
        "Trip", back_populates="likes",
    )
