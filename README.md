# RemindersTasks

Telegram-бот для персональных напоминаний и dashboard задач.

## Стек

- Python 3.11+
- aiogram 3
- SQLAlchemy 2 async
- PostgreSQL + asyncpg
- Alembic
- Pydantic v2
- Docker Compose

## Быстрый старт через Docker

```powershell
Copy-Item .env.example .env
```

Заполните `BOT_TOKEN` в `.env`, затем запустите сервисы:

```powershell
docker compose up -d --build
```

Compose поднимает:

- `postgres` - PostgreSQL 16;
- `bot` - Telegram-бот, который перед стартом выполняет `alembic upgrade head`.

Посмотреть логи бота:

```powershell
docker compose logs -f bot
```

Остановить проект:

```powershell
docker compose down
```

Остановить проект и удалить данные PostgreSQL:

```powershell
docker compose down -v
```

## Локальный запуск без контейнера бота

Этот вариант нужен только для разработки.

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e .
docker compose up -d postgres
alembic upgrade head
python -m app.main
```

Для локального запуска `DATABASE_URL` в `.env` может указывать на `localhost`.
В контейнере бота Compose переопределяет `DATABASE_URL` на хост `postgres`.

ТЗ и план реализации лежат в `docs/TECHNICAL_SPEC.md`.
