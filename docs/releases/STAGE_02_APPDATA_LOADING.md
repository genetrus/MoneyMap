# Stage 2 — AppData loading foundation

## Scope
Stage 2 establishes deterministic, offline loading of the local dataset into a single in-memory `AppData` object before recommendation/plan/export flows.

## Implemented loading contract
- `load_app_data(data_dir)` resolves and loads the following sources from local disk:
  - `meta.yaml` or `meta.json`
  - `variants.yaml` or `variants.json`
  - `rulepacks/DE.yaml` or `rulepacks/DE.json`
- YAML parsing uses safe loading.
- JSON parsing is supported for the same structures.
- The loader returns unified `AppData(meta, rulepack, variants)`.

## Ready criteria (Stage 2)
- [ ] Loader reads MVP seed data from `data/` into `AppData`.
- [ ] Loader supports YAML/JSON mapping files for `meta`, `variants`, and DE rulepack.
- [ ] Missing required files fail fast with explicit `FileNotFoundError` message listing attempted paths.
- [ ] Result remains offline-first (local FS only, no network calls).

## Validation checks
1. Run loader against repository seed data (`data/`) and confirm `dataset_version`, `rulepack.reviewed_at`, and at least one variant are present.
2. Run loader against a temporary JSON-only dataset and confirm all three structures are populated.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.5–6 (MVP data boundaries and local data usage).
- `Money_Map_Spec_Packet.pdf` p.9–10 (core entities and data model: Meta/RulePack/Variant/AppData).
- `Money_Map_Spec_Packet.pdf` p.11 (offline-only constraint and safe loading posture).
- `Money_Map_Spec_Packet.pdf` p.15 (Patch Pack data artifacts including `meta.yaml` and DE rulepack).
