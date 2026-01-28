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

## CLI

```bash
python -m money_map --help
python -m money_map validate --data-dir data
python -m money_map recommend --profile profiles/demo_fast_start.yaml --top 5
python -m money_map export --profile profiles/demo_fast_start.yaml --out exports
```

## UI

```bash
python -m money_map ui --data-dir data --port 8501
```

Open the Streamlit URL printed in the terminal (usually http://localhost:8501).

## Local development checklist

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m money_map --help
python -m money_map ui
python -m money_map validate --data-dir data
pytest
```
