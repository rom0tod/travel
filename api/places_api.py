"""REST API для точек маршрута."""
from flask import request
from flask_login import current_user
from flask_restful import Resource

from data import db_session
from data.places import PLACE_KINDS, Place
from data.trips import Trip

from .common import abort_with, check_required_fields, forbidden, not_found, ok


REQUIRED_FIELDS = ("name", "day")


class PlaceListResource(Resource):
    """Список точек поездки и добавление новых."""

    def get(self, trip_id: int):
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                return not_found("Поездка")
            if not trip.is_visible_to(current_user):
                return forbidden()
            return ok({
                "places": [place.to_dict() for place in trip.places],
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

        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                return not_found("Поездка")
            if not trip.is_editable_by(current_user):
                return forbidden()

            kind = data.get("kind", "sight")
            if kind not in PLACE_KINDS:
                return abort_with(400, f"Неизвестный тип точки: {kind}.")

            try:
                day = int(data["day"])
            except (TypeError, ValueError):
                return abort_with(400, "Поле day должно быть целым числом.")
            if day < 1 or day > trip.duration_days:
                return abort_with(
                    400,
                    f"День должен быть от 1 до {trip.duration_days}.",
                )

            place = Place(
                trip_id=trip.id,
                name=data["name"].strip(),
                kind=kind,
                address=data.get("address", "").strip(),
                notes=data.get("notes", "").strip(),
                day=day,
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                order_index=len([p for p in trip.places if p.day == day]),
            )
            session.add(place)
            session.commit()
            return ok({"place": place.to_dict()}, status=201)
        finally:
            session.close()


class PlaceResource(Resource):
    """Чтение, обновление, удаление точки."""

    def get(self, trip_id: int, place_id: int):
        session = db_session.create_session()
        try:
            place = session.query(Place).get(place_id)
            if place is None or place.trip_id != trip_id:
                return not_found("Точка маршрута")
            if not place.trip.is_visible_to(current_user):
                return forbidden()
            return ok({"place": place.to_dict()})
        finally:
            session.close()

    def put(self, trip_id: int, place_id: int):
        if not current_user.is_authenticated:
            return forbidden()

        data = request.get_json(silent=True) or {}

        session = db_session.create_session()
        try:
            place = session.query(Place).get(place_id)
            if place is None or place.trip_id != trip_id:
                return not_found("Точка маршрута")
            if not place.trip.is_editable_by(current_user):
                return forbidden()

            for field in ("name", "address", "notes"):
                if field in data:
                    setattr(place, field, str(data[field]).strip())
            if "kind" in data:
                if data["kind"] not in PLACE_KINDS:
                    return abort_with(400, "Неизвестный тип точки.")
                place.kind = data["kind"]
            if "day" in data:
                try:
                    place.day = int(data["day"])
                except (TypeError, ValueError):
                    return abort_with(400, "Поле day должно быть числом.")
            for field in ("latitude", "longitude"):
                if field in data:
                    try:
                        setattr(place, field,
                                None if data[field] in (None, "")
                                else float(data[field]))
                    except (TypeError, ValueError):
                        return abort_with(400, f"{field} должно быть числом.")

            session.commit()
            return ok({"place": place.to_dict()})
        finally:
            session.close()

    def delete(self, trip_id: int, place_id: int):
        if not current_user.is_authenticated:
            return forbidden()

        session = db_session.create_session()
        try:
            place = session.query(Place).get(place_id)
            if place is None or place.trip_id != trip_id:
                return not_found("Точка маршрута")
            if not place.trip.is_editable_by(current_user):
                return forbidden()

            session.delete(place)
            session.commit()
            return ok({"deleted_id": place_id})
        finally:
            session.close()
