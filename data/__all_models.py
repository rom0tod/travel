"""Импорт всех моделей для регистрации в metadata SQLAlchemy.

Без этого модуля create_all не увидит модели, которые ни разу
не были импортированы до вызова инициализации.
"""
from . import users  # noqa: F401
from . import trips  # noqa: F401
from . import places  # noqa: F401
from . import expenses  # noqa: F401
from . import comments  # noqa: F401
from . import likes  # noqa: F401
from . import tags  # noqa: F401
