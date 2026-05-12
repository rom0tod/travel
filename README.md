# TripPlanner

Социальный планировщик путешествий: карта маршрута, расписание по дням,
учёт бюджета, теги, лайки и комментарии, REST API и интеграция с
OpenStreetMap для геокодирования адресов.

Итоговый проект курса **«Основы промышленного программирования»**
Яндекс Лицея (модуль *WebServer + API*).

---

## Содержание

- [Стек технологий](#стек-технологий)
- [Возможности](#возможности)
- [Структура проекта](#структура-проекта)
- [Запуск](#запуск)
- [Демо-данные](#демо-данные)
- [REST API](#rest-api)
- [Безопасность](#безопасность)
- [Архитектурные решения](#архитектурные-решения)

---

## Стек технологий

| Слой | Что используем |
| --- | --- |
| Веб-фреймворк | Flask 2.3+ |
| ORM | SQLAlchemy 2.0 + sqlalchemy-serializer |
| Аутентификация | Flask-Login (хэш паролей — werkzeug.security) |
| Формы | Flask-WTF + WTForms + email-validator |
| REST API | Flask-RESTful |
| Шаблоны | Jinja2 (наследование, фильтры, контекст-процессор) |
| Внешние сервисы | Nominatim (OpenStreetMap) через `requests` |
| База | SQLite (файл `db/tripplanner.sqlite`) |
| Фронт | Bootstrap 5.3, Bootstrap Icons, Leaflet 1.9 |
| Загрузка файлов | werkzeug.utils.secure_filename + Pillow |

---

## Возможности

### Пользователи
- регистрация и вход с защитой пароля хэшированием;
- «запомнить меня» (Flask-Login remember cookie);
- профиль с аватаром и описанием;
- публичная страница профиля.

### Поездки
- создание / редактирование / удаление поездки;
- обложка (изображение), теги, описание;
- режимы «приватная» и «публичная»;
- автоматический подсчёт длительности.

### Маршрут
- интерактивная карта на Leaflet с маркерами и линиями по дням;
- цветовая раскраска маркеров по дню;
- разбиение точек по дням (accordion);
- разные типы точек: достопримечательность, жильё, еда,
  транспорт, активность, прочее;
- выбор координат кликом по карте или через автогеокодирование
  адреса (POST `/api/geocode` → Nominatim).

### Бюджет
- учёт расходов с категориями и валютой;
- сводка по категориям;
- индикатор перерасхода.

### Социалка
- лайки публичных поездок (AJAX без перезагрузки);
- комментарии (автор или владелец могут удалить);
- explore-страница с поиском, фильтром по тегам и пагинацией.

### REST API
- ресурсы Flask-RESTful для поездок, точек, расходов, пользователей;
- единый формат ответа `{"success": true, ...}`;
- единые обработчики ошибок (400/403/404/500) в JSON.

### Производственные мелочи
- кастомные страницы ошибок 403/404/413/500;
- ограничение на размер загружаемых файлов (8 МБ);
- защита от CSRF на всех POST-формах (Flask-WTF);
- CSRF выключен только для GET-формы поиска.

---

## Структура проекта

```
tripplanner/
├── main.py                  # Точка входа, фабрика приложения
├── config.py                # Конфигурация (пути, лимиты, секреты)
├── requirements.txt
├── README.md
│
├── data/                    # Слой данных
│   ├── db_session.py        # Сессии SQLAlchemy
│   ├── __all_models.py      # Регистрация моделей
│   ├── users.py
│   ├── trips.py             # + ассоциативная таблица trip_tags
│   ├── places.py
│   ├── expenses.py
│   ├── comments.py
│   ├── likes.py
│   └── tags.py
│
├── forms/                   # WTForms-формы
│   ├── auth.py              # LoginForm, RegisterForm
│   ├── profile.py
│   ├── trip.py
│   ├── place.py
│   ├── expense.py
│   ├── comment.py
│   └── search.py
│
├── api/                     # REST API (Flask-RESTful)
│   ├── common.py
│   ├── trips_api.py
│   ├── places_api.py
│   ├── expenses_api.py
│   └── users_api.py
│
├── tools/                   # Вспомогательные модули
│   ├── geocoder.py          # Запросы к Nominatim
│   ├── helpers.py           # Декораторы, загрузка файлов, пагинация
│   └── seed.py              # Демонстрационные данные
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── trips/               # list, edit, detail, explore, _card
│   ├── places/edit.html
│   ├── expenses/manage.html
│   ├── users/
│   └── errors/error.html
│
└── static/
    ├── css/style.css
    ├── js/main.js           # лайк (AJAX) и копирование ссылки
    ├── js/map.js            # Leaflet: карта поездки + выбор точки
    └── uploads/             # обложки и аватары (создаётся при загрузке)
```

---

## Запуск

### Требования
- Python 3.10+
- pip
- Доступ в интернет для CDN-ассетов (Bootstrap, Leaflet) и
  Nominatim (опционально, для автогеокодирования).

### Установка

```bash
git clone <repo>
cd tripplanner

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Заполнение демо-данными (необязательно)

```bash
python -m tools.seed
```

После сидинга появятся три пользователя и три поездки с точками,
расходами, тегами и комментариями.

### Запуск сервера

```bash
python main.py
```

По умолчанию приложение слушает `http://127.0.0.1:5000`.

При первом запуске автоматически создаётся файл
`db/tripplanner.sqlite` и папка `static/uploads/`.

---

## Демо-данные

После `python -m tools.seed` доступны:

| Логин | Пароль | Описание |
| --- | --- | --- |
| `demo` | `demo123` | Универсальный демо-пользователь |
| `anna` | `annaanna` | «Кавказ за неделю» |
| `ivan` | `ivanivan` | «Гастротур по Тбилиси» |

---

## REST API

Все ответы в формате JSON, базовый префикс — `/api`.

| Метод | URL | Действие |
| --- | --- | --- |
| GET | `/api/trips` | Список публичных поездок (`?limit=`, `?offset=`) |
| POST | `/api/trips` | Создание поездки (нужна сессия) |
| GET | `/api/trips/<id>` | Полные данные поездки + точки и расходы |
| PUT | `/api/trips/<id>` | Обновление (только владелец) |
| DELETE | `/api/trips/<id>` | Удаление (только владелец) |
| GET | `/api/trips/<id>/places` | Точки маршрута |
| POST | `/api/trips/<id>/places` | Добавить точку |
| GET | `/api/trips/<id>/places/<pid>` | Конкретная точка |
| PUT | `/api/trips/<id>/places/<pid>` | Обновить точку |
| DELETE | `/api/trips/<id>/places/<pid>` | Удалить точку |
| GET | `/api/trips/<id>/expenses` | Расходы и сводка по бюджету |
| POST | `/api/trips/<id>/expenses` | Добавить расход |
| DELETE | `/api/trips/<id>/expenses/<eid>` | Удалить расход |
| GET | `/api/users` | Список пользователей |
| GET | `/api/users/<id>` | Профиль + публичные поездки |
| GET | `/api/geocode?address=...` | Прокси к Nominatim для координат |

Пример запроса:

```bash
curl -s http://127.0.0.1:5000/api/trips?limit=3 | python -m json.tool
```

Пример ответа:

```json
{
    "success": true,
    "total": 3,
    "limit": 3,
    "offset": 0,
    "trips": [
        {
            "id": 2,
            "title": "Гастротур по Тбилиси",
            "destination": "Тбилиси, Грузия",
            "start_date": "2026-09-04",
            "end_date": "2026-09-09",
            "duration_days": 6,
            "likes_count": 1,
            "places_count": 4,
            "is_public": true,
            "owner_id": 3
        }
    ]
}
```

Формат ошибки:

```json
{ "success": false, "error": "Поездка не найдена." }
```

---

## Безопасность

- пароли хранятся только в виде хэша (`generate_password_hash`);
- все POST-формы защищены CSRF-токеном (`flask_wtf.FlaskForm`);
- загрузка файлов проверяется по расширению и через
  `secure_filename`;
- доступ к чужим приватным поездкам блокируется проверками
  `Trip.is_visible_to` / `Trip.is_editable_by`, на уровне API —
  ответом `403 Forbidden`;
- для геокодера используется собственный User-Agent (требование
  Nominatim) и таймаут запроса.

---

## Архитектурные решения

- **Фабрика приложения** (`create_app`) изолирует регистрацию
  blueprints/api/обработчиков и удобна для тестирования.
- **Слой данных независим от Flask** — модели лежат в `data/`
  и не знают о request-контексте.
- **Сериализация моделей** через `sqlalchemy_serializer.SerializerMixin`
  — однородный формат `to_dict()` во всём API.
- **Helpers вынесены в `tools/`** — пагинация, загрузка файлов,
  декораторы доступа, геокодер. Никаких хелперов в `main.py`.
- **Шаблоны строятся через наследование** от `base.html`;
  карточка поездки вынесена в `trips/_card.html` и переиспользуется
  на главной, в «Моих поездках», в explore и в профиле.
- **Все строковые константы** (категории расходов, типы точек,
  лимиты) централизованы в `config.py` и `data/places.py`.

---

## Авторство

Учебный проект для Яндекс Лицея. Лицензия — MIT.
