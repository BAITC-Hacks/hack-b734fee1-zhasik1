"""Manager workspace with cached imports and explicit calculation commits."""
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
from qor.demand.selection import select_forecast_method
from qor.planning import explain_row
from qor.service import calculate_plan, item_catalog
from qor.storage import Repository

ROOT=Path(__file__).resolve().parents[2]

@st.cache_data(max_entries=4,ttl=3600,show_spinner="Читаем и проверяем файлы поставщика…")
def cached_load(sources,snapshot):
    return load_sources(sources,snapshot=snapshot)

@st.cache_data(max_entries=8,ttl=3600,show_spinner=False)
def cached_reconcile(bundle):
    return reconcile(bundle)

@st.cache_data(max_entries=16,ttl=3600,show_spinner=False)
def cached_forecast(events,snapshot,policy,decisions,intervals,monthly,method):
    p=Policy.model_validate(policy)
    return forecast_demand(events,snapshot,p.lead_days+p.review_days+max([p.buffer_days]+list(p.category_buffers.values())),p,decisions,intervals,monthly,method=method)

@st.cache_data(max_entries=4,ttl=3600,show_spinner="Считаем проверку прогноза по времени…")
def cached_evaluation(events,snapshot,monthly,decisions):
    return evaluate(events,snapshot,monthly,decisions)

def show_table(frame,limit=300):
    if frame.empty:
        st.info("Для этого раздела нет строк.")
    else:
        st.dataframe(frame.head(limit),hide_index=True,width="stretch")
        if len(frame)>limit:
            st.caption(f"Показано {limit:,} из {len(frame):,} строк. Используйте фильтры поставщика и SKU.")

def set_bundle(bundle):
    st.session_state.bundle=bundle
    st.session_state.dataset=sha256(json.dumps(bundle.manifest,sort_keys=True).encode()).hexdigest()
    st.session_state.pop("active_run",None)

