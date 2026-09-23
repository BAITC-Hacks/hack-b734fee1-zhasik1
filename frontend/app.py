"""QOR application entry point: public product page and purchasing workspace."""

from pathlib import Path
import sys

import streamlit as st

# Keep the preserved root-level legacy package from shadowing the scaffold.
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) in sys.path:
    sys.path.remove(str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR))

# Remove legacy package modules only when this entry point was launched after them.
loaded_qor = sys.modules.get("qor")
if loaded_qor and not str(getattr(loaded_qor, "__file__", "")).startswith(str(BACKEND_DIR)):
    for name in list(sys.modules):
        if name == "qor" or name.startswith("qor."):
            del sys.modules[name]

FRONTEND_DIR = Path(__file__).resolve().parent
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(1, str(FRONTEND_DIR))
from qor.contracts import Policy


st.set_page_config(
    page_title="QOR — Закупки без догадок",
    page_icon=":material/inventory_2:",
    layout="wide",
    initial_sidebar_state="auto",
)

# These values belong to the visitor's workspace and survive navigation.
st.session_state.setdefault("bundle", None)
st.session_state.setdefault("policy", Policy().model_dump(mode="json"))

page = st.navigation(
    [
        st.Page("app_pages/landing.py", title="Главная", icon=":material/home:", url_path="", default=True),
        st.Page("app_pages/workspace.py", title="Закупки", icon=":material/inventory_2:", url_path="workspace"),
    ],
    position="top",
)
page.run()
