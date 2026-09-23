from datetime import date, timedelta
import pytest
from qor.contracts import Policy, StockInput
from qor.data.demo import demo_bundle
from qor.planning import recommend_order
from qor.service import calculate_plan

DAY=date(2026,9,22)

def plan(**kwargs):
    args=dict(supplier="S",sku="001",unit="pcs",snapshot_date=DAY,free_stock=0,daily_demand=10)
    args.update(kwargs)
    return recommend_order(**args)


def test_zero_stock_is_valid_but_missing_stock_blocks():
    assert plan()["recommended_qty"]==280
    assert plan(free_stock=None)["recommended_qty"] is None


def test_future_eta_does_not_erase_earlier_shortage_or_binding_need():
    r=plan(inbound=[dict(quantity=1000,eta=DAY+timedelta(days=20),unit="pcs")])
    assert r["shortage_date"]=="2026-09-23" and r["urgency"]=="expedite"
    assert r["raw_need"]==260  # day 19 + seven future buffer days; not final stock only


def test_same_day_arrival_precedes_daily_consumption():
    r=plan(free_stock=10,inbound=[dict(quantity=300,eta=DAY+timedelta(days=2),unit="pcs")])
    assert r["shortage_date"] is None and r["recommended_qty"]==0


def test_unknown_or_past_eta_not_double_counted():
    r=plan(inbound=[dict(quantity=999,eta=None),dict(quantity=999,eta=DAY)])
    assert r["raw_need"]==280
    assert any("Unknown ETA" in a for a in r["assumptions"])


def test_available_stock_reservations_not_subtracted_twice():
    assert plan(free_stock=120,reserved=50)["raw_need"]==160


@pytest.mark.parametrize("raw_stock,minimum,multiple,expected",[(279,20,12,24),(280,20,12,0),(267,1,12,24),(279.7,.4,.25,.5)])
def test_moq_and_pack_rules_are_separate(raw_stock,minimum,multiple,expected):
    assert plan(free_stock=raw_stock,moq=minimum,pack_multiple=multiple)["recommended_qty"]==pytest.approx(expected)


@pytest.mark.parametrize("kwargs",[{"free_stock":-1},{"daily_demand":float("nan")},{"pack_multiple":0},{"policy_unit":"coil"},{"inbound":[dict(quantity=1,eta=DAY+timedelta(days=1),unit="coil")]}])
def test_invalid_quantities_and_units_rejected(kwargs):
    with pytest.raises(ValueError):
        plan(**kwargs)


def test_lead_time_scenarios_change_need_and_stale_stock_blocks():
    needs=[plan(lead_days=n)["raw_need"] for n in (7,14,30)]
    assert needs==[210,280,440]
    assert plan(stock_date=DAY-timedelta(days=1))["urgency"]=="needs_dated_stock"


def test_realistic_service_missing_stock_and_category_policy():
    b=demo_bundle()
    ieks=calculate_plan(b,Policy(),keys={("IEK","SYN-0010_")})
    assert ieks[0]["urgency"]=="needs_stock_input"
    stock=StockInput(supplier="IEK",sku="SYN-0010_",unit="packs",free_stock=0,as_of=DAY,actor="tester",reason="Synthetic input")
    rows=calculate_plan(b,Policy(),keys={("IEK","SYN-0010_")},stock_inputs=[stock])
    assert rows[0]["recommended_qty"] is not None
    base=calculate_plan(b,Policy(),keys={("Systeme Electric","SYN-0007_")})[0]
    override=calculate_plan(b,Policy(category_buffers={"SYN-A":14}),keys={("Systeme Electric","SYN-0007_")})[0]
    assert override["raw_need"]>base["raw_need"]
