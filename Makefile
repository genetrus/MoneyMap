.PHONY: dev fmt format format-check lint test gates e2e

dev:
	./scripts/dev.sh

fmt:
	ruff format .

format: fmt

format-check:
	ruff format --check .

lint:
	ruff check .

test:
	pytest -q

gates: format-check lint test

e2e:
	MONEY_MAP_DISABLE_NETWORK=1 python -m money_map.app.cli validate --data-dir data
	MONEY_MAP_DISABLE_NETWORK=1 python -m pytest -q tests/test_e2e_api_flow.py tests/test_e2e_cli_flow.py
