from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/"frontend"/"app.py"


def assert_healthy(app):
    assert not app.exception, [e.message for e in app.exception]
    assert not app.error, [e.value for e in app.error]


def test_landing_route_and_labeled_example():
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    assert_healthy(app)
    assert app.title[0].value=="Закупки без догадок"
    assert app.metric[0].value=="120 шт."
    assert any("СИНТЕТИЧЕСКИЙ" in c.value for c in app.caption)
    assert len(app.get("page_link"))>=1
    app.switch_page("app_pages/workspace.py").run()
    assert_healthy(app)
    assert app.title[0].value=="QOR — Рабочее место закупок"


def test_streamlit_synthetic_vertical_slice_and_views(tmp_path,monkeypatch):
    monkeypatch.setenv("QOR_DB_PATH",str(tmp_path/"ui.sqlite3"))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.switch_page("app_pages/workspace.py").run()
    assert_healthy(app)
    assert app.title[0].value=="QOR — Рабочее место закупок"
    app.text_input(key="actor").set_value("UI verifier")
    app.button(key="load_demo").click().run()
    assert_healthy(app)
    app.radio(key="view").set_value("Demand").run()
    app.selectbox(key="supplier").set_value("Systeme Electric").run()
    assert_healthy(app)
    assert any("СИНТЕТИЧЕСКИЙ" in w.value for w in app.warning)
    app.button(key="evaluate").click().run()
    assert_healthy(app)
    app.radio(key="view").set_value("Scenarios").run()
    app.slider(key="eta_delay").set_value(14).run()
    assert_healthy(app)
    assert len(app.dataframe[0].value)==3
    app.radio(key="view").set_value("Orders").run()
    app.button(key="calculate").click().run()
    assert_healthy(app)
    assert "статус черновик" in " ".join(c.value for c in app.caption)
    next(w for w in app.number_input if w.label=="Количество после правки").set_value(240)
    next(w for w in app.text_input if w.label=="Причина правки").set_value("Проверка синтетического сценария")
    next(b for b in app.button if b.label=="Сохранить новую версию").click().run()
    assert_healthy(app)
    app.button(key="transition").click().run()
    assert_healthy(app)
    app.button(key="transition").click().run()
    assert_healthy(app)
    app.button(key="generate_export").click().run()
    assert_healthy(app)
    assert any("совпадают" in s.value for s in app.success)
    assert app.session_state["export"][3][:2]==b"PK"


def test_streamlit_missing_stock_has_no_export(tmp_path,monkeypatch):
    monkeypatch.setenv("QOR_DB_PATH",str(tmp_path/"ui.sqlite3"))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.switch_page("app_pages/workspace.py").run()
    app.text_input(key="actor").set_value("UI verifier")
    app.button(key="load_demo").click().run()
    app.radio(key="view").set_value("Orders").run()
    app.selectbox(key="supplier").set_value("IEK").run()
    app.button(key="calculate").click().run()
    assert_healthy(app)
    assert "needs_stock_input" in app.dataframe[0].value.urgency.tolist()
    assert not any(b.key=="generate_export" for b in app.button)
