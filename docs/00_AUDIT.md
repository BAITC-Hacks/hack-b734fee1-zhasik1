# Repository and evidence audit — 23 September 2026

## Entry point and preservation

- Active product: `frontend/app.py`, routes `/` and `/workspace`. The root `app.py` and root `qor/` are preserved legacy code. The frontend explicitly imports `backend/qor/`.
- Existing uncommitted changes were present before this work in `.gitignore`, `README.md`, `frontend/app.py`, `scripts/smoke_real_ui.py`, `tests/test_ui.py`, and untracked frontend/docs/theme/skill files. They were preserved and extended.
- No root `AGENTS.md` exists. The project Streamlit skill is a verified symlink into its installed package; the Vercel `web-design-guidelines` SKILL.md was already present and read.

## Observed baseline

| Check | Observed result |
|---|---|
| Existing `.venv` | Python 3.14.0 free-threading, Streamlit 1.64.0 |
| Before edits | `55 passed in 6.82s` |
| Active app | Four buyer views and a landing route; old landing was English |
| Real source | `C:\Users\Kuralai\Downloads\IEK.zip`, SHA-256 `fed312f909943e69b17d2cc5dd577123b5fe0874064558e8f503deaf9fc50054` |
| Missing supplied inputs | Real Systeme Electric workbook/archive, original `Вставленная ​​уценка.md` criteria file, generated QOR image, current dated IEK available stock, confirmed stockouts and participant model entitlement |
| AI probe | Stops before network because `QOR_MODEL_ENDPOINT`, `QOR_MODEL_ID`, `QOR_MODEL_API_KEY` are unset |

## Working / partial / blocked

| Area | Status | Evidence |
|---|---|---|
| IEK import, source references, reconciliation | Working | Real archive smoke; 171,603 transactions in prior full audit |
| Systeme Electric source adapter | Partial | Canonical synthetic tests; original workbook absent |
| Causal outlier review, lost-demand scenarios, baseline forecasting | Working for tested inputs | Automated demand tests; real IEK held-out experiment |
| Dated planner, MOQ/pack, SQLite approval/export | Working for tested inputs | Automated planning/workflow and synthetic UI flow |
| Actual IEK supplier order | Blocked | Current dated stock and purchase-unit confirmation absent |
| Organizer LLM | Blocked | No provider, model ID, key, checkpoint or protocol |
| Visual match to generated image | Unverified | Image was not accessible in workspace or available attachments; textual brief guided layout |

See [current QA](QA_REPORT.md), [data audit](DATA_AUDIT.md), and [criteria matrix](CRITERIA_MATRIX.md).
