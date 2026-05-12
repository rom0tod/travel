# Деплой TripPlanner

Проект готов к публикации на двух популярных бесплатных хостингах.
Выберите тот, что удобнее.

---

## Вариант 1. Render.com (рекомендуется)

Render умеет читать `render.yaml` и развернуть веб-сервис +
PostgreSQL одной кнопкой.

1. Зарегистрируйтесь на [render.com](https://render.com) (можно
   через GitHub).
2. На дашборде нажмите **New → Blueprint**.
3. Подключите репозиторий `rom0tod/travel`.
4. Render увидит файл `render.yaml` и предложит создать:
   - веб-сервис `tripplanner`,
   - базу `tripplanner-db` (PostgreSQL, бесплатный план).
5. Подтвердите. Через 3–5 минут получите URL вида
   `https://tripplanner.onrender.com`.

Render автоматически:
- сгенерирует `TRIPPLANNER_SECRET`,
- пробросит `DATABASE_URL` в переменные окружения,
- выполнит `pip install -r requirements.txt`,
- запустит `gunicorn wsgi:app`.

### Заполнить демо-данными после деплоя

В Render Shell (вкладка **Shell** у сервиса) выполните:

```bash
python -m tools.seed
```

---

## Вариант 2. PythonAnywhere (классика Яндекс Лицея)

PythonAnywhere бесплатно даёт постоянную файловую систему,
поэтому подойдёт SQLite без переезда на PostgreSQL.

1. Зарегистрируйтесь на [pythonanywhere.com](https://www.pythonanywhere.com).
2. Откройте **Consoles → Bash** и склонируйте репозиторий:

   ```bash
   git clone https://github.com/rom0tod/travel.git tripplanner
   cd tripplanner
   ```
3. Создайте виртуальное окружение и поставьте зависимости:

   ```bash
   mkvirtualenv --python=python3.12 tripplanner
   pip install -r requirements.txt
   python -m tools.seed
   ```
4. Перейдите в **Web → Add a new web app**:
   - выберите **Manual configuration → Python 3.12**.
5. На вкладке Web настройте:
   - **Source code**: `/home/<username>/tripplanner`
   - **Virtualenv**: `/home/<username>/.virtualenvs/tripplanner`
   - **WSGI configuration file** — откройте и замените содержимое на:

     ```python
     import sys
     path = "/home/<username>/tripplanner"
     if path not in sys.path:
         sys.path.insert(0, path)

     from wsgi import app as application
     ```
   - В разделе **Static files** добавьте:
     `/static/` → `/home/<username>/tripplanner/static`
6. На вкладке **Files → tripplanner** убедитесь, что папка `db/`
   и `static/uploads/` существуют (они создаются автоматически).
7. На вкладке **Environment variables** задайте
   `TRIPPLANNER_SECRET` (длинная случайная строка).
8. Нажмите зелёную кнопку **Reload**. Сайт будет доступен по адресу
   `https://<username>.pythonanywhere.com`.

---

## Локально (через Docker, опционально)

Если хочется поднять контейнер локально:

```bash
docker run -p 5000:5000 \
    -e TRIPPLANNER_SECRET=local-secret \
    python:3.12 \
    bash -c "pip install -r /app/requirements.txt && \
             gunicorn --chdir /app wsgi:app --bind 0.0.0.0:5000"
```

---

## Чек-лист перед деплоем

- [ ] Установлен `TRIPPLANNER_SECRET` (не дефолтный)
- [ ] `DATABASE_URL` задан (для production-БД)
- [ ] Папки `db/` и `static/uploads/` доступны на запись
- [ ] Выполнен `python -m tools.seed` (если нужны демо-данные)
- [ ] В навигации видна правильная ссылка
- [ ] Геокодер (Nominatim) отвечает: дёрните `/api/geocode?address=Москва`
