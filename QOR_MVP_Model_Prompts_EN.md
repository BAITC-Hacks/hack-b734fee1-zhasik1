# QOR MVP: English prompts with hackathon model integration

**Purpose:** Build a working, verifiable MVP for HackAlem AI's “Automatic calculation of supplier orders for warehouse replenishment” case, owned by Elektrokomplekt LLP.

## Critical correction to the earlier plan

The case materials supplied so far contain sales, stock, goods in transit, MOQ, and requirements. They **do not identify a downloadable AI model, model ID, participant API endpoint, or installation command**. The public HackAlem site says participants must use Codex during development; the public event announcement describes access to OpenAI technology resources. Neither establishes which runtime model this participant can use. Do not choose a model name, download weights, claim an entitlement, or report a successful integration without evidence from the participant access instructions and a live smoke test.

The sequence is therefore **verify the hackathon's actual model entitlement → install the supplied runtime or SDK → prove a live model call → design the AI adapter around its capabilities → build and test the procurement MVP**. Data import, forecasting, and stock calculations can proceed while participant access is being resolved. A real model-backed assistant remains an explicit acceptance gate.

The hackathon AI model used **inside the product** is separate from the reasoning or coding model assigned to write each module. The latter can vary by development environment; the product must use the actual participant-provided service or model once verified.

