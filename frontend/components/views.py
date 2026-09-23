"""English manager interface with cached imports and explicit calculation commits."""
from datetime import date
from hashlib import sha256
import json
import os
from pathlib import Path
from zipfile import BadZipFile
import pandas as pd
import plotly.express as px
import streamlit as st
from qor.contracts import SNAPSHOT, Policy, StockInput, Stockout, OutlierDecision
from qor.data import load_sources, reconcile
from qor.data.demo import demo_bundle
from qor.demand import clean_demand, forecast_demand, evaluate
from qor.demand.forecast import evaluation_metrics
from qor.planning import explain_row
from qor.service import calculate_plan, item_catalog
from qor.storage import Repository

ROOT=Path(__file__).resolve().parents[2]

@st.cache_data(max_entries=4,ttl=3600,show_spinner="Reading and auditing supplier files…")
def cached_load(sources,snapshot):
    return load_sources(sources,snapshot=snapshot)

@st.cache_data(max_entries=8,ttl=3600,show_spinner=False)
def cached_reconcile(bundle):
    return reconcile(bundle)

@st.cache_data(max_entries=16,ttl=3600,show_spinner=False)
def cached_forecast(events,snapshot,policy,decisions,intervals,monthly):
    p=Policy.model_validate(policy)
    return forecast_demand(events,snapshot,p.lead_days+p.review_days+max([p.buffer_days]+list(p.category_buffers.values())),p,decisions,intervals,monthly)

@st.cache_data(max_entries=4,ttl=3600,show_spinner="Running rolling-origin evaluation…")
def cached_evaluation(events,snapshot,monthly,decisions):
    return evaluate(events,snapshot,monthly,decisions)

def show_table(frame,limit=300):
    if frame.empty:
        st.info("No rows for this view.")
    else:
        st.dataframe(frame.head(limit),hide_index=True,width="stretch")
        if len(frame)>limit:
            st.caption(f"Showing {limit:,} of {len(frame):,} rows. Use supplier/SKU filters.")

def set_bundle(bundle):
    st.session_state.bundle=bundle
    st.session_state.dataset=sha256(json.dumps(bundle.manifest,sort_keys=True).encode()).hexdigest()
    st.session_state.pop("active_run",None)

def render():
    st.session_state.setdefault("bundle",None)
    st.session_state.setdefault("policy",Policy().model_dump(mode="json"))
    repo=Repository(os.environ.get("QOR_DB_PATH",str(ROOT/"runtime"/"qor.sqlite3")))
    with st.sidebar:
        st.caption("Purchasing workspace")
        view=st.radio("View",["Data","Demand","Orders","Scenarios"],key="view")
        actor=st.text_input("Responsible manager",key="actor",help="Local single-user audit identity; not an authenticated role.")
        st.caption("Live AI: blocked. Participant endpoint/provider, authorized model and credential are missing.")
    try:
        if view=="Data":
            data_view(repo,actor)
            return
        bundle=st.session_state.bundle
        if bundle is None:
            st.info("Load supplier files on the Data view first.")
            return
        if any(m["file"]=="SYNTHETIC" for m in bundle.manifest):
            st.warning("SYNTHETIC WALKTHROUGH — these are generated examples, not supplier recommendations.")
        st.caption(f"Source snapshot: {bundle.snapshot}. Shortage dates and lead times are planning estimates.")
        catalog=item_catalog(bundle)
        if catalog.empty:
            st.warning("No recognized SKU data. Check headers and source warnings on Data.")
            return
        supplier=st.selectbox("Supplier",sorted(catalog.supplier.unique()),key="supplier")
        options=catalog[catalog.supplier==supplier].sku.tolist()
        sku=st.selectbox("1C SKU (text)",options,key="sku")
        key=(supplier,sku)
        dataset=st.session_state.dataset
        decisions=repo.inputs(dataset,"outlier")
        stocks=repo.inputs(dataset,"stock")
        intervals={}
        for i in repo.inputs(dataset,"stockout"):
            intervals.setdefault((i["supplier"],i["sku"]),[]).append(i["interval"])
        if view=="Demand":
            demand_view(bundle,repo,actor,key,decisions,intervals)
        elif view=="Orders":
            orders_view(bundle,repo,actor,key,decisions,stocks,intervals)
        else:
            scenarios_view(bundle,key,decisions,stocks,intervals)
    except (ValueError,TypeError,KeyError,BadZipFile,OSError) as exc:
        st.error(str(exc))

