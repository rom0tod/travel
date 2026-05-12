"""Формы создания и редактирования поездки."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    FloatField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)


class TripForm(FlaskForm):
    """Создание и редактирование поездки."""

    title = StringField(
        "Название поездки",
        validators=[
            DataRequired(message="Дайте поездке название."),
            Length(min=3, max=120),
        ],
    )
    destination = StringField(
        "Куда едем",
        validators=[
            DataRequired(message="Укажите основной пункт назначения."),
            Length(min=2, max=120),
        ],
    )
    description = TextAreaField(
        "Описание",
        validators=[Optional(), Length(max=2000)],
    )

    start_date = DateField(
        "Дата начала",
        validators=[DataRequired(message="Укажите дату начала.")],
    )
    end_date = DateField(
        "Дата окончания",
        validators=[DataRequired(message="Укажите дату окончания.")],
    )

    budget = FloatField(
        "Бюджет",
        default=0.0,
        validators=[
            Optional(),
            NumberRange(min=0, message="Бюджет не может быть отрицательным."),
        ],
    )

    tags = StringField(
        "Теги (через запятую)",
        validators=[Optional(), Length(max=200)],
        description="Например: горы, активный отдых, осень",
    )

    is_public = BooleanField("Сделать поездку публичной")

    cover_image = FileField(
        "Обложка",
        validators=[
            Optional(),
            FileAllowed(
                {"png", "jpg", "jpeg", "gif", "webp"},
                "Поддерживаются только изображения.",
            ),
        ],
    )

    submit = SubmitField("Сохранить")

    def validate_end_date(self, field):
        """Дата окончания не должна предшествовать дате начала."""
        if self.start_date.data and field.data:
            if field.data < self.start_date.data:
                raise ValidationError(
                    "Дата окончания не может быть раньше даты начала."
                )
