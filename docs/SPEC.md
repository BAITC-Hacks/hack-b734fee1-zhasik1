# QOR product specification (Stage 1)

## Product boundary

QOR creates **supplier-specific purchase-order drafts** for a purchasing
manager. Python functions, not AI, calculate every quantity. A manager may
edit, move a draft to review, approve it, then export it. QOR never sends an
order to a supplier.

## Evidence-based acceptance map

| Requirement | Calculation / control | UI evidence | Test evidence | Demo evidence |
|---|---|---|---|---|
| Sales, stock, inbound, category, growth | Normalized typed inputs | Data screen | import and planning tests | source-to-row trace |
| Seasonality and sustained growth | Dated, leakage-safe demand forecast | Demand screen | seasonal/growth tests | switch growth mode |
| Confirmed lost demand | Only explicit interval compensation | Demand + scenario badges | confirmed/unknown stockout tests | labeled synthetic interval |
| Large one-off sales | Candidate detection, manager decision, no client claim without anonymized ID | Outlier screen | one-off vs sustained-growth tests | inspect candidate |
| Supplier grouped PO / explanation / urgency | Daily inventory timeline, MOQ and pack rounding | Draft screen | ETA, stock, MOQ tests | explain a SE row |
| Manager approval before export | State machine and SQLite audit | Draft/review/approved controls | transition/export tests | approve then export |
| AI assists but cannot invent numbers | Provider adapter invokes deterministic tools only | AI panel | capability, invalid-args and provenance tests | live call only if verified |
| Participant model live call | Real authorized model + response + tool probe | AI status | probe result | live question |

The participant-model criterion is **blocked**: `docs/MODEL_ACCESS.md` has no
verifiable entitlement. It will not be fulfilled by a mock or public model ID.

## Fixed decisions

- Snapshot is 22 Sep 2026; incomplete September is not forecast training data.
- 2025 transactions are the candidate cleaned history. 2024 monthly data can
  inform seasonality/reconciliation, but is never summed with transactions.
- Systeme Electric uses its free-stock field once; do not subtract reserves
  again. IEK needs a dated available-stock input; missing is not zero.
- Supplier plus textual 1C SKU plus unit is the item key. Leading zeroes and
  underscores remain intact.
- Default scenario is lead/review/buffer = 14/7/7 days; 7/14/30 lead scenarios
  are sensitivity views.
- File growth and observed-growth modes are mutually exclusive.
- MOQ and pack multiple are different constraints and are unit-specific.

## Non-goals / known limitations

No original archives, participation-rules PDF, case DOCX, or
`HackAlem_Logistics_Analysis_KZ.md` is currently in the workspace. No claim
about their contents, source row counts, client IDs, current IEK stock, daily
stockouts, or lead times can be made until they are supplied. Any walkthrough
fixture must be explicitly synthetic.
