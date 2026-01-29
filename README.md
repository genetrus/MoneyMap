# Money Map (M0 Walking Skeleton)

Money Map is an offline-first prototype for exploring income path variants, validating dataset integrity, and producing basic plans and exports. It ships as a Python package with a CLI and a Streamlit UI.

> Disclaimer: This project is **not legal advice** and provides **no income guarantees**.

## Requirements

- Python 3.11+

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Quickstart

```bash
python -m money_map doctor --data-dir data --lang en
python -m money_map recommend --profile profiles/demo_fast_start.yaml --top 5 --lang en
python -m money_map export --profile profiles/demo_fast_start.yaml --out exports --lang en --today 2026-01-01
```

## CLI

```bash
python -m money_map --help
python -m money_map validate --data-dir data
python -m money_map validate --data-dir data --strict
python -m money_map recommend --profile profiles/demo_fast_start.yaml --top 5
python -m money_map export --profile profiles/demo_fast_start.yaml --out exports
python -m money_map preset list --lang en
python -m money_map preset show fast_start --lang en
python -m money_map doctor --data-dir data --lang en
```

## UI

```bash
python -m money_map ui --data-dir data --port 8501
```

Open the Streamlit URL printed in the terminal (usually http://localhost:8501).

## Data setup (start here)

1. Edit `data/meta.yaml` to confirm `schema_version` and `reviewed_at`.
2. Update lookup files under `data/knowledge/` (skills, assets, constraints, objectives, risks).
3. Maintain core catalogs in `data/taxonomy.yaml`, `data/cells.yaml`, and `data/variants.yaml`.
4. Run strict validation after edits:

```bash
python -m money_map validate --data-dir data --strict
```

## Documentation

- [User Guide](docs/user_guide.md)
- [Data Workflow](docs/data_workflow.md)

## Local development checklist

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m money_map --help
python -m money_map ui
python -m money_map validate --data-dir data
python -m money_map validate --data-dir data --strict
python -m unittest discover -s tests -p "test_*.py" -v
```
