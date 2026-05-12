"""REST API для поездок.

Эндпоинты:
    GET    /api/trips                  — список публичных поездок
    POST   /api/trips                  — создание поездки (только владелец)
    GET    /api/trips/<id>             — детальная информация
    PUT    /api/trips/<id>             — обновление полей
    DELETE /api/trips/<id>             — удаление поездки
"""
import datetime

from flask import request
from flask_login import current_user
from flask_restful import Resource

from data import db_session
from data.trips import Trip

from .common import abort_with, check_required_fields, forbidden, not_found, ok


REQUIRED_CREATE_FIELDS = (
    "title", "destination", "start_date", "end_date",
)
UPDATABLE_FIELDS = (
    "title", "destination", "description",
    "start_date", "end_date", "budget", "is_public",
)


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


class TripListResource(Resource):
    """Список публичных поездок и создание новых."""

    def get(self):
        """Возвращает публичные поездки с простой пагинацией."""
        try:
            limit = int(request.args.get("limit", 20))
            offset = int(request.args.get("offset", 0))
        except ValueError:
            return abort_with(400, "limit и offset должны быть числами.")

        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        session = db_session.create_session()
        try:
            query = (
                session.query(Trip)
                .filter(Trip.is_public.is_(True))
                .order_by(Trip.created_at.desc())
            )
            total = query.count()
            trips = query.offset(offset).limit(limit).all()
            return ok({
                "total": total,
                "limit": limit,
                "offset": offset,
                "trips": [trip.to_dict() for trip in trips],
            })
        finally:
            session.close()

    def post(self):
        """Создание поездки. Доступно только аутентифицированному пользователю."""
        if not current_user.is_authenticated:
            return forbidden()

        data = request.get_json(silent=True)
        error = check_required_fields(data, REQUIRED_CREATE_FIELDS)
        if error:
            return error

        start_date = _parse_date(data.get("start_date"))
        end_date = _parse_date(data.get("end_date"))
        if not start_date or not end_date:
            return abort_with(400, "Даты должны быть в формате YYYY-MM-DD.")
        if end_date < start_date:
            return abort_with(400, "Дата окончания раньше даты начала.")

        session = db_session.create_session()
        try:
            trip = Trip(
                title=data["title"].strip(),
                destination=data["destination"].strip(),
                description=data.get("description", "").strip(),
                start_date=start_date,
                end_date=end_date,
                budget=float(data.get("budget", 0) or 0),
                is_public=bool(data.get("is_public", False)),
                owner_id=current_user.id,
            )
            session.add(trip)
            session.commit()
            return ok({"trip": trip.to_dict()}, status=201)
        finally:
            session.close()


class TripResource(Resource):
    """Чтение, обновление и удаление одной поездки."""

    def get(self, trip_id: int):
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                return not_found("Поездка")
            if not trip.is_visible_to(current_user):
                return forbidden()
            data = trip.to_dict()
            data["places"] = [place.to_dict() for place in trip.places]
            data["expenses"] = [exp.to_dict() for exp in trip.expenses]
            return ok({"trip": data})
        finally:
            session.close()

    def put(self, trip_id: int):
        if not current_user.is_authenticated:
            return forbidden()

        data = request.get_json(silent=True) or {}

        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                return not_found("Поездка")
            if not trip.is_editable_by(current_user):
                return forbidden()

            for field in UPDATABLE_FIELDS:
                if field not in data:
                    continue
                value = data[field]
                if field in ("start_date", "end_date"):
                    parsed = _parse_date(value)
                    if parsed is None:
                        return abort_with(
                            400, f"Поле {field} должно быть в формате YYYY-MM-DD."
                        )
                    setattr(trip, field, parsed)
                elif field == "budget":
                    try:
                        setattr(trip, field, float(value or 0))
                    except (TypeError, ValueError):
                        return abort_with(400, "Бюджет должен быть числом.")
                elif field == "is_public":
                    setattr(trip, field, bool(value))
                else:
                    setattr(trip, field, str(value).strip())

            if trip.end_date < trip.start_date:
                return abort_with(400, "Дата окончания раньше даты начала.")

            session.commit()
            return ok({"trip": trip.to_dict()})
        finally:
            session.close()

    def delete(self, trip_id: int):
        if not current_user.is_authenticated:
            return forbidden()

        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                return not_found("Поездка")
            if not trip.is_editable_by(current_user):
                return forbidden()

            session.delete(trip)
            session.commit()
            return ok({"deleted_id": trip_id})
        finally:
            session.close()
