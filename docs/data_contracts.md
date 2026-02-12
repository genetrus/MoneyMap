# Data Contracts (MVP)

Документ фиксирует обязательные поля, типы и правила валидации для контрактов данных:
- `Variant`
- `RuleCheck`
- `OccupationMap`

> Основание: требования к data contracts / YAML-данным и сущностям MVP. См. `Money_Map_Spec_Packet.pdf` (p.6–7, p.9–10) и `Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf` (p.2).

---

## 1) Contract: `Variant`

### Поля и типы

| Поле | Тип | Обяз. | Описание |
|---|---|---:|---|
| `id` | `string` | Да | Уникальный идентификатор варианта (`^[a-z0-9._-]+$`). |
| `title` | `string` | Да | Короткий заголовок варианта. |
| `summary` | `string` | Да | Краткое описание сути варианта. |
| `cell_id` | `string` | Да | Ячейка матрицы, например `A1`, `A2`, `B1`, `B2`. |
| `taxonomy_id` | `string` | Да | Идентификатор таксономии монетизации (snake_case). |
| `tags` | `list[string]` | Да | Набор тегов варианта (может быть пустым списком). |
| `feasibility` | `object` | Да | Ограничения/пороговые условия выполнимости. |
| `legal` | `object` | Да | Юридические условия/гейт и чек-лист. |
| `economics` | `object` | Да | Базовые экономические диапазоны и уверенность. |
| `evidence` | `object` | Да | Источники/дата ревью/уверенность в данных. |
| `next_steps` | `list[string]` | Да | Следующие шаги (actionable). |

### Минимальные под-поля (рекомендуемый минимум)

- `feasibility`:
  - `min_language_level: string` (напр. `A2`, `B1`, `B2`)
  - `min_capital_eur: integer >= 0`
  - `min_time_per_week_hours: integer >= 0`
  - `required_assets: list[string]`

- `legal`:
  - `gate: string` (`ok | require_check | registration | license | blocked`)
  - `checklist: list[string]`
  - `required_docs: list[string]` *(опционально, но рекомендовано)*

- `economics`:
  - `time_to_first_money_days_range: [int, int]`
  - `typical_net_month_eur_range: [int, int]`
  - `costs_eur_range: [int, int]`
  - `confidence: string` (`low | medium | high`)

- `evidence`:
  - `reviewed_at: string` (ISO date `YYYY-MM-DD`)
  - `sources: list[string]` (URL/идентификаторы источников)
  - `note: string` *(опционально)*

### Пример валидного YAML (`Variant`)

```yaml
id: "de.remote.translation"
title: "Translation mini-projects"
summary: "Translate short documents for local NGOs and small firms."
cell_id: "A2"
taxonomy_id: "service_fee"
tags: ["remote", "writing", "language"]
feasibility:
  min_language_level: "B2"
  min_capital_eur: 120
  min_time_per_week_hours: 8
  required_assets: ["laptop", "internet"]
legal:
  gate: "ok"
  checklist:
    - "Confirm invoicing requirements"
  required_docs: ["ID"]
economics:
  time_to_first_money_days_range: [10, 25]
  typical_net_month_eur_range: [500, 1100]
  costs_eur_range: [30, 90]
  confidence: "medium"
evidence:
  reviewed_at: "2026-01-01"
  sources:
    - "https://example.org/freelance-rates"
  note: "Initial desk research"
next_steps:
  - "Assemble translation samples (2h)"
  - "Build glossary template (1h)"
```

---

## 2) Contract: `RuleCheck`

### Поля и типы

| Поле | Тип | Обяз. | Описание |
|---|---|---:|---|
| `id` | `string` | Да | Уникальный id правила (`^[a-z0-9._-]+$`). |
| `scope` | `string` | Да | Область действия: `global`, `country`, `taxonomy`, `variant`. |
| `triggers` | `list[string]` | Да | События/условия запуска проверки. |
| `applies_to` | `object` | Да | Фильтры применимости (по стране/таксономии/cell/tags). |
| `severity` | `string` | Да | `info | warn | error | blocker`. |
| `steps` | `list[string]` | Да | Шаги проверки/исполнения правила. |
| `docs` | `list[string]` | Да | Обязательные документы/артефакты для проверки. |
| `links` | `list[string]` | Нет | Ссылки на внешние нормы/инструкции. |
| `reviewed_at` | `string` | Да | Дата последнего ревью правила (ISO date). |
| `sources` | `list[string]` | Да | Источники для правила (URL/референсы). |

### Пример валидного YAML (`RuleCheck`)

