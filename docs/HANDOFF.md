# QOR implementation handoff — 23 September 2026

## Completed in this turn

- Preserved the active backend/frontend product and pre-existing uncommitted changes. Made `pyproject.toml` the single pinned manifest; `requirements.txt` delegates to it.
- Created a clean Python 3.12 environment under ignored `runtime/venv312` with Streamlit 1.64.0, pandas 2.3.3 and scikit-learn 1.9.1. Existing Python 3.14 environment remains untouched.
- Replaced the landing copy and static preview with Russian dark navy/electric blue content and the clearly synthetic 188 − (28 + 40) = 120 / pack-20 explanation. CTA routes to the working workspace.
- Added causal anonymized-client concentration flags and an unreviewed candidate cap used only in forecast input. Raw and reviewed sales stay visible; a reasoned keep/exclude decision overrides the cap.
- Added a local CPU 21-day HGB challenger and chronological group selection experiment. No ML candidate won on the real sampled IEK evaluation; only source-bound selected baselines are used by the app. A stale or absent report falls back visibly.
- Added focused tests for giant single-client sensitivity, future-label leakage and source/horizon binding.

## Actual checks

- Before changes: `.venv\Scripts\python.exe -m pytest -q` → 55 passed.
- Clean environment: `runtime\venv312\Scripts\python.exe -m pytest -q` → **58 passed** in 10.64 s, no warnings.
- Real IEK smoke: `runtime\venv312\Scripts\python.exe scripts\smoke_real_ui.py` → import, Demand/evaluation, missing-stock gate and 7/14/30 scenarios PASS, zero AppTest exceptions; no approval/export.
- Real IEK trace: `scripts\verify_project.py --iek C:\Users\Kuralai\Downloads\IEK.zip --output runtime\verification312.json` → 171,603 transactions, 22.78 s import, default `200400085_` blocked for missing stock; hypothetical zero-stock scenario 1,547.2717 m, reopened export, source hash unchanged.
- `scripts\train_forecast.py --iek C:\Users\Kuralai\Downloads\IEK.zip --max-skus 100` → 1,597 panel rows, 876 held-out predictions, 44.294 s, selected seasonal/meters, seasonal/packs, mean3/pieces. Original SHA-256 unchanged.
- App launched on `http://127.0.0.1:8511`; health and page HTTP 200. Streamlit AppTest passes landing and synthetic manager workflow. Manual browser pixels could not be captured: the available computer-use browser inventory returned no browsers.
- Model probe stopped before network: `QOR_MODEL_ENDPOINT`, `QOR_MODEL_ID`, `QOR_MODEL_API_KEY` missing.

## Remaining external facts and release limits

Real Systeme Electric files; original case file `Вставленная ​​уценка.md`; generated QOR reference image; dated current IEK available stock; confirmed stockout intervals and real anonymized client IDs; purchase-unit/pack and lead-time confirmations; verified organizer provider/model credentials. A generated SE walkthrough and hypothetical IEK zero-stock export must not be presented as real supplier approval. No live LLM call occurred.
