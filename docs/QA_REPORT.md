# QOR current QA — 23 September 2026

## Commands and actual results

| Command / check | Result |
|---|---|
| Clean Python 3.12 `pip install -e '.[test]'` | Completed with Streamlit 1.64.0, pandas 2.3.3, scikit-learn 1.9.1 |
| `runtime\venv312\Scripts\python.exe -m pytest -q` | **58 passed** in 10.64 s; no warnings |
| `scripts/train_forecast.py --iek C:\Users\Kuralai\Downloads\IEK.zip --max-skus 100` | 1,597 causal panel rows; 876 held-out method predictions; 44.294 s; source hash unchanged |
| `scripts/smoke_real_ui.py` | Real IEK import, demand/evaluation, missing-stock gate and 7/14/30 scenarios PASS; zero AppTest exceptions; no real approval/export |
| `scripts/verify_project.py --iek ... --output runtime/verification312.json` | 171,603 real IEK transactions; 22.78 s import; original hash unchanged; default SKU `200400085_` remains `needs_stock_input` with null quantity |
| Streamlit `frontend/app.py` at `127.0.0.1:8511` | Server started; health 200 / `ok`, page 200 |
| `scripts/model_probe.py` | No network call; missing `QOR_MODEL_ENDPOINT`, `QOR_MODEL_ID`, `QOR_MODEL_API_KEY` |
| Desktop/mobile pixel review | Not completed: computer-use inventory returned no available browsers; no new screenshot is claimed |

The automated tests cover source-key preservation and duplicate joins, missing
versus zero IEK stock, returns, causal one-off and synthetic single-client
spikes, confirmed/synthetic stockout uplift, future-label leakage, dated ETA
and early shortage, MOQ versus pack, unit mismatch, reasoned edit, state
transition and reopened formula-safe CSV/XLSX. AppTest covers the landing route
and a synthetic manager workflow. It does not prove the real SE adapter against
the missing original workbook.

## Real source trace and forecast selection

Real IEK SKU `200400085_` in meters traces through imported monthly and
transaction records, source reconciliation, forecast and a blocked planning
row. Its current dated available stock is absent, so its real order quantity
remains null. An earlier hypothetical zero-stock/factor-1-unit scenario in
ignored `runtime/verification312.json` is a technical demonstration only.
That scenario produced raw/recommended 1,547.2717 meters and predicted
shortage on 2026-09-23; it is **not** a measured stock count or an authorized
supplier order. Its test approval/export reopened consistently, and the
original archive's SHA-256 was unchanged.

The sampled 21-day rolling holdout selected seasonal for IEK meters (44.02%
WAPE, +0.69% signed bias) and packs (33.68%, −19.69%), and mean3 for pieces
(29.45%, −21.96%). The HGB challenger lost where eligible. These are sampled
observed-sales errors, not a guarantee. Source-bound automatic selection uses
only these tested baselines; mismatched input/horizon falls back with a label.

## Release disposition

The deterministic local MVP is launchable and the synthetic approval/export
workflow is demonstrated. All five case outcomes have implemented code paths,
but each remains **PARTIAL** for the exact real-world evidence listed in
[CRITERIA_MATRIX.md](CRITERIA_MATRIX.md). A real Systeme Electric SKU cannot
be traced until its original file is supplied. IEK needs dated current stock
and purchase-unit confirmation. Original criteria and generated image were
not accessible, so direct document/image compliance remains unverified. Live
organizer-model integration is **BLOCKED** by missing entitlement; mock/router
tests are not represented as a live call. No supplier dispatch is implemented.
