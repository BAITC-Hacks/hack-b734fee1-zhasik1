"""Read-only, source-bound selection of a tested baseline method."""

from hashlib import sha256
import json
from pathlib import Path

from qor.demand.challenger import _features
from qor.demand.forecast import monthly_history

REPORT = Path(__file__).resolve().parents[3] / "runtime" / "forecast_evaluation.json"


def select_forecast_method(bundle, events, monthly, policy, *, decisions=(), stockouts=()):
    if policy.forecast_method != "auto":
        return policy.forecast_method, ["Forecast method explicitly selected by manager"]
    fallback = ("seasonal", ["No matching held-out evaluation: seasonal baseline used; method not validated for this source/SKU"])
    if events.empty or not REPORT.exists():
        return fallback
    reviewed_ids = {d.get("event_id") if isinstance(d, dict) else d.event_id for d in decisions}
    if (stockouts or policy.growth_mode != "observed" or policy.hypothetical_stockout_days
            or ("event_id" in events and events.event_id.isin(reviewed_ids).any())):
        return "seasonal", ["Demand evidence or growth scenario differs from the held-out experiment; seasonal baseline fallback"]
    try:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        fingerprint = sha256(json.dumps(bundle.manifest, sort_keys=True).encode()).hexdigest()
        if (report.get("manifest_fingerprint") != fingerprint
                or report.get("snapshot") != str(bundle.snapshot)
                or report.get("horizon_days") != policy.lead_days + policy.review_days):
            return fallback
        supplier, sku, unit = events.iloc[0][["supplier", "sku", "unit"]]
        if [supplier, sku] not in report.get("panel_skus", []):
            return fallback
        series, _ = monthly_history(events, bundle.snapshot, monthly_2024=monthly)
        features = _features(series, bundle.snapshot)
        if features is None:
            return fallback
        matches = [row for row in report.get("selected", [])
                   if row.get("supplier") == supplier and row.get("unit") == unit
                   and row.get("segment") == features["segment"]]
        if not matches:
            return fallback
        selected = matches[0].get("selected_method")
        if selected not in ("seasonal", "mean3"):
            return "seasonal", ["Held-out ML candidate selected but no trusted deployed artifact; seasonal fallback used"]
        return selected, [f"Source-matched {policy.lead_days + policy.review_days}-day held-out group selection: {selected}; sampled SKU cohort"]
    except (OSError, ValueError, KeyError, TypeError):
        return fallback
