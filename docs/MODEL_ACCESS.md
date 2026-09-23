# HackAlem in-product model access audit (Stage 0)

> Current clarification (2026-09-23): live participant access is still blocked.
> IEK.zip was later found in Downloads (the earlier Desktop-only source inventory
> below was incomplete). The implemented router now exposes exactly four tools:
> inspect_data, calculate_plan, simulate_policy, explain_sku. No draft-writing
> tool is exposed. The retained generic probe is Responses-shaped, not truly
> provider-neutral and not a verified SDK integration. Latest executable checks:
> [Current implementation evidence](IMPLEMENTATION_VERIFICATION.md).

## Status: unverified - live model gate blocked

**Audit time:** 2026-09-23 (Asia/Qyzylorda)

No model entitlement, model ID, API endpoint, API credential, organizer-issued
checkpoint, checksum, license, or runner instruction was found in this project
workspace. No private participant dashboard or account login was opened.

## Evidence inspected

| Source | Finding | What it proves |
|---|---|---|
| `QOR_MVP_Model_Prompts_EN.md` | States that supplied materials do not identify a downloadable model, model ID, participant endpoint, or installation command. | The prompt pack is not an entitlement. |
| Workspace root and non-virtual-environment Desktop filename audit | Only the prompt pack, Kazakh execution plan, and an unrelated static HTML prototype were present. No source data archive, participant credential, checkpoint, email, screenshot, or access instruction was found. | No local resource to install or invoke. |
| Process environment (variable *names only*) | No `OPENAI`, API-key, HackAlem, NVIDIA, or model-access variable name was present. | No configured runtime credential in this process. |
| [HackAlem public requirements](https://www.hackalem.ai/) | Requires teams to use Codex during development and describes OpenAI technology resources at event level. | Public event information; not account-level API or model access. |
| [OpenAI API quickstart](https://developers.openai.com/api/docs/quickstart) and [function-calling guide](https://developers.openai.com/api/docs/guides/function-calling) | Document the SDK and API procedure after a project credential and authorized model are supplied. | Documentation only; not an authorized model selection. |

## Classification

**D - no verifiable access details yet.**

The previously found `VibeVoice-ASR_model` files are outside this project,
are named as an ASR model, and have no organizer provenance or linkage to this
case. They are not treated as a HackAlem in-product model.

## Missing participant item(s)

Provide one of the following through the project workspace or an approved secret
mechanism:

1. Hosted API: the documented endpoint/provider, participant-authorized API-key
   variable name, and an authorized model ID; or
2. Hosted partner endpoint: endpoint, authentication method, model/deployment ID,
   capability documentation, and allowed use; or
3. Local checkpoint: official source URL or supplied path, exact ID/version,
   SHA-256, license, documented runner, and hardware requirements.

## What was and was not installed

No model SDK or runtime was installed because there is no documented participant
resource to install. Installing a generic SDK or selecting a public model ID
would not verify participant access and would violate the no-guessing gate.

## Deferred smoke test

`scripts/model_probe.py` is a safe, provider-neutral HTTP probe. It reads
`QOR_MODEL_ENDPOINT`, `QOR_MODEL_ID`, and `QOR_MODEL_API_KEY` only from the
environment and redacts credentials. It has no default endpoint or model ID.
Once the organizer supplies an OpenAI Responses entitlement, install the
documented `openai` SDK into the project environment, list authorized models,
then perform a minimal response and one function-tool request with the
organizer-authorized model. Record status, model ID, tool support, latency, and
the SHA-256 hash of the answer, never the key or private spreadsheets.

## Planned application adapter

The later `qor.ai` adapter will declare provider capabilities (responses,
structured-output/tool calling, timeout and limits). It will expose only
`inspect_data`, `calculate_plan`, `simulate_policy`, `explain_sku`, and
`build_order_draft`. Deterministic Python remains authoritative for all order
quantities; the model cannot approve, export, or dispatch an order.

## Smoke-test result

**Not run: missing participant entitlement.** This stage is not passed, and no
mock result is represented as a live integration.
