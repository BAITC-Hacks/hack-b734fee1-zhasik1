"""Reproducible read-only source audit and explicitly synthetic scale benchmark.

Writes derived evidence only under --output; never changes supplier originals.
"""
import argparse
from datetime import date
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"backend"))
import numpy as np
import pandas as pd
from qor.contracts import Policy, StockInput
from qor.data import load_sources, reconcile
from qor.demand import forecast_demand, evaluate
from qor.demand.forecast import evaluation_metrics
from qor.planning import explain_row
from qor.service import calculate_plan
from qor.storage import Repository


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iek",type=Path,help="Read-only original IEK archive")
    parser.add_argument("--benchmark",type=int,default=0,help="Generated CSV rows; explicitly synthetic")
    parser.add_argument("--output",type=Path,default=Path("runtime/verification.json"))
    args=parser.parse_args()
    evidence={"source_snapshot":"2026-09-22","live_ai":"BLOCKED: no participant endpoint, authorized model, credential or documented protocol"}
    if args.iek:
        before=sha256(args.iek.read_bytes()).hexdigest()
        started=time.perf_counter(); bundle=load_sources([args.iek]); elapsed=time.perf_counter()-started
        evidence["IEK"]={"archive":str(args.iek.resolve()),"source_sha256":before,"import_seconds":round(elapsed,3),
                         "counts":{name:len(getattr(bundle,name)) for name in ("sales","monthly","stock","inbound","policies","historical_stock")},
                         "warnings":bundle.warnings,"reconciliation_rows":len(reconcile(bundle))}
        key=("IEK","200400085_")
        sales=bundle.sales[bundle.sales.supplier.eq(key[0]) & bundle.sales.sku.eq(key[1])]
        monthly=bundle.monthly[bundle.monthly.supplier.eq(key[0]) & bundle.monthly.sku.eq(key[1])]
        forecast=forecast_demand(sales,bundle.snapshot,28,monthly=monthly)
        evidence["IEK"]["observed_trace"]={"supplier":key[0],"sku":key[1],"unit":sales.iloc[0].unit,
            "transaction_rows":len(sales),"monthly_2026":monthly[monthly.month.map(lambda d:d.year==2026)][["month","quantity","source"]].to_dict("records"),
            "default_plan":calculate_plan(bundle,Policy(),keys={key})[0],
            "forecast_daily":forecast["daily"].to_dict("records"),"history":{str(k):None if pd.isna(v) else float(v) for k,v in forecast["history"].items()},
            "evaluation":evaluation_metrics(evaluate(sales,bundle.snapshot,monthly)).to_dict("records")}
        scenario_stock=StockInput(supplier=key[0],sku=key[1],unit=sales.iloc[0].unit,free_stock=0,as_of=bundle.snapshot,actor="verification script",reason="HYPOTHETICAL zero stock; not a count of IEK inventory")
        started=time.perf_counter()
        scenario=calculate_plan(bundle,Policy(accept_unit_mapping=True),keys={key},stock_inputs=[scenario_stock])[0]
        evidence["IEK"]["scenario_compute_seconds"]=round(time.perf_counter()-started,3)
        scenario["provenance"]="ACTUAL IEK demand + HYPOTHETICAL zero stock and factor-1 purchase unit mapping"
        evidence["IEK"]["hypothetical_stock_trace"]=explain_row(scenario)
        repo=Repository(args.output.parent/"verification.sqlite3")
        run=repo.create([scenario],{"verification":"scenario, not authorized supplier order","manifest":bundle.manifest},"verification script")
        repo.transition(run,1,"review","verification reviewer")
        repo.transition(run,2,"approved","verification approver")
        csv_bytes=repo.export(run,3,"csv","verification script")
        xlsx_bytes=repo.export(run,4,"xlsx","verification script")
        evidence["IEK"]["scenario_export"]={"run_id":run,"csv_bytes":len(csv_bytes),"xlsx_bytes":len(xlsx_bytes),"state":repo.latest(run)["state"],"verified_reopen":True}
        after=sha256(args.iek.read_bytes()).hexdigest()
        if before!=after:
            raise RuntimeError("Source integrity check failed")
        evidence["IEK"]["source_unchanged"]=True
        print(json.dumps({"IEK_rows":len(bundle.sales),"import_seconds":elapsed,"scenario":{k:scenario.get(k) for k in ("sku","unit","raw_need","recommended_qty","shortage_date","moq","pack_multiple")}},ensure_ascii=True),flush=True)
    if args.benchmark:
        n=args.benchmark
        # Generated records, not augmented private data or measured production sales.
        frame=pd.DataFrame({"sku":[f"SYN-{i%1000:04}" for i in range(n)],"unit":"pcs",
            "date":pd.date_range("2025-01-01",periods=n,freq="min").strftime("%Y-%m-%d"),
            "quantity":(np.arange(n)%11)+1,"document":[f"SYN-D{i}" for i in range(n)]})
        payload=frame.to_csv(index=False).encode("utf-8")
        started=time.perf_counter(); synthetic=load_sources([("synthetic.csv",payload,"Systeme Electric")]); elapsed=time.perf_counter()-started
        assert len(synthetic.sales)==n
        evidence["synthetic_csv_benchmark"]={"rows":n,"seconds":round(elapsed,3),"bytes":len(payload),"kind":"GENERATED synthetic CSV import/audit only; not XLSX or whole-supplier forecasting benchmark"}
        print(json.dumps(evidence["synthetic_csv_benchmark"]),flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(evidence,ensure_ascii=False,indent=2,default=str,allow_nan=False),encoding="utf-8")
    print("Evidence: "+str(args.output.resolve()),flush=True)


if __name__=="__main__":
    main()
