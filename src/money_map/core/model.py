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
    tags: list[str]
    feasibility: dict[str, Any]
    prep_steps: list[str]
    economics: dict[str, Any]
    legal: dict[str, Any]
    review_date: str


@dataclass(frozen=True)
class AppData:
    meta: Meta
    rulepack: Rulepack
    variants: list[Variant]


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
    stale: bool
    staleness_policy_days: int
    generated_at: str
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
