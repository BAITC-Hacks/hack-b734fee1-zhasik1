"""Deterministic causal cleaning, seasonal forecasts and rolling-origin evaluation."""
from datetime import date, timedelta
import calendar
import numpy as np
import pandas as pd
from qor.contracts import KEY, Policy, Stockout, OutlierDecision


def clean_demand(events, exclude_outliers=False, decisions=(), as_of=None, detect_candidates=True):
    """Candidate flags use only prior transactions. Removal needs a dated decision.

    exclude_outliers=True is a hypothetical capped/excluded scenario, never default.
    Returns and blanks remain present with a separate clean_quantity column.
    """
    df = events.copy()
    if df.empty:
        return df.assign(candidate=False, outlier=False, clean_quantity=pd.Series(dtype=float), forecast_quantity=pd.Series(dtype=float))
    for col, default in {"supplier":"synthetic", "sku":"synthetic", "document":"", "event_id":"", "unit":"pcs"}.items():
        if col not in df:
            df[col] = default
    df["date"] = pd.to_datetime(df.date, errors="coerce")
    if as_of:
        df = df[df.date.dt.date <= as_of].copy()
    df["quantity"] = pd.to_numeric(df.quantity, errors="coerce")
    df = df.sort_values(KEY + ["date"], kind="stable")
    df["candidate"] = False
    df["threshold"] = np.nan
    # Document+day granularity prevents splitting a large purchase into small lines.
    group_cols = KEY + ["date", "document"]
    docs = df[df.quantity > 0].groupby(group_cols, dropna=False, as_index=False).quantity.sum() if detect_candidates else pd.DataFrame(columns=group_cols+["quantity"])
    for _, group in docs.groupby(KEY, sort=False):
        group = group.sort_values("date")
        logs = np.log1p(group.quantity)
        prior = logs.shift(1).rolling(60, min_periods=20)
        med = prior.median()
        mad = prior.apply(lambda a: np.nanmedian(np.abs(a - np.nanmedian(a))), raw=True)
        # Zero-MAD flags are conservative candidates only; human review still required.
        threshold = np.expm1(med + 6 * mad)
        threshold = np.maximum(threshold, np.expm1(med) * 10)
        docs.loc[group.index, "threshold"] = threshold
    if not docs.empty:
        # Optional anonymized-client concentration is a separate causal signal.
        # No client identity is invented when the source column is absent.
        docs["client_candidate"] = False
        docs["client_threshold"] = np.nan
        if "client_id_anonymized" in df:
            identities = df.groupby(group_cols, dropna=False).client_id_anonymized.agg(
                lambda s: s.dropna().iloc[0] if len(s.dropna().unique()) == 1 else None
            ).reset_index()
            docs = docs.merge(identities, on=group_cols, how="left", validate="one_to_one")
            for _, group in docs.groupby(KEY, sort=False):
                ordered = group.sort_values("date")
                prior = ordered.set_index("date").quantity.rolling("60D", closed="left", min_periods=5)
                med, total = prior.median().to_numpy(), prior.sum().to_numpy()
                limit = np.maximum(5 * med, 0.5 * total)
                qty = ordered.quantity.to_numpy()
                concentrated = qty / (total + qty) > 0.6
                flagged = ordered.client_id_anonymized.notna().to_numpy() & concentrated & (qty > limit)
                docs.loc[ordered.index, "client_candidate"] = flagged
                docs.loc[ordered.index, "client_threshold"] = np.where(flagged, limit, np.nan)
        docs["threshold"] = docs[["threshold", "client_threshold"]].min(axis=1, skipna=True)
        doc_flags = docs.rename(columns={"quantity":"document_quantity"})
        df = df.drop(columns="threshold").merge(doc_flags[group_cols + ["threshold", "document_quantity", "client_candidate"]], on=group_cols, how="left", validate="many_to_one")
        df["candidate"] = ((df.document_quantity > df.threshold) | df.client_candidate.eq(True)) & (df.quantity > 0)
    else:
        df["client_candidate"] = False
    df["outlier"] = df.candidate
    df["is_return"] = df.quantity < 0
    df["clean_quantity"] = df.quantity.where(df.quantity >= 0)  # returns are not negative demand
    df["decision"] = "unreviewed"
    for item in decisions:
        d = OutlierDecision.model_validate(item)
        if as_of and d.decided_at > as_of:
            continue
        mask = df.event_id.eq(d.event_id)
        df.loc[mask, "decision"] = d.action
        if d.action == "exclude":
            df.loc[mask, "clean_quantity"] = 0.0
    if exclude_outliers:
        df.loc[df.candidate, "clean_quantity"] = 0.0
        df["scenario"] = "hypothetical candidate removal"
    # Keep the reviewed/raw series intact. Until reviewed, cap only the
    # forecasting contribution of a candidate document at its causal limit.
    share = df.quantity / df.document_quantity.replace(0, np.nan)
    cap = df.threshold * share
    df["forecast_quantity"] = df.clean_quantity.astype(float)
    unreviewed = df.candidate & df.decision.eq("unreviewed") & cap.notna()
    df.loc[unreviewed, "forecast_quantity"] = np.minimum(df.loc[unreviewed, "clean_quantity"], cap.loc[unreviewed])
    return df


