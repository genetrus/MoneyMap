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

## Pre-commit hooks (format/lint safety)
Install and enable pre-commit so formatting matches CI before you commit. (Money_Map_Spec_Packet.pdf p.14)

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

The hooks run Ruff lint + format using the same pinned version as CI. If you prefer Make targets, use `make fmt` for formatting and `make fmt-check` for CI-equivalent format checks.

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
  ```powershell
  $env:MONEY_MAP_DISABLE_NETWORK = "1"
  python -m pytest -q tests/test_e2e_api_flow.py tests/test_e2e_cli_flow.py
  ```
- **Run the full test suite:**
  ```bash
  python -m pytest -q
  ```
- **Run the CLI validation gate (editable install required):**
  ```bash
  make validate
  ```
  Or explicitly:
  ```bash
  python -m pip install -e .
  python -m money_map.app.cli validate --data-dir data
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

## MVP verification (one command)
Run the automated MVP verification script, which checks validation, recommend → plan → export, determinism, staleness gating, and plan actionability. (Money_Map_Spec_Packet.pdf p.5–7, p.11, p.14)

```bash
python scripts/mvp_check.py
```

If Streamlit is installed (via `.[ui]`), the script will also verify the UI import smoke check; otherwise it will report a skip. (Money_Map_Spec_Packet.pdf p.8, p.14)

For a CLI-only run (no UI deps), use:
```bash
make mvp-lite
```

## Editable installs
- Core editable install:
  ```bash
  python -m pip install -e .
  ```
- Editable install with dev + UI dependencies:
  ```bash
  python -m pip install -e ".[dev,ui]"
  ```
The UI extra lives in `pyproject.toml` under `project.optional-dependencies`; install `.[ui]` for Streamlit, and add `.[dev]` when you need quality tools. (Money_Map_Spec_Packet.pdf p.11, p.13; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1)

## Troubleshooting
- **Activate the venv manually** if you want to run commands interactively:
  - PowerShell: `.\.venv\Scripts\Activate.ps1`
  - Bash: `source .venv/bin/activate`
- **Execution policy**: if PowerShell blocks scripts, use the provided one-command run with `-ExecutionPolicy Bypass`. (Money_Map_Spec_Packet.pdf p.11)

## Installing behind a proxy / restricted network
If you are on a corporate network or behind a proxy, configure the proxy for PowerShell and pip before running installs.

## Agent vs local environment (important)
Installed Python packages are environment-local and are **not** stored in git commits. This means:
- Streamlit installed on your laptop does not automatically exist in CI/agent containers.
- Streamlit installed in CI/agent containers does not automatically exist on your laptop.

To avoid confusion, treat UI checks as a separate environment gate and run the same preflight in every runtime where UI checks are expected:

```bash
python -c "import sys; print(sys.executable)"
python -m pip show streamlit
python -c "import streamlit as st; print(st.__version__)"
```

If preflight fails in CI/agent due to network policy, use a mirror or offline wheelhouse for that environment (see sections below). (Money_Map_Spec_Packet.pdf p.11, p.14)

### Current execution policy (Variant A for now)
For the current environment, run core/CLI gates by default and treat container UI checks as skipped when Streamlit install is blocked by proxy `403`.

- Use `make mvp-lite` (or equivalent core/CLI checks) as the default gate in agent runs.
- Keep full UI/container checks as deferred Variant B and re-enable once mirror/proxy access or wheelhouse transfer is available.

This avoids repeating the same failed UI installation loop while preserving a clear path to re-enable full UI gates later. (Money_Map_Spec_Packet.pdf p.11, p.14)

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

### What you need to provide so the agent can install Streamlit in the container
If container installs fail with `Tunnel connection failed: 403 Forbidden`, provide **one** of these inputs:

1. **Working mirror/index details** (preferred):
   - `index-url` (example: `https://<your-mirror>/simple`)
   - `trusted-host` (host name only)
   - proxy requirements (if any): `HTTP_PROXY`, `HTTPS_PROXY`
2. **Offline wheelhouse artifact**:
   - a folder/archive with wheels that includes `streamlit` and transitive dependencies
   - installation command baseline: `python -m pip install --no-index --find-links=<wheelhouse> -e ".[ui]"`

Without one of these, the container cannot install UI dependencies when outbound package access is blocked. (Money_Map_Spec_Packet.pdf p.11, p.14)


### Run `make mvp` behind a proxy/mirror
```bash
MM_PIP_ARGS="--index-url https://mirror.example.com/simple --trusted-host mirror.example.com" make mvp
```
```powershell
$env:MM_PIP_ARGS="--index-url https://mirror.example.com/simple --trusted-host mirror.example.com"; make mvp
```

### Offline install via a wheelhouse
Use a machine with internet access to download wheels into a local folder, then install from that folder.

```bash
MM_WHEELHOUSE=wheelhouse make mvp
```
```powershell
$env:MM_WHEELHOUSE="wheelhouse"; make mvp
```

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
