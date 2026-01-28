# Money Map Data Inventory (M1)

This document describes the canonical data contract for Money Map. Files are JSON-compatible YAML (JSON content inside `.yaml` files) so they can be parsed by the stdlib JSON loader in no-network environments.

## Meta

| Path | Purpose | Owner | Update frequency | Validation rules |
| --- | --- | --- | --- | --- |
| `data/meta.yaml` | Dataset metadata, schema version, and staleness policy. | System maintained | On release / review | Required. Must include `dataset_version`, `schema_version`, `reviewed_at`, and `staleness_policy` with `warn_after_days`, `force_require_check_after_days`, `regulated_tags`. `schema_version` must match code expectation. |

## Taxonomy & Cells

| Path | Purpose | Owner | Update frequency | Validation rules |
| --- | --- | --- | --- | --- |
| `data/taxonomy.yaml` | Master list of taxonomy categories. | System maintained | On taxonomy changes | Required. Array of objects; each needs `taxonomy_id` and `title_key`. `taxonomy_id` values must be unique. |
| `data/cells.yaml` | Master list of cells (activity buckets). | System maintained | On cell changes | Required. Array of objects; each needs `cell_id` and `title_key`. `cell_id` values must be unique. |

## Variants & Bridges

| Path | Purpose | Owner | Update frequency | Validation rules |
| --- | --- | --- | --- | --- |
| `data/variants.yaml` | Income-path variants. | System maintained | On variant updates | Required. Array of objects; each needs `variant_id`, `title_key`, `summary_key`, `taxonomy_id`, `cells`, `tags`, `review_date`. `variant_id` values must be unique. `taxonomy_id` must exist in taxonomy. `cells` must exist in cells. |
| `data/bridges.yaml` | Optional edges between variants (progression/compatibility). | System maintained | As needed | Required (may be empty). If entries exist, each must include `from_variant_id` and `to_variant_id` referencing valid `variant_id`. |

## Rulepacks

| Path | Purpose | Owner | Update frequency | Validation rules |
| --- | --- | --- | --- | --- |
| `data/rulepacks/DE.yaml` | Country-specific rules and compliance kits (M1 skeleton). | System maintained | On legal review | Required. Must include `country_code`, `reviewed_at`, `rules`, `compliance_kits`. |

## Knowledge Bases (lookups)

| Path | Purpose | Owner | Update frequency | Validation rules |
| --- | --- | --- | --- | --- |
| `data/knowledge/skills.yaml` | Skill taxonomy used for profile matching and recommendations. | System maintained | As taxonomy changes | Required. Array; each item needs `skill_id`, `title_key`. |
| `data/knowledge/assets.yaml` | Asset taxonomy used for profile matching. | System maintained | As taxonomy changes | Required. Array; each item needs `asset_id`, `title_key`. |
| `data/knowledge/constraints.yaml` | Constraint taxonomy used for filtering. | System maintained | As taxonomy changes | Required. Array; each item needs `constraint_id`, `title_key`. |
| `data/knowledge/objectives.yaml` | Objective presets for recommendations. | System maintained | As taxonomy changes | Required. Array; each item needs `objective_id`, `title_key`. |
| `data/knowledge/risks.yaml` | Risk/feasibility/economics/legal placeholders. | System maintained | On review | Required. Array; each item needs `risk_id`, `title_key`, `category`. |

## User Profiles

| Path | Purpose | Owner | Update frequency | Validation rules |
| --- | --- | --- | --- | --- |
| `profiles/demo_fast_start.yaml` | Example user profile for demos/tests. | System maintained | As needed | Required for repo tests. Must include `country_code`, `time_hours_per_week`, `capital_eur`, `language_level`, `skills`, `assets`, `constraints`, `objective_preset`. |

## Outputs

| Path | Purpose | Owner | Update frequency | Validation rules |
| --- | --- | --- | --- | --- |
| `exports/` | Export destination for CLI/UI outputs. | System generated | On export | Directory must exist; files are overwritten deterministically. |

## Validation behavior

- **Strict mode** (`--strict`): Missing optional files are treated as fatal. Current M1 inventory marks all files above as required; empty arrays are allowed where specified.
- **Non-strict mode**: Missing optional files produce warnings.
