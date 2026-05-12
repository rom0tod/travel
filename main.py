"""Точка входа приложения TripPlanner.

Здесь собирается Flask-приложение: регистрируются веб-роуты,
ресурсы REST API, обработчики ошибок и фильтры шаблонов.

Запуск:
    python main.py
"""
import datetime
import os
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_restful import Api
from sqlalchemy import or_

from api.expenses_api import ExpenseListResource, ExpenseResource
from api.places_api import PlaceListResource, PlaceResource
from api.trips_api import TripListResource, TripResource
from api.users_api import UserListResource, UserResource
from config import Config, DB_DIR, UPLOAD_DIR
from data import db_session
from data.comments import Comment
from data.expenses import Expense
from data.likes import Like
from data.places import PLACE_KINDS, Place
from data.tags import Tag
from data.trips import Trip
from data.users import User
from forms.auth import LoginForm, RegisterForm
from forms.comment import CommentForm
from forms.expense import EXPENSE_LABELS, ExpenseForm
from forms.place import KIND_LABELS, PlaceForm
from forms.profile import ProfileForm
from forms.search import SearchForm
from forms.trip import TripForm
from tools.geocoder import GeocodingError, geocode
from tools.helpers import paginate, remove_static_file, save_uploaded_image


def create_app(config_object: type = Config) -> Flask:
    """Фабрика Flask-приложения."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    DB_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    db_session.global_init(app.config["DATABASE_URL"])
    _maybe_auto_seed()

    _configure_login(app)
    _register_template_helpers(app)
    _register_routes(app)
    _register_api(app)
    _register_error_handlers(app)

    return app


def _maybe_auto_seed() -> None:
    """Заполняет пустую БД демо-данными, если включён флаг окружения.

    Удобно для бесплатных хостингов вроде Render, где нет Shell-доступа
    для ручного запуска ``python -m tools.seed``. Срабатывает только
    при ``TRIPPLANNER_AUTO_SEED=1`` и только когда таблица пользователей
    пуста — повторных вставок не будет.
    """
    if os.environ.get("TRIPPLANNER_AUTO_SEED", "").strip() != "1":
        return
    session = db_session.create_session()
    try:
        if session.query(User).count() > 0:
            return
    finally:
        session.close()

    from tools.seed import seed
    try:
        seed()
    except Exception as exc:  # noqa: BLE001
        # На старте не валим приложение — лучше пустая БД, чем 500.
        print(f"[auto-seed] не удалось заполнить БД: {exc}")


# ---------------------------------------------------------------------------
# Аутентификация
# ---------------------------------------------------------------------------

def _configure_login(app: Flask) -> None:
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Войдите, чтобы продолжить."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str):
        session = db_session.create_session()
        try:
            return session.query(User).get(int(user_id))
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Шаблонные фильтры и контекст
# ---------------------------------------------------------------------------

def _register_template_helpers(app: Flask) -> None:
    @app.template_filter("ru_date")
    def ru_date(value):
        """Дата в формате 12 июня 2026."""
        if value is None:
            return ""
        months = (
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря",
        )
        return f"{value.day} {months[value.month - 1]} {value.year}"

    @app.template_filter("ru_datetime")
    def ru_datetime(value):
        if value is None:
            return ""
        return value.strftime("%d.%m.%Y %H:%M")

    @app.template_filter("expense_label")
    def expense_label(value: str) -> str:
        return EXPENSE_LABELS.get(value, value)

    @app.template_filter("kind_label")
    def kind_label(value: str) -> str:
        return KIND_LABELS.get(value, value)

    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.date.today().year,
            "place_kinds": PLACE_KINDS,
            "expense_categories": Config.EXPENSE_CATEGORIES,
        }


# ---------------------------------------------------------------------------
# Веб-роуты
# ---------------------------------------------------------------------------

def _register_routes(app: Flask) -> None:

    @app.route("/")
    def index():
        session = db_session.create_session()
        try:
            featured = (
                session.query(Trip)
                .filter(Trip.is_public.is_(True))
                .order_by(Trip.created_at.desc())
                .limit(6)
                .all()
            )
            stats = {
                "users": session.query(User).count(),
                "trips": session.query(Trip).count(),
                "places": session.query(Place).count(),
            }
            return render_template(
                "index.html",
                featured=featured,
                stats=stats,
            )
        finally:
            session.close()

    @app.route("/register", methods=("GET", "POST"))
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("my_trips"))

        form = RegisterForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            try:
                username = form.username.data.strip()
                email = form.email.data.strip().lower()

                exists = (
                    session.query(User)
                    .filter(or_(User.username == username, User.email == email))
                    .first()
                )
                if exists is not None:
                    flash("Пользователь с таким логином или почтой уже есть.",
                          "danger")
                    return render_template("auth/register.html", form=form)

                user = User(username=username, email=email)
                user.set_password(form.password.data)
                session.add(user)
                session.commit()
                login_user(user)
                flash("Добро пожаловать в TripPlanner!", "success")
                return redirect(url_for("my_trips"))
            finally:
                session.close()
        return render_template("auth/register.html", form=form)

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("my_trips"))

        form = LoginForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            try:
                login_value = form.login.data.strip()
                user = (
                    session.query(User)
                    .filter(or_(
                        User.username == login_value,
                        User.email == login_value.lower(),
                    ))
                    .first()
                )
                if user is None or not user.check_password(form.password.data):
                    flash("Неверный логин или пароль.", "danger")
                    return render_template("auth/login.html", form=form)

                login_user(user, remember=form.remember.data)
                flash(f"Привет, {user.username}!", "success")
                return redirect(url_for("my_trips"))
            finally:
                session.close()
        return render_template("auth/login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Вы вышли из аккаунта.", "info")
        return redirect(url_for("index"))

    # ----- Профиль -----

    @app.route("/users/<int:user_id>")
    def user_profile(user_id: int):
        session = db_session.create_session()
        try:
            user = session.query(User).get(user_id)
            if user is None:
                abort(404)
            visible_trips = [
                trip for trip in user.trips
                if trip.is_visible_to(current_user)
            ]
            visible_trips.sort(key=lambda t: t.created_at, reverse=True)
            return render_template(
                "users/profile.html",
                profile_user=user,
                trips=visible_trips,
            )
        finally:
            session.close()

    @app.route("/profile/edit", methods=("GET", "POST"))
    @login_required
    def edit_profile():
        form = ProfileForm()
        session = db_session.create_session()
        try:
            user = session.query(User).get(current_user.id)
            if request.method == "GET":
                form.about.data = user.about

            if form.validate_on_submit():
                user.about = (form.about.data or "").strip()
                if form.avatar.data:
                    new_path = save_uploaded_image(form.avatar.data, "avatars")
                    if new_path:
                        remove_static_file(user.avatar)
                        user.avatar = new_path
                session.commit()
                flash("Профиль обновлён.", "success")
                return redirect(url_for("user_profile", user_id=user.id))
            return render_template("users/edit_profile.html",
                                   form=form, user=user)
        finally:
            session.close()

    # ----- Поездки -----

    @app.route("/my/trips")
    @login_required
    def my_trips():
        session = db_session.create_session()
        try:
            trips = (
                session.query(Trip)
                .filter(Trip.owner_id == current_user.id)
                .order_by(Trip.start_date.desc())
                .all()
            )
            return render_template("trips/my_list.html", trips=trips)
        finally:
            session.close()

    @app.route("/trips/new", methods=("GET", "POST"))
    @login_required
    def create_trip():
        form = TripForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            try:
                trip = Trip(
                    title=form.title.data.strip(),
                    destination=form.destination.data.strip(),
                    description=(form.description.data or "").strip(),
                    start_date=form.start_date.data,
                    end_date=form.end_date.data,
                    budget=form.budget.data or 0.0,
                    is_public=form.is_public.data,
                    owner_id=current_user.id,
                )
                if form.cover_image.data:
                    path = save_uploaded_image(form.cover_image.data, "covers")
                    if path:
                        trip.cover_image = path
                _apply_tags(session, trip, form.tags.data)
                session.add(trip)
                session.commit()
                flash("Поездка создана!", "success")
                return redirect(url_for("trip_detail", trip_id=trip.id))
            finally:
                session.close()
        return render_template("trips/edit.html", form=form,
                               trip=None, is_new=True)

    @app.route("/trips/<int:trip_id>")
    def trip_detail(trip_id: int):
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                abort(404)
            if not trip.is_visible_to(current_user):
                abort(403)

            days_with_places = _group_places_by_day(trip)
            comment_form = CommentForm()
            user_liked = False
            if current_user.is_authenticated:
                user_liked = bool(
                    session.query(Like)
                    .filter(Like.user_id == current_user.id,
                            Like.trip_id == trip.id)
                    .first()
                )
            return render_template(
                "trips/detail.html",
                trip=trip,
                days_with_places=days_with_places,
                comment_form=comment_form,
                user_liked=user_liked,
            )
        finally:
            session.close()

    @app.route("/trips/<int:trip_id>/edit", methods=("GET", "POST"))
    @login_required
    def edit_trip(trip_id: int):
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                abort(404)
            if not trip.is_editable_by(current_user):
                abort(403)

            form = TripForm(obj=trip)
            if request.method == "GET":
                form.tags.data = ", ".join(tag.name for tag in trip.tags)

            if form.validate_on_submit():
                trip.title = form.title.data.strip()
                trip.destination = form.destination.data.strip()
                trip.description = (form.description.data or "").strip()
                trip.start_date = form.start_date.data
                trip.end_date = form.end_date.data
                trip.budget = form.budget.data or 0.0
                trip.is_public = form.is_public.data
                if form.cover_image.data:
                    path = save_uploaded_image(form.cover_image.data, "covers")
                    if path:
                        remove_static_file(trip.cover_image)
                        trip.cover_image = path
                _apply_tags(session, trip, form.tags.data)
                session.commit()
                flash("Изменения сохранены.", "success")
                return redirect(url_for("trip_detail", trip_id=trip.id))
            return render_template("trips/edit.html", form=form,
                                   trip=trip, is_new=False)
        finally:
            session.close()

    @app.route("/trips/<int:trip_id>/delete", methods=("POST",))
    @login_required
    def delete_trip(trip_id: int):
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                abort(404)
            if not trip.is_editable_by(current_user):
                abort(403)
            remove_static_file(trip.cover_image)
            session.delete(trip)
            session.commit()
            flash("Поездка удалена.", "info")
            return redirect(url_for("my_trips"))
        finally:
            session.close()

    # ----- Точки маршрута -----

    @app.route("/trips/<int:trip_id>/places/new", methods=("GET", "POST"))
    @login_required
    def add_place(trip_id: int):
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                abort(404)
            if not trip.is_editable_by(current_user):
                abort(403)

            form = PlaceForm()
            if form.validate_on_submit():
                day = min(form.day.data, max(trip.duration_days, 1))
                place = Place(
                    trip_id=trip.id,
                    name=form.name.data.strip(),
                    kind=form.kind.data,
                    address=(form.address.data or "").strip(),
                    notes=(form.notes.data or "").strip(),
                    day=day,
                    latitude=form.latitude.data,
                    longitude=form.longitude.data,
                    order_index=len(
                        [p for p in trip.places if p.day == day]
                    ),
                )
                session.add(place)
                session.commit()
                flash("Точка добавлена.", "success")
                return redirect(url_for("trip_detail", trip_id=trip.id))
            return render_template("places/edit.html", form=form,
                                   trip=trip, place=None)
        finally:
            session.close()

    @app.route("/trips/<int:trip_id>/places/<int:place_id>/edit",
               methods=("GET", "POST"))
    @login_required
    def edit_place(trip_id: int, place_id: int):
        session = db_session.create_session()
        try:
            place = session.query(Place).get(place_id)
            if place is None or place.trip_id != trip_id:
                abort(404)
            if not place.trip.is_editable_by(current_user):
                abort(403)

            form = PlaceForm(obj=place)
            if form.validate_on_submit():
                place.name = form.name.data.strip()
                place.kind = form.kind.data
                place.address = (form.address.data or "").strip()
                place.notes = (form.notes.data or "").strip()
                place.day = form.day.data
                place.latitude = form.latitude.data
                place.longitude = form.longitude.data
                session.commit()
                flash("Точка обновлена.", "success")
                return redirect(url_for("trip_detail", trip_id=trip_id))
            return render_template("places/edit.html", form=form,
                                   trip=place.trip, place=place)
        finally:
            session.close()

    @app.route("/trips/<int:trip_id>/places/<int:place_id>/delete",
               methods=("POST",))
    @login_required
    def delete_place(trip_id: int, place_id: int):
        session = db_session.create_session()
        try:
            place = session.query(Place).get(place_id)
            if place is None or place.trip_id != trip_id:
                abort(404)
            if not place.trip.is_editable_by(current_user):
                abort(403)
            session.delete(place)
            session.commit()
            flash("Точка удалена.", "info")
            return redirect(url_for("trip_detail", trip_id=trip_id))
        finally:
            session.close()

    # ----- Расходы -----

    @app.route("/trips/<int:trip_id>/expenses", methods=("GET", "POST"))
    @login_required
    def manage_expenses(trip_id: int):
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                abort(404)
            if not trip.is_editable_by(current_user):
                abort(403)

            form = ExpenseForm()
            if form.validate_on_submit():
                expense = Expense(
                    trip_id=trip.id,
                    category=form.category.data,
                    amount=round(form.amount.data, 2),
                    currency=(form.currency.data or "RUB").upper()[:8],
                    note=(form.note.data or "").strip(),
                    spent_at=form.spent_at.data,
                )
                session.add(expense)
                session.commit()
                flash("Расход добавлен.", "success")
                return redirect(url_for("manage_expenses", trip_id=trip.id))

            by_category = _summarize_expenses(trip)
            return render_template(
                "expenses/manage.html",
                trip=trip,
                form=form,
                by_category=by_category,
            )
        finally:
            session.close()

    @app.route("/trips/<int:trip_id>/expenses/<int:expense_id>/delete",
               methods=("POST",))
    @login_required
    def delete_expense(trip_id: int, expense_id: int):
        session = db_session.create_session()
        try:
            expense = session.query(Expense).get(expense_id)
            if expense is None or expense.trip_id != trip_id:
                abort(404)
            if not expense.trip.is_editable_by(current_user):
                abort(403)
            session.delete(expense)
            session.commit()
            flash("Расход удалён.", "info")
            return redirect(url_for("manage_expenses", trip_id=trip_id))
        finally:
            session.close()

    # ----- Социалка -----

    @app.route("/trips/<int:trip_id>/comments", methods=("POST",))
    @login_required
    def add_comment(trip_id: int):
        form = CommentForm()
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                abort(404)
            if not trip.is_visible_to(current_user):
                abort(403)
            if form.validate_on_submit():
                comment = Comment(
                    trip_id=trip.id,
                    author_id=current_user.id,
                    content=form.content.data.strip(),
                )
                session.add(comment)
                session.commit()
                flash("Комментарий добавлен.", "success")
            else:
                flash("Не удалось отправить комментарий.", "danger")
            return redirect(url_for("trip_detail", trip_id=trip_id))
        finally:
            session.close()

    @app.route("/trips/<int:trip_id>/comments/<int:comment_id>/delete",
               methods=("POST",))
    @login_required
    def delete_comment(trip_id: int, comment_id: int):
        session = db_session.create_session()
        try:
            comment = session.query(Comment).get(comment_id)
            if comment is None or comment.trip_id != trip_id:
                abort(404)
            if not comment.is_deletable_by(current_user):
                abort(403)
            session.delete(comment)
            session.commit()
            flash("Комментарий удалён.", "info")
            return redirect(url_for("trip_detail", trip_id=trip_id))
        finally:
            session.close()

    @app.route("/trips/<int:trip_id>/like", methods=("POST",))
    @login_required
    def toggle_like(trip_id: int):
        """AJAX-ручка: переключает лайк, отдаёт JSON со счётчиком."""
        session = db_session.create_session()
        try:
            trip = session.query(Trip).get(trip_id)
            if trip is None:
                return jsonify({"success": False,
                                "error": "Поездка не найдена."}), 404
            if not trip.is_public and trip.owner_id != current_user.id:
                return jsonify({"success": False,
                                "error": "Поездка приватная."}), 403

            existing = (
                session.query(Like)
                .filter(Like.user_id == current_user.id,
                        Like.trip_id == trip.id)
                .first()
            )
            if existing is None:
                session.add(Like(user_id=current_user.id, trip_id=trip.id))
                liked = True
            else:
                session.delete(existing)
                liked = False
            session.commit()
            return jsonify({
                "success": True,
                "liked": liked,
                "likes_count": trip.likes_count,
            })
        finally:
            session.close()

    # ----- Explore -----

    @app.route("/explore")
    def explore():
        form = SearchForm(request.args, meta={"csrf": False})
        page = max(1, request.args.get("page", 1, type=int))

        session = db_session.create_session()
        try:
            query = (
                session.query(Trip)
                .filter(Trip.is_public.is_(True))
                .order_by(Trip.created_at.desc())
            )
            search_value = (form.query.data or "").strip()
            if search_value:
                pattern = f"%{search_value}%"
                query = query.filter(or_(
                    Trip.title.ilike(pattern),
                    Trip.destination.ilike(pattern),
                    Trip.description.ilike(pattern),
                ))
            tag_value = (form.tag.data or "").strip()
            if tag_value:
                _, slug = Tag.normalize(tag_value)
                query = query.join(Trip.tags).filter(Tag.slug == slug)

            trips, total_pages, page = paginate(
                query, page, Config.ITEMS_PER_PAGE,
            )
            popular_tags = (
                session.query(Tag)
                .join(Tag.trips)
                .group_by(Tag.id)
                .order_by(Tag.name)
                .limit(15)
                .all()
            )
            return render_template(
                "trips/explore.html",
                trips=trips,
                form=form,
                page=page,
                total_pages=total_pages,
                popular_tags=popular_tags,
            )
        finally:
            session.close()

    # ----- Геокодер (AJAX) -----

    @app.route("/api/geocode")
    def api_geocode():
        address = request.args.get("address", "").strip()
        if not address:
            return jsonify({"success": False,
                            "error": "Параметр address обязателен."}), 400
        try:
            result = geocode(address)
        except GeocodingError as exc:
            return jsonify({"success": False, "error": str(exc)}), 502
        if result is None:
            return jsonify({"success": False,
                            "error": "Адрес не найден."}), 404
        return jsonify({"success": True, **result})


# ---------------------------------------------------------------------------
# Внутренние помощники
# ---------------------------------------------------------------------------

def _apply_tags(session, trip: Trip, raw: str) -> None:
    """Перепривязывает теги поездки из строки вида ``горы, осень``."""
    trip.tags.clear()
    if not raw:
        return
    seen_slugs = set()
    for chunk in raw.split(","):
        name, slug = Tag.normalize(chunk)
        if not slug or slug in seen_slugs:
            continue
        tag = session.query(Tag).filter(Tag.slug == slug).first()
        if tag is None:
            tag = Tag(name=name, slug=slug)
            session.add(tag)
            session.flush()
        trip.tags.append(tag)
        seen_slugs.add(slug)


def _group_places_by_day(trip: Trip) -> list:
    """Возвращает список (день, [точки]) для шаблона расписания."""
    grouped: dict[int, list] = {}
    for place in trip.places:
        grouped.setdefault(place.day, []).append(place)
    total_days = max(trip.duration_days, max(grouped.keys(), default=0))
    return [
        (day, sorted(grouped.get(day, []), key=lambda p: p.order_index))
        for day in range(1, max(total_days, 1) + 1)
    ]


def _summarize_expenses(trip: Trip) -> dict:
    """Подсчитывает суммы расходов по категориям."""
    totals = {category: 0.0 for category in Config.EXPENSE_CATEGORIES}
    for expense in trip.expenses:
        totals[expense.category] = totals.get(expense.category, 0.0) + \
            expense.amount
    return {key: round(value, 2) for key, value in totals.items() if value > 0}


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

def _register_api(app: Flask) -> None:
    api = Api(app)
    api.add_resource(TripListResource, "/api/trips")
    api.add_resource(TripResource, "/api/trips/<int:trip_id>")
    api.add_resource(PlaceListResource,
                     "/api/trips/<int:trip_id>/places")
    api.add_resource(PlaceResource,
                     "/api/trips/<int:trip_id>/places/<int:place_id>")
    api.add_resource(ExpenseListResource,
                     "/api/trips/<int:trip_id>/expenses")
    api.add_resource(ExpenseResource,
                     "/api/trips/<int:trip_id>/expenses/<int:expense_id>")
    api.add_resource(UserListResource, "/api/users")
    api.add_resource(UserResource, "/api/users/<int:user_id>")


# ---------------------------------------------------------------------------
# Ошибки
# ---------------------------------------------------------------------------

def _register_error_handlers(app: Flask) -> None:

    @app.errorhandler(403)
    def forbidden(_exc):
        return render_template(
            "errors/error.html",
            code=403,
            title="Доступ запрещён",
            message="У вас нет прав для просмотра этой страницы.",
        ), 403

    @app.errorhandler(404)
    def not_found(_exc):
        return render_template(
            "errors/error.html",
            code=404,
            title="Страница не найдена",
            message="Возможно, ссылка устарела или адрес введён с ошибкой.",
        ), 404

    @app.errorhandler(413)
    def too_large(_exc):
        return render_template(
            "errors/error.html",
            code=413,
            title="Файл слишком большой",
            message="Максимальный размер загружаемого файла — 8 МБ.",
        ), 413

    @app.errorhandler(500)
    def internal_error(_exc):
        return render_template(
            "errors/error.html",
            code=500,
            title="Что-то пошло не так",
            message="Мы уже занимаемся проблемой. Попробуйте позже.",
        ), 500


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=True)
