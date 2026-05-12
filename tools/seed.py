"""Заполнение базы демонстрационными данными.

Запускается командой ``python -m tools.seed`` из корня проекта.
"""
import datetime
import sys
from pathlib import Path

# Подключаем корень проекта к sys.path, чтобы импорты работали
# при запуске модулем (python -m tools.seed).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config, DB_DIR  # noqa: E402
from data import db_session  # noqa: E402
from data.comments import Comment  # noqa: E402
from data.expenses import Expense  # noqa: E402
from data.likes import Like  # noqa: E402
from data.places import Place  # noqa: E402
from data.tags import Tag  # noqa: E402
from data.trips import Trip  # noqa: E402
from data.users import User  # noqa: E402


DEMO_USERS = [
    {
        "username": "demo",
        "email": "demo@example.com",
        "password": "demo123",
        "about": "Демо-пользователь для проверки функциональности.",
    },
    {
        "username": "anna",
        "email": "anna@example.com",
        "password": "annaanna",
        "about": "Люблю горы и медленные путешествия.",
    },
    {
        "username": "ivan",
        "email": "ivan@example.com",
        "password": "ivanivan",
        "about": "Гастротурист со стажем.",
    },
]


DEMO_TAGS = [
    "горы", "море", "город", "гастрономия", "осень", "роуд-трип",
]


DEMO_TRIPS = [
    {
        "owner": "anna",
        "title": "Кавказ за неделю",
        "destination": "Северный Кавказ, Россия",
        "description": "Эльбрус, Чегемское ущелье и водопады Софии.",
        "start_date": datetime.date(2026, 6, 12),
        "end_date": datetime.date(2026, 6, 18),
        "budget": 65000.0,
        "is_public": True,
        "tags": ["горы", "роуд-трип"],
        "places": [
            ("Эльбрус, поляна Азау", "sight", 1,
             43.2667, 42.4667,
             "Канатка работает с 9:00, очередь утром меньше."),
            ("Чегемские водопады", "sight", 3,
             43.2050, 43.2725,
             "Лучше ехать рано, после обеда туристов очень много."),
            ("Гостиница в Терсколе", "hotel", 1,
             43.2588, 42.5119, ""),
        ],
        "expenses": [
            ("transport", 18000, "RUB", "Билеты на самолёт",
             datetime.date(2026, 6, 12)),
            ("accommodation", 21000, "RUB", "Отель 6 ночей",
             datetime.date(2026, 6, 13)),
            ("food", 9500, "RUB", "Кафе и магазины",
             datetime.date(2026, 6, 14)),
        ],
    },
    {
        "owner": "ivan",
        "title": "Гастротур по Тбилиси",
        "destination": "Тбилиси, Грузия",
        "description": "Пять дней — пять кухонь, десять ресторанов.",
        "start_date": datetime.date(2026, 9, 4),
        "end_date": datetime.date(2026, 9, 9),
        "budget": 45000.0,
        "is_public": True,
        "tags": ["город", "гастрономия", "осень"],
        "places": [
            ("Старый город Тбилиси", "sight", 1,
             41.6900, 44.8100, "Прогулка по Шардени и Абанотубани."),
            ("Винный бар «8000 виноделов»", "food", 2,
             41.6925, 44.8071, "Дегустация квеври."),
            ("Хинкали в «Велиаминов»", "food", 3,
             41.7126, 44.7894, ""),
            ("Гостиница рядом с пл. Свободы", "hotel", 1,
             41.6968, 44.8014, ""),
        ],
        "expenses": [
            ("transport", 22000, "RUB", "Билеты туда-обратно",
             datetime.date(2026, 9, 4)),
            ("food", 12000, "RUB", "Рестораны",
             datetime.date(2026, 9, 5)),
            ("accommodation", 8000, "RUB", "Отель",
             datetime.date(2026, 9, 4)),
        ],
    },
    {
        "owner": "demo",
        "title": "Выходные в Санкт-Петербурге",
        "destination": "Санкт-Петербург, Россия",
        "description": "Музеи, набережные и неспешные кофейни.",
        "start_date": datetime.date(2026, 5, 23),
        "end_date": datetime.date(2026, 5, 25),
        "budget": 20000.0,
        "is_public": True,
        "tags": ["город"],
        "places": [
            ("Эрмитаж", "sight", 1, 59.9398, 30.3146, "Билеты онлайн."),
            ("Новая Голландия", "activity", 2,
             59.9281, 30.2917, "Бесплатный вход, хорошая еда."),
        ],
        "expenses": [
            ("transport", 4000, "RUB", "Сапсан",
             datetime.date(2026, 5, 23)),
            ("food", 3500, "RUB", "Кафе",
             datetime.date(2026, 5, 24)),
        ],
    },
]


