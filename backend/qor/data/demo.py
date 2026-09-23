"""Visibly synthetic fixtures; no supplied supplier facts are represented here."""
from datetime import date
import pandas as pd
from qor.data.ingestion import Bundle, _audit

def demo_bundle():
    sales=[]
    for supplier,sku,unit,mult in [("Systeme Electric","SYN-0007_","pcs",1),("IEK","SYN-0010_","packs",2)]:
        for i,d in enumerate(pd.date_range("2025-01-01","2026-09-22")):
            qty=(8 + i%5) * mult * (1.2 if d.month in (6,7,8) else 1)
            if supplier=="Systeme Electric" and d==pd.Timestamp("2026-07-15"):
                qty=4000
            sales.append(dict(supplier=supplier,sku=sku,unit=unit,date=d.date(),quantity=qty,document=f"SYN-{i}",warehouse="Synthetic warehouse",event_id=f"{sku}-{i}",source=f"SYNTHETIC generated day {i}",provenance="synthetic",client_id_anonymized="synthetic-client-01" if qty==4000 else "synthetic-client-02"))
    b=Bundle(sales=pd.DataFrame(sales))
    base=dict(supplier="Systeme Electric",sku="SYN-0007_",unit="pcs",source="SYNTHETIC fixture",provenance="synthetic")
    b.stock=pd.DataFrame([dict(base,free_stock=120,as_of=b.snapshot,reserved=20)])
    b.inbound=pd.DataFrame([dict(base,quantity=60,eta=date(2026,10,2),shipment="SYN-IN-1")])
    b.policies=pd.DataFrame([dict(base,moq=1,pack_multiple=24,category="SYN-A",article="SYN-ARTICLE",ambiguous_moq=False)])
    b.manifest=[dict(file="SYNTHETIC",sheet="generated",sha256="synthetic-fixture-v2",rows=len(sales),recognized=True)]
    _audit(b)
    return b