def render():
    st.session_state.setdefault("bundle",None)
    st.session_state.setdefault("policy",Policy().model_dump(mode="json"))
    repo=Repository(os.environ.get("QOR_DB_PATH",str(ROOT/"runtime"/"qor.sqlite3")))
    with st.sidebar:
        st.caption("Рабочее место закупок")
        view=st.radio("Раздел",["Data","Demand","Orders","Scenarios"],key="view",
                      format_func=lambda v:{"Data":"Источники","Demand":"Спрос","Orders":"Заказы","Scenarios":"Сценарии"}[v])
        actor=st.text_input("Ответственный менеджер",key="actor",help="Имя для локального журнала; вход и роль пока не подтверждаются.")
        st.caption("ИИ организатора: недоступен. Нет подтверждённого API, модели и ключа участника.")
    try:
        if view=="Data":
            data_view(repo,actor)
            return
        bundle=st.session_state.bundle
        if bundle is None:
            st.info("Сначала загрузите файлы поставщика в разделе «Источники».")
            return
        if any(m["file"]=="SYNTHETIC" for m in bundle.manifest):
            st.warning("СИНТЕТИЧЕСКИЙ ПРИМЕР — созданные данные, не рекомендация реальному поставщику.")
        st.caption(f"Исторический срез: {bundle.snapshot}. Даты дефицита и сроки поставки — расчётные оценки.")
        catalog=item_catalog(bundle)
        if catalog.empty:
            st.warning("SKU не найдены. Проверьте заголовки и предупреждения в разделе «Источники».")
            return
        supplier=st.selectbox("Поставщик",sorted(catalog.supplier.unique()),key="supplier")
        options=catalog[catalog.supplier==supplier].sku.tolist()
        sku=st.selectbox("Код 1С (текст)",options,key="sku")
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
    st.header("Источники и качество данных")
    st.caption("Импорт без изменения оригиналов: продажи, остатки, минимальный заказ и поставки. Поддерживаются ZIP, XLSX и UTF-8 CSV.")
    snapshot=st.date_input("Дата среза",SNAPSHOT,key="snapshot")
    supplier=st.selectbox("Поставщик загружаемых файлов",["Systeme Electric","IEK"],key="upload_supplier")
    uploads=st.file_uploader("Файлы поставщика",type=["zip","xlsx","csv"],accept_multiple_files=True,key="uploads")
    if st.button("Загрузить файлы",disabled=not uploads,key="load_uploads"):
        sources=[(f.name,f.getvalue(),supplier) for f in uploads]
        st.session_state.setdefault("sources",{})[supplier]=sources
        all_sources=[x for group in st.session_state.sources.values() for x in group]
        set_bundle(cached_load(all_sources,snapshot))
    local=Path.home()/"Downloads"/"IEK.zip"
    if local.exists() and st.button("Загрузить найденный архив IEK (Downloads)",key="load_iek"):
        st.session_state.setdefault("sources",{})["IEK"]=[(local.name,local.read_bytes(),"IEK")]
        all_sources=[x for group in st.session_state.sources.values() for x in group]
        set_bundle(cached_load(all_sources,snapshot))
    if st.button("Открыть синтетический пример",key="load_demo"):
        st.session_state.sources={}
        set_bundle(demo_bundle())
    b=st.session_state.bundle
    if b is None:
        st.info("Архив IEK найден в Downloads. Реальные файлы Systeme Electric и оригинал критериев в доступных папках не найдены. Их можно загрузить здесь.")
        return
    if any(m["file"]=="SYNTHETIC" for m in b.manifest):
        st.warning("СИНТЕТИЧЕСКИЕ данные — созданы только для проверки сценария.")
    st.caption(f"Дата загруженного среза: {b.snapshot}. Для другой даты загрузите файлы заново.")
    with st.container(horizontal=True):
        st.metric("Продажи",f"{len(b.sales):,}",border=True)
        st.metric("SKUs",f"{len(item_catalog(b)):,}",border=True)
        st.metric("Конфликтующие SKU",len(b.blocked_keys),border=True)
    show_table(pd.DataFrame(b.manifest))
    with st.expander("Предупреждения источников",expanded=True):
        for warning in b.warnings[:40]:
            st.text(warning)
    with st.expander("Нормализованные строки источников"):
        table=st.selectbox("Таблица источника",["sales","monthly","stock","inbound","policies","historical_stock"],key="source_table")
        filter_sku=st.text_input("Фильтр по коду 1С",key="source_sku")
        frame=getattr(b,table)
        if filter_sku and "sku" in frame:
            frame=frame[frame.sku.eq(filter_sku)]
        show_table(frame)
    if st.checkbox("Показать сверку месячных и транзакционных продаж",key="reconcile"):
        st.caption("Расхождения показаны отдельно; пересекающиеся объёмы не складываются. Пустые ячейки остаются неизвестными.")
        rec=cached_reconcile(b)
        if not rec.empty:
            code=st.text_input("Фильтр сверки по коду 1С",key="rec_sku")
            show_table(rec[rec.sku.eq(code)] if code else rec)
    st.subheader("Доступный остаток на дату")
    st.caption("Для IEK нужен новый остаток с датой. Исторические месячные остатки не заменяют текущий срез.")
    cat=item_catalog(b)
    if not cat.empty:
        with st.form("stock_form"):
            ident=st.selectbox("Товар",[f"{r.supplier} | {r.sku} | {r.unit}" for r in cat.itertuples()],key="stock_item")
            qty=st.number_input("Доступный остаток",min_value=0.0,value=0.0,key="stock_qty")
            asof=st.date_input("Дата учёта остатка",b.snapshot,key="stock_date")
            reason=st.text_input("Подтверждение остатка / причина",key="stock_reason")
            submit=st.form_submit_button("Сохранить остаток с датой")
        if submit:
            supplier,sku,unit=ident.split(" | ")
            record=StockInput(supplier=supplier,sku=sku,unit=unit,free_stock=qty,as_of=asof,actor=actor.strip(),reason=reason.strip())
            repo.record_input(st.session_state.dataset,"stock",record.model_dump(mode="json"))
            st.success("Остаток сохранён. Пересчитайте заказ, чтобы применить его.")

def selected_history(b,key):
    return b.sales[(b.sales.supplier==key[0]) & (b.sales.sku==key[1])].copy()

