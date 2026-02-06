# Stage 7 — Profile validation + draft/ready state

## Scope
Implement Profile validation for required fields, numeric ranges, and soft warnings, with clear readiness states (`draft`/`ready`) before recommendation execution.

## Implemented behavior
- Added centralized profile validator (`validate_profile`) that returns:
  - `status`: `draft` or `ready`,
  - `is_ready`: boolean,
  - `missing`: required missing fields,
  - `warnings`: non-fatal quality/range notices.
- Required fields: `country`, `language_level`, `objective`, `capital_eur`, `time_per_week`.
- Range/quality checks:
  - `capital_eur` must be numeric and non-negative,
  - `time_per_week` must be numeric and >=1 (warns if >112),
  - `country` warns when not `DE` (MVP scope),
  - empty `assets` / `skills` produce soft warnings.
- Profile page now renders:
  - missing-fields info line,
  - warnings list,
  - explicit state indicator (`Profile ready` / `Profile draft`).
- Recommendations page now enforces readiness gate:
  - blocks recommendation run for `draft` profile,
  - explains missing fields and warnings to guide completion.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.4 (Profile-first scenario flow).
- `Money_Map_Spec_Packet.pdf` p.8 (Profile screen behavior in UI flow).
- `Money_Map_Spec_Packet.pdf` p.9-10 (UserProfile inputs used by recommendation pipeline).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD and predictable, diagnosable behavior).