def data_view(repo,actor):
    st.header("Source data and quality")
    st.caption("Read-only import: transactions, monthly sales, available stock, MOQ and inbound shipments. ZIP/XLSX/UTF-8 CSV supported.")
    snapshot=st.date_input("Snapshot date",SNAPSHOT,key="snapshot")
    supplier=st.selectbox("Supplier for uploaded files",["Systeme Electric","IEK"],key="upload_supplier")
    uploads=st.file_uploader("Supplier files",type=["zip","xlsx","csv"],accept_multiple_files=True,key="uploads")
    if st.button("Load uploaded files",disabled=not uploads,key="load_uploads"):
        sources=[(f.name,f.getvalue(),supplier) for f in uploads]
        st.session_state.setdefault("sources",{})[supplier]=sources
        all_sources=[x for group in st.session_state.sources.values() for x in group]
        set_bundle(cached_load(all_sources,snapshot))
    local=Path.home()/"Downloads"/"IEK.zip"
    if local.exists() and st.button("Load located IEK archive (Downloads)",key="load_iek"):
        st.session_state.setdefault("sources",{})["IEK"]=[(local.name,local.read_bytes(),"IEK")]
        all_sources=[x for group in st.session_state.sources.values() for x in group]
        set_bundle(cached_load(all_sources,snapshot))
    if st.button("Open labeled synthetic walkthrough",key="load_demo"):
        st.session_state.sources={}
        set_bundle(demo_bundle())
    b=st.session_state.bundle
    if b is None:
        st.info("The real IEK archive was located in Downloads. Real Systeme Electric, case DOCX and rules PDF were not found in the audited paths. You can upload them here.")
        return
    if any(m["file"]=="SYNTHETIC" for m in b.manifest):
        st.warning("SYNTHETIC data — generated for verification only.")
    st.caption(f"Loaded dataset snapshot: {b.snapshot}. To change the snapshot, reload the files.")
    with st.container(horizontal=True):
        st.metric("Transactions",f"{len(b.sales):,}",border=True)
        st.metric("SKUs",f"{len(item_catalog(b)):,}",border=True)
        st.metric("Blocked SKU conflicts",len(b.blocked_keys),border=True)
    show_table(pd.DataFrame(b.manifest))
    with st.expander("Source warnings",expanded=True):
        for warning in b.warnings[:40]:
            st.text(warning)
    with st.expander("Inspect normalized source rows"):
        table=st.selectbox("Source table",["sales","monthly","stock","inbound","policies","historical_stock"],key="source_table")
        filter_sku=st.text_input("Source SKU filter",key="source_sku")
        frame=getattr(b,table)
        if filter_sku and "sku" in frame:
            frame=frame[frame.sku.eq(filter_sku)]
        show_table(frame)
    if st.checkbox("Show monthly/transaction reconciliation",key="reconcile"):
        st.caption("Differences are displayed; overlapping quantities are never added together. Blank monthly cells remain missing.")
        rec=cached_reconcile(b)
        if not rec.empty:
            code=st.text_input("Filter reconciliation by SKU",key="rec_sku")
            show_table(rec[rec.sku.eq(code)] if code else rec)
    st.subheader("Dated available-stock input")
    st.caption("Use a new dated stock input for IEK. Monthly opening balances cannot replace the snapshot.")
    cat=item_catalog(b)
    if not cat.empty:
        with st.form("stock_form"):
            ident=st.selectbox("Item",[f"{r.supplier} | {r.sku} | {r.unit}" for r in cat.itertuples()],key="stock_item")
            qty=st.number_input("Available stock",min_value=0.0,value=0.0,key="stock_qty")
            asof=st.date_input("Stock counted at",b.snapshot,key="stock_date")
            reason=st.text_input("Stock evidence / reason",key="stock_reason")
            submit=st.form_submit_button("Save dated stock")
        if submit:
            supplier,sku,unit=ident.split(" | ")
            record=StockInput(supplier=supplier,sku=sku,unit=unit,free_stock=qty,as_of=asof,actor=actor.strip(),reason=reason.strip())
            repo.record_input(st.session_state.dataset,"stock",record.model_dump(mode="json"))
            st.success("Stock input saved. Recalculate the order to use it.")

