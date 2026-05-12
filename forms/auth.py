"""Формы регистрации и входа."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
)


USERNAME_PATTERN = r"^[A-Za-z0-9_.-]+$"


class RegisterForm(FlaskForm):
    """Регистрация нового пользователя."""

    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(message="Укажите имя пользователя."),
            Length(min=3, max=40,
                   message="Имя должно содержать от 3 до 40 символов."),
            Regexp(USERNAME_PATTERN,
                   message="Допустимы латиница, цифры, '.', '_' и '-'."),
        ],
    )
    email = StringField(
        "Электронная почта",
        validators=[
            DataRequired(message="Укажите почту."),
            Email(message="Некорректный адрес электронной почты."),
            Length(max=120),
        ],
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Введите пароль."),
            Length(min=6, max=128,
                   message="Пароль должен быть от 6 до 128 символов."),
        ],
    )
    password_repeat = PasswordField(
        "Повторите пароль",
        validators=[
            DataRequired(message="Повторите пароль."),
            EqualTo("password", message="Пароли должны совпадать."),
        ],
    )
    submit = SubmitField("Создать аккаунт")


class LoginForm(FlaskForm):
    """Вход существующего пользователя."""

    login = StringField(
        "Имя пользователя или email",
        validators=[DataRequired(), Length(max=120)],
    )
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")
