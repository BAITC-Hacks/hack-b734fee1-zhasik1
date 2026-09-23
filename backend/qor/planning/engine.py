"""Inventory projections depend only on deterministic, validated inputs."""
from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING
import math
from qor.contracts import Policy


def finite(value, label, nonnegative=True):
    n = float(value)
    if not math.isfinite(n) or (nonnegative and n < 0):
        raise ValueError(f"Invalid {label}")
    return n


def project_inventory(free_stock, demand, inbound, snapshot):
    stock = finite(free_stock, "free stock")
    arrivals = {}
    for item in inbound:
        if item.get("eta") is not None and item["eta"] > snapshot:
            arrivals[item["eta"]] = arrivals.get(item["eta"], 0) + finite(item["quantity"], "inbound quantity")
    timeline = []
    for offset, d in enumerate(demand, 1):
        day = snapshot + timedelta(days=offset)
        amount = finite(d, "demand")
        received = arrivals.get(day, 0)
        stock += received - amount
        timeline.append(dict(day=offset, date=day, demand=amount, inbound=received, projected_stock=stock))
    return timeline


def recommend_order(*, supplier, sku, unit, snapshot_date, free_stock, daily_demand=None, demand=None, inbound=(), lead_days=14, review_days=7, buffer_days=7, moq=None, pack_multiple=None, stock_date=None, reserved=None, calculation_run_id="unsaved", policy_unit=None):
    policy = Policy(lead_days=lead_days, review_days=review_days, buffer_days=buffer_days)
    row = dict(supplier=supplier, sku=sku, unit=unit, snapshot_date=str(snapshot_date), stock_date=str(stock_date or snapshot_date), free_stock=free_stock, moq=moq, pack_multiple=pack_multiple, lead_days=lead_days, review_days=review_days, buffer_days=buffer_days, calculation_run_id=calculation_run_id, assumptions=[], inbound=[dict(x) for x in inbound])
    row.update(raw_need=None, recommended_qty=None, shortage_date=None, urgency="needs_stock_input", timeline=[])
    if free_stock is None:
        row["assumptions"].append("Missing current available stock; zero was not assumed")
        return row
    if stock_date and stock_date != snapshot_date:
        row["urgency"] = "needs_dated_stock"
        return row
    if not unit or (policy_unit and policy_unit != unit) or any(x.get("unit", unit) != unit for x in inbound):
        raise ValueError("Unit mismatch: stock, demand, inbound and MOQ must use the same unit")
    if moq is not None:
        moq = finite(moq, "MOQ")
    if pack_multiple is not None and finite(pack_multiple, "pack multiple") <= 0:
        raise ValueError("Pack multiple must be positive")
    days = lead_days + review_days + buffer_days
    demand = list(demand) if demand is not None else [finite(daily_demand, "daily demand")] * days
    if len(demand) < days:
        raise ValueError("Demand must cover lead + review + buffer")
    timeline = project_inventory(free_stock, demand, inbound, snapshot_date)
    for r in timeline:
        r["buffer"] = sum(demand[r["day"]:r["day"] + buffer_days])
        r["need"] = max(0.0, r["buffer"] - r["projected_stock"])
    window = timeline[lead_days-1:lead_days+review_days]
    binding = max(window, key=lambda r:r["need"])
    raw = max(0.0, binding["need"])
    qty = max(raw, moq or 0) if raw > 1e-9 else 0.0
    if qty and pack_multiple:
        qty = float((Decimal(str(round(qty, 9))) / Decimal(str(pack_multiple))).to_integral_value(rounding=ROUND_CEILING) * Decimal(str(pack_multiple)))
    shortage = next((r["date"] for r in timeline[:lead_days+review_days] if r["projected_stock"] < -1e-9), None)
    row.update(raw_need=raw, recommended_qty=qty, shortage_date=str(shortage) if shortage else None, urgency="expedite" if shortage and shortage < snapshot_date+timedelta(days=lead_days) else "order" if qty else "covered", timeline=timeline, daily_demand=sum(demand)/len(demand), binding_date=str(binding["date"]), binding_projection=binding["projected_stock"], binding_buffer=binding["buffer"])
    row["assumptions"].append("Backlog retained; shortage date is a forecast, not an observed stockout")
    row["assumptions"].append("Snapshot assumed end-of-day; forecast projection begins the next day")
    row["assumptions"].append("Inbound ETA is expected, not guaranteed; scenario receipts occur before that day's consumption")
    if reserved is not None:
        row["assumptions"].append("Available stock used once; reservations not subtracted again")
    if any(x.get("eta") is None for x in inbound):
        row["assumptions"].append("Unknown ETA excluded from arrived supply")
    if any(x.get("eta") is not None and x["eta"] <= snapshot_date for x in inbound):
        row["assumptions"].append("Past/today pending inbound excluded: reconcile with snapshot to prevent double counting")
    return row


def explain_row(row):
    return {k:v for k,v in row.items() if k != "timeline"}
