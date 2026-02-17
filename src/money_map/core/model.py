"""Core data models for MoneyMap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StalenessPolicy:
    warn_after_days: int = 180
    hard_after_days: int = 365
    stale_after_days: int | None = None

    def __post_init__(self) -> None:
        if self.stale_after_days is not None:
            object.__setattr__(self, "warn_after_days", int(self.stale_after_days))
        if self.hard_after_days < self.warn_after_days:
            object.__setattr__(self, "hard_after_days", int(self.warn_after_days))
        object.__setattr__(self, "stale_after_days", int(self.warn_after_days))


@dataclass(frozen=True)
class Meta:
    dataset_version: str
    staleness_policy: StalenessPolicy


@dataclass(frozen=True)
class Rule:
    rule_id: str
    reason: str


@dataclass(frozen=True)
class Rulepack:
    reviewed_at: str
    staleness_policy: StalenessPolicy
    compliance_kits: dict[str, list[str]]
    regulated_domains: list[str]
    rules: list[Rule]


@dataclass(frozen=True)
class Variant:
    variant_id: str
    title: str
    summary: str
    cell_id: str = ""
    taxonomy_id: str = ""
    tags: list[str] = None
    regulated_domain: str | None = None
    feasibility: dict[str, Any] = None
    prep_steps: list[str] = None
    economics: dict[str, Any] = None
    legal: dict[str, Any] = None
    review_date: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", list(self.tags or []))
        object.__setattr__(self, "feasibility", dict(self.feasibility or {}))
        object.__setattr__(self, "prep_steps", list(self.prep_steps or []))
        object.__setattr__(self, "economics", dict(self.economics or {}))
        object.__setattr__(self, "legal", dict(self.legal or {}))


@dataclass(frozen=True)
class AppData:
    meta: Meta
    rulepack: Rulepack
    variants: list[Variant]
    sources: list["DataSourceInfo"]


@dataclass(frozen=True)
class DataSourceInfo:
    source: str
    type: str
    schema_version: str
    items: int
    reviewed_at: str
    mtime: str
    notes: dict[str, Any]


@dataclass(frozen=True)
class UserProfile:
    name: str
    objective: str
    language_level: str
    capital_eur: int
    time_per_week: int
    assets: list[str]
    location: str


@dataclass(frozen=True)
class ValidationReport:
    status: str
    fatals: list[dict[str, Any]]
    warns: list[dict[str, Any]]
    dataset_version: str
    reviewed_at: str
    dataset_reviewed_at: str
    stale: bool
    staleness_policy_days: int
    generated_at: str
    sources: list[DataSourceInfo]
    staleness: dict[str, Any]


@dataclass(frozen=True)
class FeasibilityResult:
    status: str
    blockers: list[str]
    prep_steps: list[str]
    estimated_prep_weeks_range: list[int]


@dataclass(frozen=True)
class EconomicsResult:
    time_to_first_money_days_range: list[int]
    typical_net_month_eur_range: list[int]
    costs_eur_range: list[int]
    volatility_or_seasonality: str | None
    variable_costs: str | None
    scaling_ceiling: str | None
    confidence: str


@dataclass(frozen=True)
class LegalResult:
    legal_gate: str
    checklist: list[str]
    compliance_kits: list[str]
    applied_rules: list[Rule]


@dataclass(frozen=True)
class RecommendationVariant:
    variant: Variant
    score: float
    feasibility: FeasibilityResult
    economics: EconomicsResult
    legal: LegalResult
    stale: bool
    staleness: dict[str, Any]
    pros: list[str]
    cons: list[str]


@dataclass(frozen=True)
class RecommendationResult:
    ranked_variants: list[RecommendationVariant]
    diagnostics: dict[str, Any]
    profile_hash: str


@dataclass(frozen=True)
class StalenessContract:
    """Unified staleness payload for UI/DTO contracts."""

    status: str  # fresh|warn|hard|unknown
    is_stale: bool
    reviewed_at: str | None
    warn_after_days: int | None
    hard_after_days: int | None
    message: str


@dataclass(frozen=True)
class LegalContract:
    """Unified legal/compliance payload for UI/DTO contracts."""

    gate: str  # ok|require_check|registration|license|blocked
    regulated_domain: str | None
    checklist: list[str]
    compliance_kits: list[str]
    requires_human_check: bool


@dataclass(frozen=True)
class EvidenceContract:
    """Unified evidence payload for UI/DTO contracts."""

    reviewed_at: str | None
    source_refs: list[str]
    note: str | None
    confidence: float | None


@dataclass(frozen=True)
class FeasibilityFloorsContract:
    language: str | None
    assets: list[str]
    time_per_week_hours: int | None
    other: list[str]


@dataclass(frozen=True)
class EconomicsContract:
    time_to_first_money_days_range: list[int] | None
    typical_net_month_eur_range: list[int] | None
    costs_fixed_eur: int | None
    costs_variable_eur_range: list[int] | None
    volatility: str | None
    ceiling: str | None
    note: str | None


@dataclass(frozen=True)
class VariantCardV1:
    """Expanded variant card contract for Explore/Recommendations."""

    variant_id: str
    title: str
    country: str
    taxonomy_id: str
    taxonomy_label: str
    cells: list[str]
    one_liner: str
    feasibility_status: str
    prep_weeks_range: list[int] | None
    blockers: list[str]
    prep_steps: list[str]
    feasibility_floors: FeasibilityFloorsContract
    economics: EconomicsContract
    legal: LegalContract
    evidence: EvidenceContract
    staleness: StalenessContract
    pros: list[str]
    cons: list[str]


@dataclass(frozen=True)
class MiniVariantCard:
    """Compact variant card contract for Classify examples."""

    variant_id: str
    title: str
    taxonomy_id: str
    taxonomy_label: str
    cell: str
    feasibility_status: str
    time_to_first_money_days_range: list[int] | None
    typical_net_month_eur_range: list[int] | None
    legal: LegalContract
    evidence: EvidenceContract
    staleness: StalenessContract


@dataclass(frozen=True)
class ClassifyCandidate:
    taxonomy_id: str
    taxonomy_label: str
    cell_guess: str
    score: float
    reasons: list[str]
    legal: LegalContract
    evidence: EvidenceContract
    staleness: StalenessContract
    sample_variants: list[MiniVariantCard]


@dataclass(frozen=True)
class ClassifyResultV1:
    """Deterministic text-classification result contract."""

    idea_text: str
    top3: list[ClassifyCandidate]
    cell_guess: str
    backup_cell_guess: str | None
    matched_keywords: list[str]
    suggested_tags: dict[str, str | None]  # sell, to_whom, value_measure
    reasons: list[str]
    confidence: float
    ambiguity: str  # clear|ambiguous
    legal: LegalContract
    evidence: EvidenceContract
    staleness: StalenessContract


@dataclass(frozen=True)
class PlanStepV1:
    step_id: str
    action: str
    output: str
    eta: str
    depends_on: list[str]


@dataclass(frozen=True)
class PlanArtifactV1:
    artifact_id: str
    name: str
    definition: str
    done_criteria: str


@dataclass(frozen=True)
class PlanTemplateV1:
    """Plan export contract aligned with Plan Template v1 sections."""

    variant_id: str
    variant_title: str
    country: str
    objective_preset: str
    profile_hash: str
    confidence: float
    one_liner: str
    feasibility_status: str
    prep_weeks_range: list[int] | None
    blockers: list[str]
    prep_steps: list[str]
    artifacts: list[PlanArtifactV1]
    steps: list[PlanStepV1]
    week_plan: dict[str, list[str]]
    kpis: list[str]
    legal: LegalContract
    economics: EconomicsContract
    evidence: EvidenceContract
    staleness: StalenessContract


@dataclass(frozen=True)
class PlanStep:
    title: str
    detail: str


@dataclass(frozen=True)
class RoutePlan:
    variant_id: str
    steps: list[PlanStep]
    artifacts: list[str]
    week_plan: dict[str, list[str]]
    compliance: list[str]
    legal_gate: str
    applied_rules: list[Rule]
    staleness: dict[str, Any]


@dataclass
class ExportBundle:
    plan_md: str
    result_json: dict[str, Any]
    profile_yaml: dict[str, Any]
