"""Форма редактирования профиля."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Length, Optional


class ProfileForm(FlaskForm):
    """Изменение публичной информации о пользователе."""

    about = TextAreaField(
        "О себе",
        validators=[Optional(), Length(max=600)],
    )
    avatar = FileField(
        "Аватар",
        validators=[
            Optional(),
            FileAllowed(
                {"png", "jpg", "jpeg", "gif", "webp"},
                "Поддерживаются только изображения.",
            ),
        ],
    )
    submit = SubmitField("Сохранить")
