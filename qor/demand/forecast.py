from __future__ import annotations
import numpy as np
import pandas as pd

def clean_demand(events: pd.DataFrame, exclude_outliers: bool = True) -> pd.DataFrame:
    df = events.copy(); df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["is_return"] = df["quantity"] < 0
    positive = df[df["quantity"] > 0].copy()
    if positive.empty: return positive.assign(outlier=False)
    logs = np.log1p(positive["quantity"]); med = logs.median(); mad = (logs-med).abs().median()
    positive["outlier"] = False if mad == 0 or len(positive) < 20 else logs > med + 6 * mad
    return positive[~positive.outlier].copy() if exclude_outliers else positive

def seasonal_factor(history: pd.DataFrame, target_month: int) -> float:
    if history.empty or "date" not in history: return 1.0
    df=history.copy(); df["date"]=pd.to_datetime(df.date); monthly=df.groupby(df.date.dt.to_period("M")).quantity.sum()
    if len(monthly)<12: return 1.0
    factors=monthly.groupby(monthly.index.month).mean()/monthly.mean()
    return float(factors.get(target_month, 1.0))

def forecast_daily(history: pd.DataFrame, snapshot: pd.Timestamp, growth_mode: str="observed", file_growth: float|None=None) -> dict:
    if history.empty: return {"daily_demand":0.0,"method":"no-positive-history","assumptions":["no demand history"]}
    d=history.copy(); d["date"]=pd.to_datetime(d.date); complete=d[d.date.dt.to_period("M") < snapshot.to_period("M")]
    months=complete.groupby(complete.date.dt.to_period("M")).quantity.sum().tail(6)
    weights=np.arange(1,len(months)+1); base=float(np.average(months.values,weights=weights)) if len(months) else 0.0
    factor=seasonal_factor(complete, snapshot.month); monthly=base*factor
    if growth_mode=="file" and file_growth is not None: monthly*=1+file_growth
    return {"daily_demand":max(0.0,monthly/30.4375),"method":"weighted-six-month-seasonal","assumptions":["incomplete snapshot month excluded", f"seasonality={factor:.3f}", f"growth_mode={growth_mode}"]}
