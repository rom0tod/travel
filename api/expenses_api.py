"""REST API для расходов поездки."""
import datetime

from flask import request
from flask_login import current_user
from flask_restful import Resource

from config import Config
from data import db_session
from data.expenses import Expense
from data.trips import Trip

from .common import abort_with, check_required_fields, forbidden, not_found, ok


REQUIRED_FIELDS = ("category", "amount")


def _parse_date(value):
    if not value:
        return datetime.date.today()
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


class ExpenseListResource(Resource):
    """Список расходов и добавление новых."""

    def get(self, trip_id: int):
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                return not_found("Поездка")
            if not trip.is_visible_to(current_user):
                return forbidden()
            return ok({
                "expenses": [exp.to_dict() for exp in trip.expenses],
                "total": trip.total_spent,
                "budget": trip.budget,
                "remaining": trip.budget_remaining,
            })
        finally:
            session.close()

    def post(self, trip_id: int):
        if not current_user.is_authenticated:
            return forbidden()

        data = request.get_json(silent=True)
        error = check_required_fields(data, REQUIRED_FIELDS)
        if error:
            return error

        if data["category"] not in Config.EXPENSE_CATEGORIES:
            return abort_with(400, "Неизвестная категория расхода.")

        try:
            amount = float(data["amount"])
        except (TypeError, ValueError):
            return abort_with(400, "Сумма должна быть числом.")
        if amount <= 0:
            return abort_with(400, "Сумма должна быть положительной.")

        spent_at = _parse_date(data.get("spent_at"))
        if spent_at is None:
            return abort_with(400, "Дата должна быть в формате YYYY-MM-DD.")

        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                return not_found("Поездка")
            if not trip.is_editable_by(current_user):
                return forbidden()

            expense = Expense(
                trip_id=trip.id,
                category=data["category"],
                amount=round(amount, 2),
                currency=data.get("currency", "RUB").upper()[:8],
                note=data.get("note", "").strip(),
                spent_at=spent_at,
            )
            session.add(expense)
            session.commit()
            return ok({"expense": expense.to_dict()}, status=201)
        finally:
            session.close()


class ExpenseResource(Resource):
    """Удаление одного расхода."""

    def delete(self, trip_id: int, expense_id: int):
        if not current_user.is_authenticated:
            return forbidden()

        session = db_session.create_session()
        try:
            expense = session.query(Expense).get(expense_id)
            if expense is None or expense.trip_id != trip_id:
                return not_found("Расход")
            if not expense.trip.is_editable_by(current_user):
                return forbidden()
            session.delete(expense)
            session.commit()
            return ok({"deleted_id": expense_id})
        finally:
            session.close()
