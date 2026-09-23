# Five mandatory case outcomes — observed status

The original named case file was not accessible. This matrix maps the five outcomes stated in the attached brief; it must be checked against the original file when supplied.

| Outcome | Code and UI | Measured evidence | Status |
|---|---|---|---|
| Applicable inputs affect replenishment | `data/ingestion.py`, `service.calculate_plan`, `planning/engine.py`; Data, Orders, Scenarios | Stock/ETA/lead/category/growth/MOQ/unit tests; real IEK missing-stock gate | **Partial**: real IEK stock and real SE source missing |
| Seasonality and sustained growth | `demand/forecast.py`, `demand/challenger.py`; Demand evaluation | Time-ordered 21-day IEK comparison; growth and leakage tests | **Partial**: high error and sampled cohort |
| Lost demand during confirmed stockouts | `compensate_stockouts`; Demand evidence form | Synthetic confirmed interval and hypothetical scenario tests | **Partial**: no real intervals supplied |
| Resist one-off large / one-client sale | `clean_demand`; raw/reviewed/forecast-input chart and candidate table | Injected giant sale, split document, synthetic anonymized-client test; unreviewed cap and reasoned override | **Partial**: client branch is synthetic only |
| Supplier-grouped explained drafts | `service.calculate_plan`, `storage.Repository`; Orders | Synthetic SE edit/review/approval/reopened export; real IEK blocked row | **Partial**: no real SE order or confirmed IEK stock |

Live organizer model integration is a separate **blocked** access criterion: only deterministic read-only router tests exist. No supplier dispatch action exists.