Official references: [HackAlem event requirements](https://www.hackalem.ai/); [OpenAI's Python SDK setup](https://developers.openai.com/api/docs/quickstart); [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).

## How to use these prompts

For each separate coding model, paste the **Shared brief** below and then its numbered prompt. If sessions do not share a workspace, attach the source files, the previous stage's files or branch, and the handoff. Do not ask independent models to edit the same module at the same time. One Codex session can complete stages 0 through 8 in order. Choose a strong reasoning model for stages 0, 1, 3, and 8; a strong coding model for stages 2, 4, 5, and 6; a fast careful model for stage 7. These are development assignments, not claims about the event's runtime models.

| Stage | Owner | Start after | Primary ownership |
|---:|---|---|---|
| 0 | Hackathon model access and runtime engineer | Immediately | `docs/MODEL_ACCESS.md`, `scripts/model_probe.py`, `.env.example` |
| 1 | Product architect | Initial access audit; may continue if credentials pending | `docs/SPEC.md`, `docs/INTERFACES.md`, `qor/contracts.py` |
| 2 | Data engineer | 1 | `qor/data/`, `tests/test_data.py` |
| 3 | Demand science engineer | 2 | `qor/demand/`, `tests/test_demand.py` |
| 4 | Inventory engineer | 1; can start with contract fixtures | `qor/planning/`, `tests/test_planning.py` |
| 5 | Product engineer | 2–4 | `app.py`, `qor/ui/`, `qor/storage/` |
| 6 | Hackathon model integration engineer | 0, 1, 4, 5 | `qor/ai/`, AI panel, `tests/test_ai.py` |
| 7 | Release and demo writer | 5–6 | `README.md`, `docs/DEMO.md`, `docs/REQUIREMENTS_TRACE.md` |
| 8 | Independent integration and QA engineer | 0–7 | Bug fixes, integration tests, `docs/QA_REPORT.md` |

## Shared brief — prepend to every numbered prompt

```text
You are building QOR for the HackAlem AI logistics track, case owner Elektrokomplekt LLP. The primary user is a purchasing manager. Deliver a working app that turns sales history, seasonality, sustained growth, available stock, goods in transit, category policies, and confirmed lost demand into explainable supplier-specific purchase-order drafts. The manager reviews, edits, approves, and exports an order.

Source files: the participation-rules PDF, the “HackAlem AI: Automating Supplier Order Generation” DOCX, IEK.zip, and Systeme electric.zip. In the original workspace they may be under /workspace/scratch/05cf5035569d/upload/. In a different workspace locate the supplied copies or request their attachment; do not pretend an absent file exists. Read HackAlem_Logistics_Analysis_KZ.md and HackAlem_Execution_Plan_KZ.md, but verify disputed facts against the original source files. The previous Kazakh prompt pack was a plan, not an implemented app.

Mandatory case outcomes: (1) incorporate sales, current stock, inbound goods, categories, and growth; (2) reflect seasonality and sustained growth; (3) estimate lost demand for confirmed stockout intervals; (4) prevent one-off large orders, including single-client orders when anonymized client IDs exist, from inflating regular demand; (5) provide supplier-grouped order quantities, explanations, urgency, and export. Supply a repository and README describing the calculation, outlier policy, and run steps. No supplier dispatch without a responsible employee's approval. Do not use non-anonymized client information.

Known source limits: the demonstration snapshot is dated 22 September 2026, and September is incomplete. The provided transactional files contain no client ID or price; there are no daily stockout intervals, no confirmed new-order lead times, and no current IEK available-stock snapshot. Systeme Electric includes an available-stock column. Monthly and transactional sales often disagree. Treat supplier + textual 1C SKU as the key; keep initial zeros, trailing underscores, and units intact. Do not sum overlapping sales sources or convert unknown stock into zero. Synthetic proof cases must be visibly marked synthetic.

The initial configurable policy is lead time 14 days, review cycle 7 days, buffer 7 days; show lead-time sensitivity at 7/14/30 days. The provisional demand baseline is a weighted six-month deseasonalized level, with a three-month mean candidate for IEK packs. An earlier exploratory monthly comparison found 22.39% WAPE for the seasonal candidate and 25.74% for a three-month mean on Systeme Electric. These are not production guarantees; repeat time-based evaluation after building a cleaned demand series.

Default implementation stack: Python, pandas, NumPy, openpyxl, Streamlit, Plotly, SQLite, Pydantic, pytest. Use Codex as part of the development process as required by the public hackathon information. Select the in-product AI runtime only from verified hackathon participant materials or authorized account access. If the provided resource is an API, install its documented SDK/client and use a credential stored outside source control; do not attempt to download proprietary model weights. If participants receive an actual checkpoint, verify its exact ID, source, checksum, license, runner, and hardware needs before installation. Provide deterministic Python forecasting and order calculations; the runtime language model may query and explain them but cannot invent or overwrite numbers.

Do the work, inspect the actual files and outputs, run meaningful tests, fix failures, and provide a concise handoff: files changed, exact verification performed, results, remaining genuine dependencies, and the next stage's input contract. Never claim an unavailable model, unexecuted test, finished app, or proved financial savings.
```

## Stage 0 — Verify and install the actual hackathon model resource

```text
Act as the hackathon model access and runtime engineer. This is a hard first gate, not an invitation to guess a model ID. Inspect all supplied organizer instructions, attached model files, access emails or screenshots provided in this workspace, participant dashboard details explicitly made available to you, and official HackAlem/OpenAI/NVIDIA instructions. Respect the user's earlier instruction to stop account login attempts; do not open or sign in to a private site without new authorization. Identify precisely whether this team received (A) a hosted API and credentials, (B) a downloadable local checkpoint, (C) a hosted partner inference endpoint, or (D) no verifiable access details yet. Record the source of every finding. The public announcement of event resources is not proof that this account has been activated.

For a confirmed API/hosted entitlement: install the documented client SDK in the project's isolated environment; put only variable names and example values in .env.example; read credentials from the environment or approved secret store. If it is an OpenAI API entitlement, install the official Python SDK with `python -m pip install openai`, use the provided project's API key, discover its available model IDs through the documented authenticated model-list operation, and send one minimal Responses API request. A public model ID or successful model-list response by itself does not prove this account can invoke the chosen model. Probe one minimal response and one structured tool/function request if supported. Log status codes, model ID, tool support, latency, and an answer hash, without logging secrets or private spreadsheets. Do not create a paid account, change billing, or spend substantial credits merely to probe access.

For an actual downloadable checkpoint: verify official URL or supplied file, integrity hash, license and permitted use, format, runner, RAM/VRAM/disk requirements, and the laptop's real capabilities. Install only the documented compatible runtime, load the checkpoint, and run the same two probes locally. If it does not fit the hardware, document a permitted hosted route or a smaller organizer-provided checkpoint; do not silently replace it with an unrelated public model.

If access is not in the supplied materials, create docs/MODEL_ACCESS.md with status 'unverified', an exact list of the missing participant item(s), the verified public facts, and the planned adapter interface. Build scripts/model_probe.py so it can run after credentials or weights arrive, without embedding an invented model name or real secret. Continue the deterministic core in later stages, but make the real-model integration an explicit unfinished acceptance gate.

Deliver docs/MODEL_ACCESS.md, scripts/model_probe.py, .env.example, a minimal requirements entry if a documented SDK was installed, and the exact smoke-test output or a clear 'not run: missing entitlement'. Do not mark this stage passed based solely on a mocked response.
```

## Stage 1 — Freeze requirements, contracts, and acceptance criteria

```text
Act as the product architect. Read the source case and current MODEL_ACCESS.md. Build docs/SPEC.md, docs/INTERFACES.md, docs/DECISIONS.md, and minimal typed models in qor/contracts.py. Do not implement other owners' modules.

Map each mandatory requirement to a calculation, an interface view, an adversarial test, and a demo step. Include a separate acceptance criterion that the participant-provided runtime model is verified by a live call; if access remains unavailable, mark that criterion blocked rather than replacing the event resource without authorization. Define one provider-neutral interface that the actual verified model can implement, with capabilities declared explicitly: responses/messages, JSON or tool calling if available, limits, timeout, error handling, and provenance. Do not impose OpenAI-specific function calling on a checkpoint that does not support it. If the entitlement is OpenAI Responses API, use its documented tool flow.

Define Pydantic contracts for supplier, textual SKU, unit, dates, sales and returns, stock availability, reservations, inbound ETA, category and category policy, growth mode, confirmed stockout, minimum order and pack multiple. Preserve missing-versus-zero and actual/calculated/assumed/synthetic provenance. Fix public signatures for load_sources, normalize_supplier, clean_demand, forecast_demand, project_inventory, recommend_order, explain_row, and the AI provider. Define the draft -> review -> approved -> exported state machine and what permissions each transition needs.

Record decisions: transactions from 2025 are the candidate cleaned history; 2024 monthly data inform seasonality and reconciliation, never double-counted; the snapshot is 22 Sep 2026; SE free stock is used once; IEK needs a dated available-stock input; the 14/7/7-day policy is a configurable scenario; supplied growth and implicit trend are not multiplied twice. Do not invent the meaning of raw category codes, stockout dates, client IDs, or a 1C import specification.

Run an import and construction smoke check on contracts.py with one synthetic SKU. Handoff must enable the other coding models to implement their modules without redesigning these contracts.
```

## Stage 2 — Build supplier-specific import and reconciliation

```text
Own qor/data/ and tests/test_data.py. Implement safe import of the supplied IEK and Systeme Electric archives and their Excel sheets. Read contracts.py and INTERFACES.md first. Preserve raw originals, file/sheet/row provenance, date, warehouse, supplier article, and unit. Store 1C SKU as text, including leading zeroes and trailing underscores. Separate positive sales, negative returns/adjustments, missing quantities, true zero, and absent periods. Do not use abs() to turn returns into sales or infer stockout from an empty monthly cell.

Deduplicate according to an explicit supplier + SKU + event key before joins, audit conflicting repeats, and check that a join cannot multiply incoming quantities. Reconcile transactional and monthly sales by SKU-month, reporting coverage differences without adding overlapping values. Keep 2026 September partial. Use the actual SE available-stock column without subtracting its reserves again. Keep IEK's dated opening monthly stock separate from the missing September 22 snapshot. Preserve inbound quantity and its stated ETA; unknown ETA stays unknown. Reject accidental mixing of pieces, meters, packs, and sets.

Baseline audit guides, not hardcoded outcomes: IEK 171,603 and SE 77,312 transaction rows excluding total rows; 469 SE sales SKUs overlap current-stock and MOQ sources. Explain deviations if the source changes. Provide meaningful tests for leading-zero codes, duplicate joins, missing/zero distinction, unit preservation, negative rows, and inbound dates. Test representative records directly against the supplied workbook when available.

Handoff: normalized schemas, diagnostics, real-file import results, one IEK and one SE example object, and any unresolved source ambiguity.
```

## Stage 3 — Clean and forecast demand

```text
Own qor/demand/ and tests/test_demand.py. Use the normalized import layer and typed contracts. Keep raw sales intact and produce a separate, attributable cleaned series. Detect candidate large transactions using supplier + SKU + document + date and a documented robust threshold; preserve an auditable human decision. No anonymized client ID is supplied in the actual transaction files, so demonstrate the client-aware branch with clearly labeled synthetic data. Preserve sustained growth across several periods rather than classifying it as a one-off outlier.

Implement the provisional weighted six-month deseasonalized seasonal baseline; compare a three-month mean and keep the IEK pack-group exception only if it survives evaluation on cleaned data. Estimate seasonality from completed years without future information at each backtest origin. Keep stockout compensation limited to confirmed intervals; 0/7/14-day unknown-stockout cases are separately labeled scenarios. Make the file-provided growth mode and observed-growth mode mutually exclusive where the former would otherwise count growth twice. Do not present model forecasts as measured unconstrained demand when stockouts are unknown.

Run rolling-origin evaluation by supplier and unit. Show WAPE, signed bias, and intermittent-demand limitations. Record if the new cleaned-data results differ from the earlier 22.39% monthly-data experiment and why. Build meaningful tests for an injected one-off client purchase, sustained growth, confirmed stockout, missing stockout, and temporal leakage. Handoff: deterministic forecast function with inputs, provenance, explanation fields, test output, and chosen candidate per applicable segment.
```

## Stage 4 — Implement the order recommendation engine

```text
Own qor/planning/ and tests/test_planning.py. Depend only on contracts.py and deterministic demand forecasts. For available stock F, day-specific demand d(t), and only inbound stock whose ETA has arrived by t, compute P(t)=F+I(t)-cumulative_demand(1..t). With lead time L, review period R, and an S-day future-demand buffer, calculate the positive maximum of buffer(t)-P(t) over t=L..L+R. If stock depletes before L, surface an expedite warning because a standard order cannot arrive in time. Keep inbound items with unknown ETA out of the confirmed-arrival schedule unless an explicit scenario assigns them a date.

Apply minimum order and pack multiple separately and in the correct unit. Never create an order solely because MOQ is positive when raw need is zero. If a supplier field is ambiguous, label its interpretation provisional and make it configurable. Keep category-policy effects visible and raw category codes uninterpreted. Missing IEK current stock must produce a needs-stock-input status; zero current stock is a distinct valid input. Return the calculation breakdown, source timestamp, shortage date, urgency, before/after rounding, and assumptions for each row.

Test adversarial inventory timelines: late inbound does not fix an earlier shortage; increasing free stock does not increase unrounded required quantity; free stock is not reduced by the same reservations again; lead-time sensitivity behaves correctly; missing ETA is not treated as immediate; unknown IEK stock is not zero. Check this synthetic reference: 10 units/day, L=14, R=7, S=7, free stock 120, inbound 60 on day 10, pack multiple 24 => raw need 100, rounded order 120. Core planning must not depend on Streamlit or a language model.
```

## Stage 5 — Build the purchasing manager's Streamlit app

```text
Own app.py, qor/ui/, and qor/storage/. Call the data, demand, and planning contracts instead of duplicating their calculations. Build four clear screens: Data quality and upload; Demand and outliers; Supplier-grouped order drafts and row explanations; Scenario comparison. Show the 22 Sep 2026 demo snapshot date, source provenance, and assumption badges. Let managers set lead/review/buffer days, inspect 7/14/30-day sensitivity, adjust category policies and growth mode, and inspect confirmed-versus-synthetic stockout examples.

Persist calculation run ID, manager edits and reasons, approval state, and order version in SQLite. Offer a draft -> review -> approved -> exported workflow. Produce CSV/XLSX exports containing supplier, textual SKU, article, unit, current free stock, dated inbound, forecast, raw need, MOQ-adjusted quantity, urgency, snapshot date, assumption labels, and approval status. Defend exported sheets against spreadsheet formula interpretation of untrusted text. Do not implement supplier messaging or pretend to have a native 1C format without its specification.

Keep the app responsive: aggregate and filter 248,915 transactional records instead of displaying them all at once. Missing source files or credentials produce a truthful setup state; a synthetic walkthrough requires a separate, labeled demo switch. Preserve a placeholder integration point for stage 6's verified model assistant. Run `streamlit run app.py` and verify at least one actual SE SKU through import, planning, manager edit, approval, and re-opened export. Handoff: exact UI entry points and the provider integration hook.
```

## Stage 6 — Integrate the verified hackathon-provided runtime model

```text
Own qor/ai/, tests/test_ai.py, and the smallest necessary update to the app's AI panel. Read MODEL_ACCESS.md and use only the actually verified model ID, endpoint, and interface. If stage 0 recorded 'unverified', do not substitute a random model or mock a live demo; make the AI panel clearly pending, keep the deterministic workflow operational, and report precisely which access item is required.

If access is verified, implement a provider adapter for that actual service or local checkpoint. Use Responses API function calling only if the entitled provider and model support it. Otherwise use the provider's documented structured-output mechanism, validate it with Pydantic, and translate approved intents into application calls. Restrict calls to inspect_data, calculate_plan, simulate_policy, explain_sku, and build_order_draft. The AI may create a draft, never approve or send an order. Do not send the raw 248,915 rows or any non-anonymized customer data to an external model. Bound tokens and tool calls; return only compact summaries and requested SKUs.

Trace every generated explanation to calculation_run_id and the authoritative Python outputs. If a model says a different quantity, reject or correct that answer before display. Secure credentials outside source control and avoid exposing them in logs or screenshots. Test invalid arguments, unsupported provider capabilities, timeouts, missing credentials, tool-result provenance, and the disabled state. With real access, verify one live question: 'Create a Systeme Electric draft with a 14-day lead time and explain the ten SKUs likely to run out first.' Report the actual probe and execution results; mocked tests do not satisfy the live-model criterion.
```

## Stage 7 — Write documentation and the evidence-based demo

```text
Own README.md, docs/DEMO.md, and docs/REQUIREMENTS_TRACE.md. Run the app and tests yourself before describing features. README must contain reproducible setup for Windows PowerShell and Linux/macOS, the exact tested dependencies, `streamlit run app.py`, pytest, data loading, and the real participant-model setup discovered in MODEL_ACCESS.md. Do not paste keys or publish supplied private spreadsheets. Document API-vs-local installation accurately; if access is pending, include the exact missing step and a usable deterministic-core run path.

Explain source precedence, anomaly handling, seasonal baseline, growth mode, confirmed stockout, inventory projection, MOQ, and every scenario assumption. Include the known limits: no true IEK current stock, no daily stockout intervals, no anonymized client ID in the supplied transactions, and no demonstrated monetary savings. Do not claim native 1C integration without a supplied 1C import contract.

Build a 3–5 minute demo with actual screen actions and a real SE SKU: load files, inspect source/audit, explain a one-off purchase candidate, change ETA/lead time, demonstrate a separately labeled synthetic confirmed-stockout example, show a supplier-grouped draft, manager approval and export, and one verified live model call if available. Map each mandatory requirement to code, test, UI, and demo evidence. The public event requires Codex use during development; show the repo work produced with it without inventing team member contributions. End with an honest list of completed, partial, and blocked requirements.
```

## Stage 8 — Independent integration and release check

```text
Act as the final independent QA and integration engineer. Read the original case, MODEL_ACCESS.md, contracts, code, and documentation. Create a clean environment, install exactly the documented dependencies, run meaningful tests, launch Streamlit, and inspect representative IEK and SE imports. Fix integration failures rather than stopping at a review report.

Trace one real SE SKU end-to-end: original Excel cell -> normalized transaction/stock/inbound -> cleaned demand -> forecast -> day-by-day projection -> MOQ -> UI explanation -> approved export. Confirm an IEK SKU with missing current stock is marked incomplete and becomes calculable only after a dated available-stock input. Test leakage from future months, incomplete September 2026, supplier-specific SKU collisions, unit mismatch, duplicate joins, late ETA, pre-lead shortage, category policy, growth once only, anonymized-client synthetic example, real-vs-synthetic stockout labels, audit/version persistence, and CSV/XLSX re-opened values.

Verify the hackathon in-product model against stage 0 evidence. A live provider smoke test, real invocation from the app, bounded tool calls, and correct explanation of a calculation_run_id must pass before AI integration is marked complete. If the actual entitlement is not present, mark only this criterion blocked with the missing access; do not describe mock output as a provided model. Verify Codex use as required by the public event instructions. Re-run tests after fixing bugs, update README and DEMO to match reality, and write docs/QA_REPORT.md with pass/partial/blocked per case requirement, test command and results, launch command, exact model verification status, and remaining source-data limitations. Report only work actually executed.
```

**Handoff rule for all stages:** the checked-in code and observed test output are the evidence. Do not turn a proposed design, mock provider, public model catalog listing, or unavailable organizer entitlement into a claim that the MVP is complete.
