# Requirements trace

> Historical root-app matrix retained. Use the updated requirement–evidence
> table in [Current implementation evidence](IMPLEMENTATION_VERIFICATION.md).
> Real IEK is now verified; real SE and live model access remain blocked.

| Requirement | Evidence | Status |
|---|---|---|
| Deterministic demand / order core | `qor/demand`, `qor/planning`, pytest | implemented (synthetic tests) |
| ETA, stock, MOQ, missing stock | `tests/test_planning.py` | verified |
| Import / textual SKU / missing vs zero | `qor/data`, `tests/test_data.py` | verified on synthetic tables; real archives absent |
| Manager approval before export | `app.py`, SQLite transition | implemented; UI smoke launched |
| CSV/XLSX export formula safety | `app.py` prefix guard | implemented |
| Live participant AI | `docs/MODEL_ACCESS.md`, `scripts/model_probe.py` | blocked - entitlement absent |
