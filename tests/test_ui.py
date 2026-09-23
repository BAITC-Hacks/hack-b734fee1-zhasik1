from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/"frontend"/"app.py"


def assert_healthy(app):
    assert not app.exception, [e.message for e in app.exception]
    assert not app.error, [e.value for e in app.error]


def test_streamlit_synthetic_vertical_slice_and_views(tmp_path,monkeypatch):
    monkeypatch.setenv("QOR_DB_PATH",str(tmp_path/"ui.sqlite3"))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    assert_healthy(app)
    assert app.title[0].value=="QOR — Supplier Replenishment"
    app.text_input(key="actor").set_value("UI verifier")
    app.button(key="load_demo").click().run()
    assert_healthy(app)
    app.radio(key="view").set_value("Demand").run()
    app.selectbox(key="supplier").set_value("Systeme Electric").run()
    assert_healthy(app)
    assert any("SYNTHETIC" in w.value for w in app.warning)
    app.button(key="evaluate").click().run()
    assert_healthy(app)
    app.radio(key="view").set_value("Scenarios").run()
    app.slider(key="eta_delay").set_value(14).run()
    assert_healthy(app)
    assert len(app.dataframe[0].value)==3
    app.radio(key="view").set_value("Orders").run()
    app.button(key="calculate").click().run()
    assert_healthy(app)
    assert "state draft" in " ".join(c.value for c in app.caption)
    next(w for w in app.number_input if w.label=="Manager quantity").set_value(240)
    next(w for w in app.text_input if w.label=="Reason for adjustment").set_value("Synthetic verification adjustment")
    next(b for b in app.button if b.label=="Save adjusted version").click().run()
    assert_healthy(app)
    app.button(key="transition").click().run()
    assert_healthy(app)
    app.button(key="transition").click().run()
    assert_healthy(app)
    app.button(key="generate_export").click().run()
    assert_healthy(app)
    assert any("reopened" in s.value for s in app.success)
    assert app.session_state["export"][3][:2]==b"PK"


def test_streamlit_missing_stock_has_no_export(tmp_path,monkeypatch):
    monkeypatch.setenv("QOR_DB_PATH",str(tmp_path/"ui.sqlite3"))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.text_input(key="actor").set_value("UI verifier")
    app.button(key="load_demo").click().run()
    app.radio(key="view").set_value("Orders").run()
    app.selectbox(key="supplier").set_value("IEK").run()
    app.button(key="calculate").click().run()
    assert_healthy(app)
    assert "needs_stock_input" in app.dataframe[0].value.urgency.tolist()
    assert not any(b.key=="generate_export" for b in app.button)
