# Money Map Data Workflow

This guide covers how to update data catalogs, translations, and objective presets while keeping validation and exports deterministic.

## Add or update variants

1. Update `data/taxonomy.yaml` and `data/cells.yaml` if you need new taxonomy or cells.
2. Add or edit entries in `data/variants.yaml`.
3. Update `data/bridges.yaml` for directed relationships between variants.
4. Run validation:

```bash
python -m money_map validate --data-dir data --strict
```

## Update translations

1. Add any new translation keys in **all** language files under `src/money_map/i18n/`.
2. Run an i18n audit:

```bash
python -m money_map i18n audit --data-dir data --strict --strict-dataset
```

3. Optionally list unused keys:

```bash
python -m money_map i18n audit --data-dir data --report-unused
```

## Objective presets

Objective presets live in `data/presets.yaml`. Each preset defines scoring weights and optional overrides:

- `preset_id`: unique identifier used in profiles.
- `title_key` / `summary_key`: translation keys for UI/CLI.
- `weight_*`: deterministic scoring weights.
- `constraints_profile_overrides`: optional list that replaces profile constraints.
- `sorting_policy`: documented tie-breaker policy.

## Profiles

Profiles are YAML files under `profiles/`. The default demo profile is `profiles/demo_fast_start.yaml`. The `objective_preset` must reference a valid preset ID.

## Deterministic exports

To generate deterministic artifacts for testing or review:

```bash
python -m money_map export --profile profiles/demo_fast_start.yaml --out exports --lang en --today 2026-01-01
```

This pins time-dependent outputs and produces stable `plan.md`, `result.json`, `profile.yaml`, and `checklist.md` files.