def compensate_stockouts(cleaned, intervals, as_of):
    """Impute once per confirmed day from prior available calendar days only."""
    df = cleaned.copy()
    dates = pd.to_datetime(df.date)
    daily = df.groupby(dates.dt.normalize()).forecast_quantity.sum(min_count=1)
    additions = {}
    notes = []
    for raw in intervals:
        item = Stockout.model_validate(raw)
        if item.confirmed_at > as_of:
            continue
        prior = daily.loc[(daily.index < pd.Timestamp(item.start)) & (daily.index >= pd.Timestamp(item.start - timedelta(days=60)))]
        if prior.empty or prior.notna().sum() < 3:
            notes.append("Confirmed stockout lacks prior available history; no compensation")
            continue
        elapsed = (pd.Timestamp(item.start) - prior.index.min()).days
        rate = max(0.0, float(prior.sum()) / max(1, elapsed))
        for day in pd.date_range(item.start, min(item.end, as_of)):
            observed = daily.get(day, 0.0)
            observed = 0.0 if pd.isna(observed) else observed
            additions[day] = max(additions.get(day, 0), rate - observed, 0)
        notes.append(f"{item.provenance}: confirmed interval {item.start}..{item.end}; estimate {rate:.4f}/day; {item.evidence}")
    adjusted = daily.add(pd.Series(additions, dtype=float), fill_value=0).sort_index()
    return adjusted, notes


def monthly_history(events, as_of, decisions=(), stockouts=(), monthly_2024=None):
    # Rebuild causal anomaly limits at every forecast origin; future rows are
    # excluded before any threshold is computed.
    clean = clean_demand(events, decisions=decisions, as_of=as_of)
    daily, notes = compensate_stockouts(clean, stockouts, as_of)
    series = daily.groupby(daily.index.to_period("M")).sum(min_count=1)
    # 2025+ transactional history; 2024 is a separate monthly source, never overlapped.
    series = series[series.index >= pd.Period("2025-01")]
    if monthly_2024 is not None and not monthly_2024.empty:
        early = monthly_2024.copy()
        early["period"] = pd.to_datetime(early.month).dt.to_period("M")
        early = early[(early.period.dt.year == 2024) & (early.period < pd.Period(as_of, freq="M"))]
        extra = early.groupby("period").quantity.sum(min_count=1)
        extra = extra.where(extra >= 0)
        series = pd.concat([extra, series]).sort_index()
    series = series[series.index < pd.Period(as_of, freq="M")]
    if len(series):
        series = series.reindex(pd.period_range(series.index.min(), pd.Period(as_of, freq="M") - 1, freq="M"))
    return series.astype(float), notes


def seasonal_profile(series, origin):
    """Only full, completed years before this origin; missing months never zero-filled."""
    eligible = series[series.index < pd.Period(origin, freq="M")].dropna()
    profiles = []
    for year, group in eligible.groupby(eligible.index.year):
        if year < origin.year and len(group) == 12 and group.mean() > 0:
            profiles.append((year, pd.Series(group.values / group.mean(), index=group.index.month)))
    if not profiles:
        return pd.Series(1.0, index=range(1,13)), "No complete year: neutral seasonality scenario"
    profiles = sorted(profiles)[-2:]
    factors = profiles[-1][1] if len(profiles) == 1 else 0.25 * profiles[0][1] + 0.75 * profiles[1][1]
    factors = factors.clip(lower=0.1, upper=5.0)
    return factors / factors.mean(), "Seasonality from completed years only"


def forecast_month(series, target, method="seasonal", factors=None, policy=None):
    policy = policy or Policy()
    train = series[series.index < target]
    if policy.growth_mode == "file":
        base = train.get(target - 12, np.nan)
        return float(base * (1 + policy.file_growth)) if pd.notna(base) else np.nan
    recent = train.reindex(pd.period_range(target - 6, target - 1)).dropna()
    if recent.empty:
        return np.nan
    if method == "mean3":
        recent = train.reindex(pd.period_range(target - 3, target - 1)).dropna()
        return float(recent.mean()) if len(recent) else np.nan
    factors = seasonal_profile(train, target.start_time.date())[0] if factors is None else factors
    weights = np.arange(1, len(recent) + 1)
    level = np.average(recent.values / factors.reindex(recent.index.month).values, weights=weights)
    return max(0.0, float(level * factors[target.month]))


