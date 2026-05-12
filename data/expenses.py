"""Модель расходов по поездке."""
import datetime

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Expense(SqlAlchemyBase, SerializerMixin):
    """Запись о трате в рамках поездки."""

    __tablename__ = "expenses"

    serialize_only = (
        "id", "trip_id", "category", "amount", "currency",
        "note", "spent_at",
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

    category = sqlalchemy.Column(sqlalchemy.String(40), nullable=False)
    amount = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    currency = sqlalchemy.Column(sqlalchemy.String(8), default="RUB")
    note = sqlalchemy.Column(sqlalchemy.String(255), default="")
    spent_at = sqlalchemy.Column(
        sqlalchemy.Date, default=datetime.date.today,
    )

    trip: orm.Mapped["Trip"] = orm.relationship(  # noqa: F821
        "Trip", back_populates="expenses",
    )

    def __repr__(self) -> str:
        return (
            f"<Expense id={self.id} "
            f"category={self.category!r} amount={self.amount}>"
        )
