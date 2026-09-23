"""Private, local IEK UI smoke test. No approval or actual order is submitted."""
import os
from pathlib import Path
import tempfile
from streamlit.testing.v1 import AppTest


def healthy(app):
    assert not app.exception,[e.message for e in app.exception]
    assert not app.error,[e.value for e in app.error]


def main():
    root=Path(__file__).resolve().parents[1]
    archive=Path.home()/"Downloads"/"IEK.zip"
    if not archive.is_file():
        raise SystemExit("NOT RUN: Downloads/IEK.zip absent")
    previous=os.environ.get("QOR_DB_PATH")
    try:
        with tempfile.TemporaryDirectory(prefix="qor-ui-verification-") as temp:
            os.environ["QOR_DB_PATH"]=str(Path(temp)/"qor.sqlite3")
            app=AppTest.from_file(str(root/"frontend"/"app.py"),default_timeout=90).run()
            app.switch_page("app_pages/workspace.py").run()
            app.text_input(key="actor").set_value("Local UI test; no order approval")
            app.button(key="load_iek").click().run()
            healthy(app)
            assert len(app.session_state["bundle"].sales)>=170000
            app.radio(key="view").set_value("Demand").run()
            app.selectbox(key="sku").set_value("200400085_").run()
            healthy(app)
            app.button(key="evaluate").click().run()
            healthy(app)
            app.radio(key="view").set_value("Orders").run()
            app.button(key="calculate").click().run()
            healthy(app)
            assert app.dataframe[0].value.iloc[0].urgency=="needs_stock_input"
            assert not any(b.key=="generate_export" for b in app.button)
            app.radio(key="view").set_value("Scenarios").run()
            healthy(app)
            assert set(app.dataframe[0].value.status)=={"needs_stock_input"}
            print("PASS: real IEK import, Demand/evaluation, Orders missing-stock gate, 7/14/30 scenarios; zero app exceptions; no approval/export")
    finally:
        if previous is None:
            os.environ.pop("QOR_DB_PATH",None)
        else:
            os.environ["QOR_DB_PATH"]=previous


if __name__=="__main__":
    main()
