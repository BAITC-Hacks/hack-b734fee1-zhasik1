from datetime import date
import numpy as np
import pandas as pd
import pytest
from qor.contracts import Policy
from qor.demand.forecast import clean_demand, compensate_stockouts, monthly_history, seasonal_profile, forecast_month, forecast_demand, evaluate, evaluation_metrics


def events(values, start="2025-01-01"):
    dates=pd.date_range(start,periods=len(values))
    return pd.DataFrame(dict(supplier="S",sku="001",unit="pcs",date=dates,quantity=values,document=[f"D{i}" for i in range(len(values))],event_id=[f"E{i}" for i in range(len(values))]))


def test_outlier_review_is_effective_only_after_decision_date():
    data=events([10]*30+[10000])
    decision=dict(event_id="E30",action="exclude",decided_at="2025-02-02",actor="manager",reason="Confirmed project purchase")
    before=clean_demand(data,decisions=[decision],as_of=date(2025,2,1))
    after=clean_demand(data,decisions=[decision],as_of=date(2025,2,2))
    assert before.iloc[-1].candidate and before.iloc[-1].clean_quantity==10000
    assert after.iloc[-1].clean_quantity==0 and len(after)==31


def test_split_large_document_is_flagged_as_a_document():
    data=events([10]*30+[60])
    repeat=pd.concat([data.iloc[-1:]]*3,ignore_index=True)
    result=clean_demand(pd.concat([data.iloc[:-1],repeat],ignore_index=True))
    assert result.candidate.sum()==3


def test_anonymized_single_client_spike_is_bounded_until_reviewed():
    base=events([10]*10+[10000])
    base["client_id_anonymized"]=["client-regular"]*10+["client-one-off"]
    flagged=clean_demand(base,as_of=date(2025,1,11))
    assert flagged.iloc[-1].client_candidate
    assert flagged.iloc[-1].clean_quantity==10000  # source observation preserved
    assert flagged.iloc[-1].forecast_quantity < 1000
    larger=base.copy()
    larger.loc[larger.index[-1],"quantity"]=100000
    a,_=monthly_history(base,date(2025,2,1))
    b,_=monthly_history(larger,date(2025,2,1))
    pd.testing.assert_series_equal(a,b)  # regular forecast insensitive to spike magnitude
    keep=dict(event_id="E10",action="keep",decided_at="2025-01-12",actor="manager",reason="Recurring contract confirmed")
    reviewed=clean_demand(base,decisions=[keep],as_of=date(2025,1,12))
    assert reviewed.iloc[-1].forecast_quantity==10000


def test_sustained_growth_retained_and_no_future_leakage():
    base=events([10]*100+[15]*100)
    full=pd.concat([base,events([100000],"2026-01-01")],ignore_index=True)
    clean=clean_demand(full,as_of=date(2025,8,1))
    assert not clean.candidate.any()
    assert clean.clean_quantity.sum()==2500
    pd.testing.assert_frame_equal(clean,clean_demand(base,as_of=date(2025,8,1)))


def test_returns_not_negative_demand_and_missing_kept():
    out=clean_demand(events([10,-7,None,0]))
    assert out.clean_quantity.sum()==10 and out.clean_quantity.isna().sum()==2
    assert out.is_return.sum()==1


def test_stockout_compensation_confirmed_only_once_and_prior_history():
    data=clean_demand(events([10]*10+[0]*3))
    interval=dict(start="2025-01-11",end="2025-01-13",confirmed_at="2025-01-14",evidence="Inventory log",provenance="synthetic")
    not_yet,_=compensate_stockouts(data,[interval],date(2025,1,13))
    confirmed,notes=compensate_stockouts(data,[interval,interval],date(2025,1,14))
    assert not_yet.sum()==100 and confirmed.sum()==130
    assert "synthetic" in notes[0]


def test_incomplete_september_and_future_sales_excluded():
    d=events([10]*31,"2026-08-01")
    d=pd.concat([d,events([999999],"2026-09-01"),events([999999],"2026-10-01")])
    series,_=monthly_history(d,date(2026,9,22))
    assert str(series.index[-1])=="2026-08" and series.sum()==310


def test_seasonality_uses_completed_year_and_changes_by_month():
    index=pd.period_range("2025-01","2026-08",freq="M")
    series=pd.Series([100]*6+[200]*6+[100]*6+[200]*2,index=index,dtype=float)
    profile,_=seasonal_profile(series,date(2026,9,22))
    assert profile[7]==pytest.approx(profile[1]*2)
    extended=pd.concat([series,pd.Series([999999],index=pd.PeriodIndex(["2026-12"],freq="M"))])
    pd.testing.assert_series_equal(profile,seasonal_profile(extended,date(2026,9,22))[0])


def test_file_growth_applied_exactly_once():
    series=pd.Series([100]*12+[900]*8,index=pd.period_range("2025-01","2026-08",freq="M"))
    result=forecast_month(series,pd.Period("2026-09"),policy=Policy(growth_mode="file",file_growth=.1))
    assert result==pytest.approx(110)  # not recent level * growth and not twice


def test_hypothetical_stockout_only_changes_scenario_forecast():
    d=events([10]*600)
    plain=forecast_demand(d,date(2026,9,22),28)
    scenario=forecast_demand(d,date(2026,9,22),28,Policy(hypothetical_stockout_days=7))
    assert scenario["daily"].demand.sum()==pytest.approx(plain["daily"].demand.sum()*30/23)
    assert any("HYPOTHETICAL" in a for a in scenario["assumptions"])


def test_evaluation_is_time_ordered_and_metrics_group_units():
    d=events([10]*600)
    result=evaluate(d,date(2026,9,22),max_origins=2)
    future=pd.concat([d,events([100000],"2027-01-01")])
    pd.testing.assert_frame_equal(result,evaluate(future,date(2026,9,22),max_origins=2))
    assert set(result.method)=={"seasonal","mean3"}
    metrics=evaluation_metrics(result)
    assert set(metrics.unit)=={"pcs"} and metrics.WAPE_pct.notna().all()
    assert np.isfinite(metrics.bias_pct).all()
