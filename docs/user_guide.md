# Money Map User Guide

Money Map is an offline-first toolkit for exploring income path variants, running deterministic recommendations, and exporting stable artifacts. This guide walks through setup, validation, recommendations, and export workflows.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Core workflows

### Validate data

```bash
python -m money_map validate --data-dir data
python -m money_map validate --data-dir data --strict
```

### Run recommendations

```bash
python -m money_map recommend --profile profiles/demo_fast_start.yaml --top 5 --lang en
```

### Export artifacts

```bash
python -m money_map export --profile profiles/demo_fast_start.yaml --out exports --lang en
python -m money_map export --profile profiles/demo_fast_start.yaml --out exports --lang en --today 2026-01-01
```

The `--today` flag pins time-based outputs for deterministic snapshots.

### Objective presets

List and inspect objective presets:

```bash
python -m money_map preset list --lang en
python -m money_map preset show fast_start --lang en
```

### Doctor checks

```bash
python -m money_map doctor --data-dir data --lang en
```

The doctor command validates dependencies, data integrity, i18n coverage, and runs a quick recommendation pass.

## Streamlit UI

```bash
python -m money_map ui --data-dir data --port 8501
```

Open the Streamlit URL (usually http://localhost:8501) and explore:

- **Profile**: edit user profile fields and select an objective preset.
- **Recommendations**: generate ranked variants with localized scores.
- **Plan**: view the 4-week plan and compliance checklist.
- **Export**: download `plan.md`, `result.json`, `profile.yaml`, and `checklist.md`.
- **Data Editor**: safely edit YAML files with validation, diffs, backups, and normalized formatting.

## Data Editor workflow

1. Open the **Data Editor** page.
2. Select a YAML file under `data/` or `profiles/`.
3. Use **Validate draft** to check the edited YAML.
4. Use **Show diff** to review changes.
5. Use **Save** for safe, atomic writes (backup is created automatically).
6. Use **Normalize YAML** to apply deterministic formatting.

## Safety notes

- Money Map is offline-only and does not make network calls.
- All YAML parsing uses safe loaders.
- Export outputs are deterministic and stable for snapshot tests.
