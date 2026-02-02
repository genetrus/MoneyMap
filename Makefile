.PHONY: dev format lint test gates

dev:
	./scripts/dev.sh

format:
	ruff format .

lint:
	ruff check .

test:
	pytest -q

gates: format lint test
