"""Модель комментария к поездке."""
import datetime

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Comment(SqlAlchemyBase, SerializerMixin):
    """Комментарий другого пользователя к публичной поездке."""

    __tablename__ = "comments"

    serialize_only = (
        "id", "trip_id", "author_id", "content", "created_at",
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
    author_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.utcnow,
    )

    trip: orm.Mapped["Trip"] = orm.relationship(  # noqa: F821
        "Trip", back_populates="comments",
    )
    author: orm.Mapped["User"] = orm.relationship(  # noqa: F821
        "User", back_populates="comments",
    )

    def is_deletable_by(self, user) -> bool:
        """Удалить комментарий может автор или владелец поездки."""
        if user is None or not user.is_authenticated:
            return False
        return user.id == self.author_id or user.id == self.trip.owner_id

    def __repr__(self) -> str:
        return f"<Comment id={self.id} trip_id={self.trip_id}>"
