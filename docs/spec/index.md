# MoneyMap — Specification Index

## Source of Truth
- Единственный источник требований: `docs/spec/source/*.pdf`.
- Этот `index.md` — навигация по PDF и правила использования.
- Любые другие документы/README — вторичны и должны соответствовать PDF.

## Spec Files
- `docs/spec/source/Money_Map_Spec_Packet.pdf`
  - Назначение: основной пакет требований (цели, MVP, функции/контракты, UX, данные, NFR, архитектура, план релиза, DoD).
  - Ключевые разделы/страницы: One-pager (p.3), Use cases (p.4), MVP boundaries (p.5), Features/contracts (p.6–7), UX (p.8), Data (p.9–10), NFR (p.11), Architecture (p.12), Release plan (p.13), DoD/tests (p.14), Appendix/Patch Pack (p.15).
  - Заметки: закрепляет offline-first, YAML/JSON, Streamlit UI и Typer CLI как обязательные для MVP.
- `docs/spec/source/Блок-схема_старт_разработки_A4_FINAL_v3.pdf`
  - Назначение: чеклист готовности старта разработки и Release 0.1 (бриеф, quality gates, CI, walking skeleton, hardening).
  - Ключевые разделы/страницы: Release 0.1 brief и MVP flows; quality gates/CI; walking skeleton; backlog/Hardening (p.1).
  - Заметки: использовать как контрольный список перед стартом и в процессе релиза.
- `docs/spec/source/Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf`
  - Назначение: требования к данным и план их сбора/подготовки.
  - Ключевые разделы/страницы: Full Data Requirements (inventory, классификация, data dictionary, ER, producer/consumer, policies) (p.1); Data Sourcing & Collection Plan (источники, каналы, seed/fixture packs, data contracts, gate) (p.2).
  - Заметки: определяет артефакты data-inventory и data contracts для CI.

## UI Specs
- `docs/spec/ui/data_status.md`

## How we develop
- Перед любой задачей: открыть `index.md` и релевантные PDF.
- Если есть конфликт: PDF всегда правее любых других документов.
- Если нужно допущение: записать в `docs/DECISIONS.md` (с датой и причиной, с указанием PDF+страницы).

## Optional parsed text
- `docs/spec/parsed/*.md` — необязательная текстовая копия для поиска, но PDF главнее.
