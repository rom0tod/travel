"""Форма добавления расхода."""
import datetime

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    FloatField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from config import Config


EXPENSE_LABELS = {
    "transport": "Транспорт",
    "accommodation": "Жильё",
    "food": "Еда",
    "activities": "Развлечения",
    "souvenirs": "Сувениры",
    "other": "Другое",
}


class ExpenseForm(FlaskForm):
    """Добавление и редактирование расхода по поездке."""

    category = SelectField(
        "Категория",
        choices=[
            (value, EXPENSE_LABELS.get(value, value))
            for value in Config.EXPENSE_CATEGORIES
        ],
    )
    amount = FloatField(
        "Сумма",
        validators=[
            DataRequired(message="Укажите сумму."),
            NumberRange(min=0.01, message="Сумма должна быть положительной."),
        ],
    )
    currency = StringField(
        "Валюта",
        default="RUB",
        validators=[Optional(), Length(min=1, max=8)],
    )
    note = StringField(
        "Комментарий",
        validators=[Optional(), Length(max=255)],
    )
    spent_at = DateField(
        "Дата",
        default=datetime.date.today,
        validators=[DataRequired()],
    )
    submit = SubmitField("Добавить")
