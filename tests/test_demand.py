import pandas as pd
from qor.demand import clean_demand, forecast_daily
def test_large_one_off_is_candidate():
 d=pd.DataFrame({"date":pd.date_range("2025-01-01",periods=30),"quantity":([10,11,12,13,14]*5)+[10,11,12,13,100000]})
 reviewed=clean_demand(d)
 assert len(reviewed)==30 and reviewed.candidate.sum()==1
 assert reviewed.iloc[-1].clean_quantity==100000  # no automatic destructive exclusion
def test_future_month_excluded():
 d=pd.DataFrame({"date":pd.to_datetime(["2026-07-01","2026-08-01","2026-09-25"]),"quantity":[30,30,99999]}); assert forecast_daily(d,pd.Timestamp("2026-09-22"))["daily_demand"]<10
