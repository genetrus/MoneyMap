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
    risk_tolerance: str = "medium"
    horizon_months: int = 6
    target_net_monthly_eur: int | None = None
    preferred_modes: list[str] = Field(default_factory=list)


class TaxonomyItem(BaseModel):
    taxonomy_id: str
    title_key: str


class Cell(BaseModel):
    cell_id: str
    title_key: str


class Feasibility(BaseModel):
    prerequisites: list[str] = Field(default_factory=list)
    complexity: int = 1
    time_to_first_eur_days: int | None = None
    operational_mode: str = "service"


class EconomicsSnapshot(BaseModel):
    capex_eur: int | None = None
    opex_monthly_eur: int | None = None
    expected_net_monthly_eur_low: int | None = None
    expected_net_monthly_eur_high: int | None = None
    margin_notes_key: str | None = None


class Legal(BaseModel):
    regulated_level: str = "none"
    required_kits: list[str] = Field(default_factory=list)
    permits: list[str] = Field(default_factory=list)
    disclaimers_key: str | None = None


class Evidence(BaseModel):
    sources: list[dict[str, Any]] = Field(default_factory=list)
    last_verified_at: date | str | None = None
    confidence: int = 3


class Variant(BaseModel):
    variant_id: str
    title_key: str
    summary_key: str
    taxonomy_id: str
    cells: list[str]
    tags: list[str] = Field(default_factory=list)
    review_date: date | str
    feasibility: Feasibility | None = Field(default_factory=Feasibility)
    economics: EconomicsSnapshot | None = Field(default_factory=EconomicsSnapshot)
    legal: Legal | None = Field(default_factory=Legal)
    evidence: Evidence | None = Field(default_factory=Evidence)
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


class ObjectivePreset(BaseModel):
    preset_id: str
    title_key: str
    summary_key: str
    weight_feasibility: float
    weight_economics: float
    weight_legal: float
    weight_fit: float
    weight_staleness: float
    constraints_profile_overrides: list[str] | None = None
    sorting_policy: str | None = None


class Risk(BaseModel):
    risk_id: str
    title_key: str
    category: str


class Rule(BaseModel):
    rule_id: str
    title_key: str
    summary_key: str

    applies_if: dict[str, Any] = Field(default_factory=dict)
    effects: dict[str, Any] = Field(default_factory=dict)


class ComplianceKit(BaseModel):
    kit_id: str
    title_key: str
    summary_key: str
    regulated_level: str = "none"
    checklist: list[str] = Field(default_factory=list)
    applies_to_tags: list[str] = Field(default_factory=list)
    stale_after_days: int | None = None


class RulePack(BaseModel):
    country_code: str
    reviewed_at: date | str
    rules: list[Rule] = Field(default_factory=list)
    compliance_kits: list[ComplianceKit] = Field(default_factory=list)


class RankedVariant(BaseModel):
    variant_id: str
    score_total: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    compliance_summary: dict[str, Any] = Field(default_factory=dict)
    staleness: dict[str, Any] = Field(default_factory=dict)


class RecommendationResult(BaseModel):
    ranked_variants: list[RankedVariant]
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class RoutePlan(BaseModel):
    selected_variant_id: str
    overview: dict[str, Any] = Field(default_factory=dict)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    week_plan: list[dict[str, Any]] = Field(default_factory=list)
    compliance_checklist: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_reviews: list[dict[str, Any]] = Field(default_factory=list)


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
    presets: list[ObjectivePreset]
    risks: list[Risk]
    rulepacks: dict[str, RulePack]
    rulepack: RulePack
