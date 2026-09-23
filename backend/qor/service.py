"""Application orchestration shared by Streamlit and bounded AI tools."""
from datetime import date, timedelta
import math
import numpy as np
import pandas as pd
from qor.contracts import Policy, StockInput, KEY
from qor.demand import forecast_demand
from qor.planning import recommend_order

def item_catalog(bundle):
    frames = [t[KEY + ["unit"]] for t in (bundle.sales, bundle.monthly, bundle.stock) if not t.empty]
    if not frames:
        return pd.DataFrame(columns=KEY+["unit"])
    return pd.concat(frames).drop_duplicates(KEY).sort_values(KEY).reset_index(drop=True)

def _groups(df):
    return {k:g for k,g in df.groupby(KEY, sort=False)} if not df.empty else {}

def _optional(value):
    return None if value is None or pd.isna(value) else value

def calculate_plan(bundle, policy, *, keys=None, stock_inputs=(), decisions=(), stockouts=None):
    policy = Policy.model_validate(policy)
    inputs = {(s.supplier,s.sku):s for s in [StockInput.model_validate(x) for x in stock_inputs]}
    sales, months, stocks, incoming, rules = [_groups(getattr(bundle,c)) for c in ("sales","monthly","stock","inbound","policies")]
    rows = []
    catalog = item_catalog(bundle)
    for item in catalog.to_dict("records"):
        key = (item["supplier"],item["sku"])
        if keys is not None and key not in keys:
            continue
        row = dict(item, snapshot_date=str(bundle.snapshot), raw_need=None, recommended_qty=None, urgency="data_conflict", assumptions=[], timeline=[])
        if key in bundle.blocked_keys or pd.isna(item["unit"]):
            row["assumptions"] = ["Conflicting data or missing unit: review input before calculation"]
            rows.append(row)
            continue
        stock_table = stocks.get(key)
        st = stock_table.iloc[0].to_dict() if stock_table is not None else {}
        if key in inputs:
            s = inputs[key]
            if s.unit != item["unit"]:
                raise ValueError("Manual stock unit mismatch")
            st = dict(free_stock=s.free_stock, as_of=s.as_of, source=f"manager:{s.actor}: {s.reason}", provenance="manager supplied")
        stock = _optional(st.get("free_stock"))
        if stock is None or _optional(st.get("as_of")) != bundle.snapshot:
            row.update(free_stock=stock, stock_date=str(st.get("as_of")) if st.get("as_of") else None,
                       source_stock=st.get("source"), urgency="needs_stock_input" if stock is None else "needs_dated_stock",
                       assumptions=["Current available stock and its snapshot date must be evidenced; missing values are not zero"])
            rows.append(row)
            continue
        rule = rules[key].iloc[0].to_dict() if key in rules else {}
        moq, pack = _optional(rule.get("moq")), _optional(rule.get("pack_multiple"))
        assumptions = []
        inbound = incoming[key].to_dict("records") if key in incoming else []
        unit_inferred = bool(rule.get("unit_inferred",False)) or any(x.get("unit_inferred",False) for x in inbound)
        if unit_inferred and not policy.accept_unit_mapping:
            row.update(urgency="needs_unit_confirmation", free_stock=stock, assumptions=["Confirm purchase quantities use the unique sales unit before using MOQ or inbound"])
            if stock is None:
                row["urgency"] = "needs_stock_input"
            rows.append(row)
            continue
        if unit_inferred:
            assumptions.append("Manager-confirmed scenario: unitless purchase values mapped to sales unit, conversion factor 1")
        if rule.get("ambiguous_moq"):
            assumptions.append(f"IEK ambiguous dispatch field interpreted as {policy.iek_moq_mode}")
            if policy.iek_moq_mode == "multiple":
                pack, moq = moq, None
        for shipment in inbound:
            eta = _optional(shipment.get("eta"))
            if eta is None and policy.unknown_eta:
                eta = policy.unknown_eta
                assumptions.append("Scenario assigns a date to unknown ETA")
            if eta:
                eta += timedelta(days=policy.eta_shift_days)
            shipment["eta"] = eta
            if shipment.get("quantity") is None or pd.isna(shipment["quantity"]):
                assumptions.append("Missing inbound quantity excluded")
                shipment["quantity"] = 0
        category = str(rule.get("category") or "")
        buffer = policy.category_buffers.get(category,policy.buffer_days)
        if buffer != policy.buffer_days:
            assumptions.append(f"Category {category}: buffer {buffer} days")
        history = sales.get(key, bundle.sales.iloc[:0])
        forecast = forecast_demand(history,bundle.snapshot,policy.lead_days+policy.review_days+buffer,policy,decisions,(stockouts or {}).get(key,()),months.get(key))
        if forecast["daily"].demand.isna().any():
            row.update(urgency="needs_demand_input",assumptions=forecast["assumptions"]+["Insufficient observed demand / prior-year growth base"])
            rows.append(row)
            continue
        result = recommend_order(**item,snapshot_date=bundle.snapshot,free_stock=stock,stock_date=_optional(st.get("as_of")),demand=forecast["daily"].demand.tolist(),inbound=inbound,lead_days=policy.lead_days,review_days=policy.review_days,buffer_days=buffer,moq=moq,pack_multiple=pack,reserved=_optional(st.get("reserved")))
        result.update(article=str(rule.get("article") or ""), category=category, source_stock=st.get("source"), source_policy=rule.get("source"), forecast_method=forecast["method"], candidate_count=forecast["candidate_count"], forecast_history={str(k): None if pd.isna(v) else float(v) for k,v in forecast["history"].items()}, source_sales=history.source.head(5).tolist(), provenance="synthetic" if not history.empty and set(history.provenance)=={"synthetic"} else "actual sources / calculated recommendation")
        result["assumptions"] += forecast["assumptions"] + assumptions
        result["assumptions"].append("MOQ absent: no minimum enforced" if moq is None else f"Minimum order: {moq}")
        result["assumptions"].append("Pack multiple absent: fractional quantities possible; manager review required" if pack is None else f"Pack multiple: {pack}")
        rows.append(result)
    return rows
