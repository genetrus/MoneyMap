# Money Map Data Dictionary

Generated from schema and data templates in `data`.

## data/meta.yaml

**Purpose:** Dataset metadata, schema versioning, and staleness policy.

**Root model:** `Meta`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `dataset_version` | `string` | required | Dataset release identifier. |
| `schema_version` | `string` | required | Schema version string. |
| `reviewed_at` | `date` | required | Last review date (ISO 8601). |
| `supported_countries` | `list[string]` | optional | Country codes covered by data. |
| `staleness_policy.warn_after_days` | `int` | required | Days before staleness warning. |
| `staleness_policy.force_require_check_after_days` | `int` | required | Days before regulated tags require checks. |
| `staleness_policy.regulated_tags` | `list[string]` | optional | Tags that require checks when stale. |

**Cross references:** Used by validation for staleness and regulated tag checks.

## data/taxonomy.yaml

**Purpose:** Master taxonomy for income paths.

**Root model:** `TaxonomyItem[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `taxonomy_id` | `string` | required | Unique taxonomy identifier. |
| `title_key` | `string` | required | i18n key for taxonomy title. |

**Cross references:** Referenced by variants.taxonomy_id.

## data/cells.yaml

**Purpose:** Master list of activity cells.

**Root model:** `Cell[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `cell_id` | `string` | required | Unique cell identifier. |
| `title_key` | `string` | required | i18n key for cell title. |

**Cross references:** Referenced by variants.cells.

## data/variants.yaml

**Purpose:** Income-path variants with feasibility and requirements.

**Root model:** `Variant[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `variant_id` | `string` | required | Unique variant identifier. |
| `title_key` | `string` | required | i18n key for variant title. |
| `summary_key` | `string` | required | i18n key for variant summary. |
| `taxonomy_id` | `string` | required | Foreign key to taxonomy. |
| `cells` | `list[string]` | required | Foreign keys to cells. |
| `tags` | `list[string]` | optional | Tag list for filtering. |
| `review_date` | `date` | required | Variant review date. |
| `feasibility` | `object` | optional | Feasibility payload. |
| `economics` | `object` | optional | Economics payload. |
| `legal` | `object` | optional | Legal payload. |
| `required_skills` | `list[string]` | optional | Skill references. |
| `required_assets` | `list[string]` | optional | Asset references. |
| `constraints` | `list[string]` | optional | Constraint references. |
| `objectives` | `list[string]` | optional | Objective references. |
| `risks` | `list[string]` | optional | Risk references. |

**Cross references:** References taxonomy, cells, skills, assets, constraints, objectives, risks.

## data/bridges.yaml

**Purpose:** Directed edges between variants.

**Root model:** `Bridge[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `from_variant_id` | `string` | required | Source variant id. |
| `to_variant_id` | `string` | required | Target variant id. |
| `notes` | `string` | optional | Optional relationship notes. |

**Cross references:** References variants.variant_id.

## data/knowledge/skills.yaml

**Purpose:** Skill taxonomy for profile matching.

**Root model:** `Skill[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `skill_id` | `string` | required | Unique skill identifier. |
| `title_key` | `string` | required | i18n key for skill title. |

**Cross references:** Referenced by variants.required_skills and profiles.

## data/knowledge/assets.yaml

**Purpose:** Asset taxonomy for profile matching.

**Root model:** `Asset[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `asset_id` | `string` | required | Unique asset identifier. |
| `title_key` | `string` | required | i18n key for asset title. |

**Cross references:** Referenced by variants.required_assets and profiles.

## data/knowledge/constraints.yaml

**Purpose:** Constraint taxonomy for profile matching.

**Root model:** `Constraint[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `constraint_id` | `string` | required | Unique constraint identifier. |
| `title_key` | `string` | required | i18n key for constraint title. |

**Cross references:** Referenced by variants.constraints and profiles.

## data/knowledge/objectives.yaml

**Purpose:** Objective taxonomy for recommendations.

**Root model:** `Objective[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `objective_id` | `string` | required | Unique objective identifier. |
| `title_key` | `string` | required | i18n key for objective title. |

**Cross references:** Referenced by variants.objectives and profiles.

## data/knowledge/risks.yaml

**Purpose:** Risk taxonomy used for diagnostics.

**Root model:** `Risk[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `risk_id` | `string` | required | Unique risk identifier. |
| `title_key` | `string` | required | i18n key for risk title. |
| `category` | `string` | required | Risk grouping identifier. |

**Cross references:** Referenced by variants.risks.

## data/rulepacks/<COUNTRY>.yaml

**Purpose:** Country-specific rules and compliance kits.

**Root model:** `RulePack`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `country_code` | `string` | required | ISO country code. |
| `reviewed_at` | `date` | required | Rulepack review date. |
| `rules` | `list[Rule]` | required | Rules applicable to the country. |
| `compliance_kits` | `list[ComplianceKit]` | required | Compliance kit list. |

**Cross references:** Rule and compliance kit titles require i18n entries.
