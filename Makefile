include .env
export


SHELL := /bin/bash
PYTHON_SOURCES = gh_automation_base/ stubs/
DSN := postgresql+psycopg://${GH_AUTO_PG_USER}:${GH_AUTO_PG_PASSWORD}@${GH_AUTO_PG_AIVEN_SERVICE}-${GH_AUTO_PG_AIVEN_PROJECT}.aivencloud.com:${GH_AUTO_PG_PORT}/${GH_AUTO_PG_DATABASE}?sslmode=require


install:
	poetry install

format-check:
	poetry run black --check $(PYTHON_SOURCES)
	poetry run ruff check $(PYTHON_SOURCES)
	poetry run mypy $(PYTHON_SOURCES)

format:
	poetry run black $(PYTHON_SOURCES)
	poetry run ruff check $(PYTHON_SOURCES) --fix
	poetry run mypy $(PYTHON_SOURCES)

migration-init:
	poetry run auto init
	poetry run yoyo init migrations

migration-new:
	poetry run yoyo new --sql --config yoyo.ini --batch

migration-apply:
	poetry run yoyo apply --config yoyo.ini --database $(DSN)

migration-list:
	poetry run yoyo list --config yoyo.ini --database $(DSN)
