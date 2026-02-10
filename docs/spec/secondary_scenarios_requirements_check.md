# Сверка требований: второстепенные сценарии Explore и Classify

Дата сверки: 2026-02-10.

## 1) Что считалось источником требований

1. `docs/spec/index.md` — использован только как навигация к PDF и страницам.
2. `docs/spec/source/Money_Map_Spec_Packet.pdf` — основной источник требований по сценариям и MVP-границам.
3. `docs/spec/source/Блок-схема_старт_разработки_A4_FINAL_v3.pdf` — контроль release-gates (walking skeleton, CI, quality gates).
4. `docs/spec/source/Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf` — требования к данным и воспроизводимости пайплайна.

## 2) Релевантные фрагменты спецификации (по PDF)

### Money_Map_Spec_Packet.pdf
- p.4: вторичные сценарии включают
  - A) исследование карты (по механизму/ячейке/тегам, просмотр мостов/маршрутов),
  - B) классификацию идеи (текст -> 3 кандидата taxonomy + cell + объяснения).
- p.5 (MoSCoW):
  - MUST: offline-first, validate, recommend (objective presets), feasibility/economics/legal, plan, export, Streamlit UI.
  - SHOULD: guided flow, compare, presets, HTML graph taxonomy, расширение вариантов.
  - COULD: более богатая классификация.
- p.6-7: обязательные контракты рекомендаций + реальные ограничения (feasibility/economics/legal/staleness), детерминизм, ranges-only, force require_check при устаревшем legal/rulepack для regulated domains.
- p.8 (UX): Explore помечен как SHOULD-экран: matrix/taxonomy graph/bridges/paths (browse).
- p.11: NFR offline + staleness warning policy.
- p.14: DoD включает детерминизм и staleness behavior.

### Блок-схема_старт_разработки_A4_FINAL_v3.pdf (p.1)
- Для релиза обязателен проход quality gates, CI и сквозного сценария (walking skeleton -> интеграционный/smoke -> MVP flow).

### Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf (p.1-2)
- Обязательны инвентарь/словарь данных, producer-consumer matrix, data quality checks.
- Сбор данных должен быть воспроизводимым (один и тот же процесс -> те же данные), плюс contract tests в CI.

## 3) MUST/SHOULD для MVP (фокус: Explore + Classify + real-world rules)

### MUST (MVP)
1. **Offline-first и локальные данные**: сценарии не должны зависеть от сети.
2. **Детерминизм результатов**: одинаковые входы -> одинаковые результаты (включая stable tie-breaks в ranking-контрактах).
3. **Real-world слой в выдаче**: feasibility + economics + legal/compliance + staleness behavior.
4. **Без обещаний дохода / только диапазоны**: money/time выводятся как ranges, не гарантии.
5. **Staleness safety**: предупреждения при stale и усиление осторожности legal gate для регулируемых доменов.

### SHOULD (для MVP scope сценариев)
1. **Explore/Browse экран** как отдельный исследовательский режим с элементами карты:
   matrix + taxonomy graph + bridges/paths.
2. **Поясняющий UX** (browse-first): экран Explore помогает изучить пространство перед выбором.

### COULD (в контексте Classify)
1. **Более богатая классификация** (в MoSCoW помечено как COULD), т.е. усложнение engine/UX классификации после базового уровня.

## 4) Практический вывод по двум второстепенным сценариям

- **Explore**: в MVP трактуется как **SHOULD-функциональность UI**, но при наличии должна соблюдать MUST-ограничения (offline, staleness/legal safety, no-income-promises, deterministic behavior where ranking/filtering applies).
- **Classify Idea**: как use-case зафиксирован в пакете; при этом именно "богатая" версия классификации относится к COULD. Для MVP минимально допустима базовая/объяснимая классификация без противоречия MUST-блокам.

## 5) Чеклист сверки (для дальнейшей реализации)

- [ ] Explore не нарушает offline-first.
- [ ] Explore/filters/routing не ломают детерминизм при одинаковом input.
- [ ] Classify возвращает top-кандидаты с объяснением и не дает обещаний дохода.
- [ ] Любые legal hints в Explore/Classify учитывают staleness policy.
- [ ] Для расширения классификации зафиксирован отдельный backlog как COULD/после MVP.