```yaml
id: "de.legal.regulated.require_check_if_stale"
scope: "country"
triggers:
  - "variant_selected"
  - "rulepack_stale"
applies_to:
  country: "DE"
  tags_any: ["regulated"]
  taxonomy_ids: ["labor", "commission"]
severity: "error"
steps:
  - "Verify whether activity requires registration or license"
  - "Check most recent municipal and federal guidance"
docs:
  - "ID"
  - "Address registration"
  - "Background check"
links:
  - "https://example.org/de-regulatory-guidance"
reviewed_at: "2026-01-01"
sources:
  - "rulepack:DE:2026-01-01"
  - "https://example.org/de-regulatory-guidance"
```

---

## 3) Contract: `OccupationMap`

`OccupationMap` связывает признаки входного профиля/описания с назначением целевых полей классификации.

### Структура

| Поле | Тип | Обяз. | Описание |
|---|---|---:|---|
| `id` | `string` | Да | Уникальный id mapping-правила. |
| `match` | `object` | Да | Условия совпадения (`match-условия`). |
| `assign` | `object` | Да | Значения, назначаемые при совпадении (`assign-поля`). |
| `priority` | `integer` | Нет | Приоритет применения (выше = раньше). |
| `active` | `boolean` | Нет | Флаг активности правила. По умолчанию `true`. |

### `match`-условия (поддерживаемые ключи)

| Ключ | Тип | Обяз. | Семантика |
|---|---|---:|---|
| `occupation_codes_any` | `list[string]` | Нет | Совпадение по любому коду профессии. |
| `keywords_any` | `list[string]` | Нет | Совпадение по любому ключевому слову. |
| `keywords_all` | `list[string]` | Нет | Должны совпасть все ключевые слова. |
| `country_in` | `list[string]` | Нет | Ограничение по стране(ам). |
| `language_level_gte` | `string` | Нет | Минимальный языковой уровень для срабатывания. |

> Минимум одно условие внутри `match` обязательно.

### `assign`-поля (поддерживаемые ключи)

| Ключ | Тип | Обяз. | Семантика |
|---|---|---:|---|
| `taxonomy_id` | `string` | Нет | Назначаемая таксономия монетизации. |
| `cell_id` | `string` | Нет | Назначаемая ячейка матрицы. |
| `tags_add` | `list[string]` | Нет | Теги для добавления. |
| `confidence` | `number` | Нет | Уверенность маппинга (`0..1`). |
| `reason` | `string` | Нет | Объяснение, почему применено назначение. |

> Минимум одно поле внутри `assign` обязательно.

### Пример валидного YAML (`OccupationMap`)

```yaml
id: "map.de.translation_to_service_fee"
match:
  occupation_codes_any: ["2643", "NACE_M74.30"]
  keywords_any: ["translator", "translation", "localization"]
  country_in: ["DE"]
assign:
  taxonomy_id: "service_fee"
  cell_id: "A2"
  tags_add: ["remote", "writing", "language"]
  confidence: 0.84
  reason: "Language-service occupations typically map to remote service_fee in MVP"
priority: 90
active: true
```

---

## 4) Общие правила валидации

### Обязательные поля

- Для `Variant`: обязательны **все** перечисленные поля (`id`, `title`, `summary`, `cell_id`, `taxonomy_id`, `tags`, `feasibility`, `legal`, `economics`, `evidence`, `next_steps`).
- Для `RuleCheck`: обязательны `id`, `scope`, `triggers`, `applies_to`, `severity`, `steps`, `docs`, `reviewed_at`, `sources`; `links` — опционально.
- Для `OccupationMap`: обязательны `id`, `match`, `assign`; `priority`, `active` — опционально.

### Форматные правила

- Все `id` должны быть уникальными в рамках своего набора.
- Поля-списки (`tags`, `triggers`, `steps`, `docs`, `sources` и т.п.) должны быть YAML-массивами.
- `reviewed_at` — дата в формате `YYYY-MM-DD`.
- Для диапазонов вида `[min, max]`: оба значения целые, `min <= max`.
- Для `confidence` в `OccupationMap.assign`: число в диапазоне `0..1`.
- Для `Variant.next_steps`: как минимум 1 шаг.
- Для `OccupationMap.match`: задан хотя бы 1 ключ-условие.
- Для `OccupationMap.assign`: задан хотя бы 1 ключ назначения.

### Семантические правила

- `Variant.cell_id` должен принадлежать допустимому набору ячеек матрицы проекта.
- `Variant.taxonomy_id` должен существовать в таксономии данных проекта.
- `RuleCheck.applies_to` должен быть согласован с `scope` (например, при `scope=country` обязательно указывать страну).
- Если `RuleCheck.severity=blocker`, в `steps` должен быть явный шаг остановки/эскалации.