def _ensure_directories() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)


def _create_users(session) -> dict:
    """Создаёт демо-пользователей, возвращает map username → user."""
    users = {}
    for spec in DEMO_USERS:
        user = (
            session.query(User)
            .filter(User.username == spec["username"])
            .first()
        )
        if user is None:
            user = User(
                username=spec["username"],
                email=spec["email"],
                about=spec["about"],
            )
            user.set_password(spec["password"])
            session.add(user)
        users[spec["username"]] = user
    session.commit()
    return users


def _create_tags(session) -> dict:
    tags = {}
    for raw_name in DEMO_TAGS:
        name, slug = Tag.normalize(raw_name)
        tag = session.query(Tag).filter(Tag.slug == slug).first()
        if tag is None:
            tag = Tag(name=name, slug=slug)
            session.add(tag)
        tags[slug] = tag
    session.commit()
    return tags


def _create_trips(session, users: dict, tags: dict) -> None:
    for spec in DEMO_TRIPS:
        owner = users[spec["owner"]]
        existing = (
            session.query(Trip)
            .filter(Trip.title == spec["title"], Trip.owner_id == owner.id)
            .first()
        )
        if existing is not None:
            continue

        trip = Trip(
            title=spec["title"],
            destination=spec["destination"],
            description=spec["description"],
            start_date=spec["start_date"],
            end_date=spec["end_date"],
            budget=spec["budget"],
            is_public=spec["is_public"],
            owner_id=owner.id,
        )
        for raw in spec.get("tags", []):
            _, slug = Tag.normalize(raw)
            tag = tags.get(slug)
            if tag is not None:
                trip.tags.append(tag)

        for index, place_spec in enumerate(spec.get("places", [])):
            name, kind, day, lat, lng, notes = place_spec
            trip.places.append(Place(
                name=name, kind=kind, day=day,
                latitude=lat, longitude=lng, notes=notes,
                order_index=index,
            ))

        for category, amount, currency, note, spent_at in spec.get("expenses", []):
            trip.expenses.append(Expense(
                category=category, amount=amount,
                currency=currency, note=note, spent_at=spent_at,
            ))

        session.add(trip)
    session.commit()


def _create_social_signals(session, users: dict) -> None:
    """Несколько лайков и комментариев для оживления explore-страницы."""
    demo = users.get("demo")
    anna = users.get("anna")
    ivan = users.get("ivan")
    if not demo or not anna or not ivan:
        return

    trips = session.query(Trip).all()
    for trip in trips:
        for fan in (demo, anna, ivan):
            if fan.id == trip.owner_id:
                continue
            already = (
                session.query(Like)
                .filter(Like.user_id == fan.id, Like.trip_id == trip.id)
                .first()
            )
            if already is None:
                session.add(Like(user_id=fan.id, trip_id=trip.id))

    sample_comments = [
        (demo, "Очень полезный маршрут, забираю в закладки!"),
        (anna, "Согласна, Чегем стоит каждой минуты в дороге."),
    ]
    target = (
        session.query(Trip)
        .filter(Trip.title == "Гастротур по Тбилиси")
        .first()
    )
    if target is not None:
        for author, content in sample_comments:
            already = (
                session.query(Comment)
                .filter(
                    Comment.trip_id == target.id,
                    Comment.author_id == author.id,
                    Comment.content == content,
                )
                .first()
            )
            if already is None:
                session.add(Comment(
                    trip_id=target.id,
                    author_id=author.id,
                    content=content,
                ))
    session.commit()


def seed() -> None:
    _ensure_directories()
    db_session.global_init(Config.DATABASE_URL)
    session = db_session.create_session()
    try:
        users = _create_users(session)
        tags = _create_tags(session)
        _create_trips(session, users, tags)
        _create_social_signals(session, users)
    finally:
        session.close()
    print("База заполнена демонстрационными данными.")
    print("Демо-логин: demo / demo123")


if __name__ == "__main__":
    seed()
