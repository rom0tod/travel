"""Форма добавления и редактирования точки маршрута."""
from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional,
)

from data.places import PLACE_KINDS


KIND_LABELS = {
    "sight": "Достопримечательность",
    "hotel": "Жильё",
    "food": "Еда",
    "transport": "Транспорт",
    "activity": "Активность",
    "other": "Другое",
}


class PlaceForm(FlaskForm):
    """Создание и редактирование точки маршрута."""

    name = StringField(
        "Название",
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    kind = SelectField(
        "Тип",
        choices=[(value, KIND_LABELS[value]) for value in PLACE_KINDS],
        default="sight",
    )
    address = StringField(
        "Адрес (для автопоиска координат)",
        validators=[Optional(), Length(max=255)],
    )
    latitude = FloatField(
        "Широта",
        validators=[
            Optional(),
            NumberRange(min=-90, max=90, message="Широта от -90 до 90."),
        ],
    )
    longitude = FloatField(
        "Долгота",
        validators=[
            Optional(),
            NumberRange(min=-180, max=180, message="Долгота от -180 до 180."),
        ],
    )
    day = IntegerField(
        "День поездки",
        default=1,
        validators=[
            DataRequired(),
            NumberRange(min=1, max=365, message="День должен быть от 1 до 365."),
        ],
    )
    notes = TextAreaField(
        "Заметки",
        validators=[Optional(), Length(max=1000)],
    )
    submit = SubmitField("Сохранить точку")
