.PHONY: dev venv install install-dev install-ui fmt format fmt-check format-check lint lint-fix test qa gates validate e2e mvp mvp-lite ui

PYTHON ?= python
VENV_DIR := .venv
ifeq ($(OS),Windows_NT)
VENV_PYTHON := $(VENV_DIR)/Scripts/python.exe
else
VENV_PYTHON := $(VENV_DIR)/bin/python
endif
PYTHON_BIN := $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(PYTHON))

dev:
	./scripts/dev.sh

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(PYTHON_BIN) -m pip install -e .

install-dev: venv
	$(PYTHON_BIN) -m pip install -e ".[dev]"

install-ui: venv
	$(PYTHON_BIN) -m pip install -e ".[ui]"

fmt:
	$(PYTHON_BIN) -m ruff format .

format: fmt

fmt-check: format-check

format-check:
	$(PYTHON_BIN) -m ruff format --check .

lint:
	$(PYTHON_BIN) -m ruff check .

lint-fix:
	$(PYTHON_BIN) -m ruff check --fix .

test:
	$(PYTHON_BIN) -m pytest -q

qa: format-check lint test

gates: format-check lint test

validate: install
	$(PYTHON_BIN) -m money_map.app.cli validate --data-dir data

e2e: install-dev
	MONEY_MAP_DISABLE_NETWORK=1 $(PYTHON_BIN) -m money_map.app.cli validate --data-dir data
	MONEY_MAP_DISABLE_NETWORK=1 $(PYTHON_BIN) -m pytest -q tests/test_e2e_api_flow.py tests/test_e2e_cli_flow.py

mvp:
	./scripts/mvp.sh

mvp-lite: install
	MM_UI_CHECK=optional $(PYTHON_BIN) scripts/mvp_check.py

ui:
	$(PYTHON_BIN) -m money_map.app.cli ui
