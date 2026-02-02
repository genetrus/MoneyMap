# Development environment

## Supported platforms
- Windows is the primary development platform; Linux/macOS are optional. (Money_Map_Spec_Packet.pdf p.11)

## One-command setup/run
- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
  ```
- **Linux/macOS (bash):**
  ```bash
  ./scripts/dev.sh
  ```
These commands create `.venv`, install editable dependencies (including UI dependencies via the `ui` extra), and run `money-map --help` as a smoke check. If you also want the quality tools in the same environment, install `.[dev,ui]`. (Money_Map_Spec_Packet.pdf p.11, p.13; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)

## Local quality gates (Step 4)
Run the local format/lint/tests gates as a single command. (Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1; Money_Map_Spec_Packet.pdf p.14)

- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/quality.ps1
  ```
- **Linux/macOS (bash):**
  ```bash
  ./scripts/quality.sh
  ```
- **Linux/macOS (Make):**
  ```bash
  make gates
  ```
  > If `make` cannot find `ruff`/`pytest`, activate `.venv` first or use `scripts/quality.*`.

CI runs the same gates on every push/PR (ruff format check, ruff lint, pytest). (Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1; Money_Map_Spec_Packet.pdf p.13–14)

## Editable installs
- Core editable install:
  ```bash
  pip install -e .
  ```
- Editable install with dev + UI dependencies:
  ```bash
  pip install -e ".[dev,ui]"
  ```
The UI extra lives in `pyproject.toml` under `project.optional-dependencies`; install `.[ui]` for Streamlit, and add `.[dev]` when you need quality tools. (Money_Map_Spec_Packet.pdf p.11, p.13; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)

## Troubleshooting
- **Activate the venv manually** if you want to run commands interactively:
  - PowerShell: `.\.venv\Scripts\Activate.ps1`
  - Bash: `source .venv/bin/activate`
- **Execution policy**: if PowerShell blocks scripts, use the provided one-command run with `-ExecutionPolicy Bypass`. (Money_Map_Spec_Packet.pdf p.11)

## Walking skeleton note
Step 7 (walking skeleton) is implemented; follow Step 8+ for full end-to-end test suite and release activities. (Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)
