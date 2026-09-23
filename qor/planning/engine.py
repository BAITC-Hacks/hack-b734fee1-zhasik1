from __future__ import annotations
from datetime import date, timedelta
import math

def project_inventory(free_stock, daily_demand, inbound, days, start):
    qty=float(free_stock); rows=[]
    for day in range(1, days+1):
        current=start+timedelta(days=day); arriving=sum(float(x["quantity"]) for x in inbound if x.get("eta")==current)
        qty += arriving-float(daily_demand); rows.append({"day":day,"date":current,"inbound":arriving,"projected_stock":qty})
    return rows

def recommend_order(*, supplier, sku, unit, snapshot_date:date, free_stock, daily_demand, inbound=(), lead_days=14, review_days=7, buffer_days=7, moq=None, pack_multiple=None, calculation_run_id="run"):
    if free_stock is None: return {"supplier":supplier,"sku":sku,"unit":unit,"raw_need":None,"recommended_qty":None,"urgency":"needs_stock_input","shortage_date":None,"assumptions":["current stock missing; not treated as zero"]}
    known=[x for x in inbound if x.get("eta") is not None]; unknown=[x for x in inbound if x.get("eta") is None]
    timeline=project_inventory(free_stock,daily_demand,known,lead_days+review_days+buffer_days,snapshot_date)
    shortage=next((r["date"] for r in timeline if r["projected_stock"]<0),None)
    needs=[]
    for r in timeline:
        if lead_days <= r["day"] <= lead_days+review_days:
            buffer=float(daily_demand)*buffer_days; needs.append(max(0.0, buffer-r["projected_stock"]))
    raw=max(needs,default=0.0); rounded=raw
    if raw>0 and moq is not None: rounded=max(rounded,float(moq))
    if raw>0 and pack_multiple: rounded=math.ceil(rounded/float(pack_multiple))*float(pack_multiple)
    urgency="expedite" if shortage and shortage < snapshot_date+timedelta(days=lead_days) else ("high" if raw>0 else "none")
    assumptions=[]
    if unknown: assumptions.append("inbound with unknown ETA excluded from confirmed schedule")
    return {"supplier":supplier,"sku":sku,"unit":unit,"raw_need":raw,"recommended_qty":rounded,"urgency":urgency,"shortage_date":shortage,"timeline":timeline,"assumptions":assumptions,"calculation_run_id":calculation_run_id}
