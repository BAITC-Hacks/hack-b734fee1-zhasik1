# Active QOR interfaces

The package imported by `frontend/app.py` is `backend/qor/`. The root
`qor/` remains legacy code and is not the active contract.

| Function / object | Input → output |
|---|---|
| `data.load_sources(sources, supplier=None, snapshot=SNAPSHOT)` | Paths or `(name, bytes, supplier)` tuples → audited `Bundle` |
| `data.reconcile(bundle)` | Bundle → SKU-month disagreements |
| `demand.clean_demand(events, decisions=(), as_of=None)` | Transactions → source, reviewed and capped forecast quantities |
| `demand.forecast_demand(events, snapshot, days, policy, decisions, stockouts, monthly, method)` | Completed history → daily demand and assumptions |
| `demand.challenger.make_panel(bundle, horizon_days, max_skus)` | Audited bundle → causal SKU-origin experiment rows |
| `demand.challenger.evaluate_panel(panel)` | Chronological group refits → predictions and method selection metrics |
| `demand.selection.select_forecast_method(bundle, events, monthly, policy)` | Matching offline JSON evidence → selected baseline or labeled fallback |
| `planning.recommend_order(...)` | Dated stock, daily demand, inbound, MOQ and pack → explained row |
| `service.calculate_plan(bundle, policy, *, keys, stock_inputs, decisions, stockouts)` | Shared order calculation → supplier/SKU rows |
| `storage.Repository(path)` | SQLite runs, input evidence, versions, review, approval and reopened export |

`Policy`, `StockInput`, `Stockout`, `OutlierDecision` and `ToolRequest`
are Pydantic 2 contracts. `None` means absent, and zero is explicit. The
source key is supplier + textual SKU; unit mismatches block a row. Purchase
MOQ and pack multiple are separate inputs. A dated current stock is required
for an actionable order; historical IEK monthly stock cannot replace it.

The workflow is import → demand → forecast → dated planning → persisted
draft → reasoned edit → manager review → approval → verified CSV/XLSX export.
An edit returns the run to draft. Export reads the latest approved version.
No supplier transmission exists. `qor.ai.ToolRouter` exposes only
`inspect_data`, `calculate_plan`, `simulate_policy` and `explain_sku`;
the model provider is unverified and has no write/approval/dispatch tool.
