# Current implementation and verified evidence — 2026-09-23

This report supersedes the earlier root-app scaffold/9-test reports without
deleting them. The implemented entry point is `frontend/app.py`; backend code
is in `backend/qor/`. Existing root `app.py`, root `qor/`, source archives,
analysis documents and prior reports were not moved or deleted.

## Scope and installed skills used

The latest attached brief requests the full implementation, replacing the
earlier scaffold-only scope. No extra skill copies or all-repository skill
downloads were needed. Existing skills shaped these controls:

- `demand-forecasting`: causal candidate review, seasonality and temporal backtests.
- `inventory-optimization`: dated availability, explicit buffer assumptions,
  separate MOQ/pack rules; no invented service-level or savings claims.
- `replenishment-strategy`: lead/review/buffer planning and supplier-specific drafts.
- `scenario-planning`: isolated lead-time, ETA and unknown-stockout sensitivities.
- `supply-chain-decision-to-delegation`: named manager ownership, bounded read-only
  calculation tools, explicit approval and no autonomous dispatch.
- `developing-with-streamlit`: installed-version documentation, conditional views,
  bounded caching, session state and AppTest verification.

The decision owner is the purchasing manager. Inputs and their provenance must
be inspectable; human approval is mandatory for export. Any inconsistent unit,
missing dated stock or unavailable demand is an approval blocker. The AI gate
is independent of the deterministic workflow and remains closed.

## Stage record: files and observed result

| Stage | Files changed/added | Verified result |
|---|---|---|
| 0 — participant access/source audit | `.env.example`, this report and clarification in `MODEL_ACCESS.md` | No project entitlement variables or documented participant resource found. Probe stopped before network; no live result or installed model SDK claimed. **Blocked.** |
| 1 — existing architecture/contracts | `pyproject.toml`, `.gitignore`, `backend/qor/contracts.py`, package `__init__.py` files | Editable install succeeded; backend import path verified from frontend; originals and legacy root code retained. |
| 2 — import/audit | `backend/qor/data/ingestion.py`, `data/demo.py`, `tests/test_ingestion_audit.py` | Real IEK import: 171,603 transactions; missing, return, text-SKU, overlapping totals, repeated-file and conflicting-lookup tests pass. ZIP SHA-256 unchanged. |
| 3 — demand/forecast | `backend/qor/demand/forecast.py`, `tests/test_demand.py`, `tests/test_forecast_rules.py` | Causal flags, human decisions, growth once, confirmed stockout, seasonal factors, partial month, future leakage and grouped metrics tested. Real single-SKU baseline outperformed seasonal: no improvement claim. |
| 4 — dated planning | `backend/qor/planning/engine.py`, `backend/qor/service.py`, `tests/test_planning_rules.py` | Late ETA, same-day receipts, shortages before lead, missing vs zero/stale stock, MOQ/pack/unit and scenario changes pass. Reference raw 100 → multiple-24 order 120. |
| 5 — manager UI and persistence | `frontend/app.py`, `frontend/components/views.py`, `backend/qor/storage/repository.py`, `tests/test_workflow.py`, `tests/test_ui.py` | Four views work; reasoned edit creates new version; review/approval required; reopened CSV/XLSX match; approver retained across re-export; stale revisions rejected. |
| 6 — AI boundary | `backend/qor/ai/provider.py`, `tests/test_ai.py`, workflow router tests | Only four named operations; writes/invalid inputs/call-limit violations rejected. **Actual model + function-call round trip blocked by Stage 0.** |
| 7 — scenarios and private evidence | `scripts/verify_project.py`, `scripts/smoke_real_ui.py`, UI views | Real IEK UI import/evaluation/missing-stock/7–14–30 paths pass; source unchanged; hypothetical stock trace and exports verified separately, not an actual order. |
| 8 — integrated delivery | `README.md`, this report, historical-doc pointers | 54 tests pass, editable install and pip consistency pass, server runs on localhost:8507; HTTP page/health 200; actual UI execution verified with AppTest, not HTTP alone. |

The requested real-SE-first vertical slice could not be performed because the
SE archive was not found. A fully labeled synthetic SE slice was implemented
and tested; a real IEK demand trace was then verified. This is an explicit
external-data deviation, not a claim that synthetic SE was the original file.

## Source inventory and preservation

Search scope: workspace, Desktop, Documents, Downloads, Codex attachments and
relevant filename searches in the user profile. No unrelated private account
sign-in or third-party project credentials were used.

Found: `C:\Users\Kuralai\Downloads\IEK.zip` (10,334,256 bytes). SHA-256 before
and after verification:

`fed312f909943e69b17d2cc5dd577123b5fe0874064558e8f503deaf9fc50054`

| Imported IEK table | Rows | Interpretation |
|---|---:|---|
| Transactions | 171,603 | 171,470 positive sales, 115 returns, 18 missing quantities |
| Monthly sales | 81,279 | Month cells incl. blanks, not added to overlapping transactions |
| Current available stock | 0 | Missing; monthly balances cannot replace it |
| Pending shipment lines | 306 | ETA headers read, not guaranteed delivery commitments |
| Purchase rules | 1,937 | Ambiguous dispatch minimum/multiple requires manager choice |
| Historical monthly stock | 94,149 | Historical opening balances only |

Two numeric-SKU warnings are visible: original leading zeroes cannot be
reconstructed. The IEK seasonality sheet is an unverified reference, not an
automatically trusted multiplier. Reconciliation produced 81,331 rows.

Not found: actual Systeme Electric archive/workbook, original Elektrokomplekt
case DOCX, participation-rules PDF, `HackAlem_Logistics_Analysis_KZ.md`, organizer
model endpoint/authorized model/checkpoint/access instructions. Existing
`HackAlem_Execution_Plan_KZ.md` and `QOR_MVP_Model_Prompts_EN.md` were inspected.
The absence claim is limited to the searched locations, not all possible storage.

## Real IEK SKU trace (not a confirmed purchase order)

SKU **200400085_**, source unit **м**. Observed monthly-sheet values for 2026:
January 1,530; February 3,000; March 470; April 1,745; May 1,155; June 4,980;
July 2,770; August 1,800; incomplete September 605.

Transactional positive-demand values differ: February 2,695, March 775, April
1,545. The source discrepancies remain visible; these sources are not added.
Forecast fitting uses monthly 2024 and transactions 2025–August 2026. September
is excluded. The default result is **needs_stock_input**, with no order quantity.

For a separately labeled verification scenario ONLY:

- Hypothetical available stock: 0 м on 2026-09-22 (not measured inventory).
- Purchase-unit mapping: explicit factor-1 assumption. Lead/review/buffer: 14/7/7.
- No inbound lines for this SKU. MOQ 1 from `MOQ  ИЭК.xlsx`, sheet `Лист7`,
  row 1825, interpreted as minimum. Pack multiple is absent.
- Seasonal daily demand averages 55.259703689 м over the 28-day projection.
- Binding day: 2026-10-13. Projected stock without new order:
  −1,180.600914574 м. Forward seven-day buffer: 366.670788719 м.
- Raw need = 366.670788719 − (−1,180.600914574) = **1,547.271703294 м**.
  With minimum 1 and no evidenced multiple, proposed quantity is the same;
  fractional meters require manager review, not an invented pack rule.
- Predicted first shortage: 2026-09-23; urgency `expedite`. It is not an observed
  stockout and cannot be covered by an order arriving after 14 days.

Six rolling evaluation origins for this SKU (March–August 2026):

| Method | WAPE | Signed bias |
|---|---:|---:|
| Three-month mean | 62.2137% | +0.3071% |
| Seasonal | 76.2854% | +34.3515% |

These large errors are a material limitation. Seasonal was not proven superior;
the UI allows selecting `mean3`. These metrics describe one SKU, not every IEK
unit or supplier-wide performance. All-unit evaluation is available in the UI
but was not benchmarked across the full archive during this audit.

Full private source references, daily forecast, history, assumptions and
verified scenario-export sizes are in ignored `runtime/verification.json`.
Verification approvals used test identities in an isolated verification DB;
they are not purchasing-manager approval of a real order.

## Exact verification commands

Executed in the workspace with its existing `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q backend frontend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/verify_project.py --help
.\.venv\Scripts\python.exe scripts/verify_project.py --iek 'C:\Users\Kuralai\Downloads\IEK.zip' --benchmark 249000 --output runtime/verification.json
.\.venv\Scripts\python.exe scripts/smoke_real_ui.py
.\.venv\Scripts\python.exe scripts/model_probe.py
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py --server.address 127.0.0.1 --server.headless true --server.port 8507 --browser.gatherUsageStats false
Invoke-WebRequest -Uri 'http://127.0.0.1:8507/_stcore/health' -UseBasicParsing
Invoke-WebRequest -Uri 'http://127.0.0.1:8507' -UseBasicParsing
```

Additional import check from `frontend/`:

```powershell
..\.venv\Scripts\python.exe -c "import qor; print(qor.__file__)"
```

