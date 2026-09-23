from datetime import timedelta
from hashlib import sha256
import json
import pandas as pd
from qor.contracts import Policy
from qor.data.demo import demo_bundle
from qor.demand.challenger import FEATURES, evaluate_panel
from qor.demand import selection


def test_challenger_held_out_prediction_does_not_see_later_label():
    origins = pd.date_range("2026-01-01", periods=8, freq="MS")
    rows = []
    for i, origin in enumerate(origins):
        for sku in range(12):
            row = dict(supplier="Synthetic", unit="pcs", segment="regular",
                       sku=f"S{sku}", origin=origin.date().isoformat(),
                       label_end=(origin.date() + timedelta(days=21)).isoformat(),
                       actual=float(20 + i + sku), seasonal=20.0, mean3=22.0)
            row.update({name: float(i + sku + j) for j, name in enumerate(FEATURES)})
            rows.append(row)
    panel = pd.DataFrame(rows)
    first, metrics = evaluate_panel(panel, holdout_origins=2, min_train=20, min_skus=10)
    assert not metrics.empty and "hgb" in first.method.values
    changed = panel.copy()
    changed.loc[changed.origin.eq("2026-08-01"), "actual"] = 100000
    second, _ = evaluate_panel(changed, holdout_origins=2, min_train=20, min_skus=10)
    prior = "2026-07-01"
    pd.testing.assert_frame_equal(
        first.loc[first.origin.eq(prior)].drop(columns="fit_seconds").reset_index(drop=True),
        second.loc[second.origin.eq(prior)].drop(columns="fit_seconds").reset_index(drop=True),
    )


def test_auto_selection_requires_exact_source_and_horizon(tmp_path, monkeypatch):
    bundle = demo_bundle()
    events = bundle.sales[bundle.sales.supplier.eq("Systeme Electric")]
    report = dict(
        manifest_fingerprint=sha256(json.dumps(bundle.manifest, sort_keys=True).encode()).hexdigest(),
        snapshot=str(bundle.snapshot), horizon_days=21,
        panel_skus=[["Systeme Electric", "SYN-0007_"]],
        selected=[dict(supplier="Systeme Electric", unit="pcs", segment="regular", selected_method="mean3")],
    )
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(selection, "REPORT", path)
    method, _ = selection.select_forecast_method(bundle, events, None, Policy())
    assert method == "mean3"
    method, _ = selection.select_forecast_method(bundle, events, None, Policy(), decisions=[dict(event_id=events.iloc[0].event_id)])
    assert method == "seasonal"
    method, notes = selection.select_forecast_method(bundle, events, None, Policy(review_days=14))
    assert method == "seasonal" and "No matching" in notes[0]
