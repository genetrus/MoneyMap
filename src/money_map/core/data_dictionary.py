from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FieldInfo:
    name: str
    field_type: str
    required: bool
    description: str


@dataclass(frozen=True)
class DictionaryEntry:
    path: str
    purpose: str
    model: str
    fields: list[FieldInfo]
    cross_refs: str


DATA_DICTIONARY = [
    DictionaryEntry(
        path="data/meta.yaml",
        purpose="Dataset metadata, schema versioning, and staleness policy.",
        model="Meta",
        fields=[
            FieldInfo("dataset_version", "string", True, "Dataset release identifier."),
            FieldInfo("schema_version", "string", True, "Schema version string."),
            FieldInfo("reviewed_at", "date", True, "Last review date (ISO 8601)."),
            FieldInfo(
                "supported_countries", "list[string]", False, "Country codes covered by data."
            ),
            FieldInfo(
                "staleness_policy.warn_after_days",
                "int",
                True,
                "Days before staleness warning.",
            ),
            FieldInfo(
                "staleness_policy.force_require_check_after_days",
                "int",
                True,
                "Days before regulated tags require checks.",
            ),
            FieldInfo(
                "staleness_policy.regulated_tags",
                "list[string]",
                False,
                "Tags that require checks when stale.",
            ),
        ],
        cross_refs="Used by validation for staleness and regulated tag checks.",
    ),
    DictionaryEntry(
        path="data/taxonomy.yaml",
        purpose="Master taxonomy for income paths.",
        model="TaxonomyItem[]",
        fields=[
            FieldInfo("taxonomy_id", "string", True, "Unique taxonomy identifier."),
            FieldInfo("title_key", "string", True, "i18n key for taxonomy title."),
        ],
        cross_refs="Referenced by variants.taxonomy_id.",
    ),
    DictionaryEntry(
        path="data/cells.yaml",
        purpose="Master list of activity cells.",
        model="Cell[]",
        fields=[
            FieldInfo("cell_id", "string", True, "Unique cell identifier."),
            FieldInfo("title_key", "string", True, "i18n key for cell title."),
        ],
        cross_refs="Referenced by variants.cells.",
    ),
    DictionaryEntry(
        path="data/variants.yaml",
        purpose="Income-path variants with feasibility and requirements.",
        model="Variant[]",
        fields=[
            FieldInfo("variant_id", "string", True, "Unique variant identifier."),
            FieldInfo("title_key", "string", True, "i18n key for variant title."),
            FieldInfo("summary_key", "string", True, "i18n key for variant summary."),
            FieldInfo("taxonomy_id", "string", True, "Foreign key to taxonomy."),
            FieldInfo("cells", "list[string]", True, "Foreign keys to cells."),
            FieldInfo("tags", "list[string]", False, "Tag list for filtering."),
            FieldInfo("review_date", "date", True, "Variant review date."),
            FieldInfo("feasibility", "object", False, "Feasibility payload."),
            FieldInfo("economics", "object", False, "Economics payload."),
            FieldInfo("legal", "object", False, "Legal payload."),
            FieldInfo("required_skills", "list[string]", False, "Skill references."),
            FieldInfo("required_assets", "list[string]", False, "Asset references."),
            FieldInfo("constraints", "list[string]", False, "Constraint references."),
            FieldInfo("objectives", "list[string]", False, "Objective references."),
            FieldInfo("risks", "list[string]", False, "Risk references."),
        ],
        cross_refs="References taxonomy, cells, skills, assets, constraints, objectives, risks.",
    ),
    DictionaryEntry(
        path="data/bridges.yaml",
        purpose="Directed edges between variants.",
        model="Bridge[]",
        fields=[
            FieldInfo("from_variant_id", "string", True, "Source variant id."),
            FieldInfo("to_variant_id", "string", True, "Target variant id."),
            FieldInfo("notes", "string", False, "Optional relationship notes."),
        ],
        cross_refs="References variants.variant_id.",
    ),
    DictionaryEntry(
        path="data/knowledge/skills.yaml",
        purpose="Skill taxonomy for profile matching.",
        model="Skill[]",
        fields=[
            FieldInfo("skill_id", "string", True, "Unique skill identifier."),
            FieldInfo("title_key", "string", True, "i18n key for skill title."),
        ],
        cross_refs="Referenced by variants.required_skills and profiles.",
    ),
    DictionaryEntry(
        path="data/knowledge/assets.yaml",
        purpose="Asset taxonomy for profile matching.",
        model="Asset[]",
        fields=[
            FieldInfo("asset_id", "string", True, "Unique asset identifier."),
            FieldInfo("title_key", "string", True, "i18n key for asset title."),
        ],
        cross_refs="Referenced by variants.required_assets and profiles.",
    ),
    DictionaryEntry(
        path="data/knowledge/constraints.yaml",
        purpose="Constraint taxonomy for profile matching.",
        model="Constraint[]",
        fields=[
            FieldInfo("constraint_id", "string", True, "Unique constraint identifier."),
            FieldInfo("title_key", "string", True, "i18n key for constraint title."),
        ],
        cross_refs="Referenced by variants.constraints and profiles.",
    ),
    DictionaryEntry(
        path="data/knowledge/objectives.yaml",
        purpose="Objective taxonomy for recommendations.",
        model="Objective[]",
        fields=[
            FieldInfo("objective_id", "string", True, "Unique objective identifier."),
            FieldInfo("title_key", "string", True, "i18n key for objective title."),
        ],
        cross_refs="Referenced by variants.objectives and profiles.",
    ),
    DictionaryEntry(
        path="data/knowledge/risks.yaml",
        purpose="Risk taxonomy used for diagnostics.",
        model="Risk[]",
        fields=[
            FieldInfo("risk_id", "string", True, "Unique risk identifier."),
            FieldInfo("title_key", "string", True, "i18n key for risk title."),
            FieldInfo("category", "string", True, "Risk grouping identifier."),
        ],
        cross_refs="Referenced by variants.risks.",
    ),
    DictionaryEntry(
        path="data/rulepacks/<COUNTRY>.yaml",
        purpose="Country-specific rules and compliance kits.",
        model="RulePack",
        fields=[
            FieldInfo("country_code", "string", True, "ISO country code."),
            FieldInfo("reviewed_at", "date", True, "Rulepack review date."),
            FieldInfo("rules", "list[Rule]", True, "Rules applicable to the country."),
            FieldInfo(
                "compliance_kits",
                "list[ComplianceKit]",
                True,
                "Compliance kit list.",
            ),
        ],
        cross_refs="Rule and compliance kit titles require i18n entries.",
    ),
]


def _format_field(field: FieldInfo) -> str:
    required = "required" if field.required else "optional"
    return f"| `{field.name}` | `{field.field_type}` | {required} | {field.description} |"


def generate_data_dictionary(data_dir: Path, out_path: Path) -> None:
    lines = ["# Money Map Data Dictionary", ""]
    lines.append(f"Generated from schema and data templates in `{data_dir}`.")
    lines.append("")
    for entry in DATA_DICTIONARY:
        lines.append(f"## {entry.path}")
        lines.append("")
        lines.append(f"**Purpose:** {entry.purpose}")
        lines.append("")
        lines.append(f"**Root model:** `{entry.model}`")
        lines.append("")
        lines.append("| Field | Type | Required | Description |")
        lines.append("| --- | --- | --- | --- |")
        for field in entry.fields:
            lines.append(_format_field(field))
        lines.append("")
        lines.append(f"**Cross references:** {entry.cross_refs}")
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