def selected_history(b,key):
    return b.sales[(b.sales.supplier==key[0]) & (b.sales.sku==key[1])].copy()

def demand_view(b,repo,actor,key,decisions,intervals):
    events=selected_history(b,key)
    cleaned=clean_demand(events,decisions=decisions,as_of=b.snapshot)
    if cleaned.empty:
        st.info("No transactional demand for this SKU.")
        return
    daily=cleaned.groupby("date",as_index=False).agg(observed_positive=("quantity",lambda s:s[s>0].sum()),cleaned=("clean_quantity","sum"))
    st.plotly_chart(px.line(daily,x="date",y=["observed_positive","cleaned"],title="Observed and reviewed demand"))
    st.caption("Candidates are not automatically removed. No customer claim is made without an anonymized ID. Returns stay separate.")
    if "client_id_anonymized" in cleaned and cleaned.client_id_anonymized.notna().any():
        with st.expander("Anonymized customer evidence (synthetic IDs in walkthrough)"):
            show_table(cleaned.groupby("client_id_anonymized",as_index=False).agg(positive_quantity=("clean_quantity","sum"),events=("event_id","size")))
    candidates=cleaned[cleaned.candidate]
    show_table(candidates[[c for c in ["date","quantity","threshold","document","event_id","client_id_anonymized","decision","source"] if c in candidates]])
    if not candidates.empty:
        with st.form("outlier_form"):
            event=st.selectbox("Candidate event",candidates.event_id.tolist(),key="outlier_id")
            action=st.selectbox("Decision",["keep","exclude"],key="outlier_action")
            reason=st.text_input("Decision evidence",key="outlier_reason")
            submitted=st.form_submit_button("Save demand review")
        if submitted:
            decision=OutlierDecision(event_id=event,action=action,decided_at=b.snapshot,actor=actor.strip(),reason=reason.strip())
            repo.record_input(st.session_state.dataset,"outlier",decision.model_dump(mode="json"))
            st.success("Review saved; recalculate or refresh the view to apply it.")
    with st.expander("Confirmed stockout interval"):
        st.caption("Enter actual evidence. The synthetic walkthrough stores intervals as synthetic.")
        with st.form("stockout_form"):
            start=st.date_input("Unavailable from",date(2026,8,1),key="stockout_start")
            end=st.date_input("Unavailable through",date(2026,8,7),key="stockout_end")
            evidence=st.text_input("Confirmation evidence",key="stockout_evidence")
            submit=st.form_submit_button("Save confirmed interval")
        if submit:
            if not actor.strip():
                raise ValueError("Responsible manager required")
            provenance="synthetic" if set(events.provenance)=={"synthetic"} else "actual"
            record=Stockout(start=start,end=end,confirmed_at=b.snapshot,evidence=evidence.strip(),provenance=provenance)
            repo.record_input(st.session_state.dataset,"stockout",dict(supplier=key[0],sku=key[1],actor=actor,interval=record.model_dump(mode="json")))
            st.success("Confirmed interval saved with evidence and provenance.")
    monthly=b.monthly[(b.monthly.supplier==key[0]) & (b.monthly.sku==key[1])]
    forecast=cached_forecast(events,b.snapshot,st.session_state.policy,decisions,intervals.get(key,[]),monthly)
    st.subheader("Daily forecast")
    show_table(forecast["daily"])
    st.text("\n".join(forecast["assumptions"]))
    scope=st.selectbox("Evaluation scope",["Selected SKU","Selected supplier / all units"],key="eval_scope")
    if st.button("Run time-ordered evaluation",key="evaluate"):
        data=events if scope=="Selected SKU" else b.sales[b.sales.supplier==key[0]]
        results=cached_evaluation(data,b.snapshot,b.monthly,decisions)
        show_table(evaluation_metrics(results))
        st.caption("WAPE and signed bias measure observed positive sales; missing targets excluded. No production guarantee; intermittent items may have too few observations.")

