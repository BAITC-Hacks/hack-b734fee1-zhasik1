# QOR interfaces (Stage 1)

> Historical planned signatures below are not the current API contract.
> Current implementations: `backend/qor/contracts.py`, `service.calculate_plan`,
> `data.load_sources`, `demand.forecast_demand`, `planning.recommend_order`,
> `storage.Repository`. See README and the current verification report.

## Input and output contracts

The canonical Pydantic shapes live in `qor/contracts.py`. Every number carries
the distinction between actual, calculated, assumed, synthetic, and missing.
`None` represents missing; zero is an explicit value.

Public implementation signatures are intentionally stable:

```text
load_sources(paths) -> source bundle
normalize_supplier(raw, supplier) -> normalized tables
clean_demand(events) -> attributable cleaned history
forecast_demand(cleaned, scenario) -> ForecastResult[]
project_inventory(...) -> dated projection
recommend_order(...) -> OrderRecommendation
explain_row(recommendation) -> calculation breakdown
```

## AI provider boundary

The provider interface exposes declared capabilities rather than assuming
OpenAI. It must state responses/tool/structured output availability, timeouts,
tool-call limit, provider name, and verification status. Calls can request only
`inspect_data`, `calculate_plan`, `simulate_policy`, `explain_sku`, and
`build_order_draft`; results are validated and reconciled to Python outputs.

## Draft state machine

```text
draft -> review -> approved -> exported
          ^          |
          |----------| (manager correction creates a new version)
```

Only a responsible manager can move a draft to review or approve it. Export
requires `approved`; export never dispatches to a supplier. Each transition
records the run ID, manager, reason where applicable, timestamp, and version.
