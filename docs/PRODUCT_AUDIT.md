# QOR product audit

> Earlier pre-redesign audit. See [current QA](QA_REPORT.md) and
> [criteria matrix](CRITERIA_MATRIX.md) for the Python 3.12 / Russian UI result.

Audited on 23 September 2026 against the repository, the running Streamlit app,
the local IEK archive, and automated UI and calculation tests. The product entry
point is `frontend/app.py`; its routes are `/` (overview) and `/workspace`.
The older root `app.py` and `qor/` package are preserved legacy code, not the
current deployment path. The screenshot of an earlier scaffold was contextual;
the current running app and code were inspected directly.

Status means **WORKING** when the action runs in the current app, **PARTIAL**
when the mechanism runs but a required real input or interpretation is absent,
**PLACEHOLDER** when no feature is implemented, and **BLOCKED** when it cannot
operate until an external resource is supplied. A passed synthetic test proves
the code path, not the availability of supplier facts.

| Capability | Status | Source / route | Test performed | User-visible limit | Next action |
|---|---|---|---|---|---|
| Excel and ZIP import | PARTIAL | `backend/qor/data/ingestion.py`; `/workspace` → Data | Real `Downloads/IEK.zip` import in `scripts/smoke_real_ui.py`; importer tests | IEK read successfully; actual Systeme Electric archive absent, so its format is not validated | Obtain SE files and run source audit |
| Source and monthly reconciliation | WORKING | `data.reconcile`; Data | Real IEK reconciliation and duplicate-join tests | Conflicting monthly and transaction totals are shown, not resolved automatically | Manager investigates material differences |
| Missing, zero and returns | WORKING | `data._audit`, `demand.clean_demand`; Data/Demand | Import and forecast tests | Missing periods cannot establish stockout or zero demand | Provide evidence for gaps |
| Large-sale anomalies | WORKING | `demand.clean_demand`; Demand | Injected large-purchase, split-document and dated-review tests | Candidates remain in demand until a manager records a decision; no real customer ID is inferred | Review candidates with evidence |
| Seasonality and baseline | WORKING | `demand.forecast_demand`, `evaluate`; Demand/Orders | Rolling-origin tests and real IEK SKU evaluation | Historical error is high for the audited SKU; no production accuracy guarantee | Compare methods by supplier and unit |
| Growth | PARTIAL | `Policy.growth_mode`, `forecast_month`; Orders | Growth-once test | File-provided growth is not automatically validated from a trusted source; manual fraction is an assumption | Confirm source and period before use |
| Confirmed lost-demand adjustment | PARTIAL | `Stockout`, `compensate_stockouts`; Demand | Confirmed-date and overlap tests | No real confirmed stockout intervals were supplied | Enter evidenced interval or keep adjustment off |
| Dated inbound and projected stock | WORKING | `data.load_sources`, `planning.project_inventory`; Orders/Scenarios | Real IEK ETA fields plus late/same-day/unknown ETA tests | ETA is expected, not guaranteed; IEK current available stock is missing | Confirm receipt dates and dated stock |
| MOQ and pack multiple | PARTIAL | `planning.recommend_order`; Orders | MOQ/multiple rounding and unit tests | IEK dispatch field is ambiguous; pack multiple may be absent | Manager selects interpretation and verifies units |
| Supplier-grouped draft orders | PARTIAL | `service.calculate_plan`, `Repository.create`; Orders | Synthetic SE end-to-end UI, real IEK missing-stock gate | Real IEK needs current dated stock; real SE import unavailable | Provide those inputs before an actual order |
| Quantity edits and reason | WORKING | `Repository.edit`; Orders | Version reset and reason tests | Actor is a local audit label, not an authenticated identity | Add authentication before wider deployment |
| Review and approval | WORKING | `Repository.transition`; Orders | Synthetic draft → review → approved UI test | Only local single-user controls are present | Keep purchasing manager responsible |
| CSV/XLSX export | WORKING | `Repository.export`; Orders | Synthetic export reopened and compared in tests | Export is blocked for incomplete or unapproved runs | Review source and policy first |
| SQLite revisions and audit | WORKING | `storage/repository.py`; Orders | Restart, stale-version and audit tests | Local DB is not encrypted or multi-user permissioned | Add governance for production |
| Hackathon-provided AI model | BLOCKED | `ai/PendingProvider`; workspace status | Provider raises explicit blocked error; `model_probe.py` stopped before networking | No participant endpoint, authorized model ID, credential or checkpoint was found | Supply organizer access; then install documented runtime and run live text/tool probes |

No active capability is called a placeholder on the landing page. `PendingProvider`
is intentionally a blocked adapter. The deterministic local `ToolRouter` has
four bounded operations but has no verified model connection.

## Verified source and performance facts

The IEK archive at `C:\Users\Kuralai\Downloads\IEK.zip` has SHA-256
`fed312f909943e69b17d2cc5dd577123b5fe0874064558e8f503deaf9fc50054`.
The prior read-only audit counted 171,603 transactions, 81,279 monthly sales
cells/rows, 306 inbound shipment lines and 1,937 purchase-rule rows. The same
archive was present with the same hash at this audit. Real IEK UI smoke exercises
import, Demand evaluation, missing-stock Orders gate and 7/14/30 scenarios.
The 249,000-row timing in `docs/IMPLEMENTATION_VERIFICATION.md` is for generated
CSV import only, not whole-supplier forecasting.

The real IEK SKU `200400085_` requires current stock input before an order is
recommended. The documented 1,547.27 m calculation uses a **hypothetical zero
stock** and factor-one purchase-unit assumption. The real file did not prove
either. The six-origin WAPE reported for that SKU was 62.21% for the three-month
mean and 76.29% for the seasonal method, not a production guarantee. The 22.39%
exploratory value in an earlier plan is not used as a product claim.

The actual Systeme Electric archive, original case DOCX/rules PDF,
`HackAlem_Logistics_Analysis_KZ.md` and participant AI access instructions were
not found in the searched project/Downloads paths. Existing
`HackAlem_Execution_Plan_KZ.md` and `QOR_MVP_Model_Prompts_EN.md` were reviewed.
The absence statement is limited to those searched locations.

## Visual and interaction checks

Desktop 1440 px and mobile 390 px screenshots were taken from the running app.
Native Streamlit links and controls provide keyboard operation and focus states;
the landing example updates when lead time changes; the workspace link opens
the registered route. The generated files are kept under ignored `runtime/`:
`landing-desktop.png` and `landing-mobile.png`. See
[design tokens and responsive rules](DESIGN_SYSTEM.md).
