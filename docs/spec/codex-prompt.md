# Codex Working Prompt (operational guide, not a requirements source)

- Read `docs/spec/index.md` first to locate the relevant PDF(s).
- Identify the exact PDF filename(s) and page ranges that apply.
- Restate the requirement with PDF+page citations before changing code.
- If an assumption is needed, record it in `docs/DECISIONS.md` *before* coding.
- Do not invent requirements; chat/README are not sources of truth.
- Prefer offline-first behavior; use YAML/JSON data formats **only when required by the PDFs**.
- Use Streamlit UI and Typer CLI **only when explicitly required by the PDFs**.
- Keep outputs deterministic and testable; follow DoD/Release plan gates from the PDFs.
- Update documentation alongside implementation changes.
- Include PDF+page citations in PR/commit messages or in `docs/DECISIONS.md` entries.