def demand_view(b,repo,actor,key,decisions,intervals):
    events=selected_history(b,key)
    cleaned=clean_demand(events,decisions=decisions,as_of=b.snapshot)
    if cleaned.empty:
        st.info("По этому SKU нет транзакционных продаж.")
        return
    daily=cleaned.groupby("date",as_index=False).agg(observed_positive=("quantity",lambda s:s[s>0].sum()),reviewed=("clean_quantity","sum"),forecast_input=("forecast_quantity","sum"))
    st.plotly_chart(px.line(daily,x="date",y=["observed_positive","reviewed","forecast_input"],title="Исходные продажи, решения менеджера и вход прогноза"))
    st.caption("Непроверенная разовая крупная продажа ограничивается только во входе прогноза. Оригинал остаётся видимым; менеджер может оставить или исключить её с причиной. Концентрация клиента проверяется лишь при наличии обезличенного ID. Возвраты учитываются отдельно.")
    if "client_id_anonymized" in cleaned and cleaned.client_id_anonymized.notna().any():
        with st.expander("Данные обезличенных клиентов (в примере ID синтетические)"):
            show_table(cleaned.groupby("client_id_anonymized",as_index=False).agg(positive_quantity=("clean_quantity","sum"),events=("event_id","size")))
    candidates=cleaned[cleaned.candidate]
    show_table(candidates[[c for c in ["date","quantity","threshold","forecast_quantity","client_candidate","document","event_id","client_id_anonymized","decision","source"] if c in candidates]])
    if not candidates.empty:
        with st.form("outlier_form"):
            event=st.selectbox("Подозрительная продажа",candidates.event_id.tolist(),key="outlier_id")
            action=st.selectbox("Решение",["keep","exclude"],key="outlier_action",
                                format_func=lambda v:{"keep":"Оставить","exclude":"Исключить"}[v])
            reason=st.text_input("Основание решения",key="outlier_reason")
            submitted=st.form_submit_button("Сохранить решение")
        if submitted:
            decision=OutlierDecision(event_id=event,action=action,decided_at=b.snapshot,actor=actor.strip(),reason=reason.strip())
            repo.record_input(st.session_state.dataset,"outlier",decision.model_dump(mode="json"))
            st.success("Решение сохранено. Пересчитайте или обновите раздел.")
    with st.expander("Подтверждённый период отсутствия товара"):
        st.caption("Укажите фактическое подтверждение. В демонстрации интервалы помечены как синтетические.")
        with st.form("stockout_form"):
            start=st.date_input("Нет товара с",date(2026,8,1),key="stockout_start")
            end=st.date_input("Нет товара по",date(2026,8,7),key="stockout_end")
            evidence=st.text_input("Подтверждающий документ",key="stockout_evidence")
            submit=st.form_submit_button("Сохранить подтверждённый период")
        if submit:
            if not actor.strip():
                raise ValueError("Укажите ответственного менеджера")
            provenance="synthetic" if set(events.provenance)=={"synthetic"} else "actual"
            record=Stockout(start=start,end=end,confirmed_at=b.snapshot,evidence=evidence.strip(),provenance=provenance)
            repo.record_input(st.session_state.dataset,"stockout",dict(supplier=key[0],sku=key[1],actor=actor,interval=record.model_dump(mode="json")))
            st.success("Период сохранён с подтверждением и происхождением данных.")
    monthly=b.monthly[(b.monthly.supplier==key[0]) & (b.monthly.sku==key[1])]
    selected_method, selection_notes=select_forecast_method(b,events,monthly,Policy.model_validate(st.session_state.policy),
                                                             decisions=decisions,stockouts=intervals.get(key,[]))
    forecast=cached_forecast(events,b.snapshot,st.session_state.policy,decisions,intervals.get(key,[]),monthly,selected_method)
    forecast["assumptions"]+=selection_notes
    st.subheader("Прогноз по дням")
    show_table(forecast["daily"])
    st.text("\n".join(forecast["assumptions"]))
    scope=st.selectbox("Охват проверки",["Selected SKU","Selected supplier / all units"],key="eval_scope",
                       format_func=lambda v:{"Selected SKU":"Выбранный SKU","Selected supplier / all units":"Все единицы выбранного поставщика"}[v])
    if st.button("Проверить прогноз на прошлых периодах",key="evaluate"):
        data=events if scope=="Selected SKU" else b.sales[b.sales.supplier==key[0]]
        results=cached_evaluation(data,b.snapshot,b.monthly,decisions)
        show_table(evaluation_metrics(results))
        st.caption("WAPE и смещение рассчитаны по наблюдённым положительным продажам; отсутствующие периоды исключены. Это не гарантия точности.")

