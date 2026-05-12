"""Модель поездки.

Поездка — центральная сущность приложения. Содержит метаданные,
ссылки на точки маршрута, расходы, комментарии, лайки и теги.
"""
import datetime
from typing import List

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


trip_tags_table = sqlalchemy.Table(
    "trip_tags",
    SqlAlchemyBase.metadata,
    sqlalchemy.Column(
        "trip_id", sqlalchemy.Integer,
        sqlalchemy.ForeignKey("trips.id"), primary_key=True,
    ),
    sqlalchemy.Column(
        "tag_id", sqlalchemy.Integer,
        sqlalchemy.ForeignKey("tags.id"), primary_key=True,
    ),
)


class Trip(SqlAlchemyBase, SerializerMixin):
    """Путешествие пользователя."""

    __tablename__ = "trips"

    serialize_only = (
        "id", "title", "destination", "description",
        "start_date", "end_date", "budget", "is_public",
        "cover_image", "owner_id", "created_at",
        "places_count", "likes_count", "duration_days",
    )

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True,
    )
    title = sqlalchemy.Column(sqlalchemy.String(120), nullable=False)
    destination = sqlalchemy.Column(sqlalchemy.String(120), nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text, default="")

    start_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    end_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    budget = sqlalchemy.Column(sqlalchemy.Float, default=0.0)

    is_public = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    cover_image = sqlalchemy.Column(sqlalchemy.String(255), default="")

    owner_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.utcnow,
    )

    owner: orm.Mapped["User"] = orm.relationship(  # noqa: F821
        "User", back_populates="trips",
    )
    places: orm.Mapped[List["Place"]] = orm.relationship(  # noqa: F821
        "Place", back_populates="trip",
        cascade="all, delete-orphan",
        order_by="Place.day, Place.order_index",
    )
    expenses: orm.Mapped[List["Expense"]] = orm.relationship(  # noqa: F821
        "Expense", back_populates="trip",
        cascade="all, delete-orphan",
        order_by="Expense.spent_at",
    )
    comments: orm.Mapped[List["Comment"]] = orm.relationship(  # noqa: F821
        "Comment", back_populates="trip",
        cascade="all, delete-orphan",
        order_by="Comment.created_at.desc()",
    )
    likes: orm.Mapped[List["Like"]] = orm.relationship(  # noqa: F821
        "Like", back_populates="trip",
        cascade="all, delete-orphan",
    )
    tags: orm.Mapped[List["Tag"]] = orm.relationship(  # noqa: F821
        "Tag", secondary=trip_tags_table, back_populates="trips",
    )

    @property
    def duration_days(self) -> int:
        """Длительность поездки в днях (включая первый день)."""
        if not self.start_date or not self.end_date:
            return 0
        return (self.end_date - self.start_date).days + 1

    @property
    def places_count(self) -> int:
        return len(self.places)

    @property
    def likes_count(self) -> int:
        return len(self.likes)

    @property
    def total_spent(self) -> float:
        """Сумма всех расходов по поездке."""
        return round(sum(expense.amount for expense in self.expenses), 2)

    @property
    def budget_remaining(self) -> float:
        """Сколько денег осталось от бюджета."""
        return round((self.budget or 0.0) - self.total_spent, 2)

    @property
    def is_over_budget(self) -> bool:
        return self.total_spent > (self.budget or 0.0) > 0

    def is_editable_by(self, user) -> bool:
        """Только владелец может редактировать поездку."""
        return user is not None and user.is_authenticated and \
               user.id == self.owner_id

    def is_visible_to(self, user) -> bool:
        """Публичные поездки видны всем, приватные — только владельцу."""
        if self.is_public:
            return True
        return self.is_editable_by(user)

    def __repr__(self) -> str:
        return f"<Trip id={self.id} title={self.title!r}>"
