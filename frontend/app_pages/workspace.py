"""The existing manager workspace, exposed as a first-class page."""
import streamlit as st

from components.views import render


st.title("QOR — Рабочее место закупок")
st.caption("Локальный расчёт · проверка черновиков · согласование и выгрузка")
render()
