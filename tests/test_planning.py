from datetime import date
from qor.planning import recommend_order
def test_reference_eta_and_pack():
 r=recommend_order(supplier="S",sku="1",unit="pcs",snapshot_date=date(2026,1,1),free_stock=120,daily_demand=10,inbound=[{"quantity":60,"eta":date(2026,1,11)}],lead_days=14,review_days=7,buffer_days=7,pack_multiple=24)
 assert r["raw_need"]==100 and r["recommended_qty"]==120
def test_unknown_stock_not_zero(): assert recommend_order(supplier="I",sku="1",unit="pcs",snapshot_date=date.today(),free_stock=None,daily_demand=1)["urgency"]=="needs_stock_input"
def test_late_inbound_does_not_prevent_expedite():
 r=recommend_order(supplier="S",sku="1",unit="pcs",snapshot_date=date(2026,1,1),free_stock=1,daily_demand=10,inbound=[{"quantity":100,"eta":date(2026,2,1)}])
 assert r["urgency"]=="expedite"
