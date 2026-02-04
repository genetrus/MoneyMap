# Data status (Canonical)

## Purpose
Show dataset metadata + validation + staleness at a glance, and provide a downloadable validate report. Offline-first.

## Status states
The page status MUST be one of:
- valid
- invalid
- stale

### Status rules
1) If fatals_count > 0 => status = "invalid"
2) Else if stale == true (reviewed_at older than staleness_policy) => status = "stale"
3) Else => status = "valid"

Warnings:
- warns_count MUST be shown as a KPI on the page.
- If stale == true, the page MUST show a warning about staleness and cautious behavior.

## Top-to-bottom page layout

### 1) Header
H1: `Data status`
Subheader: `Validation, staleness, and dataset metadata (offline-first).`

### 2) Summary grid (above the fold)
Show 6 KPI cards:

A) Dataset version
- Label: `Dataset version`
- Value: {dataset_version}

B) Reviewed at
- Label: `Reviewed at`
- Value: {reviewed_at} (YYYY-MM-DD)

C) Status
- Label: `Status`
- Value: valid | invalid | stale

D) Warnings
- Label: `Warnings`
- Value: {warns_count}
- Secondary (optional): short comma-separated summary if available

E) Fatals
- Label: `Fatals`
- Value: {fatals_count}

F) Stale
- Label: `Stale`
- Value: {stale} (True/False)
- Secondary (MUST): `Staleness policy: {staleness_policy_days} days`

### 3) Alert strip (conditional)
3.1 If status == invalid:
- Title: `Data validation failed`
- Body: `Fix FATAL issues and re-run validation. Recommendations/Plan/Export may be unreliable until data is valid.`

3.2 If status == stale:
- Title: `Data is stale`
- Body: `Reviewed_at is older than staleness_policy. Show warnings and apply cautious behavior.`
- Extra line (MUST): `For regulated domains: force legal_gate=require_check when rulepack is stale.`

3.3 If status == valid:
- Optional small success line: `Data is valid.` (no big alert)

### 4) Validate report (always present)
Section title: `Validate report`

4.1 Download
- Button label: `Download validate report`
- File name template: `money_map_validate_report__{dataset_version}__{generated_at}.json`

4.2 Summary lines (MUST)
- `Generated at: {generated_at}`
- `Includes: status, fatals[], warns[], dataset_version, reviewed_at, stale, staleness_policy_days`

4.3 Raw report JSON (collapsible)
Expander title: `Raw report JSON`
- Render pretty JSON of the exact report object.

### 5) Validation summary (tables)
Section title: `Validation summary`

If fatals_count > 0:
Subheader: `FATAL issues (must fix)`
Table columns:
- Code
- Message
- Source
- Location
- Hint

If warns_count > 0:
Subheader: `Warnings (non-blocking)`
Same columns.

### 6) Staleness details (expander)
Expander title: `Staleness details`
Fields:

RulePack:
- `RulePack: {country}` (use DE in current dataset)
- `rulepack_reviewed_at: {rulepack_reviewed_at}`
- `staleness_policy_days: {staleness_policy_days}`
- `rulepack_stale: {rulepack_stale}`

Variants freshness:
- `variants_count: {variants_count}`
- `oldest_variant_review_date: {min_variant_review_date}`
- `newest_variant_review_date: {max_variant_review_date}`
- `variants_stale: {variants_stale}` (if computed; if not available, omit line)

Behavior note:
`If rulepack/variants are stale: show warning. For regulated domains apply cautious behavior (force require_check).`

### 7) Data sources & diagnostics (expander)
Expander title: `Data sources & diagnostics`

7.1 Loaded sources table
Columns:
- Source
- Type
- Schema version
- Items

Minimum expected sources (if present in repo):
- data/meta.yaml
- data/rulepacks/DE.yaml
- variants data source (e.g., data/variants.yaml)

7.2 Reproducibility & where to look (fixed text)
- `Reproducibility gate: one script/process should rebuild the same dataset from sources.`
- `Errors must be diagnosable: this page shows validation report + sources; use the report to locate failing items.`
- `CI should run: pytest + money-map validate.`

### 8) Disclaimer (always visible, NOT inside expander)
Section title: `Disclaimer`
Text MUST include the following lines (keep Russian text exactly):
- `Не является: юридическим сервисом, биржей вакансий, системой прогнозирования дохода.`
- `Ограничение: не делаем юридических заключений и гарантий дохода; только диапазоны и чеклисты.`

## Validate report JSON contract (required keys)
The downloaded JSON MUST contain keys:
- status (valid|invalid|stale)
- dataset_version (string)
- reviewed_at (YYYY-MM-DD string)
- stale (bool)
- staleness_policy_days (int)
- generated_at (ISO string or YYYY-MM-DDTHH:MM:SS)
- fatals (array)
- warns (array)

Each fatal/warn item SHOULD include (when available):
- code
- message
- source
- location
- hint

## Acceptance criteria
- Data status page matches the layout and exact labels above.
- Warnings KPI is visible even when raw JSON is collapsed.
- “Download validate report” downloads JSON with the required keys.
- If stale==true, the alert strip includes the “force legal_gate=require_check …” line.
- Disclaimer section is visible on the page (not hidden).
- Offline-first: no network calls.

## Traceability (PDF page references)
- Money_Map_Spec_Packet: UX/UI Data status elements/states (p.8)
- Money_Map_Spec_Packet: NFR staleness warnings (p.11)
- Money_Map_Spec_Packet: DoD checklist + staleness behavior + disclaimer check (p.14)
- Money_Map_Spec_Packet: entities RulePack/Variant reviewed_at/review_date (p.9)
- Data block-scheme: reproducibility gate + errors diagnosable (page 2)
