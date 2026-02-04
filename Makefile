.PHONY: dev fmt format fmt-check format-check lint lint-fix test gates e2e mvp

dev:
	./scripts/dev.sh

fmt:
	python -m ruff format .

format: fmt

fmt-check: format-check

format-check:
	python -m ruff format --check .

lint:
	python -m ruff check .

lint-fix:
	python -m ruff check --fix .

test:
	pytest -q

gates: format-check lint test

e2e:
	MONEY_MAP_DISABLE_NETWORK=1 python -m money_map.app.cli validate --data-dir data
	MONEY_MAP_DISABLE_NETWORK=1 python -m pytest -q tests/test_e2e_api_flow.py tests/test_e2e_cli_flow.py

mvp:
	./scripts/mvp.sh
