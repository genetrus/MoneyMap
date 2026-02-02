.PHONY: dev fmt format format-check lint test gates

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
