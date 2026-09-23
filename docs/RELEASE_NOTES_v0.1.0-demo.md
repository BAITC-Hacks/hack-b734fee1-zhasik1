# QOR v0.1.0 demo

First reviewable demo of the QOR supplier replenishment workspace.

## Included

- Russian product overview and Streamlit purchasing workspace
- audited ZIP, XLSX, and CSV import flow
- synthetic walkthrough that contains no private supplier data
- demand history review, stockout correction, and forecast evaluation
- dated inventory planning with MOQ and pack rounding
- base, optimistic, and stress scenarios
- versioned draft, review, approval, and verified CSV/XLSX export
- local SQLite audit trail
- automated test and release workflows

## Demo boundaries

- No purchase order is sent to suppliers.
- Live AI provider access is unavailable and is reported as blocked.
- Real supplier source archives are not included.
- SQLite and uploaded data on Streamlit Community Cloud are ephemeral and can
  be reset when the app restarts or redeploys.

See [docs/DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the walkthrough and
[docs/DEPLOYMENT.md](DEPLOYMENT.md) for deployment settings.
