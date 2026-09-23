"""Chronological local CPU comparison; writes only ignored derived evidence."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import sklearn
from qor.data import load_sources
from qor.demand.challenger import FEATURES, make_panel, evaluate_panel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iek", type=Path, required=True)
    parser.add_argument("--max-skus", type=int, default=100, help="Largest observed SKU histories; experiment subset")
    parser.add_argument("--lead-days", type=int, default=14)
    parser.add_argument("--review-days", type=int, default=7)
    parser.add_argument("--output", type=Path, default=Path("runtime/forecast_evaluation.json"))
    args = parser.parse_args()
    if args.max_skus < 1:
        parser.error("--max-skus must be positive")
    horizon = args.lead_days + args.review_days
    if not 1 <= horizon <= 120:
        parser.error("lead + review must be in 1..120")
    before = sha256(args.iek.read_bytes()).hexdigest()
    started = perf_counter()
    bundle = load_sources([args.iek])
    panel = make_panel(bundle, horizon_days=horizon, max_skus=args.max_skus)
    predictions, metrics = evaluate_panel(panel)
    after = sha256(args.iek.read_bytes()).hexdigest()
    if after != before:
        raise RuntimeError("Original workbook/archive changed")
    report = dict(
        kind="READ-ONLY OFFLINE EXPERIMENT; no model is deployed by this command",
        source_sha256=before, snapshot=str(bundle.snapshot), horizon_days=horizon,
        manifest_fingerprint=sha256(json.dumps(bundle.manifest, sort_keys=True).encode()).hexdigest(),
        panel_skus=sorted(set(zip(panel.supplier, panel.sku))) if not panel.empty else [],
        max_skus=args.max_skus, panel_rows=len(panel), held_out_rows=len(predictions),
        elapsed_seconds=round(perf_counter() - started, 3),
        model="sklearn.ensemble.HistGradientBoostingRegressor",
        sklearn_version=sklearn.__version__, features=list(FEATURES),
        selected=metrics.to_dict("records"), source_unchanged=True,
        limits=["Largest-history SKU subset, not supplier-wide validation",
                "Observed sales are a proxy for demand without confirmed stockout intervals",
                "September 2026 is excluded as an incomplete target",
                "No model artifact is trusted or loaded by the purchasing app"],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    unique = metrics.drop_duplicates(["supplier", "unit", "segment"]) if not metrics.empty else metrics
    print(json.dumps(dict(panel_rows=len(panel), held_out_rows=len(predictions),
                          selection=unique[["supplier", "unit", "segment", "selected_method", "selected_wape_pct", "selected_bias_pct"]].to_dict("records") if not unique.empty else []),
                     ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
