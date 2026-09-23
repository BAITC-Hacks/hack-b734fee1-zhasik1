"""Local CPU challenger evaluated at the planner's lead-plus-review horizon.

Every feature is calculated from completed periods before its forecast origin.
The one-off-sale limits are causal at each transaction date, so building the
panel once cannot let later sales change an earlier feature.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from qor.contracts import KEY
from qor.demand.forecast import clean_demand, forecast_month, seasonal_profile

FEATURES = (
    "lag1", "lag2", "lag3", "lag6", "lag12", "recent3", "recent6",
    "slope3", "observed12", "zero_share12", "month_sin", "month_cos",
)


def _month_series(events: pd.DataFrame, monthly: pd.DataFrame, snapshot: date) -> pd.Series:
    cleaned = clean_demand(events, as_of=snapshot)
    if cleaned.empty:
        series = pd.Series(dtype=float)
    else:
        period = pd.to_datetime(cleaned.date).dt.to_period("M")
        series = cleaned.groupby(period).forecast_quantity.sum(min_count=1)
        series = series[series.index >= pd.Period("2025-01")]
    if monthly is not None and not monthly.empty:
        early = monthly.copy()
        periods = pd.to_datetime(early.month).dt.to_period("M")
        values = early.assign(period=periods).loc[periods.dt.year.eq(2024)].groupby("period").quantity.sum(min_count=1)
        series = pd.concat([values, series]).sort_index()
    series = series[series.index < pd.Period(snapshot, freq="M")]
    if len(series):
        series = series.reindex(pd.period_range(series.index.min(), series.index.max(), freq="M"))
    return series.astype(float)


def _features(series: pd.Series, origin: date) -> dict | None:
    target = pd.Period(origin, freq="M")
    prior = series[series.index < target]
    recent = prior.reindex(pd.period_range(target - 12, target - 1))
    if recent.notna().sum() < 6:
        return None
    last3 = recent.iloc[-3:]
    last6 = recent.iloc[-6:]
    valid3 = last3.dropna()
    result = {}
    for lag in (1, 2, 3, 6, 12):
        v = recent.iloc[-lag]
        result[f"lag{lag}"] = float(v) if pd.notna(v) else np.nan
    result["recent3"] = float(valid3.mean()) if len(valid3) else np.nan
    result["recent6"] = float(last6.mean()) if last6.notna().any() else np.nan
    result["slope3"] = float(valid3.iloc[-1] - valid3.iloc[0]) if len(valid3) >= 2 else np.nan
    result["observed12"] = int(recent.notna().sum())
    result["zero_share12"] = float(recent.eq(0).sum() / max(1, recent.notna().sum()))
    result["month_sin"] = float(np.sin(2 * np.pi * target.month / 12))
    result["month_cos"] = float(np.cos(2 * np.pi * target.month / 12))
    result["segment"] = "intermittent" if recent.fillna(0).gt(0).sum() < 6 else "regular"
    return result


def _baseline(series: pd.Series, origin: date, days: int, method: str) -> float:
    train = series[series.index < pd.Period(origin, freq="M")]
    factors, _ = seasonal_profile(train, origin)
    dates = pd.date_range(origin + timedelta(days=1), periods=days)
    total = 0.0
    for target, count in pd.Series(dates.to_period("M")).value_counts().items():
        monthly = forecast_month(train, target, method, factors)
        if not np.isfinite(monthly):
            return np.nan
        total += max(0.0, monthly) * count / calendar.monthrange(target.year, target.month)[1]
    return float(total)


def make_panel(bundle, *, horizon_days=21, max_skus=None) -> pd.DataFrame:
    """Build causal SKU-origin examples; targets require observed transactions."""
    if horizon_days < 1 or horizon_days > 120:
        raise ValueError("horizon_days must be in 1..120")
    sales = bundle.sales
    if sales.empty:
        return pd.DataFrame()
    groups = list(sales.groupby(KEY + ["unit"], dropna=False, sort=False))
    if max_skus is not None:
        groups = sorted(groups, key=lambda pair: len(pair[1]), reverse=True)[:max_skus]
    monthly_groups = {
        key: frame for key, frame in bundle.monthly.groupby(KEY, sort=False)
    } if not bundle.monthly.empty else {}
    origins = pd.date_range("2025-05-01", bundle.snapshot, freq="MS").date
    records = []
    for (supplier, sku, unit), events in groups:
        series = _month_series(events, monthly_groups.get((supplier, sku)), bundle.snapshot)
        event_dates = pd.to_datetime(events.date).dt.date
        quantity = pd.to_numeric(events.quantity, errors="coerce")
        for origin in origins:
            end = origin + timedelta(days=horizon_days)
            if end > bundle.snapshot or end >= pd.Period(bundle.snapshot, freq="M").start_time.date():
                continue  # September 2026 is incomplete, even if partly observed.
            features = _features(series, origin)
            if features is None:
                continue
            mask = event_dates.gt(origin) & event_dates.le(end)
            if not mask.any():
                continue  # An unobserved target is not a zero-sales month.
            actual = float(quantity.loc[mask & quantity.ge(0)].sum())
            row = dict(supplier=supplier, sku=sku, unit=unit, origin=origin.isoformat(),
                       label_end=end.isoformat(), horizon_days=horizon_days, actual=actual,
                       seasonal=_baseline(series, origin, horizon_days, "seasonal"),
                       mean3=_baseline(series, origin, horizon_days, "mean3"), **features)
            if np.isfinite(row["seasonal"]) and np.isfinite(row["mean3"]):
                records.append(row)
    return pd.DataFrame.from_records(records)


def _metrics(frame: pd.DataFrame, method: str) -> dict:
    actual = frame.actual.to_numpy(dtype=float)
    predicted = frame.predicted.to_numpy(dtype=float)
    error = predicted - actual
    denominator = float(actual.sum())
    return dict(method=method, observations=len(frame),
                wape_pct=100 * float(np.abs(error).sum()) / denominator if denominator > 0 else None,
                mae=float(np.abs(error).mean()), bias=float(error.mean()),
                bias_pct=100 * float(error.sum()) / denominator if denominator > 0 else None)


def evaluate_panel(panel: pd.DataFrame, *, holdout_origins=3, min_train=100, min_skus=10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chronological refit per origin and supplier/unit/intermittency segment."""
    if panel.empty:
        return pd.DataFrame(), pd.DataFrame()
    predictions = []
    for (supplier, unit, segment), group in panel.groupby(["supplier", "unit", "segment"], dropna=False):
        origins = sorted(group.origin.unique())
        for origin in origins[-holdout_origins:]:
            train = group[group.label_end < origin]
            test = group[group.origin.eq(origin)]
            fitted = None
            runtime = None
            if len(train) >= min_train and train.sku.nunique() >= min_skus:
                started = perf_counter()
                fitted = HistGradientBoostingRegressor(
                    max_iter=100, max_leaf_nodes=15, min_samples_leaf=20,
                    learning_rate=0.05, l2_regularization=1.0, random_state=0,
                    early_stopping=False,
                ).fit(train[list(FEATURES)], train.actual)
                runtime = perf_counter() - started
            for row in test.to_dict("records"):
                for method in ("seasonal", "mean3", "hgb"):
                    if method == "hgb" and fitted is None:
                        continue
                    predicted = (float(fitted.predict(pd.DataFrame([row])[list(FEATURES)])[0])
                                 if method == "hgb" else row[method])
                    predictions.append(dict(supplier=supplier, unit=unit, segment=segment,
                                            sku=row["sku"], origin=origin, actual=row["actual"],
                                            method=method, predicted=max(0.0, predicted),
                                            training_rows=len(train) if method == "hgb" else None,
                                            fit_seconds=runtime if method == "hgb" else None))
    pred = pd.DataFrame(predictions)
    if pred.empty:
        return pred, pd.DataFrame()
    metrics = []
    for (supplier, unit, segment, method), part in pred.groupby(["supplier", "unit", "segment", "method"], dropna=False):
        metrics.append(dict(supplier=supplier, unit=unit, segment=segment, **_metrics(part, method)))
    metric_frame = pd.DataFrame(metrics)
    choices = []
    for key, group in metric_frame.groupby(["supplier", "unit", "segment"], dropna=False):
        baseline = group[group.method.isin(("seasonal", "mean3"))].sort_values("wape_pct", na_position="last")
        if baseline.empty:
            continue
        selected = baseline.iloc[0]
        challenger = group[group.method.eq("hgb")]
        if len(challenger) and selected.wape_pct is not None:
            candidate = challenger.iloc[0]
            if (candidate.observations == selected.observations
                    and candidate.wape_pct is not None
                    and candidate.wape_pct <= 0.95 * selected.wape_pct
                    and abs(candidate.bias_pct) <= abs(selected.bias_pct) + 5):
                selected = candidate
        choices.append(dict(zip(("supplier", "unit", "segment"), key),
                            selected_method=selected.method, selected_wape_pct=selected.wape_pct,
                            selected_bias_pct=selected.bias_pct))
    return pred, metric_frame.merge(pd.DataFrame(choices), on=["supplier", "unit", "segment"], how="left")