def policy_form():
    current=Policy.model_validate(st.session_state.policy)
    with st.form("policy_form"):
        c1,c2,c3=st.columns(3)
        lead=c1.number_input("Lead time (days)",1,120,current.lead_days,key="lead_days")
        review=c2.number_input("Review cycle (days)",0,90,current.review_days,key="review_days")
        buffer=c3.number_input("Buffer (days)",0,90,current.buffer_days,key="buffer_days")
        method=st.selectbox("Forecast method (compare time-ordered metrics first)",["seasonal","mean3"],index=0 if current.forecast_method=="seasonal" else 1,key="forecast_method")
        mode=st.selectbox("Growth mode",["observed","file"],index=0 if current.growth_mode=="observed" else 1,key="growth_mode")
        growth=st.number_input("Confirmed file growth fraction (0.10 = 10%)",-1.0,10.0,current.file_growth or 0.0,key="file_growth")
        unit=st.checkbox("Confirm unitless purchase quantities use sales units (factor 1)",value=current.accept_unit_mapping,key="units_confirmed")
        moq=st.selectbox("IEK ambiguous dispatch field interpretation",["minimum","multiple"],index=0 if current.iek_moq_mode=="minimum" else 1,key="moq_mode")
        category=st.text_input("Raw category for buffer override",key="category_code")
        cat_buffer=st.number_input("Category buffer days",0,90,7,key="category_buffer")
        apply=st.form_submit_button("Apply calculation assumptions")
    if apply:
        overrides=dict(current.category_buffers)
        if category.strip():
            overrides[category.strip()]=cat_buffer
        st.session_state.policy=Policy(lead_days=lead,review_days=review,buffer_days=buffer,forecast_method=method,growth_mode=mode,file_growth=growth if mode=="file" else None,category_buffers=overrides,accept_unit_mapping=unit,iek_moq_mode=moq).model_dump(mode="json")
        st.success("Assumptions applied. Existing saved drafts retain their previous calculation.")

