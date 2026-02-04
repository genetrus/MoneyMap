# MoneyMap

## Specification
See [docs/spec/index.md](docs/spec/index.md). The PDFs in `docs/spec/source` are the single source of requirements.
Release 0.1 scope/flows/DoD are summarized in [docs/releases/0.1-brief.md](docs/releases/0.1-brief.md).

## Development
See [docs/DEV.md](docs/DEV.md) for the Windows-first setup and one-command run instructions.

## UI dependencies (Streamlit)
Install the UI dependencies (Streamlit) using the `ui` extra before running UI checks or MVP verification:

```bash
python -m pip install -e ".[ui]"
python scripts/mvp_check.py
```

### UI deps in restricted networks
If your network blocks PyPI, retry without build isolation or use a wheelhouse:

```bash
python -m pip install --no-build-isolation -e ".[ui]"
# or: python scripts/install_ui_deps.py
# or (offline): python -m pip download -d wheelhouse "money-map[ui]"
# then: python -m pip install --no-index --find-links=wheelhouse -e ".[ui]"
```

Without the UI check, you cannot claim “MVP criteria passed.”

## Formatting guardrails
This repo uses Ruff for formatting and linting (same commands as CI). To avoid future "would reformat" failures, enable pre-commit hooks and use the Make targets for formatting checks. (Money_Map_Spec_Packet.pdf p.14)

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Use `make fmt` to auto-format and `make fmt-check` to run the CI-equivalent formatting check.
