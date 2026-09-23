from datetime import date
import io, uuid
import pandas as pd
import streamlit as st
from openpyxl import Workbook
from qor.data import load_table, normalize_columns, validate_table
from qor.demand import clean_demand, forecast_daily
from qor.planning import recommend_order
from qor.storage import init_db, transition

st.set_page_config(page_title="QOR | Supplier orders", layout="wide")
st.session_state.setdefault("recommendations", [])
st.session_state.setdefault("run_id", str(uuid.uuid4()))
st.title("QOR: explainable supplier-order drafts")
st.caption("Demo snapshot: 22 Sep 2026. Missing data remains missing; AI model access is pending verification.")

with st.sidebar:
    st.header("Planning scenario")
    lead=st.selectbox("Lead time (days)",[7,14,30],index=1,key="lead")
    review=st.number_input("Review cycle (days)",0,90,7,key="review")
    buffer=st.number_input("Buffer (days)",0,90,7,key="buffer")
    demo=st.toggle("Use labeled synthetic walkthrough",value=False,key="demo")

tab_data, tab_demand, tab_orders, tab_scenario=st.tabs(["Data quality", "Demand & outliers", "Order drafts", "Scenario comparison"])
with tab_data:
    uploads=st.file_uploader("Upload IEK / Systeme Electric XLSX or CSV files",type=["xlsx","xls","csv"],accept_multiple_files=True)
    if uploads:
        rows=[]
        for item in uploads:
            try:
                df=normalize_columns(load_table(item.getvalue() if item.name.endswith(("xlsx","xls")) else item.getvalue()))
                rows.append({"file":item.name,"rows":len(df),"columns":", ".join(df.columns),"issues":"; ".join(validate_table(df,["sku","unit"])) or "none"})
            except Exception as exc: rows.append({"file":item.name,"rows":0,"columns":"","issues":str(exc)})
        st.dataframe(pd.DataFrame(rows),hide_index=True)
    else: st.info("No source archives are present in this workspace. Upload supplier files, or enable the explicitly synthetic walkthrough.")

def synthetic_events():
    dates=pd.date_range("2025-01-01",periods=240,freq="D")
    q=[10.0]*240; q[120]=500.0
    return pd.DataFrame({"date":dates,"quantity":q,"supplier":"Systeme Electric","sku":"0007_","unit":"pcs"})

with tab_demand:
    if demo:
        raw=synthetic_events(); cleaned=clean_demand(raw,exclude_outliers=True); fc=forecast_daily(cleaned,pd.Timestamp("2026-09-22"))
        st.warning("Synthetic walkthrough only: no supplied supplier source data is being shown.")
        st.metric("Daily demand forecast",f"{fc['daily_demand']:.2f} pcs/day",border=True)
        st.line_chart(raw.set_index("date")[["quantity"]])
        st.dataframe(raw.assign(outlier=~raw.index.isin(cleaned.index)).query("outlier"),hide_index=True)
    else: st.info("Upload data or enable the labeled synthetic walkthrough to inspect cleaning and demand.")

with tab_orders:
    if demo:
        fc=forecast_daily(clean_demand(synthetic_events()),pd.Timestamp("2026-09-22"))
        result=recommend_order(supplier="Systeme Electric",sku="0007_",unit="pcs",snapshot_date=date(2026,9,22),free_stock=120,daily_demand=fc["daily_demand"],inbound=[{"quantity":60,"eta":date(2026,10,2)}],lead_days=lead,review_days=review,buffer_days=buffer,pack_multiple=24,calculation_run_id=st.session_state.run_id)
        st.session_state.recommendations=[result]
        display=pd.DataFrame([{k:v for k,v in result.items() if k not in {"timeline"}}])
        edited=st.data_editor(display,disabled=[c for c in display.columns if c not in {"recommended_qty"}],key="orders_editor",hide_index=True)
        st.json({"calculation":result["timeline"],"assumptions":result["assumptions"]})
        state=st.selectbox("Manager state",["draft","review","approved"],key="order_state")
        reason=st.text_input("Edit / approval reason",key="reason")
        if st.button("Record manager decision",key="record"):
            transition(init_db(),st.session_state.run_id,state,edited.to_dict("records"),reason); st.success(f"Recorded {state}; export is enabled only after approval.")
        if state=="approved":
            safe=edited.map(lambda x: "'"+x if isinstance(x,str) and x[:1] in "=+-@" else x)
            st.download_button("Export approved CSV",safe.to_csv(index=False).encode(),"qor_order_draft.csv","text/csv",key="export")
            book=Workbook(); ws=book.active; ws.title="Approved order"
            ws.append(list(safe.columns)); [ws.append(list(row)) for row in safe.itertuples(index=False,name=None)]
            payload=io.BytesIO(); book.save(payload)
            st.download_button("Export approved XLSX",payload.getvalue(),"qor_order_draft.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",key="export_xlsx")
    else: st.info("Order drafts require loaded data; the available walkthrough is visibly synthetic.")
with tab_scenario:
    if demo:
        rows=[]
        for l in (7,14,30):
            r=recommend_order(supplier="Systeme Electric",sku="0007_",unit="pcs",snapshot_date=date(2026,9,22),free_stock=120,daily_demand=10,inbound=[{"quantity":60,"eta":date(2026,10,2)}],lead_days=l,review_days=7,buffer_days=7,pack_multiple=24)
            rows.append({"lead_days":l,"raw_need":r["raw_need"],"recommended_qty":r["recommended_qty"],"urgency":r["urgency"]})
        st.dataframe(pd.DataFrame(rows),hide_index=True)
    else: st.info("Scenario values are shown after data load or the synthetic switch.")
st.divider()
st.caption("AI assistant: pending - no HackAlem participant model endpoint, model ID, or credential has been verified. Deterministic planning remains available.")
