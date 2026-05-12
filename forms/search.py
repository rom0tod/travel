"""Форма поиска по публичным поездкам."""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Optional


class SearchForm(FlaskForm):
    """Поисковая строка для explore-страницы."""

    class Meta:
        csrf = False  # поиск идёт GET-запросом

    query = StringField(
        "Поиск",
        validators=[Optional(), Length(max=120)],
    )
    tag = StringField(
        "Тег",
        validators=[Optional(), Length(max=40)],
    )
    submit = SubmitField("Найти")
