"""Deterministic text classification pipeline for ideas."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from money_map.core.model import (
    AppData,
    ClassifyCandidate,
    ClassifyResultV1,
    EvidenceContract,
    LegalContract,
    MiniVariantCard,
    StalenessContract,
)
from money_map.core.staleness import evaluate_staleness
from money_map.storage.fs import read_mapping

_TOKEN_PATTERN = re.compile(r"[\w€]+", re.UNICODE)


def _normalize_text(idea_text: str) -> str:
    lowered = idea_text.lower().strip()
    cleaned = re.sub(r"\s+", " ", lowered)
    return cleaned


def _tokens_and_ngrams(normalized_text: str) -> list[str]:
    tokens = _TOKEN_PATTERN.findall(normalized_text)
    bigrams = [f"{tokens[idx]} {tokens[idx + 1]}" for idx in range(len(tokens) - 1)]
    return tokens + bigrams


def _load_keywords(data_dir: str | Path) -> dict[str, dict]:
    try:
        payload = read_mapping(Path(data_dir) / "keywords.yaml")
    except (FileNotFoundError, ValueError):
        return {}
    return payload.get("keywords", {}) if isinstance(payload, dict) else {}


def _load_mappings(data_dir: str | Path) -> dict[str, dict]:
    try:
        payload = read_mapping(Path(data_dir) / "mappings.yaml")
    except (FileNotFoundError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _variant_taxonomy_from_tags(tags: list[str]) -> str:
    tag_set = set(tags)
    if "writing" in tag_set:
        return "service_fee"
    if "physical" in tag_set:
        return "labor"
    if "regulated" in tag_set:
        return "commission"
    if "remote" in tag_set:
        return "subscription"
    return "service_fee"


def _variant_cell_from_tags(tags: list[str]) -> str:
    tag_set = set(tags)
    if "remote" in tag_set and "regulated" in tag_set:
        return "B2"
    if "remote" in tag_set:
        return "A2"
    if "regulated" in tag_set:
        return "B1"
    return "A1"


def _extract_signals(
    phrases: list[str], keywords: dict[str, dict], mappings: dict[str, dict]
) -> tuple[list[str], dict[str, float], dict[str, float], dict[str, str | None]]:
    taxonomy_scores: defaultdict[str, float] = defaultdict(float)
    cell_scores: defaultdict[str, float] = defaultdict(float)
    matched: list[str] = []
    suggested_tags: dict[str, str | None] = {
        "sell": None,
        "to_whom": None,
        "value_measure": None,
    }

    seen = set(phrases)
    for phrase, rule in keywords.items():
        if phrase not in seen:
            continue
        matched.append(phrase)
        for taxonomy_id, weight in (rule.get("taxonomy", {}) or {}).items():
            taxonomy_scores[taxonomy_id] += float(weight)
        for cell_id, weight in (rule.get("cell", {}) or {}).items():
            cell_scores[cell_id] += float(weight)
        for tag_name, tag_value in (rule.get("tags", {}) or {}).items():
            if suggested_tags.get(tag_name) is None:
                suggested_tags[tag_name] = str(tag_value)

    tag_keywords = mappings.get("tag_keywords", {})
    for tag_name, tag_map in tag_keywords.items():
        for tag_value, words in tag_map.items():
            if any(word in seen for word in words):
                suggested_tags[tag_name] = suggested_tags.get(tag_name) or tag_value

    return sorted(set(matched)), dict(taxonomy_scores), dict(cell_scores), suggested_tags


def _score_taxonomy(
    taxonomy_scores: dict[str, float],
    mappings: dict[str, dict],
    phrases: list[str],
) -> list[tuple[str, float, list[str]]]:
    scores: defaultdict[str, float] = defaultdict(float)
    reasons: defaultdict[str, list[str]] = defaultdict(list)

    for taxonomy_id, score in taxonomy_scores.items():
        scores[taxonomy_id] += score
        reasons[taxonomy_id].append(f"keyword_score={score:.2f}")

    seen = set(phrases)
    for taxonomy_id, info in (mappings.get("taxonomy", {}) or {}).items():
        mapping_hits = [word for word in (info.get("keywords") or []) if word in seen]
        if mapping_hits:
            bonus = float(len(mapping_hits)) * 0.8
            scores[taxonomy_id] += bonus
            reasons[taxonomy_id].append(f"mapping_hits={', '.join(sorted(mapping_hits))}")

    if not scores:
        scores["service_fee"] = 0.1
        reasons["service_fee"].append("fallback_default")

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [(taxonomy_id, score, reasons[taxonomy_id]) for taxonomy_id, score in ranked[:3]]


def _score_cell(
    cell_scores: dict[str, float],
    mappings: dict[str, dict],
    phrases: list[str],
    top_taxonomy: str,
) -> tuple[str, str | None, list[str]]:
    scores: defaultdict[str, float] = defaultdict(float)
    reasons: list[str] = []

    for cell_id, score in cell_scores.items():
        scores[cell_id] += score
        reasons.append(f"cell_keywords:{cell_id}={score:.2f}")

    cell_keywords = mappings.get("cell_keywords", {}) or {}
    seen = set(phrases)
    for cell_id, words in cell_keywords.items():
        hits = [word for word in words if word in seen]
        if hits:
            bonus = float(len(hits)) * 0.6
            scores[cell_id] += bonus
            reasons.append(f"cell_mapping:{cell_id}={','.join(sorted(hits))}")

    taxonomy_cells = (mappings.get("taxonomy", {}).get(top_taxonomy, {}) or {}).get(
        "typical_cells", []
    )
    for idx, cell_id in enumerate(taxonomy_cells):
        scores[cell_id] += max(0.0, 1.2 - idx * 0.3)
        reasons.append(f"taxonomy_typical_cell:{cell_id}")

    if not scores:
        scores["A1"] = 0.1
        reasons.append("fallback_cell:A1")

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    cell_guess = ranked[0][0]
    backup = ranked[1][0] if len(ranked) > 1 else None
    return cell_guess, backup, reasons


def _common_contracts(
    app_data: AppData,
) -> tuple[LegalContract, EvidenceContract, StalenessContract]:
    staleness = evaluate_staleness(
        app_data.rulepack.reviewed_at,
        app_data.meta.staleness_policy,
        label="rulepack",
        invalid_severity="warn",
    )
    staleness_status = (
        "hard"
        if staleness.is_hard_stale
        else "warn"
        if staleness.is_stale or staleness.severity != "ok"
        else "fresh"
    )
    legal = LegalContract(
        gate="require_check" if staleness_status != "fresh" else "ok",
        regulated_domain="general",
        checklist=["Verify legal/regulatory requirements in your country"],
        compliance_kits=list(app_data.rulepack.compliance_kits.keys()),
        requires_human_check=True,
    )
    evidence = EvidenceContract(
        reviewed_at=app_data.rulepack.reviewed_at,
        source_refs=["data/rulepacks/DE.yaml", "data/variants.yaml"],
        note="Deterministic keyword and mapping based classification",
        confidence=None,
    )
    stale = StalenessContract(
        status=staleness_status,
        is_stale=staleness.is_stale,
        reviewed_at=app_data.rulepack.reviewed_at,
        warn_after_days=staleness.warn_after_days,
        hard_after_days=staleness.hard_after_days,
        message=staleness.message,
    )
    return legal, evidence, stale


def _sample_variants(app_data: AppData, taxonomy_id: str, cell_guess: str) -> list[MiniVariantCard]:
    legal, evidence, stale = _common_contracts(app_data)
    selected = [
        variant
        for variant in app_data.variants
        if _variant_taxonomy_from_tags(variant.tags) == taxonomy_id
    ]
    if not selected:
        selected = list(app_data.variants)
    selected = sorted(selected, key=lambda variant: variant.variant_id)[:5]

    cards: list[MiniVariantCard] = []
    for variant in selected:
        cards.append(
            MiniVariantCard(
                variant_id=variant.variant_id,
                title=variant.title,
                taxonomy_id=taxonomy_id,
                taxonomy_label=taxonomy_id.replace("_", " ").title(),
                cell=cell_guess,
                feasibility_status="feasible_with_prep",
                time_to_first_money_days_range=variant.economics.get(
                    "time_to_first_money_days_range"
                ),
                typical_net_month_eur_range=variant.economics.get("typical_net_month_eur_range"),
                legal=legal,
                evidence=evidence,
                staleness=stale,
            )
        )
    return cards


def classify_idea_text(
    idea_text: str,
    app_data: AppData,
    data_dir: str | Path = "data",
) -> ClassifyResultV1:
    normalized = _normalize_text(idea_text)
    phrases = _tokens_and_ngrams(normalized)
    keywords = _load_keywords(data_dir)
    mappings = _load_mappings(data_dir)
    loading_warnings: list[str] = []
    if not keywords:
        loading_warnings.append("keywords_missing_or_invalid")
    if not mappings:
        loading_warnings.append("mappings_missing_or_invalid")

    matched, taxonomy_signals, cell_signals, suggested_tags = _extract_signals(
        phrases,
        keywords,
        mappings,
    )
    top3 = _score_taxonomy(taxonomy_signals, mappings, phrases)
    top_taxonomy = top3[0][0]

    cell_guess, backup_cell_guess, cell_reasons = _score_cell(
        cell_signals,
        mappings,
        phrases,
        top_taxonomy,
    )

    legal, evidence, stale = _common_contracts(app_data)

    candidates: list[ClassifyCandidate] = []
    for taxonomy_id, score, reasons in top3:
        candidates.append(
            ClassifyCandidate(
                taxonomy_id=taxonomy_id,
                taxonomy_label=taxonomy_id.replace("_", " ").title(),
                cell_guess=cell_guess,
                score=round(float(score), 4),
                reasons=list(reasons[:6]),
                legal=legal,
                evidence=evidence,
                staleness=stale,
                sample_variants=_sample_variants(app_data, taxonomy_id, cell_guess),
            )
        )

    top1 = candidates[0].score if candidates else 0.0
    top2 = candidates[1].score if len(candidates) > 1 else -999.0
    confidence = 0.95 if (top1 - top2) >= 1.0 else 0.6
    ambiguity = "ambiguous" if (top1 - top2) < 1.0 else "clear"

    explanation: list[str] = []
    if matched:
        explanation.append(f"Matched keywords: {', '.join(matched[:6])}")
    explanation.append(f"Top taxonomy: {top_taxonomy}")
    explanation.extend(cell_reasons[:3])
    if ambiguity == "ambiguous":
        explanation.append("Top-1 and Top-2 scores are close; clarification is recommended")
    explanation.extend(loading_warnings)

    return ClassifyResultV1(
        idea_text=idea_text,
        top3=candidates,
        cell_guess=cell_guess,
        backup_cell_guess=backup_cell_guess,
        matched_keywords=matched,
        suggested_tags=suggested_tags,
        reasons=explanation[:6],
        confidence=round(confidence, 4),
        ambiguity=ambiguity,
        legal=legal,
        evidence=evidence,
        staleness=stale,
    )