def policy_form():
    current=Policy.model_validate(st.session_state.policy)
    with st.form("policy_form"):
        c1,c2,c3=st.columns(3)
        lead=c1.number_input("Срок поставки, дней",1,120,current.lead_days,key="lead_days")
        review=c2.number_input("Период пересмотра, дней",0,90,current.review_days,key="review_days")
        buffer=c3.number_input("Буфер, дней",0,90,current.buffer_days,key="buffer_days")
        method=st.selectbox("Метод прогноза",["auto","seasonal","mean3"],index=["auto","seasonal","mean3"].index(current.forecast_method),key="forecast_method",
                            format_func=lambda v:{"auto":"Авто по проверке","seasonal":"Сезонный","mean3":"Среднее за 3 месяца"}[v])
        mode=st.selectbox("Режим роста",["observed","file"],index=0 if current.growth_mode=="observed" else 1,key="growth_mode",
                          format_func=lambda v:{"observed":"Наблюдаемый","file":"Подтверждённый из файла"}[v])
        growth=st.number_input("Подтверждённый рост (0,10 = 10%)",-1.0,10.0,current.file_growth or 0.0,key="file_growth")
        unit=st.checkbox("Подтвердить единицу закупки = единице продаж (коэффициент 1)",value=current.accept_unit_mapping,key="units_confirmed")
        moq=st.selectbox("Поле IEK «мин. разр. к отгр.»",["minimum","multiple"],index=0 if current.iek_moq_mode=="minimum" else 1,key="moq_mode",
                         format_func=lambda v:{"minimum":"Минимальный заказ","multiple":"Кратность"}[v])
        category=st.text_input("Исходный код категории для буфера",key="category_code")
        cat_buffer=st.number_input("Буфер категории, дней",0,90,7,key="category_buffer")
        apply=st.form_submit_button("Применить параметры расчёта")
    if apply:
        overrides=dict(current.category_buffers)
        if category.strip():
            overrides[category.strip()]=cat_buffer
        st.session_state.policy=Policy(lead_days=lead,review_days=review,buffer_days=buffer,forecast_method=method,growth_mode=mode,file_growth=growth if mode=="file" else None,category_buffers=overrides,accept_unit_mapping=unit,iek_moq_mode=moq).model_dump(mode="json")
        st.success("Параметры применены. Сохранённые черновики сохраняют прежний расчёт.")