Observed: `backend\qor\__init__.py`, no broken pip requirements, pytest
**54 passed**, health **200 / ok**, page **200**, synthetic workflow AppTests
without exceptions. Real IEK smoke printed:

```text
PASS: real IEK import, Demand/evaluation, Orders missing-stock gate,
7/14/30 scenarios; zero app exceptions; no approval/export
```

Probe output (no network request):

```text
not run: missing participant entitlement variables: QOR_MODEL_ENDPOINT, QOR_MODEL_ID, QOR_MODEL_API_KEY
```

No model SDK/runtime or weights were installed and no successful model response
was observed. The retained generic HTTP probe is not a verified provider adapter.
Stage 0 requires organizer endpoint/provider and protocol documentation, an
authorized exact model/deployment ID, and the participant credential; or an
authenticated local checkpoint with license/checksum/runner requirements.

Measured environment: Python 3.14.0 free-threading build, Streamlit 1.64.0,
pandas 3.0.6, NumPy 2.5.3, openpyxl 3.1.5, Plotly 7.1.0, Pydantic 2.13.5.
Real cold ZIP import measured 20.01 s in the first full audit and 24.42 s when
another UI import ran concurrently. First generated 249,000-row CSV import/audit:
7.868 s. These are machine-specific cold runs, not production SLA claims. The
latest machine-readable results are in `runtime/verification.json`. No complete
249k-row all-SKU forecasting latency claim is made.

## Requirement–evidence map

| Requirement | Status | Evidence |
|---|---|---|
| Preserve original files and single-process structure | Complete for performed operations | Source hash unchanged; root legacy files retained; frontend uses backend package |
| Two-supplier ingestion engine | Implemented; real SE validation blocked | IEK real archive + canonical SE fixture tests |
| Missing/zero, returns, identifiers and duplicate safety | Tested | `test_ingestion_audit.py`, `test_data.py` |
| Outlier candidate and human exclusion | Tested | `test_forecast_rules.py`; original rows retained |
| Single-customer branch | Synthetic only | Explicitly labeled anonymized demo IDs; no real customer inference |
| Seasonal baseline comparison; no future leakage | Tested | `test_forecast_rules.py`, one real SKU metrics above |
| Confirmed stockout and separate hypothetical sensitivity | Tested; real intervals absent | Stockout evidence model and overlap/confirmation-date tests |
| ETA, availability, MOQ/multiple, urgency and explanations | Tested | `test_planning_rules.py`, binding-day trace |
| Editable 14/7/7 and 7/14/30 scenarios | Tested | Policy validation, UI tests and real IEK UI smoke |
| Versioned drafts/edits/approval and CSV/XLSX reopen | Tested | `test_workflow.py`, synthetic end-to-end AppTest |
| No automatic supplier dispatch | Complete | No dispatch action/tool or external purchasing network client |
| Live organizer model + SDK/function calling | Blocked | Missing exact participant entitlement; no mock integration |
| Real SE order through export | Blocked | Missing SE archive/current source headers |
| Rules/case compliance against original PDF/DOCX | Unverified | Original documents not found |
| Large-file responsiveness | Partly measured | 171,603 real XLSX transactions + 249k generated CSV, cached views; all-SKU forecasting not benchmarked |

## Short judge demo

1. Open localhost:8507. Show the live-AI blocked notice and enter a test manager.
2. Data → **Open labeled synthetic walkthrough**. State clearly this is generated
   SE data. Demand → Systeme Electric → show candidate, reasoned keep/exclude,
   and temporal seasonal/baseline metrics. Real customers are not identified.
3. Orders → calculate → inspect sources/binding-day projection → adjust quantity
   with a reason → move to review → approved → generate/reopen CSV or XLSX.
   Show audit versions and that editing resets approval; no dispatch button exists.
4. Scenarios → change ETA delay / 7–14–30 lead time. Explain forecast versus fact.
5. Data → **Load located IEK archive (Downloads)**. Show real warnings and SKU
   `200400085_`. Its missing current stock prevents a confirmed order. Show
   reconciliation and the real baseline/seasonal errors, not a claimed AI success.

## Limits before operational use

Obtain real SE sources and original case/rules; verify IEK dated available stock,
purchase units, packing constraints, lead/ETA commitments and any stockout/growth
evidence. Validate forecast choice per group and do not treat the high-error
single-SKU result as production accuracy. This localhost app has no authenticated
roles or encrypted storage. Use manager review for all orders, and obtain the
exact organizer model resource before enabling any live AI.
