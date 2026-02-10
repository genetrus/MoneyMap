# Аудит текущей реализации: второстепенные сценарии Explore / Classify

Дата: 2026-02-10.

## 1) Цель аудита

Проверить фактическую реализацию UI/навигации относительно требований по второстепенным сценариям:
- Explore (browse mode);
- Classify Idea (текст -> taxonomy/cell + explanation);
- состояния UI (loading, ready, invalid_data, stale_warning, empty_view, ambiguous и т.д.);
- переходы в Recommendations.

## 2) Что реально есть в коде сейчас

### 2.1 Навигация и экраны
В `NAV_ITEMS` доступны только страницы:
- Data status
- Profile
- Recommendations
- Plan
- Export

Отдельных страниц/вкладок `Explore` и `Classify` в текущей навигации нет.

### 2.2 Recommendations: фильтры и действия
На экране Recommendations есть:
- objective preset (`fastest_money`, `max_net`);
- фильтры: `max_time_to_money_days`, `exclude_blocked`, `exclude_not_feasible`;
- quick fixes: `Allow not feasible`, `Allow blocked`, `Extend time window`, `Startable in 2 weeks`, `Focus on fastest money`, `Reduce legal friction`;
- выбор варианта (`Select {variant_id}`) для перехода в Plan/Export через состояние `selected_variant_id`.

### 2.3 Валидация/статус данных
Есть полноценный экран Data status с `valid/invalid/stale` и деталями warn/fatal/staleness.
Критические fatals блокируют Recommendations/Plan/Export через `_guard_fatals`.

## 3) Сопоставление требуемых UI-состояний с фактическими

## 3.1 Explore
Требуемые состояния (по задаче): `loading`, `ready`, `invalid_data`, `stale_warning`, `empty_view`.

Фактически:
- `Explore` как страница отсутствует.
- Частичное покрытие аналогичных состояний есть косвенно в Data status / Recommendations:
  - `invalid_data` -> есть блокировка действий через validation fatals;
  - `stale_warning` -> есть предупреждение stale в Data status и warnings на карточках рекомендаций;
  - `empty_view` -> есть в Recommendations как `No results found`.
- `loading`/`ready` именно для Explore-данных (matrix/taxonomy/bridges/paths) отсутствуют.

Итог: состояние Explore не реализовано (0/5 прямого покрытия).

## 3.2 Classify
Требуемые состояния: `draft`, `loading`, `results`, `ambiguous`, `error`.

Фактически:
- Экран/пайплайн Classify отсутствует.
- Нет text input для идеи, нет top-3 taxonomy+cell, нет explanation/ambiguous/next actions.

Итог: состояние Classify не реализовано (0/5).

## 4) Переходы в Recommendations

### Что реализовано
- Основной переход внутри текущего flow: `Profile -> Recommendations`.
- Из Recommendations можно выбрать вариант для `Plan` и далее `Export`.

### Что отсутствует (относительно вторичных сценариев)
- Нет переходов:
  - `Explore -> Recommendations` с предзаполненными фильтрами/taxonomy/cell;
  - `Classify -> Recommendations` с предфильтрацией по выбранному кандидату;
  - `Classify -> Explore` (taxonomy detail + cell highlight).

## 5) GAP-list (приоритизировано)

### P0 (блокирующие для полного покрытия вторичных сценариев)
1. Нет UI-экрана Explore и его вкладок (Matrix/Taxonomy/Bridges; Paths/Library опционально).
2. Нет UI-экрана Classify (input/pipeline/results/ambiguous).
3. Нет переходов Explore/Classify -> Recommendations с сохранением контекста (prefilter).

### P1 (важные для корректного UX состояния)
4. Нет явной state-модели для Explore: `loading/ready/invalid_data/stale_warning/empty_view`.
5. Нет state-модели Classify: `draft/loading/results/ambiguous/error`.
6. Нет explainability-блока для классификации (matched signals/reasons).

### P2 (улучшения после базового внедрения)
7. Нет Mini-Variant Cards в Classify как bridge к Recommendations.
8. Нет явного browse-first summary в Explore (cell/taxonomy/bridge summaries).

## 6) Краткий вывод

Текущая реализация хорошо закрывает основной MVP-поток `Data status -> Profile -> Recommendations -> Plan -> Export`, включая real-world ограничения (feasibility/economics/legal/staleness) и блокировку по validation fatals.

Однако оба второстепенных сценария (Explore и Classify) в коде на текущий момент отсутствуют как самостоятельные пользовательские потоки; требуется отдельная реализация экранов, state-моделей и переходов в Recommendations.
