# QuestionsAnswersService


Небольшой сервис вопросов и ответов на FastAPI с асинхронным SQLAlchemy 2.0, PostgreSQL, миграциями (Alembic), тестами (pytest) и запуском в Docker Compose.
- CRUD для вопросов и ответов 
- Валидация входных данных через Pydantic v2 (обрезка пробелов, запрет пустых строк)
- Каскадное удаление ответов при удалении вопроса 
- Асинхронный стек: FastAPI + SQLAlchemy Async + asyncpg 
- Автотесты на ключевую бизнес-логику

## Запуск
1. Подготовить .env (пример в .env.example)
```
# .env
DB_HOST=
DB_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

DATABASE_URL=
```

2. Собрать и запустить контейнеры:
```
make up
```
3. Опционально. Для просмотра всех команд напишите:
```
make help
```

## Примеры запросов:

Это все можно увидеть в http://localhost:8000/docs, после запуска сервиса. Для наглядности запросы/параметры/ответы перечислены и тут:

### GET /questions/ — список всех вопросов (новые сверху)
ответ (200):
```json
[
  { "id": 2, "text": "Почему небо голубое?", "created_at": "2025-08-21T12:00:00Z" },
  { "id": 1, "text": "Как работает API?", "created_at": "2025-08-20T12:00:00Z" }
]
```

### POST /questions/ — создать вопрос
тело:
```json
{ "text": "   Почему небо голубое?   " }
```
ответ (201):
```json
{
	"id": 1,
	"text": "Почему небо голубое?",
	"created_at": "2025-08-31T12:52:30.724469"
}
```

### GET /questions/{id} — получить вопрос со всеми ответами
ответ (200):
```json
{
  "id": 3,
  "text": "Почему небо голубое?",
  "created_at": "2025-08-31T12:00:00Z",
  "answers": [
    {
      "id": 10,
      "question_id": 3,
      "user_id": "f5c4b0c6-5a3d-4b8b-9f9a-1f1f6d39f111",
      "text": "Из-за рассеяния Рэлея",
      "created_at": "2025-08-31T12:05:00Z"
    }
  ]
}
```
Если вопрос не найден → 404 
```json
{"detail":"question_not_found"}
```

### DELETE questions/{id} — удалить вопрос
ответ (204).  
Если вопрос не найден → 404:
```json
{"detail":"question_not_found"}
```

### POST /questions/{id}/answers/ — добавить ответ к вопросу
Тело:
```json
{ "user_id": "a2bd70b6-3f73-49a9-8cbb-3d9d5b9a3be2", "text": "  Мой вариант ответа  " }

```
ответ (201):
```json
{
  "id": 11,
  "question_id": 3,
  "user_id": "a2bd70b6-3f73-49a9-8cbb-3d9d5b9a3be2",
  "text": "Мой вариант ответа",
  "created_at": "2025-08-31T12:06:00Z"
}
```
Если вопрос не найден → 404 
```json
{"detail":"answer_not_found"}
```

### GET /answers/{id} — получить конкретный ответ
ответ (200):
```json
{
  "id": 11,
  "question_id": 3,
  "user_id": "a2bd70b6-3f73-49a9-8cbb-3d9d5b9a3be2",
  "text": "Мой вариант ответа",
  "created_at": "2025-08-31T12:06:00Z"
}

```
Если вопрос не найден → 404 
```json
{"detail":"answer_not_found"}
```

### DELETE /answers/{id} — удалить ответ
ответ (204).  
Если вопрос не найден → 404:
```json
{"detail":"answer_not_found"}
```

# Некоторые замечания по реализации

- Можно было бы выделить Repository для работы с бд, но проект довольно маленький, чтобы "размазывать логику".