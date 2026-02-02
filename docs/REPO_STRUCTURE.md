# Repository structure

## Current structure (as-is)
Top-level entries captured from git-tracked files:
- `.gitattributes`
- `.gitignore`
- `AGENTS.md`
- `Makefile`
- `README.md`
- `data/` (placeholder data artifacts)
- `docs/` (includes `DEV.md`, `DECISIONS.md`, `releases/`, and `spec/` PDFs)
- `exports/` (placeholder exports location; artifacts are gitignored, placeholder kept)
- `pyproject.toml`
- `scripts/` (PowerShell + bash dev scripts)
- `src/` (Python package `money_map`)
- `tests/` (pytest tests)

## Target structure (per spec architecture)
Reference: Money_Map_Spec_Packet.pdf p.12.

- `data/` (exists; placeholders only)
  - `meta.yaml` (missing; to be added later)
  - `rulepacks/` (exists; placeholders only)
- `exports/` (exists; gitignored output folder placeholder)
- `scripts/` (exists)
- `src/money_map/` (exists)
  - `core/` (exists; placeholder package)
  - `render/` (exists; placeholder package)
  - `app/` (exists; placeholder package; CLI entrypoint in `app/cli.py`)
  - `ui/` (exists; placeholder package)
- `tests/` (exists; minimal smoke test)
- `docs/` (exists)
  - `releases/` (exists)
  - `spec/` (exists)
