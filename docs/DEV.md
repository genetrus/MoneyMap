# Development environment

## Supported platforms
- Windows is the primary development platform; Linux/macOS are optional. (Money_Map_Spec_Packet.pdf p.11)
- Release scope, MVP flows, and quality gates are summarized in `docs/releases/0.1-brief.md`. (Money_Map_Spec_Packet.pdf p.13–14; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)

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

## E2E smoke tests (Step 8)
Run the end-to-end API + CLI smoke tests locally with the demo profile. (Money_Map_Spec_Packet.pdf p.14; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)

- **Recommended (Windows, PowerShell):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/e2e.ps1
  ```
  > Creates `.venv`, installs `.[dev]`, runs validate + E2E. (Money_Map_Spec_Packet.pdf p.14; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)
- **Alternatives:**
  - **Linux/macOS (bash):**
    ```bash
    ./scripts/e2e.sh
    ```
  - **Make (if available):**
    ```bash
    make e2e
    ```
- **Run only the E2E tests:**
  ```bash
  MONEY_MAP_DISABLE_NETWORK=1 python -m pytest -q tests/test_e2e_api_flow.py tests/test_e2e_cli_flow.py
  ```
- **Run the full test suite:**
  ```bash
  python -m pytest -q
  ```
- **Run the CLI validation gate:**
  ```bash
  MONEY_MAP_DISABLE_NETWORK=1 python -m money_map.app.cli validate --data-dir data
  ```
  > If the console script is installed, `money-map validate --data-dir data` is equivalent. The canonical form is `python -m money_map.app.cli ...`. (Money_Map_Spec_Packet.pdf p.14)

- **Machine-readable CLI output (recommend):**
  ```bash
  python -m money_map.app.cli recommend --profile profiles/demo_fast_start.yaml --data-dir data --format json
  ```
  Use `--output path/to/recommend.json` to write JSON to disk, for example:
  ```bash
  python -m money_map.app.cli recommend --profile profiles/demo_fast_start.yaml --data-dir data --format json --output exports/recommend.json
  ```
  (Money_Map_Spec_Packet.pdf p.14)

Demo profiles live in `profiles/`, with `profiles/demo_fast_start.yaml` used by the E2E tests.

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

## Installing behind a proxy / restricted network
If you are on a corporate network or behind a proxy, configure the proxy for PowerShell and pip before running installs.

### PowerShell: HTTP(S) proxy environment variables
```powershell
$env:HTTP_PROXY = "http://proxy.example.com:8080"
$env:HTTPS_PROXY = "http://proxy.example.com:8080"
```

### pip config: mirror index + trusted host
```powershell
pip config set global.index-url https://mirror.example.com/simple
pip config set global.trusted-host mirror.example.com
```

### Offline install via a wheelhouse
Use a machine with internet access to download wheels into a local folder, then install from that folder.

```powershell
# On an online machine
@"
money-map[dev,ui]
"@ | Out-File -Encoding utf8 requirements-offline.txt
python -m pip download -d wheelhouse -r requirements-offline.txt

# On the offline machine (from the repo root)
python -m pip install --no-index --find-links=wheelhouse -e ".[dev,ui]"
```

## Walking skeleton note
Step 7 (walking skeleton) is implemented; follow Step 8+ for full end-to-end test suite and release activities. (Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)
