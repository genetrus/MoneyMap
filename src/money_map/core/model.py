from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - optional dependency

    class _FieldInfo:
        def __init__(self, default_factory: Any | None = None) -> None:
            self.default_factory = default_factory

    def Field(default_factory: Any | None = None) -> Any:  # type: ignore[override]
        return _FieldInfo(default_factory=default_factory)

    class BaseModel:  # type: ignore[override]
        def __init__(self, **data: Any) -> None:
            annotations = getattr(self, "__annotations__", {})
            for name in annotations:
                if name in data:
                    setattr(self, name, data[name])
                elif hasattr(self.__class__, name):
                    default = getattr(self.__class__, name)
                    if isinstance(default, _FieldInfo):
                        value = default.default_factory() if default.default_factory else None
                        setattr(self, name, value)
                    elif isinstance(default, (list, dict)):
                        setattr(self, name, default.copy())
                    else:
                        setattr(self, name, default)
            for key, value in data.items():
                if key not in annotations:
                    setattr(self, key, value)

        @classmethod
        def model_validate(cls, data: Any) -> "BaseModel":
            if isinstance(data, cls):
                return data
            if not isinstance(data, dict):
                raise TypeError("model_validate expects a dict")
            return cls(**data)

        def model_dump(self) -> dict[str, Any]:
            return dict(self.__dict__)


class StalenessPolicy(BaseModel):
    warn_after_days: int
    force_require_check_after_days: int
    regulated_tags: list[str] = Field(default_factory=list)


class Meta(BaseModel):
    dataset_version: str
    schema_version: str
    reviewed_at: date | str
    staleness_policy: StalenessPolicy
    supported_countries: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    country_code: str = "DE"
    time_hours_per_week: int
    capital_eur: int
    language_level: str
    skills: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    objective_preset: str


class TaxonomyItem(BaseModel):
    taxonomy_id: str
    title_key: str


class Cell(BaseModel):
    cell_id: str
    title_key: str


class Variant(BaseModel):
    variant_id: str
    title_key: str
    summary_key: str
    taxonomy_id: str
    cells: list[str]
    tags: list[str] = Field(default_factory=list)
    review_date: date | str
    feasibility: dict[str, Any] = Field(default_factory=dict)
    economics: dict[str, Any] = Field(default_factory=dict)
    legal: dict[str, Any] = Field(default_factory=dict)
    required_skills: list[str] = Field(default_factory=list)
    required_assets: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class Skill(BaseModel):
    skill_id: str
    title_key: str


class Asset(BaseModel):
    asset_id: str
    title_key: str


class Constraint(BaseModel):
    constraint_id: str
    title_key: str


class Objective(BaseModel):
    objective_id: str
    title_key: str


class Risk(BaseModel):
    risk_id: str
    title_key: str
    category: str


class Rule(BaseModel):
    rule_id: str
    title_key: str
    summary_key: str
    sources: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ComplianceKit(BaseModel):
    kit_id: str
    title_key: str
    summary_key: str
    requirements: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class RulePack(BaseModel):
    country_code: str
    reviewed_at: date | str
    rules: list[Rule] = Field(default_factory=list)
    compliance_kits: list[ComplianceKit] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    ranked_variants: list[dict[str, Any]]
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class RoutePlan(BaseModel):
    selected_variant_id: str
    steps: list[dict[str, Any]] = Field(default_factory=list)
    week_plan: list[dict[str, Any]] = Field(default_factory=list)
    aggregated_checklist: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)


@dataclass
class AppData:
    meta: Meta
    taxonomy: list[TaxonomyItem]
    cells: list[Cell]
    variants: list[Variant]
    bridges: list[dict[str, Any]]
    skills: list[Skill]
    assets: list[Asset]
    constraints: list[Constraint]
    objectives: list[Objective]
    risks: list[Risk]
    rulepacks: dict[str, RulePack]
    rulepack: RulePack