def orders_view(b,repo,actor,key,decisions,stocks,intervals):
    with st.expander("Planning assumptions",expanded=True):
        policy_form()
    all_items=st.checkbox("Calculate all items for selected supplier",key="all_items")
    if st.button("Calculate and save draft",key="calculate"):
        if not actor.strip():
            raise ValueError("Enter the responsible manager before creating a draft")
        catalog=item_catalog(b)
        keys={(key[0],s) for s in catalog.loc[catalog.supplier.eq(key[0]),"sku"]} if all_items else {key}
        with st.spinner("Calculating demand and inventory by date…"):
            rows=calculate_plan(b,st.session_state.policy,keys=keys,stock_inputs=stocks,decisions=decisions,stockouts=intervals)
        context=dict(policy=st.session_state.policy,dataset=st.session_state.dataset,manifest=b.manifest,snapshot=str(b.snapshot))
        st.session_state.active_run=repo.create(rows,context,actor)
        st.session_state.selected_run=st.session_state.active_run
    runs=repo.list_runs()
    if not runs:
        st.info("Calculate a draft to begin manager review.")
        return
    ids=[r["run_id"] for r in runs]
    active=st.session_state.get("active_run",ids[0])
    run_id=st.selectbox("Saved calculation",ids,index=ids.index(active) if active in ids else 0,key="selected_run")
    current=repo.latest(run_id)
    st.caption(f"Run {run_id} · version {current['version']} · state {current['state']}")
    if current["context"].get("dataset") != st.session_state.dataset:
        st.warning("This saved calculation belongs to a different dataset version. Current uploads and policy changes do not recalculate it.")
    with st.expander("Saved input version and calculation policy"):
        st.json(current["context"],expanded=False)
    frame=pd.DataFrame([{k:v for k,v in r.items() if k not in {"timeline","inbound","forecast_history","assumptions","source_sales"}} for r in current["rows"]])
    show_table(frame)
    line=st.selectbox("Inspect order line",list(range(len(current["rows"]))),format_func=lambda i:current["rows"][i]["sku"],key=f"order_line_{run_id}")
    row=current["rows"][line]
    st.json(explain_row(row),expanded=False)
    if row.get("timeline"):
        projection=pd.DataFrame(row["timeline"])
        st.plotly_chart(px.line(projection,x="date",y=["projected_stock","buffer"],title="Projected stock without new order and required buffer"))
    if row.get("recommended_qty") is not None:
        identity=f"{run_id}_{current['version']}_{line}"
        with st.form(f"edit_{identity}"):
            qty=st.number_input("Manager quantity",0.0,value=float(row["manager_qty"]),key=f"edit_qty_{identity}")
            reason=st.text_input("Reason for adjustment",key=f"edit_reason_{identity}")
            submit=st.form_submit_button("Save adjusted version")
        if submit:
            repo.edit(run_id,current["version"],[dict(supplier=row["supplier"],sku=row["sku"],manager_qty=qty,reason=reason)],actor)
            st.rerun()
    next_state={"draft":"review","review":"approved"}.get(current["state"])
    if next_state and st.button(f"Move to {next_state}",key="transition"):
        repo.transition(run_id,current["version"],next_state,actor)
        st.rerun()
    if current["state"] in ("approved","exported"):
        fmt=st.selectbox("Export format",["xlsx","csv"],key="export_format")
        if st.button("Generate and reopen approved export",key="generate_export"):
            payload=repo.export(run_id,current["version"],fmt,actor)
            st.session_state.export=(run_id,repo.latest(run_id)["version"],fmt,payload)
            st.rerun()
    exported=st.session_state.get("export")
    if exported and exported[0]==run_id and exported[1]==current["version"] and current["state"]=="exported":
        st.success("Export reopened and compared with approved values.")
        st.download_button("Download verified order",exported[3],f"qor_{run_id}.{exported[2]}",key="download")
    with st.expander("Version and approval audit"):
        show_table(pd.DataFrame(repo.audit(run_id)))

def scenarios_view(b,key,decisions,stocks,intervals):
    policy=Policy.model_validate(st.session_state.policy)
    shift=st.slider("Delay inbound ETA (scenario days)",0,60,0,key="eta_delay")
    lost=st.selectbox("Hypothetical unknown stockout days",[0,7,14],key="hypothetical_stockout")
    assign=st.checkbox("Assign unknown ETAs in this scenario",key="assign_eta")
    eta=st.date_input("Scenario arrival date",b.snapshot,key="scenario_eta") if assign else None
    st.caption("Scenario changes are not actual stockout or delivery facts. Saved approved drafts are unchanged.")
    rows=[]
    for lead in (7,14,30):
        params=dict(policy.model_dump(),lead_days=lead,eta_shift_days=shift,hypothetical_stockout_days=lost,unknown_eta=eta)
        result=calculate_plan(b,params,keys={key},stock_inputs=stocks,decisions=decisions,stockouts=intervals)
        if result:
            r=result[0]
            rows.append(dict(lead_days=lead,raw_need=r.get("raw_need"),rounded_quantity=r.get("recommended_qty"),shortage_date=r.get("shortage_date"),status=r["urgency"]))
    show_table(pd.DataFrame(rows))
