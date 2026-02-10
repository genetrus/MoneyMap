# DTO Contracts v1 (Explore / Classify / Plan)

Дата: 2026-02-10.

## Что зафиксировано

Контракты DTO зафиксированы в `src/money_map/core/model.py` и включают:

- `VariantCardV1`
- `MiniVariantCard`
- `ClassifyResultV1` (+ `ClassifyCandidate`)
- `PlanTemplateV1`

Для унификации добавлены общие контракты:

- `StalenessContract`
- `LegalContract`
- `EvidenceContract`

А также структурные подтипы:

- `FeasibilityFloorsContract`
- `EconomicsContract`
- `PlanStepV1`
- `PlanArtifactV1`

## Единый формат staleness/legal/evidence

### StalenessContract
Используется во всех новых DTO:
- `status` (`fresh|warn|hard|unknown`)
- `is_stale`
- `reviewed_at`
- `warn_after_days`
- `hard_after_days`
- `message`

### LegalContract
Используется во всех новых DTO:
- `gate` (`ok|require_check|registration|license|blocked`)
- `regulated_domain`
- `checklist`
- `compliance_kits`
- `requires_human_check`

### EvidenceContract
Используется во всех новых DTO:
- `reviewed_at`
- `source_refs`
- `note`
- `confidence`

## Примечание по применению

Это этап проектирования контрактов данных. Реализация маппинга этих DTO в UI/engine
(Explore/Classify/Plan rendering) выполняется отдельным этапом.