def forecast_demand(events, snapshot, days, policy=None, decisions=(), stockouts=(), monthly=None, method=None):
    policy = policy or Policy()
    method = method or policy.forecast_method
    auto_fallback = method == "auto"
    if method == "auto":
        method = "seasonal"  # no source-bound report is available at this low-level API
    series, notes = monthly_history(events, snapshot, decisions, stockouts, monthly)
    factors, note = seasonal_profile(series, snapshot)
    if policy.growth_mode == "file":
        note = "Previous-year base with confirmed growth; seasonal factors and recent level not additionally applied"
    elif method == "mean3":
        note = "Three-month mean baseline selected; seasonal factors not applied"
    notes += [note, "Current partial month excluded", "Absent months stay missing; estimates use observed months", "Uniform demand within calendar month", "Lead/review/buffer are scenario assumptions"]
    if auto_fallback:
        notes.append("Auto requested without source-bound evaluation at this API; seasonal fallback")
    if policy.growth_mode == "file":
        notes.append("File growth applied once to corresponding previous-year month; current level not multiplied")
    elif method == "seasonal":
        notes.append("Recent weighted level retains sustained growth; no extra trend multiplier")
    else:
        notes.append("Recent completed-month mean; no extra trend multiplier")
    dates = pd.date_range(pd.Timestamp(snapshot + timedelta(days=1)), periods=days)
    predictions = {m: forecast_month(series, m, method, factors, policy) for m in dates.to_period("M").unique()}
    values = [predictions[d.to_period("M")] / calendar.monthrange(d.year, d.month)[1] for d in dates]
    if policy.hypothetical_stockout_days:
        # Explicit sensitivity, not a claim that lost demand was measured.
        multiplier = 30 / (30 - policy.hypothetical_stockout_days)
        values = [v * multiplier for v in values]
        notes.append(f"HYPOTHETICAL unknown stockout: {policy.hypothetical_stockout_days}/30 days; multiplier {multiplier:.4f}")
    return {"daily": pd.DataFrame({"date":dates.date, "demand":values}), "history":series, "method":"prior_year_growth_once" if policy.growth_mode == "file" else method, "assumptions":notes, "candidate_count":int(clean_demand(events, as_of=snapshot).candidate.sum())}


def evaluate(events, snapshot, monthly=None, decisions=(), max_origins=6):
    """Evaluate each SKU at origins before snapshot; refit seasonality at every origin."""
    outputs = []
    if events.empty:
        return pd.DataFrame()
    groups = events.groupby(KEY + ["unit"], dropna=False)
    last = pd.Period(snapshot, freq="M") - 1
    for (supplier, sku, unit), group in groups:
        early = monthly[(monthly.supplier == supplier) & (monthly.sku == sku)] if monthly is not None and not monthly.empty else None
        for target in pd.period_range(last - max_origins + 1, last):
            origin = target.start_time.date()
            train, _ = monthly_history(group, origin, decisions, monthly_2024=early)
            # Actual is observed positive demand, not compensated future knowledge.
            dates = pd.to_datetime(group.date, errors="coerce").dt.to_period("M")
            actual_rows = group.loc[dates.eq(target), "quantity"]
            actual = actual_rows[actual_rows >= 0].sum(min_count=1)
            if train.notna().sum() < 3 or pd.isna(actual):
                continue
            for method in ("seasonal", "mean3"):
                prediction = forecast_month(train, target, method)
                if np.isfinite(prediction):
                    outputs.append(dict(supplier=supplier, unit=unit, sku=sku, origin=str(target), method=method, actual=float(actual), predicted=prediction))
    return pd.DataFrame(outputs)


def evaluation_metrics(results):
    if results.empty:
        return pd.DataFrame()
    df = results.assign(abs_error=(results.predicted-results.actual).abs(), error=results.predicted-results.actual)
    agg = df.groupby(["supplier", "unit", "method"], dropna=False).agg(actual=("actual","sum"), abs_error=("abs_error","sum"), error=("error","sum"), forecasts=("sku","size")).reset_index()
    agg["WAPE_pct"] = 100 * agg.abs_error / agg.actual.replace(0, np.nan)
    agg["bias_pct"] = 100 * agg.error / agg.actual.replace(0, np.nan)
    return agg


def forecast_daily(history, snapshot, growth_mode="observed", file_growth=None):
    result = forecast_demand(history, pd.Timestamp(snapshot).date(), 30, Policy(growth_mode=growth_mode, file_growth=file_growth))
    return {"daily_demand":result["daily"].demand.mean(), "method":result["method"], "assumptions":result["assumptions"]}
