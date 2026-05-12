"""REST API для пользователей (только чтение публичных данных)."""
from flask_restful import Resource

from data import db_session
from data.users import User

from .common import not_found, ok


class UserListResource(Resource):
    """Каталог зарегистрированных пользователей."""

    def get(self):
        session = db_session.create_session()
        try:
            users = session.query(User).order_by(User.username).all()
            return ok({"users": [user.to_dict() for user in users]})
        finally:
            session.close()


class UserResource(Resource):
    """Профиль одного пользователя + его публичные поездки."""

    def get(self, user_id: int):
        session = db_session.create_session()
        try:
            user = session.query(User).get(user_id)
            if user is None:
                return not_found("Пользователь")
            payload = user.to_dict()
            payload["public_trips"] = [
                trip.to_dict() for trip in user.public_trips()
            ]
            return ok({"user": payload})
        finally:
            session.close()
