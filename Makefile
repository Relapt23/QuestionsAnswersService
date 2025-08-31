# ---- settings ----
COMPOSE      := docker compose
APP_SVC      := app
DB_SVC       := db
MIGRATE_SVC  := migrate

# читаем DATABASE_URL из .env (не обязательно, просто для echo/логов)
DATABASE_URL := $(shell awk -F= '/^DATABASE_URL=/{print $$2}' .env)

.PHONY: help up down f-down logs app-logs db-logs \
        rev rev-empty upgrade downgrade current heads history \
        psql shell

help: ## показать все цели
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------- базовые команды ----------
up: ## поднять БД, применить миграции и запустить приложение
	$(COMPOSE) up -d --build

down: ## остановить стек и удалить контейнеры
	$(COMPOSE) down

f-down: ## остановить стек и удалить контейнеры и почистить вольюмы
	$(COMPOSE) down -v

logs: ## общие логи
	$(COMPOSE) logs -f

app-logs: ## логи приложения
	$(COMPOSE) logs -f $(APP_SVC)

db-logs: ## логи БД
	$(COMPOSE) logs -f $(DB_SVC)

# ---------- миграции ----------
rev: ## создать новую миграцию (autogenerate). Использование: make rev m="add index"
	@test '$(m)' != '' || (echo 'Usage: make rev m="your message"'; exit 1)
	$(COMPOSE) up -d $(DB_SVC)
	$(COMPOSE) run --rm --no-deps $(APP_SVC) alembic revision --autogenerate -m "$(m)"

upgrade: ## применить все миграции до head
	$(COMPOSE) run --rm --no-deps $(APP_SVC) alembic upgrade head

downgrade: ## откатить на одну миграцию назад
	$(COMPOSE) run --rm --no-deps $(APP_SVC) alembic downgrade -1

current: ## показать текущую ревизию БД
	$(COMPOSE) run --rm --no-deps $(APP_SVC) alembic current

heads: ## показать head-ревизии в коде
	$(COMPOSE) run --rm --no-deps $(APP_SVC) alembic heads

history: ## история миграций
	$(COMPOSE) run --rm --no-deps $(APP_SVC) alembic history

# ---------- утилиты ----------
psql: ## psql в контейнере БД
	$(COMPOSE) exec $(DB_SVC) psql -U $$POSTGRES_USER -d $$POSTGRES_DB

shell: ## shell внутри контейнера app (одноразовый)
	$(COMPOSE) run --rm --no-deps $(APP_SVC) bash -l

print-db-url: ## показать DATABASE_URL, который увидит alembic
	@echo "$(DATABASE_URL)"
