# Stage 15 — UI Audit & Mapping to UX Spec v1 (Этап 1)

## Цель этапа
Провести инвентаризацию текущего Streamlit UI и сопоставить его с целевой структурой UX Spec v1 по ключевым блокам:
- App Shell
- Context Bar
- Detail Drawer
- Explore subviews
- Recommendations / Plan / Export

## Что проверено
- `src/money_map/ui/app.py`
- `src/money_map/ui/navigation.py`
- `src/money_map/ui/view_mode.py`
- `src/money_map/ui/data_status.py`
- `src/money_map/ui/variant_card.py`
- UI-smoke и навигационные тесты в `tests/`

## Итоговый статус соответствия (кратко)
- **Есть базовый каркас UI:** sidebar-навигация, page header, view mode toggle, stateful flow между страницами.
- **Частично реализовано:** Explore tabs (Matrix/Taxonomy/Bridges), Recommendations с quick fixes, Plan/Export базового уровня.
- **Отсутствует/неполно:** единый `ContextBar`, универсальный `DetailDrawer`, единый selection state для всех сущностей, graph fallback layer (interactive→graphviz→table), расширенные Explore subviews (routes/library), стандартизированные cross-links из любой сущности.

---

## Mapping: текущая реализация vs UX Spec v1

### 1) App Shell

| Требование UX Spec v1 | Текущее состояние | Статус |
|---|---|---|
| Sidebar с основными разделами | Есть `radio`-навигация в sidebar, страницы: data-status/profile/explore/classify/recommendations/plan/export | ✅ Частично (есть extra `classify`, нет фиксации/контрактного SidebarNav-компонента) |
| Header bar с country/dataset/staleness/view mode | Есть page header + отдельные KPI/бейджи и `view_mode` control; единая строка хедера с постоянными badge-полями не унифицирована | ⚠️ Частично |
| Main content + правая панель деталей | Main content есть; отдельного постоянного drawer-компонента нет | ❌ |

### 2) Context Bar (always visible)

| Требование UX Spec v1 | Текущее состояние | Статус |
|---|---|---|
| Breadcrumbs page/subview/focus | Нет выделенного компонента breadcrumbs | ❌ |
| Pinned selections (cell/taxonomy/variant/bridge/path) | Есть точечные ключи state (`selected_variant_id`, explore-selected-*), но без единой закреплённой панели | ⚠️ Частично |
| Active filters summary | Есть controls на странице Recommendations, но нет global summary bar | ❌ |

### 3) Detail Drawer (entity inspector)

| Требование UX Spec v1 | Текущее состояние | Статус |
|---|---|---|
| Универсальный drawer для любой сущности | Нет общего компонента | ❌ |
| Cross-links: Open in Explore / Filter Recommendations / Build Plan | Частично встречаются action-кнопки/переключения (например выбор варианта, переходы), но нет унифицированного контракта для всех entity types | ⚠️ Частично |
| Dev details (id/raw/diagnostics) | Есть Developer mode и отдельные expanded блоки, но не в унифицированном drawer | ⚠️ Частично |

### 4) Explore subviews

| Требование UX Spec v1 | Текущее состояние | Статус |
|---|---|---|
| Matrix subview | Реализован tab Matrix, выбор cell и список variant cards | ✅ Базово |
| Taxonomy subview | Реализован tab Taxonomy, фильтр и вывод примеров | ✅ Базово |
| Bridges subview | Реализован tab Bridges, базовые preconditions/steps + variants | ✅ Базово |
| Paths subview | Есть feature-flag и placeholder (pending) | ⚠️ Частично |
| Library subview | Есть feature-flag и placeholder (pending) | ⚠️ Частично |
| Graph fallback (interactive→graphviz→table) | Нет общего слоя fallback-рендера графов | ❌ |

### 5) Recommendations

| Требование UX Spec v1 | Текущее состояние | Статус |
|---|---|---|
| Objective + Top-N + quick filters + recompute | Реализованы objective/top-N/filters + запуск recommendations | ✅ |
| Reality Check + quick fixes | Реализовано: блокеры/диагностика + quick-fix кнопки | ✅ |
| Card/table режимы | Карточный поток реализован, table-toggle как отдельный режим отсутствует/не унифицирован | ⚠️ Частично |
| Explainability (score contributions) | Есть причины/диагностика; унифицированного мини-графика вкладов факторов для каждой карточки пока нет | ⚠️ Частично |

### 6) Plan

| Требование UX Spec v1 | Текущее состояние | Статус |
|---|---|---|
| План на базе выбранного variant | Реализовано (генерация plan по selected variant) | ✅ |
| Вкладки Checklist / 4 weeks / Compliance | Отображается checklist/4-week/compliance контент, но не как структурированные UI tabs-компоненты по spec-контракту | ⚠️ Частично |
| Детали шага в правом drawer | Нет унифицированного drawer для step details | ❌ |

### 7) Export

| Требование UX Spec v1 | Текущее состояние | Статус |
|---|---|---|
| Артефакты plan.md/result.json/profile.yaml | Реализованы download-кнопки + генерация экспорта | ✅ |
| Metadata panel (dataset/reviewed/objective/profile_hash) | Частично: мета участвует в рендерах и отчетах, но отдельной унифицированной metadata panel нет | ⚠️ Частично |
| Воспроизводимость run command | Явного блока "Copy run command" нет | ❌ |

---

## Текущее покрытие целевых элементов (сводно)
- **Сильно реализовано уже сейчас:**
  - E2E skeleton страницы + переходы
  - recommendations runtime c empty-state quick fixes
  - базовый plan/export поток
- **Основные разрывы относительно UX Spec v1:**
  1. Нет общего слоя компонентов (`ContextBar`, `DetailDrawer`, `GraphView` fallback wrapper).
  2. Selection state не унифицирован по всем entity типам и не визуализируется глобально.
  3. Explore визуально пока list-first, а не graph-first с fallback.
  4. Нет единого cross-link контракта “from any entity to Explore/Recommendations/Plan”.

## Приоритизированный backlog для следующих этапов
1. **P0:** Ввести единый `session_state` контракт (meta/navigation/selection/filters/results).
2. **P0:** Добавить `ContextBar` (breadcrumbs + pinned selections + filters summary).
3. **P0:** Добавить `DetailDrawer` с entity-aware cross-links.
4. **P1:** Вынести Explore subviews в отдельные view-модули и подключить fallback strategy.
5. **P1:** Стандартизировать Recommendation card contracts + score contribution mini-bars.
6. **P1:** Довести Plan/Export до полного UX-контракта (tabs + metadata panel + reproducibility command).

## Проверка на соответствие этапу 1
Этап 1 выполнен: проведён аудит и сформирован mapping текущего UI к UX Spec v1 с выделением реализованного, частично реализованного и отсутствующего функционала.
