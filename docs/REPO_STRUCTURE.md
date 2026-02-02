# Repository structure

## Current structure (as-is)
Top-level entries captured from `git ls-files`/`ls -la`:
- `AGENTS.md`
- `Makefile`
- `README.md`
- `pyproject.toml`
- `docs/` (includes `DEV.md`, `DECISIONS.md`, `releases/`, and `spec/` PDFs)
- `scripts/` (PowerShell + bash dev scripts)
- `src/` (Python package `money_map`)

## Target structure (per spec architecture)
Reference: Money_Map_Spec_Packet.pdf p.12.

- `data/` (exists; placeholders only)
  - `meta.yaml` (missing; to be added later)
  - `rulepacks/` (exists; placeholders only)
- `exports/` (missing; gitignored output folder)
- `scripts/` (exists)
- `src/money_map/` (exists)
  - `core/` (exists; placeholder package)
  - `render/` (exists; placeholder package)
  - `app/` (exists; placeholder package)
  - `ui/` (exists; placeholder package)
- `tests/` (exists; minimal smoke test)
- `docs/` (exists)
  - `releases/` (exists)
  - `spec/` (exists)