def orders_view(b,repo,actor,key,decisions,stocks,intervals):
    with st.expander("Параметры планирования",expanded=True):
        policy_form()
    all_items=st.checkbox("Рассчитать все товары выбранного поставщика",key="all_items")
    if st.button("Рассчитать и сохранить черновик",key="calculate"):
        if not actor.strip():
            raise ValueError("Укажите ответственного менеджера перед созданием черновика")
        catalog=item_catalog(b)
        keys={(key[0],s) for s in catalog.loc[catalog.supplier.eq(key[0]),"sku"]} if all_items else {key}
        with st.spinner("Рассчитываем спрос и остатки по датам…"):
            rows=calculate_plan(b,st.session_state.policy,keys=keys,stock_inputs=stocks,decisions=decisions,stockouts=intervals)
        context=dict(policy=st.session_state.policy,dataset=st.session_state.dataset,manifest=b.manifest,snapshot=str(b.snapshot))
        st.session_state.active_run=repo.create(rows,context,actor)
        st.session_state.selected_run=st.session_state.active_run
    runs=repo.list_runs()
    if not runs:
        st.info("Рассчитайте черновик, чтобы начать проверку.")
        return
    ids=[r["run_id"] for r in runs]
    active=st.session_state.get("active_run",ids[0])
    run_id=st.selectbox("Сохранённый расчёт",ids,index=ids.index(active) if active in ids else 0,key="selected_run")
    current=repo.latest(run_id)
    state_label={"draft":"черновик","review":"на проверке","approved":"утверждён","exported":"выгружен"}.get(current["state"],current["state"])
    st.caption(f"Расчёт {run_id} · версия {current['version']} · статус {state_label}")
    if current["context"].get("dataset") != st.session_state.dataset:
        st.warning("Расчёт относится к другой версии данных. Новые файлы и параметры не меняют сохранённый черновик.")
    with st.expander("Версия исходных данных и параметры расчёта"):
        st.json(current["context"],expanded=False)
    frame=pd.DataFrame([{k:v for k,v in r.items() if k not in {"timeline","inbound","forecast_history","assumptions","source_sales"}} for r in current["rows"]])
    show_table(frame)
    line=st.selectbox("Строка заказа",list(range(len(current["rows"]))),format_func=lambda i:current["rows"][i]["sku"],key=f"order_line_{run_id}")
    row=current["rows"][line]
    st.json(explain_row(row),expanded=False)
    if row.get("timeline"):
        projection=pd.DataFrame(row["timeline"])
        st.plotly_chart(px.line(projection,x="date",y=["projected_stock","buffer"],title="Прогноз остатка без нового заказа и требуемый буфер"))
    if row.get("recommended_qty") is not None:
        identity=f"{run_id}_{current['version']}_{line}"
        with st.form(f"edit_{identity}"):
            qty=st.number_input("Количество после правки",0.0,value=float(row["manager_qty"]),key=f"edit_qty_{identity}")
            reason=st.text_input("Причина правки",key=f"edit_reason_{identity}")
            submit=st.form_submit_button("Сохранить новую версию")
        if submit:
            repo.edit(run_id,current["version"],[dict(supplier=row["supplier"],sku=row["sku"],manager_qty=qty,reason=reason)],actor)
            st.rerun()
    next_state={"draft":"review","review":"approved"}.get(current["state"])
    if next_state and st.button("Передать на проверку" if next_state=="review" else "Утвердить заказ",key="transition"):
        repo.transition(run_id,current["version"],next_state,actor)
        st.rerun()
    if current["state"] in ("approved","exported"):
        fmt=st.selectbox("Формат выгрузки",["xlsx","csv"],key="export_format")
        if st.button("Создать и проверить утверждённую выгрузку",key="generate_export"):
            payload=repo.export(run_id,current["version"],fmt,actor)
            st.session_state.export=(run_id,repo.latest(run_id)["version"],fmt,payload)
            st.rerun()
    exported=st.session_state.get("export")
    if exported and exported[0]==run_id and exported[1]==current["version"] and current["state"]=="exported":
        st.success("Файл открыт повторно; значения совпадают с утверждёнными.")
        st.download_button("Скачать проверенный заказ",exported[3],f"qor_{run_id}.{exported[2]}",key="download")
    with st.expander("Журнал версий и согласования"):
        show_table(pd.DataFrame(repo.audit(run_id)))

def scenarios_view(b,key,decisions,stocks,intervals):
    policy=Policy.model_validate(st.session_state.policy)
    shift=st.slider("Задержка поставки, дней (сценарий)",0,60,0,key="eta_delay")
    lost=st.selectbox("Гипотетические дни отсутствия товара",[0,7,14],key="hypothetical_stockout")
    assign=st.checkbox("Назначить неизвестным поставкам дату в сценарии",key="assign_eta")
    eta=st.date_input("Дата прихода в сценарии",b.snapshot,key="scenario_eta") if assign else None
    st.caption("Сценарии не подтверждают фактический дефицит или доставку. Утверждённые черновики не меняются.")
    rows=[]
    for lead in (7,14,30):
        params=dict(policy.model_dump(),lead_days=lead,eta_shift_days=shift,hypothetical_stockout_days=lost,unknown_eta=eta)
        result=calculate_plan(b,params,keys={key},stock_inputs=stocks,decisions=decisions,stockouts=intervals)
        if result:
            r=result[0]
            rows.append(dict(lead_days=lead,raw_need=r.get("raw_need"),rounded_quantity=r.get("recommended_qty"),shortage_date=r.get("shortage_date"),status=r["urgency"]))
    show_table(pd.DataFrame(rows))
