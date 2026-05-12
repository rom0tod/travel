"""Форма комментария к поездке."""
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class CommentForm(FlaskForm):
    """Оставить комментарий под публичной поездкой."""

    content = TextAreaField(
        "Ваш комментарий",
        validators=[
            DataRequired(message="Сообщение не может быть пустым."),
            Length(min=2, max=1000,
                   message="Комментарий должен быть от 2 до 1000 символов."),
        ],
    )
    submit = SubmitField("Отправить")
