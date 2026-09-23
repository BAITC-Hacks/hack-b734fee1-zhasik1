# QOR integration QA report (Stage 8)

> Historical root-app report retained. The current backend/frontend MVP and
> 54-test verification supersede the results below:
> [Current implementation evidence](IMPLEMENTATION_VERIFICATION.md).
> Correction: IEK.zip was subsequently found in Downloads; real SE remains missing.

**Executed:** 2026-09-23, Windows PowerShell, Python virtual environment.

## Commands and observed results

| Command | Result |
|---|---|
| `.\\venv\\Scripts\\python.exe -m pytest -q` | `9 passed in 0.58s` |
| Streamlit `AppTest.from_file('app.py').run(timeout=15)` | `app_exceptions=0`, `tabs=4` |
| `streamlit run app.py --server.headless true --server.port 8501` plus `Invoke-WebRequest http://localhost:8501` | server launched; HTTP `200` |
| `py -3 scripts/model_probe.py` | exit `2`: missing endpoint/model/key variables; no network model call was made |

## Requirement disposition

| Area | Result | Evidence |
|---|---|---|
| Deterministic demand / planning | Pass for tested synthetic cases | 9 pytest tests |
| ETA arrives only on its date, pre-lead shortage | Pass | `test_late_inbound_does_not_prevent_expedite` |
| MOQ / pack rounding reference | Pass | `test_reference_eta_and_pack`: raw 100, rounded 120 |
| Unknown IEK stock distinct from zero | Pass | `test_unknown_stock_not_zero` |
| SKU text, zero versus missing, future-month exclusion | Pass | data/demand tests |
| Manager workflow and export UI | Partial | UI renders; interactive approval/export should be rechecked with real source rows |
| Real IEK / SE import and source-to-export trace | Blocked | original archives are absent from this workspace |
| Live HackAlem in-product model and tools | Blocked | no organizer endpoint, authorized model ID, or participant credential |

## Remaining source-data limits

There is no current IEK stock snapshot, confirmed daily stockout interval,
anonymized client ID, guaranteed lead time, source participation PDF/DOCX, or
IEK/Systeme Electric archive in the workspace. Synthetic demonstration is
separately marked and is not a factual supplier recommendation.
