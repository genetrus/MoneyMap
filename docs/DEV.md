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
These commands create `.venv`, install editable dependencies (including the UI extra), and run `money-map --help` as a smoke check. (Money_Map_Spec_Packet.pdf p.11, p.13; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)

## Editable installs
- Core editable install:
  ```bash
  pip install -e .
  ```
- Editable install with UI extra:
  ```bash
  pip install -e ".[ui]"
  ```
The UI extra lives in `pyproject.toml` under `project.optional-dependencies`. (Money_Map_Spec_Packet.pdf p.11, p.13)

## Troubleshooting
- **Activate the venv manually** if you want to run commands interactively:
  - PowerShell: `.\.venv\Scripts\Activate.ps1`
  - Bash: `source .venv/bin/activate`
- **Execution policy**: if PowerShell blocks scripts, use the provided one-command run with `-ExecutionPolicy Bypass`. (Money_Map_Spec_Packet.pdf p.11)
