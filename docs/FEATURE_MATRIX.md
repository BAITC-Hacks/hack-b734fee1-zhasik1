# HackAlem requirement and evidence matrix

> Earlier detailed matrix. Current five-outcome release status:
> [CRITERIA_MATRIX.md](CRITERIA_MATRIX.md); current test and training evidence:
> [QA_REPORT.md](QA_REPORT.md).

Statuses refer to the current Streamlit entry point `frontend/app.py`. A code
path that works with generated data is not evidence that a missing real supplier
input exists. Detailed findings: [product audit](PRODUCT_AUDIT.md).

| Case requirement | Implementation | UI evidence | Test evidence | Status / remaining blocker |
|---|---|---|---|---|
| Sales, returns and missing values | `data.load_sources`, `_audit`, `demand.clean_demand` | Data source tables and warnings; Demand chart | `test_ingestion_audit.py`, `test_forecast_rules.py`; real IEK UI smoke | Working for real IEK; real SE archive not found |
| Current available stock and reservations | `StockInput`, `service.calculate_plan`, `planning.recommend_order` | Dated stock form; incomplete-order status | Missing vs zero, stale stock, reservation tests | Partial: dated current IEK stock absent |
| Goods in transit by delivery date | IEK inbound adapter, `project_inventory` | Orders daily timeline; Scenarios ETA delay | Late, same-day, unknown ETA tests; real IEK import | Working as planning estimate; ETA commitments unverified |
| Categories and differentiated policy | `Policy.category_buffers`, matching rule category | Orders policy form | Category-buffer test | Working on supplied raw codes; category meaning unverified |
| Sustained growth and optional source growth | Weighted recent level, prior-year `file_growth` applied once | Demand forecast; Orders growth mode | Growth-once and sustained-change tests | Partial: source growth fraction not confirmed |
| Seasonality and baseline accuracy | `seasonal_profile`, `forecast_month`, `evaluate` | Demand WAPE and signed bias; Orders method selector | Temporal evaluation and future-leakage tests; real IEK SKU evaluation | Working as an experiment; seasonal method worse on audited SKU, no guarantee |
| Lost demand during confirmed stockout | `Stockout`, `compensate_stockouts` | Demand evidence form; Scenarios hypothetical slider | Confirmation-date and overlap tests | Partial: no real interval evidence supplied |
| Isolated large/single-client sale | Causal document-level candidate; dated `OutlierDecision` | Demand candidate review and reason | Injected outlier, split-document and decision-date tests | Working candidate handling; real files lack anonymized customer ID, client branch synthetic only |
| Supplier-specific proposed quantity and reason | `service.calculate_plan`, `recommend_order`, `explain_row` | Orders row, source references, timeline | Planning rules and synthetic end-to-end UI | Partial operationally: real IEK stock missing and real SE file absent |
| Urgency and early shortage | Daily stock timeline and `expedite` status | Orders/Scenarios | Pre-lead shortage and late ETA tests | Working forecast label; not an observed stockout date |
| Manager edit, review, approval | `Repository.edit/transition` | Orders reason form and transition controls | `test_workflow.py`, `test_ui.py` | Working locally; audit names are not authenticated identities |
| Export after approval only | `Repository.export`, CSV/XLSX reopen comparison | Orders download appears after verified export | Export, formula-safety and UI tests | Working for approved complete drafts; no supplier dispatch |
| Deterministic calculation with bounded AI role | Python demand/planning; `ToolRouter` four operations | Live AI blocked notice | `test_ai.py` and router rejection test | Core working; model-backed calls blocked by missing participant entitlement |
| Two-supplier upload capability | Supplier-selectable import and common calculation service | Data upload selector | Canonical fixture tests, real IEK UI smoke | Partial validation: SE source archive not available |
| Original source and private data preservation | Read-only ZIP/XLSX adapter, Git excludes raw sources | Data source manifest | IEK SHA-256 before/after; import tests | Working for audited operations; do not publish private workbook |
| README, repo and demo | `README.md`, this matrix, architecture, demo script | Overview and workspace routes | 58 current automated tests; prior screenshots only, new pixel review unavailable | Delivered with listed source/model blockers |

The exploratory 22.39% WAPE from an earlier monthly-only plan is not a verified
production result and is not shown as such. The real audited IEK SKU has its own
rolling-origin metrics in [PRODUCT_AUDIT.md](PRODUCT_AUDIT.md).
